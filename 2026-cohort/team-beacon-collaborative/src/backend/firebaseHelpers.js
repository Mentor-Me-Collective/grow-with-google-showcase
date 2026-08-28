import {
  collection,
  doc,
  getDoc,
  getDocs,
  addDoc,
  setDoc,
  updateDoc,
  query,
  where,
  runTransaction,
} from "https://www.gstatic.com/firebasejs/12.17.0/firebase-firestore.js";

/**
 * Creates the pending organization and user profile
 * for a newly registered Donor or Recipient.
 * Organization approval remains an Admin action.
 */
export async function createPendingAccountProfile(
  db,
  auth,
  { role, displayName, organizationName, profile }
) {
  const user = auth.currentUser;

  if (!user) throw new Error("User must be signed in.");
  if (!["donor", "recipient"].includes(role)) {
    throw new Error("Invalid account role.");
  }

  const organizationRef = doc(collection(db, "organizations"));

  await setDoc(organizationRef, {
    name: organizationName.trim(),
    type: role,
    verificationStatus: "pending",
    createdBy: user.uid,
  });

  await setDoc(doc(db, "users", user.uid), {
    role,
    accountStatus: "active",
    displayName: displayName.trim(),
    organizationId: organizationRef.id,
    profile,
  });

  return {
    userId: user.uid,
    organizationId: organizationRef.id,
    verificationStatus: "pending",
  };
}

/**
 * Returns the signed-in user's Firestore profile.
 */
export async function getCurrentUserProfile(db, auth) {
  const user = auth.currentUser;

  if (!user) {
    throw new Error("User must be signed in.");
  }

  const userRef = doc(db, "users", user.uid);
  const snapshot = await getDoc(userRef);

  if (!snapshot.exists()) {
    throw new Error("User profile does not exist.");
  }

  return {
    id: snapshot.id,
    ...snapshot.data(),
  };
}

/**
 * Creates a new donation for the signed-in donor.
 *
 * Security Rules still enforce:
 * - active account
 * - donor role
 * - approved organization
 * - matching organizationId
 * - matching createdBy UID
 * - initial status = available
 */

async function geocodeChicagoAddress(address) {
  const rawAddress = String(address || "").trim();

  if (!rawAddress) {
    return null;
  }

  const queryAddress =
    /chicago|illinois|\bil\b/i.test(rawAddress)
      ? rawAddress
      : `${rawAddress}, Chicago, Illinois`;

  const url = new URL(
    "https://nominatim.openstreetmap.org/search"
  );

  url.searchParams.set("q", queryAddress);
  url.searchParams.set("format", "jsonv2");
  url.searchParams.set("limit", "1");
  url.searchParams.set("countrycodes", "us");
  url.searchParams.set(
    "viewbox",
    "-87.9401,42.0230,-87.5237,41.6445"
  );
  url.searchParams.set("bounded", "1");

  const response = await fetch(url.toString(), {
    headers: {
      Accept: "application/json",
      "Accept-Language": "en"
    }
  });

  if (!response.ok) {
    throw new Error(
      `Address geocoding failed (${response.status}).`
    );
  }

  const matches = await response.json();
  const match = matches[0];

  if (!match) {
    return null;
  }

  const latitude = Number(match.lat);
  const longitude = Number(match.lon);

  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude)
  ) {
    return null;
  }

  return {
    address: rawAddress,
    latitude,
    longitude,
    displayName: match.display_name || rawAddress,
    source: "OpenStreetMap Nominatim"
  };
}

export async function createDonation(
  db,
  auth,
  {
    title,
    description,
    quantity,
    photos = [],
  }
) {
  const user = auth.currentUser;

  if (!user) {
    throw new Error("User must be signed in.");
  }

  const profile =
    await getCurrentUserProfile(db, auth);

  if (profile.role !== "donor") {
    throw new Error(
      "Only donor accounts can create donations."
    );
  }

  const pickupAddress =
    String(
      profile.profile?.business?.bizAddress || ""
    ).trim();

  let pickupLocation = null;

  if (pickupAddress) {
    try {
      pickupLocation =
        await geocodeChicagoAddress(pickupAddress);
    } catch (error) {
      console.warn(
        "Could not geocode donation pickup address:",
        error
      );
    }
  }

  const donation = {
    organizationId: profile.organizationId,
    createdBy: user.uid,
    status: "available",
    title: title.trim(),
    description: description.trim(),
    quantity: quantity.trim(),
    photos: Array.isArray(photos) ? photos : [],
    pickupAddress,
    pickupLocation,
  };

  const donationRef = await addDoc(
    collection(db, "donations"),
    donation
  );

  return {
    id: donationRef.id,
    ...donation,
  };
}

/**
 * Returns donations created by the signed-in donor.
 */
export async function getMyDonations(db, auth) {
  const user = auth.currentUser;

  if (!user) {
    throw new Error("User must be signed in.");
  }

  const profile =
    await getCurrentUserProfile(db, auth);

  if (profile.role !== "donor") {
    throw new Error(
      "Only donor accounts can view donor donations."
    );
  }

  const donationsQuery = query(
    collection(db, "donations"),
    where("createdBy", "==", user.uid)
  );

  const snapshot = await getDocs(donationsQuery);

  return snapshot.docs.map((donationDoc) => ({
    id: donationDoc.id,
    ...donationDoc.data(),
  }));
}

/**
 * Returns donations currently marked available.
 *
 * Firestore Security Rules determine whether
 * the current user is permitted to read them.
 */
export async function getAvailableDonations(db) {
  const donationsQuery = query(
    collection(db, "donations"),
    where("status", "==", "available")
  );

  const snapshot =
    await getDocs(donationsQuery);

  return snapshot.docs.map((item) => ({
    id: item.id,
    ...item.data(),
  }));
}

/**
 * Atomically reserves one donation.
 *
 * The reservation document ID intentionally equals
 * the donation document ID.
 *
 * Both writes succeed together:
 *
 * donations/{donationId}
 * status: available -> reserved
 *
 * reservations/{donationId}
 * new active reservation
 *
 * Security Rules independently enforce the same
 * relationship with getAfter().
 */
export async function reserveDonation(
  db,
  auth,
  donationId
) {
  const user = auth.currentUser;

  if (!user) {
    throw new Error("User must be signed in.");
  }

  const profile =
    await getCurrentUserProfile(db, auth);

  if (profile.role !== "recipient") {
    throw new Error(
      "Only recipient accounts can reserve donations."
    );
  }

  const donationRef = doc(
    db,
    "donations",
    donationId
  );

  const reservationRef = doc(
    db,
    "reservations",
    donationId
  );

  const conversationRef = doc(
    db,
    "conversations",
    donationId
  );

  await runTransaction(
    db,
    async (transaction) => {
      const donationSnapshot =
        await transaction.get(donationRef);

      if (!donationSnapshot.exists()) {
        throw new Error(
          "Donation does not exist."
        );
      }

      const donation =
        donationSnapshot.data();

      if (donation.status !== "available") {
        throw new Error(
          "Donation is no longer available."
        );
      }

      transaction.update(
        donationRef,
        {
          status: "reserved",
        }
      );

      transaction.set(
        reservationRef,
        {
          donationId,
          recipientOrganizationId:
            profile.organizationId,
          createdBy: user.uid,
          status: "active",
        }
      );

      transaction.set(
        conversationRef,
        {
          donationId,
          donorUid: donation.createdBy,
          recipientUid: user.uid,
          participants: [
            donation.createdBy,
            user.uid,
          ],
        }
      );
    }
  );

  return {
    donationId,
    reservationId: donationId,
    status: "active",
  };
}

/**
 * Returns reservations belonging to the signed-in
 * recipient organization.
 */
export async function getMyReservations(
  db,
  auth
) {
  const user = auth.currentUser;

  if (!user) {
    throw new Error("User must be signed in.");
  }

  const profile =
    await getCurrentUserProfile(db, auth);

  if (profile.role !== "recipient") {
    throw new Error(
      "Only recipient accounts have recipient reservations."
    );
  }

  const reservationsQuery = query(
    collection(db, "reservations"),
    where(
      "recipientOrganizationId",
      "==",
      profile.organizationId
    ),
    where("createdBy", "==", user.uid)
  );

  const snapshot =
    await getDocs(reservationsQuery);

  return snapshot.docs.map((item) => ({
    id: item.id,
    ...item.data(),
  }));
}
/**
 * Returns recipient reservations with their donation details.
 */
export async function getMyReservationDetails(db, auth) {
  const reservations =
    await getMyReservations(db, auth);

  return Promise.all(
    reservations.map(async (reservation) => {
      const donationSnapshot = await getDoc(
        doc(db, "donations", reservation.donationId)
      );

      return {
        ...reservation,
        donation: donationSnapshot.exists()
          ? {
              id: donationSnapshot.id,
              ...donationSnapshot.data(),
            }
          : null,
      };
    })
  );
}


/**
 * Returns messages for one reservation conversation.
 */
export async function getConversationMessages(db, auth, conversationId) {
  const user = auth.currentUser;

  if (!user) {
    throw new Error("User must be signed in.");
  }

  const messagesQuery = query(
    collection(db, "messages"),
    where("conversationId", "==", conversationId)
  );

  const snapshot = await getDocs(messagesQuery);

  return snapshot.docs
    .map((messageDoc) => ({
      id: messageDoc.id,
      ...messageDoc.data(),
    }))
    .sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
}

/**
 * Sends a message in one reservation conversation.
 */
export async function sendConversationMessage(
  db,
  auth,
  { conversationId, senderName, senderRole, senderEmail, text }
) {
  const user = auth.currentUser;

  if (!user) {
    throw new Error("User must be signed in.");
  }

  const cleanText = String(text || "").trim();
  if (!cleanText) {
    throw new Error("Message cannot be empty.");
  }

  const messageRef = await addDoc(
    collection(db, "messages"),
    {
      conversationId,
      senderUid: user.uid,
      senderName,
      senderRole,
      senderEmail,
      text: cleanText,
      timestamp: Date.now(),
    }
  );

  return {
    id: messageRef.id,
    conversationId,
    senderUid: user.uid,
    senderName,
    senderRole,
    senderEmail,
    text: cleanText,
  };
}

/**
 * Saves editable profile data for the signed-in user.
 */
export async function saveUserProfile(db, auth, { displayName, profile }) {
  const user = auth.currentUser;

  if (!user) {
    throw new Error("User must be signed in.");
  }

  const userRef = doc(db, "users", user.uid);

  await updateDoc(userRef, {
    displayName: String(displayName || "").trim(),
    profile: profile || {},
  });

  return {
    displayName: String(displayName || "").trim(),
    profile: profile || {},
  };
}

/**
 * Saves non-sensitive settings for the signed-in user.
 */
export async function saveUserSettings(db, auth, settings) {
  const user = auth.currentUser;

  if (!user) {
    throw new Error("User must be signed in.");
  }

  const userRef = doc(db, "users", user.uid);

  await updateDoc(userRef, {
    "profile.settings": {
      notifyEmail: Boolean(settings?.notifyEmail),
      notifySms: Boolean(settings?.notifySms),
    },
  });

  return {
    notifyEmail: Boolean(settings?.notifyEmail),
    notifySms: Boolean(settings?.notifySms),
  };
}

/**
 * Approves an organization.
 *
 * This is intended for an authenticated admin.
 * Firestore Security Rules provide the authoritative
 * authorization check.
 */
export async function approveOrganization(
  db,
  organizationId
) {
  const organizationRef = doc(
    db,
    "organizations",
    organizationId
  );

  await updateDoc(
    organizationRef,
    {
      verificationStatus: "approved",
    }
  );

  return {
    organizationId,
    verificationStatus: "approved",
  };
}

/**
 * Rejects an organization.
 *
 * Firestore Security Rules restrict organization
 * updates to admins.
 */
export async function rejectOrganization(
  db,
  organizationId
) {
  const organizationRef = doc(
    db,
    "organizations",
    organizationId
  );

  await updateDoc(
    organizationRef,
    {
      verificationStatus: "rejected",
    }
  );

  return {
    organizationId,
    verificationStatus: "rejected",
  };
}

