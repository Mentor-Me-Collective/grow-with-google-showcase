(() => {
  async function waitForAuthService() {
    const timeoutAt = Date.now() + 5000;

    while (Date.now() < timeoutAt) {
      if (
        window.NourishShareAuth &&
        typeof window.NourishShareAuth.signIn === 'function'
      ) {
        return window.NourishShareAuth;
      }

      await new Promise(resolve => setTimeout(resolve, 50));
    }

    throw new Error(
      'Secure sign-in service did not finish loading.'
    );
  }

  const form = document.getElementById('login-form');
  const email = document.getElementById('login-email');
  const password = document.getElementById('login-password');
  const toggle = document.getElementById('password-toggle');
  const submit = form.querySelector('.login-button');
  const status = document.getElementById('login-status');
  const showStatus = (message, type) => { status.textContent = message; status.className = `login-status ${type}`; status.hidden = false; status.focus(); };
  const setError = (input, message) => { input.closest('.form-field').classList.toggle('invalid', Boolean(message)); input.setAttribute('aria-invalid', Boolean(message)); document.getElementById(`${input.id}-error`).textContent = message || ''; };
  const validate = () => {
    const emailError = !email.value.trim() ? 'Enter your email address.' : !email.validity.valid ? 'Enter a valid email address.' : '';
    const passwordError = !password.value ? 'Enter your password.' : '';
    setError(email, emailError); setError(password, passwordError);
    return !emailError && !passwordError;
  };
  [email, password].forEach(input => input.addEventListener('input', validate));
  toggle.addEventListener('click', () => { const isHidden = password.type === 'password'; password.type = isHidden ? 'text' : 'password'; toggle.setAttribute('aria-pressed', String(isHidden)); toggle.setAttribute('aria-label', isHidden ? 'Hide password' : 'Show password'); toggle.querySelector('i').className = `fa-solid fa-eye${isHidden ? '-slash' : ''}`; });
  document.getElementById('forgot-password').addEventListener('click', event => { event.preventDefault(); showStatus('Password reset will be available when the account connection is added.', 'info'); });
  form.addEventListener('submit', async event => {
    event.preventDefault(); status.hidden = true;
    if (!validate()) { form.querySelector('[aria-invalid="true"]').focus(); return; }
    let auth;

    try {
      auth = await waitForAuthService();
    } catch (error) {
      console.error('Auth service initialization failed:', error);
      showStatus(
        error.message || 'Secure sign-in could not initialize.',
        'error'
      );
      return;
    }
    submit.setAttribute('aria-busy', 'true'); submit.disabled = true; submit.querySelector('span').textContent = 'Logging in…';
    try {
      const session = await auth.signIn({
        email: email.value.trim(),
        password: password.value,
        remember: form.elements.remember.checked
      });

      const profile = session && session.profile;

      if (!profile) {
        throw new Error(
          'Authenticated user profile could not be loaded.'
        );
      }

      if (profile.accountStatus !== 'active') {
        showStatus(
          'Your account is not currently active. Please contact Nourish & Share support.',
          'error'
        );
        return;
      }

      if (['donor', 'recipient'].includes(profile.role)) {
        const organization = session && session.organization;
        const verificationStatus =
          organization && organization.verificationStatus;

        if (verificationStatus !== 'approved') {
          const message =
            verificationStatus === 'rejected'
              ? 'Your organization registration was not approved. Please contact Nourish & Share support.'
              : 'Your organization is still awaiting Admin approval. You will be able to log in once your registration has been approved.';

          showStatus(message, 'info');
          return;
        }
      }

      const workspaceByRole = {
        donor: '../private/Donor/index%20(3).html',
        recipient: '../private/Recipient/index%20(4).html',
        admin: '../admin/index.html'
      };

      const destination = workspaceByRole[profile.role];

      if (!destination) {
        showStatus(
          profile.role === 'admin'
            ? 'Signed in successfully. The Admin workspace is still being connected.'
            : 'Signed in successfully, but this account does not have a recognized workspace role.',
          'info'
        );
        return;
      }

      showStatus(
        'Signed in. Opening your workspace?',
        'success'
      );

      window.location.href =
        `${destination}?verified=${encodeURIComponent(profile.role)}`;
    }
    catch (error) {
      console.error('Login failed:', error);

      const code = error && error.code;

      const message =
        code === 'auth/invalid-credential' ||
        code === 'auth/wrong-password'
          ? 'That email or password did not match an account. Please try again.'
          : code === 'auth/network-request-failed'
            ? 'We could not connect just now. Check your connection and try again.'
            : 'We could not sign you in right now. Please try again.';

      showStatus(message, 'error');
    }
    finally { submit.removeAttribute('aria-busy'); submit.disabled = false; submit.querySelector('span').textContent = 'Log In'; }
  });
})();
