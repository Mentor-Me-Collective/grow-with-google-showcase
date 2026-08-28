import {
  connectAuthEmulator,
  onAuthStateChanged,
} from "https://www.gstatic.com/firebasejs/12.17.0/firebase-auth.js";

import {
  connectFirestoreEmulator,
} from "https://www.gstatic.com/firebasejs/12.17.0/firebase-firestore.js";

import {
  auth,
  db,
} from "../../backend/firebaseConfig.js";

import {
  createDonation,
  getAvailableDonations,
  reserveDonation,
} from "../../backend/firebaseHelpers.js";

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
    // Ignore if this Firestore instance was already connected.
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
window.NourishShareData = {
  createDonation: async ({
    title,
    description,
    quantity,
  }) => {
    return createDonation(
      db,
      auth,
      {
        title,
        description,
        quantity,
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
};