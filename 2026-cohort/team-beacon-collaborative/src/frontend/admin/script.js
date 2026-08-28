// =========================================================
// Nourish & Share Admin Panel
// =========================================================

let adminSnapshot = {
  users: [],
  organizations: [],
  donations: [],
  reservations: [],
};

let currentAdminProfile = null;

const EMAILJS_CONFIG = {
  serviceId: "service_1ct2z2h",
  templateId: "template_qbppeol",
  publicKey: "YVllZSyw6TVu0ZjHg",
};

async function sendOrganizationApprovalEmail(
  organizationId
) {
  const organization =
    adminSnapshot.organizations.find(
      org => org.id === organizationId
    );

  const user =
    adminSnapshot.users.find(
      item => item.organizationId === organizationId
    );

  if (!organization || !user) {
    console.warn(
      "Approval email skipped: organization or user was not found."
    );
    return false;
  }

  const toEmail =
    user.profile?.contact?.ctEmail ||
    user.email ||
    "";

  if (!toEmail) {
    console.warn(
      "Approval email skipped: no contact email was found."
    );
    return false;
  }

  if (!window.emailjs) {
    console.warn(
      "Approval email skipped: EmailJS SDK is unavailable."
    );
    return false;
  }

  const loginUrl =
    new URL(
      "../public/login.html",
      window.location.href
    ).href;

  const response = await window.emailjs.send(
    EMAILJS_CONFIG.serviceId,
    EMAILJS_CONFIG.templateId,
    {
      to_email: toEmail,
      contact_name:
        user.displayName || "there",
      organization_name:
        organization.name || "your organization",
      login_url: loginUrl,
    },
    {
      publicKey: EMAILJS_CONFIG.publicKey,
    }
  );

  alert(
    `Approval email sent to ${toEmail}. EmailJS status: ${response.status}`
  );

  return true;
}


document.addEventListener("DOMContentLoaded", async () => {
  initNavigation();
  initSubmenus();
  initMobileMenu();

  await bootAdmin();
});

async function waitForAdminData(timeoutMs = 5000) {
  const started = Date.now();

  while (
    !window.NourishShareAdminData &&
    Date.now() - started < timeoutMs
  ) {
    await new Promise(resolve => setTimeout(resolve, 50));
  }

  if (!window.NourishShareAdminData) {
    throw new Error("Admin data service did not finish loading.");
  }

  return window.NourishShareAdminData;
}

async function bootAdmin() {
  try {
    const adminData = await waitForAdminData();
    const session = await adminData.requireAdmin();

    currentAdminProfile = session.profile;

    await refreshAdminData();
    renderDashboard();
    renderAdminProfile();
    renderPrivacySafeChat();
  } catch (error) {
    console.error("Admin boot failed:", error);

    window.location.href =
      "../public/login.html";
  }
}

async function refreshAdminData() {
  const adminData = await waitForAdminData();
  adminSnapshot = await adminData.getAdminSnapshot();

  renderDashboard();
  renderListings();
  renderReservations();
  renderPickups();
  renderUsers("donor");
  renderUsers("recipient");
}

function initNavigation() {
  const menuButtons =
    document.querySelectorAll(".menu-item[data-screen]");

  menuButtons.forEach(btn => {
    btn.addEventListener("click", async () => {
      const targetScreen = btn.dataset.screen;

      menuButtons.forEach(b =>
        b.classList.remove("active")
      );

      btn.classList.add("active");

      const submenuTrigger =
        document.getElementById("menu-users-trigger");

      if (btn.classList.contains("submenu-item")) {
        submenuTrigger?.classList.add("active");
      } else if (
        targetScreen !== "donors" &&
        targetScreen !== "recipients"
      ) {
        submenuTrigger?.classList.remove("active");
      }

      showScreen(targetScreen);
      closeMobileSidebar();

      if (
        [
          "dashboard",
          "listings",
          "reservations",
          "pickups",
          "donors",
          "recipients",
        ].includes(targetScreen)
      ) {
        await refreshAdminData();
      }
    });
  });
}

function showScreen(screenId) {
  document
    .querySelectorAll(".admin-screen")
    .forEach(screen =>
      screen.classList.remove("active")
    );

  document
    .getElementById(`screen-${screenId}`)
    ?.classList.add("active");
}

function initSubmenus() {
  const usersTrigger =
    document.getElementById("menu-users-trigger");

  const usersContainer =
    document.getElementById("submenu-users-container");

  usersTrigger?.addEventListener("click", (event) => {
    event.stopPropagation();
    usersContainer?.classList.toggle("open");
  });
}

function initMobileMenu() {
  const burger =
    document.getElementById("mobile-menu-burger");

  const closeBtn =
    document.getElementById("mobile-menu-close");

  const overlay =
    document.getElementById("sidebar-overlay");

  const sidebar =
    document.getElementById("admin-sidebar");

  burger?.addEventListener("click", () => {
    sidebar?.classList.add("active");
    overlay?.classList.add("active");
  });

  closeBtn?.addEventListener(
    "click",
    closeMobileSidebar
  );

  overlay?.addEventListener(
    "click",
    closeMobileSidebar
  );
}

function closeMobileSidebar() {
  document
    .getElementById("admin-sidebar")
    ?.classList.remove("active");

  document
    .getElementById("sidebar-overlay")
    ?.classList.remove("active");
}

async function logoutAdmin() {
  try {
    const adminData = await waitForAdminData();
    await adminData.signOutAdmin();
  } finally {
    window.location.href =
      "../public/login.html";
  }
}

function renderDashboard() {
  const dashboard =
    document.getElementById("screen-dashboard");

  if (!dashboard) return;

  let stats =
    dashboard.querySelector(".admin-live-stats");

  if (!stats) {
    stats = document.createElement("div");
    stats.className = "admin-live-stats";

    const header =
      dashboard.querySelector(".dashboard-header");

    header?.insertAdjacentElement(
      "afterend",
      stats
    );
  }

  const donors =
    adminSnapshot.users.filter(
      user => user.role === "donor"
    ).length;

  const recipients =
    adminSnapshot.users.filter(
      user => user.role === "recipient"
    ).length;

  const available =
    adminSnapshot.donations.filter(
      donation => donation.status === "available"
    ).length;

  const activeReservations =
    adminSnapshot.reservations.filter(
      reservation => reservation.status === "active"
    ).length;

  stats.innerHTML = `
    ${statCard("Donors", donors)}
    ${statCard("Recipients", recipients)}
    ${statCard("Available Food", available)}
    ${statCard("Active Reservations", activeReservations)}
  `;

  const title =
    dashboard.querySelector(".welcome-title");

  if (title && currentAdminProfile?.displayName) {
    title.textContent =
      `Welcome, ${currentAdminProfile.displayName}!`;
  }
}

function statCard(label, value) {
  return `
    <div class="admin-stat-card">
      <span class="admin-stat-value">${value}</span>
      <span class="admin-stat-label">${escapeHtml(label)}</span>
    </div>
  `;
}

function renderListings() {
  const container =
    document.getElementById(
      "admin-listings-content"
    );

  if (!container) return;

  if (!adminSnapshot.donations.length) {
    container.innerHTML =
      emptyState("No food listings yet.");
    return;
  }

  const orgById =
    Object.fromEntries(
      adminSnapshot.organizations.map(org => [
        org.id,
        org,
      ])
    );

  const rows =
    adminSnapshot.donations.map(donation => `
      <tr>
        <td>${escapeHtml(donation.title || "Untitled")}</td>
        <td>${escapeHtml(orgById[donation.organizationId]?.name || "Unknown donor")}</td>
        <td>${escapeHtml(donation.quantity || "-")}</td>
        <td>${statusBadge(donation.status)}</td>
        <td>${escapeHtml(donation.pickupAddress || "-")}</td>
      </tr>
    `).join("");

  container.innerHTML = tableHtml(
    ["Listing", "Donor", "Quantity", "Status", "Pickup"],
    rows
  );
}

function renderReservations() {
  const container =
    document.getElementById(
      "admin-reservations-content"
    );

  if (!container) return;

  if (!adminSnapshot.reservations.length) {
    container.innerHTML =
      emptyState("No reservations yet.");
    return;
  }

  const donationById =
    Object.fromEntries(
      adminSnapshot.donations.map(donation => [
        donation.id,
        donation,
      ])
    );

  const orgById =
    Object.fromEntries(
      adminSnapshot.organizations.map(org => [
        org.id,
        org,
      ])
    );

  const rows =
    adminSnapshot.reservations.map(reservation => {
      const donation =
        donationById[reservation.donationId];

      const recipientOrg =
        orgById[
          reservation.recipientOrganizationId
        ];

      return `
        <tr>
          <td>${escapeHtml(donation?.title || reservation.donationId || "-")}</td>
          <td>${escapeHtml(recipientOrg?.name || "Unknown recipient")}</td>
          <td>${statusBadge(reservation.status)}</td>
        </tr>
      `;
    }).join("");

  container.innerHTML = tableHtml(
    ["Donation", "Recipient", "Status"],
    rows
  );
}

function renderPickups() {
  const container =
    document.getElementById(
      "admin-pickups-content"
    );

  if (!container) return;

  const donationById =
    Object.fromEntries(
      adminSnapshot.donations.map(donation => [
        donation.id,
        donation,
      ])
    );

  const orgById =
    Object.fromEntries(
      adminSnapshot.organizations.map(org => [
        org.id,
        org,
      ])
    );

  const pickupReservations =
    adminSnapshot.reservations.filter(
      reservation =>
        ["active", "picked_up"].includes(
          reservation.status
        )
    );

  if (!pickupReservations.length) {
    container.innerHTML =
      emptyState("No pickup activity yet.");
    return;
  }

  const rows =
    pickupReservations.map(reservation => {
      const donation =
        donationById[reservation.donationId];

      const recipient =
        orgById[
          reservation.recipientOrganizationId
        ];

      const action =
        reservation.status === "active"
          ? `
            <button
              class="admin-action-btn"
              onclick="markPickupComplete('${reservation.id}')"
            >
              Mark Picked Up
            </button>
          `
          : "Completed";

      return `
        <tr>
          <td>${escapeHtml(donation?.title || "-")}</td>
          <td>${escapeHtml(recipient?.name || "Unknown recipient")}</td>
          <td>${escapeHtml(donation?.pickupAddress || "-")}</td>
          <td>${statusBadge(reservation.status)}</td>
          <td>${action}</td>
        </tr>
      `;
    }).join("");

  container.innerHTML = tableHtml(
    ["Donation", "Recipient", "Pickup", "Status", "Action"],
    rows
  );
}

function renderUsers(role) {
  const targetId =
    role === "donor"
      ? "admin-donors-content"
      : "admin-recipients-content";

  const container =
    document.getElementById(targetId);

  if (!container) return;

  const users =
    adminSnapshot.users.filter(
      user => user.role === role
    );

  if (!users.length) {
    container.innerHTML =
      emptyState(
        `No ${role} accounts yet.`
      );
    return;
  }

  const orgById =
    Object.fromEntries(
      adminSnapshot.organizations.map(org => [
        org.id,
        org,
      ])
    );

  const rows =
    users.map(user => {
      const org =
        orgById[user.organizationId];

      const orgStatus =
        org?.verificationStatus || "unknown";

      const accountStatus =
        user.accountStatus || "unknown";

      const orgActions =
        orgStatus === "pending"
          ? `
            <div class="admin-action-group">
              <button
                class="admin-action-btn"
                onclick="setOrganizationStatus('${org.id}', 'approved')"
              >
                Approve
              </button>
              <button
                class="admin-action-btn admin-danger"
                onclick="setOrganizationStatus('${org.id}', 'rejected')"
              >
                Reject
              </button>
            </div>
          `
          : statusBadge(orgStatus);

      const accountAction =
        accountStatus === "active"
          ? `
            <button
              class="admin-action-btn admin-danger"
              onclick="setAccountStatus('${user.id}', 'suspended')"
            >
              Suspend
            </button>
          `
          : `
            <button
              class="admin-action-btn"
              onclick="setAccountStatus('${user.id}', 'active')"
            >
              Reactivate
            </button>
          `;

      return `
        <tr>
          <td>${escapeHtml(user.displayName || "-")}</td>
          <td>${escapeHtml(org?.name || "-")}</td>
          <td>${orgActions}</td>
          <td>${statusBadge(accountStatus)}</td>
          <td>${accountAction}</td>
        </tr>
      `;
    }).join("");

  container.innerHTML = tableHtml(
    ["Contact", "Organization", "Verification", "Account", "Action"],
    rows
  );
}

function renderAdminProfile() {
  const container =
    document.getElementById(
      "admin-profile-content"
    );

  if (!container) return;

  container.innerHTML = `
    <div class="admin-profile-card">
      <strong>${escapeHtml(currentAdminProfile?.displayName || "Nourish & Share Admin")}</strong>
      <span>Role: Administrator</span>
      <span>Account: ${escapeHtml(currentAdminProfile?.accountStatus || "active")}</span>
    </div>
  `;
}

function renderPrivacySafeChat() {
  const deck =
    document.getElementById(
      "conversations-deck"
    );

  const empty =
    document.getElementById(
      "chat-empty-state"
    );

  const panel =
    document.getElementById(
      "chat-active-panel"
    );

  if (deck) {
    deck.innerHTML = `
      <div class="admin-chat-notice">
        <strong>Private conversations stay private.</strong>
        <p>
          Donor and recipient reservation chats are visible only
          to their participants. Admin accounts do not receive
          blanket access to private messages.
        </p>
      </div>
    `;
  }

  if (empty) {
    empty.innerHTML = `
      <i class="fa-solid fa-shield-halved"></i>
      <h3>Participant-only messaging</h3>
      <p>
        Admin support messaging can be added as a separate
        participant-based conversation flow without exposing
        donor-recipient chats.
      </p>
    `;
  }

  if (panel) {
    panel.style.display = "none";
  }

  document
    .getElementById("chat-admin-filters")
    ?.remove();

  document
    .querySelector(".chat-search-container")
    ?.remove();
}

async function setOrganizationStatus(
  organizationId,
  status
) {
  try {
    const adminData = await waitForAdminData();

    await adminData.setOrganizationStatus(
      organizationId,
      status
    );

    if (status === "approved") {
      try {
        const emailSent =
          await sendOrganizationApprovalEmail(
            organizationId
          );

        if (!emailSent) {
          console.warn(
            "Organization approved, but approval email was not sent."
          );
        }
      } catch (emailError) {
        console.error(
          "Organization approved, but approval email failed:",
          emailError
        );

        alert(
          "Organization approved successfully, but the approval email could not be sent."
        );
      }
    }

    await refreshAdminData();
  } catch (error) {
    console.error(error);
    alert(
      error.message ||
      "Organization could not be updated."
    );
  }
}

async function setAccountStatus(
  userId,
  status
) {
  try {
    const adminData = await waitForAdminData();

    await adminData.setUserAccountStatus(
      userId,
      status
    );

    await refreshAdminData();
  } catch (error) {
    console.error(error);
    alert(
      error.message ||
      "Account could not be updated."
    );
  }
}

async function markPickupComplete(
  reservationId
) {
  try {
    const adminData = await waitForAdminData();

    await adminData.completePickup(
      reservationId
    );

    await refreshAdminData();
  } catch (error) {
    console.error(error);
    alert(
      error.message ||
      "Pickup could not be completed."
    );
  }
}

function tableHtml(headers, rows) {
  return `
    <div class="admin-table-wrap">
      <table class="admin-table">
        <thead>
          <tr>
            ${headers.map(header =>
              `<th>${escapeHtml(header)}</th>`
            ).join("")}
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function statusBadge(status) {
  const clean =
    String(status || "unknown");

  return `
    <span class="admin-status-badge admin-status-${escapeHtml(clean)}">
      ${escapeHtml(clean.replaceAll("_", " "))}
    </span>
  `;
}

function emptyState(message) {
  return `
    <div class="admin-empty-state">
      ${escapeHtml(message)}
    </div>
  `;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
