import {
  connectAuthEmulator,
  onAuthStateChanged,
  EmailAuthProvider,
  reauthenticateWithCredential,
  updatePassword,
} from "https://www.gstatic.com/firebasejs/12.17.0/firebase-auth.js";

import {
  connectFirestoreEmulator,
} from "https://www.gstatic.com/firebasejs/12.17.0/firebase-firestore.js";

import {
  auth,
  db,
} from "../../../backend/firebaseConfig.js";

import {
  registerWithEmail,
  logout as logoutFirebase,
} from "../../../backend/authHelpers.js?v=20260823f";

import {
  createPendingAccountProfile,
  getAvailableDonations,
  reserveDonation,
  getMyReservationDetails,
  getConversationMessages,
  sendConversationMessage,
  getCurrentUserProfile,
  saveUserProfile,
  saveUserSettings,
} from "../../../backend/firebaseHelpers.js?v=20260823f";

const isLocalDevelopment =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1";

if (isLocalDevelopment && !auth.emulatorConfig) {
  connectAuthEmulator(
    auth,
    "http://127.0.0.1:9099",
    { disableWarnings: true }
  );
}

if (isLocalDevelopment) {
  try {
    connectFirestoreEmulator(
      db,
      "127.0.0.1",
      8080
    );
  } catch (error) {
    if (!String(error?.message).includes("already been called")) {
      throw error;
    }
  }
}

function waitForAuthReady() {
  if (auth.currentUser) {
    return Promise.resolve(auth.currentUser);
  }

  return new Promise((resolve) => {
    const unsubscribe = onAuthStateChanged(
      auth,
      (user) => {
        unsubscribe();
        resolve(user);
      }
    );
  });
}

window.NourishShareRecipientData = {
  registerAccount: async ({
    email,
    password,
    displayName,
    organizationName,
    profile,
  }) => {
    await registerWithEmail(auth, email, password);

    return createPendingAccountProfile(
      db,
      auth,
      {
        role: "recipient",
        displayName,
        organizationName,
        profile,
      }
    );
  },

  getAvailableDonations: async () => {
    await waitForAuthReady();
    return getAvailableDonations(db);
  },

  reserveDonation: async (donationId) => {
    await waitForAuthReady();
    return reserveDonation(
      db,
      auth,
      donationId
    );
  },

  getMyReservationDetails: async () => {
    await waitForAuthReady();
    return getMyReservationDetails(
      db,
      auth
    );
  },

  getConversationMessages: async (conversationId) => {
    await waitForAuthReady();
    return getConversationMessages(db, auth, conversationId);
  },

  sendConversationMessage: async (payload) => {
    await waitForAuthReady();
    return sendConversationMessage(db, auth, payload);
  },

  getCurrentUserProfile: async () => {
    await waitForAuthReady();
    return getCurrentUserProfile(db, auth);
  },

  saveUserProfile: async (payload) => {
    await waitForAuthReady();
    return saveUserProfile(db, auth, payload);
  },

  saveUserSettings: async (settings) => {
    await waitForAuthReady();
    return saveUserSettings(db, auth, settings);
  },

  changePassword: async (currentPassword, newPassword) => {
    const user = await waitForAuthReady();

    if (!user?.email) {
      throw new Error("Signed-in user email is unavailable.");
    }

    const credential = EmailAuthProvider.credential(
      user.email,
      currentPassword
    );

    await reauthenticateWithCredential(user, credential);
    await updatePassword(user, newPassword);
  },
  logout: async () => {
    await logoutFirebase(auth);
  },

};


