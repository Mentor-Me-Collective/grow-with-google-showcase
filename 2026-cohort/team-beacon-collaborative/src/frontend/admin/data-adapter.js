import {
  collection,
  doc,
  getDocs,
  updateDoc,
  writeBatch,
} from "https://www.gstatic.com/firebasejs/12.17.0/firebase-firestore.js";

import {
  onAuthStateChanged,
} from "https://www.gstatic.com/firebasejs/12.17.0/firebase-auth.js";

import {
  auth,
  db,
} from "../../backend/firebaseConfig.js";

import {
  logout,
} from "../../backend/authHelpers.js";

import {
  getCurrentUserProfile,
  approveOrganization,
  rejectOrganization,
} from "../../backend/firebaseHelpers.js";

function waitForAuth() {
  return new Promise((resolve) => {
    if (auth.currentUser) {
      resolve(auth.currentUser);
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, (user) => {
      unsubscribe();
      resolve(user);
    });
  });
}

async function requireAdmin() {
  const user = await waitForAuth();

  if (!user) {
    throw new Error("ADMIN_AUTH_REQUIRED");
  }

  const profile = await getCurrentUserProfile(db, auth);

  if (
    profile?.role !== "admin" ||
    profile?.accountStatus !== "active"
  ) {
    throw new Error("ADMIN_ACCESS_DENIED");
  }

  return {
    user,
    profile,
  };
}

async function readCollection(name) {
  const snapshot = await getDocs(collection(db, name));

  return snapshot.docs.map((item) => ({
    id: item.id,
    ...item.data(),
  }));
}

async function getAdminSnapshot() {
  await requireAdmin();

  const [
    users,
    organizations,
    donations,
    reservations,
  ] = await Promise.all([
    readCollection("users"),
    readCollection("organizations"),
    readCollection("donations"),
    readCollection("reservations"),
  ]);

  return {
    users,
    organizations,
    donations,
    reservations,
  };
}

async function setOrganizationStatus(
  organizationId,
  status
) {
  await requireAdmin();

  if (status === "approved") {
    return approveOrganization(db, organizationId);
  }

  if (status === "rejected") {
    return rejectOrganization(db, organizationId);
  }

  throw new Error("Unsupported organization status.");
}

async function setUserAccountStatus(
  userId,
  accountStatus
) {
  await requireAdmin();

  if (!["active", "suspended"].includes(accountStatus)) {
    throw new Error("Unsupported account status.");
  }

  await updateDoc(
    doc(db, "users", userId),
    { accountStatus }
  );

  return {
    userId,
    accountStatus,
  };
}

async function completePickup(reservationId) {
  await requireAdmin();

  const batch = writeBatch(db);

  batch.update(
    doc(db, "reservations", reservationId),
    { status: "picked_up" }
  );

  batch.update(
    doc(db, "donations", reservationId),
    { status: "picked_up" }
  );

  await batch.commit();

  return {
    reservationId,
    status: "picked_up",
  };
}

async function signOutAdmin() {
  await logout(auth);
}

window.NourishShareAdminData = {
  requireAdmin,
  getAdminSnapshot,
  setOrganizationStatus,
  setUserAccountStatus,
  completePickup,
  signOutAdmin,
};
