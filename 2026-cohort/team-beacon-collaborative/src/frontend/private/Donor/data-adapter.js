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
  createDonation,
  createPendingAccountProfile,
  getCurrentUserProfile,
  getMyDonations,
  getConversationMessages,
  sendConversationMessage,
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
    // Ignore if Firestore is already connected.
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

window.NourishShareDonorData = {
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
        role: "donor",
        displayName,
        organizationName,
        profile,
      }
    );
  },

  createDonation: async ({
    title,
    description,
    quantity,
    photos = [],
  }) => {
    await waitForAuthReady();

    return createDonation(
      db,
      auth,
      {
        title,
        description,
        quantity,
        photos,
      }
    );
  },

  getCurrentUserProfile: async () => {
    await waitForAuthReady();
    return getCurrentUserProfile(db, auth);
  },

  getMyDonations: async () => {
    await waitForAuthReady();
    return getMyDonations(db, auth);
  },

  getConversationMessages: async (conversationId) => {
    await waitForAuthReady();
    return getConversationMessages(db, auth, conversationId);
  },

  sendConversationMessage: async (payload) => {
    await waitForAuthReady();
    return sendConversationMessage(db, auth, payload);
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






