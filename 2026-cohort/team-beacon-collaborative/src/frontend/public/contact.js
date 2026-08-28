(() => {
  const CONTACT_API_URL =
    "http://127.0.0.1:5001/beacon-food-network/us-central1/api/contact";

  const form = document.getElementById("contact-form");
  const success = document.getElementById("form-success");
  const reason = document.getElementById("reason");
  const submit = form.querySelector('button[type="submit"]');

  const fields = [
    ["full-name", "Please enter your full name."],
    ["email", "Enter a valid email address."],
    ["reason", "Please select a reason for contacting us."],
    ["message", "Please tell us how we can help."],
  ];

  const setError = (input, message) => {
    const wrapper = input.closest(".form-field");
    const error = document.getElementById(`${input.id}-error`);

    wrapper.classList.toggle("invalid", Boolean(message));
    input.setAttribute("aria-invalid", Boolean(message));
    error.textContent = message || "";
  };

  const validate = (input, message) => {
    const invalid =
      !input.value.trim() ||
      (input.type === "email" && !input.validity.valid);

    setError(input, invalid ? message : "");
    return !invalid;
  };

  fields.forEach(([id, message]) => {
    document
      .getElementById(id)
      .addEventListener("input", (event) =>
        validate(event.target, message)
      );
  });

  document.querySelectorAll(".pathway").forEach((button) => {
    button.addEventListener("click", () => {
      reason.value = button.dataset.reason;
      setError(reason, "");

      document
        .getElementById("message")
        .focus({ preventScroll: true });

      form.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    success.hidden = true;

    const valid = fields
      .map(([id, message]) =>
        validate(document.getElementById(id), message)
      )
      .every(Boolean);

    if (!valid) {
      form
        .querySelector('[aria-invalid="true"]')
        .focus();

      return;
    }

    const payload = {
      name: document.getElementById("full-name").value.trim(),
      email: document.getElementById("email").value.trim(),
      reason: reason.value.trim(),
      message: document.getElementById("message").value.trim(),
    };

    if (submit) {
      submit.disabled = true;
      submit.setAttribute("aria-busy", "true");
    }

    try {
      const response = await fetch(CONTACT_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const result = await response.json();

      if (!response.ok || !result.ok) {
        if (
          result.error === "validation_error" &&
          result.fields
        ) {
          const fieldMap = {
            name: "full-name",
            email: "email",
            reason: "reason",
            message: "message",
          };

          Object.entries(result.fields).forEach(
            ([field, message]) => {
              const input = document.getElementById(
                fieldMap[field]
              );

              if (input) {
                setError(input, message);
              }
            }
          );

          const firstInvalid = form.querySelector(
            '[aria-invalid="true"]'
          );

          if (firstInvalid) {
            firstInvalid.focus();
          }
        }

        throw new Error("Contact submission failed.");
      }

      success.hidden = false;
      success.focus();
      form.reset();
    } catch (error) {
      console.error("Contact form submission failed.");

      success.hidden = false;
      success.textContent =
        "We could not send your message right now. Please try again.";
      success.focus();
    } finally {
      if (submit) {
        submit.disabled = false;
        submit.removeAttribute("aria-busy");
      }
    }
  });
})();
