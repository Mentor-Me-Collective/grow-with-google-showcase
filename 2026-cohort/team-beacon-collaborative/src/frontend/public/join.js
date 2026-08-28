(() => {
  const notice = document.getElementById("selection-note");

  const routes = {
    Donor: "../private/Donor/index%20(3).html",
    Recipient: "../private/Recipient/index%20(4).html",
  };

  document.querySelectorAll(".path-button").forEach((button) => {
    button.addEventListener("click", () => {
      const role = button.dataset.role;

      if (routes[role]) {
        window.location.href = routes[role];
        return;
      }

      notice.textContent =
        "Volunteer registration is not available in the current MVP.";
      notice.hidden = false;
      notice.focus();
    });
  });
})();
