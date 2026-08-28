import {
  browserLocalPersistence,
  browserSessionPersistence,
  connectAuthEmulator,
  setPersistence,
} from "https://www.gstatic.com/firebasejs/12.17.0/firebase-auth.js";

import {
  connectFirestoreEmulator,
} from "https://www.gstatic.com/firebasejs/12.17.0/firebase-firestore.js";

import { auth, db } from "../../backend/firebaseConfig.js";
import {
  doc,
  getDoc,
} from "https://www.gstatic.com/firebasejs/12.17.0/firebase-firestore.js";
import { loginWithEmail } from "../../backend/authHelpers.js";
import { getCurrentUserProfile } from "../../backend/firebaseHelpers.js";

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

window.NourishShareAuth = {
  authHost: auth.emulatorConfig
    ? `${auth.emulatorConfig.host}:${auth.emulatorConfig.port}`
    : "production",

  async signIn({ email, password, remember }) {
    await setPersistence(
      auth,
      remember
        ? browserLocalPersistence
        : browserSessionPersistence
    );

    const user =
      await loginWithEmail(auth, email, password);

    const profile =
      await getCurrentUserProfile(db, auth);

    let organization = null;

    if (
      ["donor", "recipient"].includes(profile?.role) &&
      profile?.organizationId
    ) {
      const organizationSnapshot = await getDoc(
        doc(db, "organizations", profile.organizationId)
      );

      if (organizationSnapshot.exists()) {
        organization = {
          id: organizationSnapshot.id,
          ...organizationSnapshot.data(),
        };
      }
    }

    return {
      user,
      profile,
      organization,
    };
  },
};
