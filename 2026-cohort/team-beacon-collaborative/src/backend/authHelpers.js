import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
} from "https://www.gstatic.com/firebasejs/12.17.0/firebase-auth.js";

/**
 * Creates a new Firebase Authentication user.
 */
export async function registerWithEmail(
  auth,
  email,
  password
) {
  const credential =
    await createUserWithEmailAndPassword(
      auth,
      email.trim(),
      password
    );

  return credential.user;
}

/**
 * Signs in an existing Firebase Authentication user.
 */
export async function loginWithEmail(
  auth,
  email,
  password
) {
  const credential =
    await signInWithEmailAndPassword(
      auth,
      email.trim(),
      password
    );

  return credential.user;
}

/**
 * Signs out the current Firebase user.
 */
export async function logout(auth) {
  await signOut(auth);
}

/**
 * Registers a callback that runs whenever
 * authentication state changes.
 *
 * Returns Firebase's unsubscribe function.
 */
export function watchAuthState(
  auth,
  callback
) {
  return onAuthStateChanged(
    auth,
    callback
  );
}
