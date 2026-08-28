// =========================================================
// STATE
// =========================================================
const state = {
  recipientType: null,
  org: {},
  contact: {},
  capacity: {},
  account: {},
};

const STAMP_STEPS = ["type", "org", "contact", "capacity", "account", "review"];

function normalizeRecipientAvatarState() {
  const avatar =
    state.profilePhoto ||
    state.avatarDataUrl ||
    "";

  state.profilePhoto = avatar;
  state.avatarDataUrl = avatar;
}

let currentStep = "welcome";

// =========================================================
// RECIPIENT TYPES
// All five are live in this build (not future-expansion-only).
// Each has an icon, short description, and fields specific to
// how that org actually receives and distributes food.
// =========================================================
const RECIPIENT_TYPES = [
  {
    id: "pantry",
    name: "Food Pantry",
    icon: "🥫",
    desc: "Distributes groceries directly to individuals and families.",
    fields: [
      { id: "householdsWeekly", label: "Households served weekly", type: "number", placeholder: "e.g. 80" },
      { id: "distributionModel", label: "Distribution model", type: "select", options: ["Walk-in", "Pre-scheduled pickup", "Home delivery", "Mixed"] },
    ],
  },
  {
    id: "soupkitchen",
    name: "Soup Kitchen",
    icon: "🍲",
    desc: "Prepares and serves hot meals on-site.",
    fields: [
      { id: "mealsPerDay", label: "Meals served per day", type: "number", placeholder: "e.g. 120" },
      { id: "serviceHours", label: "Service days / hours", type: "text", placeholder: "e.g. Mon–Fri, 11am–1pm" },
    ],
  },
  {
    id: "school",
    name: "School Meal Program",
    icon: "🎒",
    desc: "Provides meals to students during or after school hours.",
    fields: [
      { id: "studentsServed", label: "Number of students served", type: "number", placeholder: "e.g. 300" },
      { id: "district", label: "School / district name", type: "text", placeholder: "e.g. Lincoln Elementary" },
    ],
  },
  {
    id: "community",
    name: "Community Organization",
    icon: "🤝",
    desc: "Redistributes food through drives, events, or partner networks.",
    fields: [
      { id: "missionType", label: "Organization mission / type", type: "text", placeholder: "e.g. Neighborhood mutual aid" },
      { id: "nonprofitStatus", label: "Nonprofit status", type: "select", options: ["Registered nonprofit", "Fiscally sponsored", "Not incorporated"] },
    ],
  },
  {
    id: "foodbank",
    name: "Regional Food Bank",
    icon: "🏢",
    desc: "Redistributes food at scale to smaller partner organizations.",
    fields: [
      { id: "serviceArea", label: "Service area", type: "text", placeholder: "e.g. Cook County" },
      { id: "partnerOrgs", label: "Number of partner organizations", type: "number", placeholder: "e.g. 25" },
    ],
  },
];

// =========================================================
// INIT
// =========================================================
function init() {
  renderCrateGrid();
  renderTopbarStamps();
  wireChoiceGroups();
  wireForms();
  updateStamps();
  seedDemoMessages();
}

function renderCrateGrid() {
  const grid = document.getElementById("crate-grid");
  grid.innerHTML = RECIPIENT_TYPES.map(t => `
    <button type="button" class="crate" data-id="${t.id}" onclick="selectRecipientType('${t.id}')">
      <span class="crate-icon">${t.icon}</span>
      <span class="crate-name">${t.name}</span>
      <span class="crate-desc">${t.desc}</span>
    </button>
  `).join("");
}

function renderTopbarStamps() {
  const wrap = document.getElementById("topbar-stamps");
  wrap.innerHTML = STAMP_STEPS.map(s => `<span data-step="${s}"></span>`).join("");
}

// =========================================================
// RECIPIENT TYPE SELECTION
// =========================================================
function selectRecipientType(id) {
  state.recipientType = id;
  document.querySelectorAll(".crate").forEach(el => {
    el.classList.toggle("selected", el.dataset.id === id);
  });
  document.getElementById("type-continue").disabled = false;

  const type = RECIPIENT_TYPES.find(t => t.id === id);
  const tag = document.getElementById("rail-tag");
  tag.hidden = false;
  document.getElementById("rail-tag-value").textContent = type.name;
  document.getElementById("org-type-echo").textContent = type.name.toLowerCase();

  renderTypeFields(type);
}

function renderTypeFields(type) {
  const container = document.getElementById("type-specific-fields");
  if (!type.fields.length) { container.innerHTML = ""; return; }

  container.innerHTML = `<div class="type-fields-label">Specific to ${type.name.toLowerCase()}s</div>` +
    type.fields.map(f => {
      if (f.type === "select") {
        return `
          <div class="field">
            <label for="tf-${f.id}">${f.label}</label>
            <select id="tf-${f.id}" name="${f.id}">
              <option value="" disabled selected>Select one</option>
              ${f.options.map(o => `<option>${o}</option>`).join("")}
            </select>
          </div>`;
      }
      return `
        <div class="field">
          <label for="tf-${f.id}">${f.label}</label>
          <input type="${f.type}" id="tf-${f.id}" name="${f.id}" placeholder="${f.placeholder || ""}">
        </div>`;
    }).join("");
}

// =========================================================
// PILL / CHIP CHOICE GROUPS (contact method, storage, categories)
// =========================================================
function wireChoiceGroups() {
  document.querySelectorAll(".pill-choices").forEach(group => {
    group.addEventListener("click", e => {
      const btn = e.target.closest(".pill");
      if (!btn) return;
      group.querySelectorAll(".pill").forEach(p => p.classList.remove("selected"));
      btn.classList.add("selected");
      group.dataset.value = btn.dataset.value;
    });
  });

  document.querySelectorAll(".chip-choices").forEach(group => {
    group.addEventListener("click", e => {
      const btn = e.target.closest(".chip");
      if (!btn) return;
      btn.classList.toggle("selected");
    });
  });
}

function getChipValues(groupId) {
  return Array.from(document.querySelectorAll(`#${groupId} .chip.selected`)).map(c => c.dataset.value);
}

// =========================================================
// FORM SUBMIT HANDLERS
// =========================================================
function wireForms() {
  document.getElementById("form-org").addEventListener("submit", e => {
    e.preventDefault();
    state.org = Object.fromEntries(new FormData(e.target).entries());
    const type = RECIPIENT_TYPES.find(t => t.id === state.recipientType);
    type.fields.forEach(f => {
      const el = document.getElementById(`tf-${f.id}`);
      if (el) state.org[f.id] = el.value;
    });
    goTo("contact");
  });

  document.getElementById("form-contact").addEventListener("submit", e => {
    e.preventDefault();
    state.contact = Object.fromEntries(new FormData(e.target).entries());
    state.contact.ctMethod = document.querySelector('[data-name="ctMethod"]').dataset.value || "";
    document.getElementById("acc-email").value = state.contact.ctEmail || "";
    goTo("capacity");
  });

  document.getElementById("form-capacity").addEventListener("submit", e => {
    e.preventDefault();
    state.capacity = Object.fromEntries(new FormData(e.target).entries());
    state.capacity.foodCategories = getChipValues("food-categories");
    state.capacity.capStorage = document.querySelector('[data-name="capStorage"]').dataset.value || "";
    goTo("account");
  });

  document.getElementById("form-account").addEventListener("submit", e => {
    e.preventDefault();
    const pass = document.getElementById("acc-pass").value;
    const pass2 = document.getElementById("acc-pass2").value;
    const hint = document.getElementById("pass-match-hint");
    if (pass !== pass2) {
      hint.hidden = false;
      return;
    }
    hint.hidden = true;
    state.account = Object.fromEntries(new FormData(e.target).entries());
    buildReview();
    goTo("review");
  });

  document.getElementById("review-confirm").addEventListener("change", e => {
    document.getElementById("submit-btn").disabled = !e.target.checked;
  });
}

// =========================================================
// REVIEW SCREEN
// =========================================================
function buildReview() {
  const type = RECIPIENT_TYPES.find(t => t.id === state.recipientType);

  const blocks = [
    {
      title: "Recipient type",
      step: "type",
      items: [["Organization type", type.name]],
    },
    {
      title: "Organization information",
      step: "org",
      items: [
        ["Name", state.org.orgName],
        ["Address", state.org.orgAddress],
        ["Registration #", state.org.orgLicense],
        ["Years in operation", state.org.orgYears || "—"],
        ["Website", state.org.orgWebsite || "—"],
        ...type.fields.map(f => [f.label, state.org[f.id] || "—"]),
      ],
    },
    {
      title: "Contact information",
      step: "contact",
      items: [
        ["Name", state.contact.ctName],
        ["Title", state.contact.ctTitle],
        ["Phone", state.contact.ctPhone],
        ["Email", state.contact.ctEmail],
        ["Preferred contact", state.contact.ctMethod || "—"],
      ],
    },
    {
      title: "Capacity profile",
      step: "capacity",
      items: [
        ["Categories needed", (state.capacity.foodCategories || []).join(", ") || "—"],
        ["People served weekly", state.capacity.capServed || "—"],
        ["Receiving frequency", state.capacity.capFrequency || "—"],
        ["Receiving window", state.capacity.capWindow || "—"],
        ["Storage available", state.capacity.capStorage || "—"],
      ],
    },
    {
      title: "Account",
      step: "account",
      items: [
        ["Login email", state.account.accEmail],
        ["Password", "••••••••"],
      ],
    },
  ];

  document.getElementById("review-list").innerHTML = blocks.map(b => `
    <div class="review-block">
      <div class="review-block-head">
        <h4>${b.title}</h4>
        <button type="button" class="review-edit" onclick="goTo('${b.step}')">Edit</button>
      </div>
      <dl class="review-block-body">
        ${b.items.map(([k, v]) => `
          <div class="review-item"><dt>${k}</dt><dd>${escapeHtml(String(v ?? "—"))}</dd></div>
        `).join("")}
      </dl>
    </div>
  `).join("");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// =========================================================
// SUBMIT
// =========================================================
async function submitApplication() {
  const email =
    state.account?.accEmail ||
    state.account?.email ||
    "";

  const password =
    state.account?.accPassword ||
    state.account?.password ||
    state.account?.accPass ||
    "";

  try {
    if (!email || !password) {
      throw new Error("Email and password are required.");
    }

    if (!window.NourishShareRecipientData) {
      await import("./data-adapter.js?v=20260823f");
    }

    if (!window.NourishShareRecipientData?.registerAccount) {
      throw new Error("Registration service is not available.");
    }

    await window.NourishShareRecipientData.registerAccount({
      email,
      password,
      displayName:
        state.contact?.ctName ||
        state.org?.orgName ||
        "Recipient",
      organizationName:
        state.org?.orgName ||
        "Recipient Organization",
      profile: {
        recipientType:
          state.recipientType ||
          state.type ||
          "",
        org: state.org || {},
        contact: state.contact || {},
        capacity: state.capacity || {},
        avatarUrl: state.avatarDataUrl || "",
      },
    });

    localStorage.setItem(
      "recipient_onboarding_state",
      JSON.stringify(state)
    );

    document.getElementById("pending-name").textContent =
      state.contact?.ctName || "there";

    document.getElementById("pending-org").textContent =
      state.org?.orgName || "your organization";

    document.getElementById("pending-email").textContent =
      email;

    goTo("pending");
  } catch (error) {
    console.error(
      "Could not submit recipient application:",
      error
    );

    alert(
      error?.message ||
      "Could not submit application."
    );
  }
}

// =========================================================
// NAVIGATION
// =========================================================
function goTo(step) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.getElementById(`screen-${step}`).classList.add("active");
  currentStep = step;
  window.scrollTo({ top: 0, behavior: "smooth" });
  updateStamps();
}

function updateStamps() {
  const idx = STAMP_STEPS.indexOf(currentStep);
  document.querySelectorAll(".stamp-row").forEach(row => {
    const s = row.dataset.step;
    const sIdx = STAMP_STEPS.indexOf(s);
    row.classList.remove("is-current", "is-done");
    if (sIdx < idx) row.classList.add("is-done");
    else if (sIdx === idx) row.classList.add("is-current");
  });
  document.querySelectorAll("#topbar-stamps span").forEach(el => {
    const s = el.dataset.step;
    const sIdx = STAMP_STEPS.indexOf(s);
    el.classList.remove("is-current", "is-done");
    if (sIdx < idx) el.classList.add("is-done");
    else if (sIdx === idx) el.classList.add("is-current");
  });
}

function restart() {
  location.reload();
}

// =========================================================
// RECIPIENT DASHBOARD HOME & ROUTING (PHASE 1)
// =========================================================
const dashboardStats = {
  availableFood: 0,
  myReservations: 0,
  upcomingPickups: 0,
  mealsImpacted: 0
};

function bypassVerification() {
  // Enter Dashboard View Mode (hides onboarding rail/topbar)
  document.body.classList.add("dashboard-mode");
  
  // Hydrate & load stats
  hydrateDashboardStats();
  
  // Wire nav click listeners
  initDashboardNavigation();
  
  // Route to the dashboard tab
  showDashboardTab("dashboard");
}

async function hydrateDashboardStats() {
  const saved = localStorage.getItem("recipient_dashboard_stats");
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      Object.assign(dashboardStats, parsed);
    } catch (error) {
      console.error("Error reading saved recipient stats:", error);
    }
  }

  try {
    const recipientData = await waitForRecipientData();
    const [available, reservations] = await Promise.all([
      recipientData.getAvailableDonations(),
      recipientData.getMyReservationDetails(),
    ]);

    dashboardStats.availableFood = available.length;
    dashboardStats.myReservations = reservations.length;
  } catch (error) {
    console.error("Could not load recipient dashboard stats:", error);
  }

  updateDashboardStats();
}

function updateDashboardStats() {
  const elAvailable = document.getElementById("stat-available-food");
  const elReservations = document.getElementById("stat-my-reservations");
  const elPickups = document.getElementById("stat-upcoming-pickups");
  const elMeals = document.getElementById("stat-meals-impacted");
  
  if (elAvailable) elAvailable.textContent = dashboardStats.availableFood;
  if (elReservations) elReservations.textContent = dashboardStats.myReservations;
  if (elPickups) elPickups.textContent = dashboardStats.upcomingPickups;
  if (elMeals) elMeals.textContent = dashboardStats.mealsImpacted;
}

function showDashboardTab(tabId) {
  // Hide all screens
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  
  // Close profile dropdown
  const dropdown = document.getElementById("profile-dropdown");
  if (dropdown) {
    dropdown.classList.remove("open");
  }
  
  // Show target screen
  const screen = document.getElementById(`screen-${tabId}-tab`);
  if (screen) {
    screen.classList.add("active");
  }
  
  // Update desktop active navigation highlights
  document.querySelectorAll(".recipient-nav-item").forEach(item => {
    item.classList.toggle("active", item.dataset.tab === tabId);
  });
  
  // Update mobile drawer active states
  document.querySelectorAll(".recipient-mobile-nav-item").forEach(item => {
    item.classList.toggle("active", item.dataset.tab === tabId);
  });
  
  // Render list when visiting the available food tab
  if (tabId === "available") {
    renderAvailableFoodList();
  }
  
  // Render list when visiting the reservations tab
  if (tabId === "reservations") {
    renderReservationsList();
  }
  
  // Render list when visiting the pickup schedule tab
  if (tabId === "schedule") {
    renderPickupSchedule();
  }
  
  // Populate form fields for Profile & Settings
  if (tabId === "profile") {
    populateProfileFields();
  }
  if (tabId === "settings") {
    populateSettingsFields();
  }
  if (tabId === "chat") {
    renderConversations();
  }
  
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function initDashboardNavigation() {
  // Wire desktop & mobile navigation clicks
  document.querySelectorAll(".recipient-nav-item, .recipient-mobile-nav-item").forEach(item => {
    item.addEventListener("click", () => {
      const tab = item.dataset.tab;
      showDashboardTab(tab);
      
      // Close mobile drawer if open
      const drawer = document.getElementById("mobile-drawer");
      const overlay = document.getElementById("drawer-overlay");
      if (drawer) drawer.classList.remove("open");
      if (overlay) overlay.classList.remove("open");
    });
  });

  // Mobile Hamburger Toggle
  const burger = document.getElementById("mobile-hamburger");
  const drawer = document.getElementById("mobile-drawer");
  const overlay = document.getElementById("drawer-overlay");
  const drawerClose = document.getElementById("drawer-close");

  if (burger) {
    burger.addEventListener("click", () => {
      drawer.classList.add("open");
      overlay.classList.add("open");
    });
  }
  if (drawerClose) {
    drawerClose.addEventListener("click", () => {
      drawer.classList.remove("open");
      overlay.classList.remove("open");
    });
  }
  if (overlay) {
    overlay.addEventListener("click", () => {
      drawer.classList.remove("open");
      overlay.classList.remove("open");
    });
  }

  // Wire profile dropdown trigger on desktop wood nav
  const profileTrigger = document.getElementById("nav-profile-menu-trigger");
  const dropdownMenu = document.getElementById("profile-dropdown");
  if (profileTrigger && dropdownMenu) {
    profileTrigger.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdownMenu.classList.toggle("open");
    });
    
    // Close dropdown on click outside
    document.addEventListener("click", (e) => {
      if (!profileTrigger.contains(e.target) && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.remove("open");
      }
    });
  }
}

// =========================================================
// RECIPIENT AVAILABLE FOOD FILTERING & RENDERING (PHASE 1)
// =========================================================
let currentFilters = {
  search: "",
  category: "all",
  availability: "all",
  storage: "all",
  sort: "newest"
};

let recipientAvailableDonations = [];

function getDescriptionField(description, label) {
  const prefix = `${label}:`;
  const line = (description || "")
    .split(/\r?\n/)
    .find(item => item.startsWith(prefix));

  return line
    ? line.slice(prefix.length).trim()
    : "";
}

function mapFirestoreDonation(donation) {
  const quantityParts =
    String(donation.quantity || "").trim().split(/\s+/);
  const parsedQty = parseFloat(quantityParts[0]);

  return {
    id: donation.id,
    foodName: donation.title || "Untitled Donation",
    foodCategory:
      getDescriptionField(donation.description, "Category") || "Other",
    foodQty: Number.isNaN(parsedQty) ? 0 : parsedQty,
    foodUnit: quantityParts.slice(1).join(" ") || "",
    foodExpiry:
      getDescriptionField(donation.description, "Expiry") || "",
    foodDesc:
      getDescriptionField(donation.description, "Description"),
    pickupAvail:
      getDescriptionField(donation.description, "Pickup availability") ||
      "Not specified",
    storageReq:
      getDescriptionField(donation.description, "Storage requirements"),
    pickupInstructions:
      getDescriptionField(donation.description, "Pickup instructions"),
    specialNotes:
      getDescriptionField(donation.description, "Special notes"),
    donorName: "Nourish & Share Donor",
    photos: [],
    date: "",
      pickupAddress: donation.pickupAddress || "",
    pickupLocation: donation.pickupLocation || null,
};
}

async function waitForRecipientData() {
  if (!window.NourishShareRecipientData) {
    await import("./data-adapter.js?v=20260823f");
  }

  if (!window.NourishShareRecipientData) {
    throw new Error("Recipient data service failed to initialize.");
  }

  return window.NourishShareRecipientData;
}

function getAvailableDonations() {
  return recipientAvailableDonations;
}

async function renderAvailableFoodList() {
  const container = document.getElementById("listings-cards-list");
  if (!container) return;

  try {
    const recipientData = await waitForRecipientData();
    const firestoreDonations =
      await recipientData.getAvailableDonations();
    recipientAvailableDonations =
      firestoreDonations.map(mapFirestoreDonation);
  } catch (error) {
    console.error("Could not load available donations:", error);
    recipientAvailableDonations = [];
  }
  
  await renderFoodAccessMap(recipientAvailableDonations);

  const allDonations = getAvailableDonations();
  
  // Apply filters
  let filtered = allDonations.filter(d => {
    // Search match
    if (currentFilters.search) {
      const q = currentFilters.search.toLowerCase();
      const nameMatch = d.foodName && d.foodName.toLowerCase().includes(q);
      const catMatch = d.foodCategory && d.foodCategory.toLowerCase().includes(q);
      const donorMatch = d.donorName && d.donorName.toLowerCase().includes(q);
      const descMatch = d.foodDesc && d.foodDesc.toLowerCase().includes(q);
      if (!nameMatch && !catMatch && !donorMatch && !descMatch) return false;
    }
    
    // Category match
    if (currentFilters.category !== "all") {
      if (d.foodCategory !== currentFilters.category) return false;
    }
    
    // Pickup Availability match
    if (currentFilters.availability !== "all") {
      const avail = (d.pickupAvail || "").toLowerCase();
      if (currentFilters.availability === "weekdays" && !avail.includes("weekday") && !avail.includes("mon") && !avail.includes("fri")) {
        return false;
      }
      if (currentFilters.availability === "daily" && !avail.includes("daily") && !avail.includes("every")) {
        return false;
      }
    }
    
    // Storage match
    if (currentFilters.storage !== "all") {
      const storage = (d.storageReq || "").toLowerCase();
      if (d.storageReq !== currentFilters.storage && !storage.includes(currentFilters.storage.toLowerCase())) {
        return false;
      }
    }
    
    return true;
  });
  
  // Apply sorting
  if (currentFilters.sort === "newest") {
    filtered.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
  } else if (currentFilters.sort === "oldest") {
    filtered.sort((a, b) => new Date(a.date || 0) - new Date(b.date || 0));
  }
  
  // Update showing count label
  const countLabel = document.getElementById("showing-donations-count");
  if (countLabel) {
    countLabel.textContent = `Showing ${filtered.length} available donations`;
  }
  
  // Render list
  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state-container">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--ink-faint)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin: 0 auto 12px; display: block;">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <p>No available donations at this time. Check back later!</p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = filtered.map(d => {
    // Map category to CSS class
    let catClass = "produce";
    if (d.foodCategory === "Bakery") catClass = "bakery";
    else if (d.foodCategory === "Dairy") catClass = "dairy";
    else if (d.foodCategory === "Prepared meals") catClass = "prepared";
    else if (d.foodCategory === "Packaged goods") catClass = "packaged";
    else if (d.foodCategory === "Meat & seafood") catClass = "meat";
    
    // Use fallback photos if not provided or empty
    let photoSrc = "../Donor/mock_apples.jpg";
    if (d.photos && d.photos.length > 0) {
      photoSrc = d.photos[0];
    } else {
      if (d.foodCategory === "Bakery") photoSrc = "../Donor/mock_bread.jpg";
      else if (d.foodCategory === "Produce" && d.foodName.toLowerCase().includes("tomato")) photoSrc = "../Donor/mock_tomatoes.jpg";
    }
    
    const donor = d.donorName || "Green Valley Farms";
    const dateFormatted = d.foodExpiry ? formatDate(d.foodExpiry) : "N/A";
    
    return `
      <div class="food-card" data-id="${d.id}">
        <div class="food-card-img">
          <img src="${photoSrc}" alt="${d.foodName}" onerror="this.src='../Donor/mock_apples.jpg'">
        </div>
        <div class="food-card-content">
          <div class="food-card-top">
            <div class="food-card-title-row">
              <h3 class="food-card-title">${escapeHtml(d.foodName)}</h3>
              <button class="btn-favorite" onclick="toggleFavorite('${d.id}')" aria-label="Add to favorites">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                </svg>
              </button>
            </div>
            <span class="food-card-category ${catClass}">${d.foodCategory}</span>
            <p class="food-card-desc">${escapeHtml(d.foodDesc || "No description provided.")}</p>
          </div>
          <div class="food-card-donor">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 3.5 2 7a7 7 0 0 1-7 7h-3"></path>
            </svg>
            Donated by: ${escapeHtml(donor)}
          </div>
        </div>
        <div class="food-card-details">
          <div class="food-card-info-list">
            <div class="info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 8v4l3 3"></path>
              </svg>
              <span>Quantity: <span class="qty-badge">${d.foodQty} ${d.foodUnit}</span></span>
            </div>
            <div class="info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
              <span>Best Before: <strong>${dateFormatted}</strong></span>
            </div>
            <div class="info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="10" r="3"></circle>
                <path d="M12 21c-3.6-3.8-6-7.2-6-11a6 6 0 1 1 12 0c0 3.8-2.4 7.2-6 11z"></path>
              </svg>
              <span>Pickup: <strong>${escapeHtml(d.pickupAvail)}</strong></span>
            </div>
          </div>
          <button class="btn btn-primary btn-reserve" onclick="reserveFoodItem('${d.id}')">Reserve Food</button>
        </div>
      </div>
    `;
  }).join("");
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  const options = { month: 'short', day: 'numeric', year: 'numeric' };
  return d.toLocaleDateString('en-US', options);
}

function applyAvailableFilters(event) {
  event.preventDefault();
  currentFilters.search = document.getElementById("filter-search").value;
  currentFilters.category = document.getElementById("filter-category").value;
  currentFilters.availability = document.getElementById("filter-availability").value;
  currentFilters.storage = document.getElementById("filter-storage").value;
  currentFilters.sort = document.getElementById("filter-sort").value;
  renderAvailableFoodList();
}

function resetAvailableFilters() {
  document.getElementById("form-available-filters").reset();
  currentFilters = {
    search: "",
    category: "all",
    availability: "all",
    storage: "all",
    sort: "newest"
  };
  renderAvailableFoodList();
}

async function reserveFoodItem(id) {
  try {
    const recipientData = await waitForRecipientData();
    await recipientData.reserveDonation(id);

    alert("Food item reserved successfully!");
    await renderAvailableFoodList();
  } catch (error) {
    console.error("Reservation failed:", error);
    alert(error.message || "Food item could not be reserved.");
  }
}

function toggleFavorite(id) {
  const btn = document.querySelector(`.food-card[data-id="${id}"] .btn-favorite`);
  if (btn) {
    btn.classList.toggle("active");
  }
}

// =========================================================
// RECIPIENT MY RESERVATIONS CONTROLLERS (PHASE 2)
// =========================================================
let reservationsFilters = {
  search: "",
  status: "all",
  category: "all",
  date: ""
};

let recipientReservations = [];

function getReservedDonations() {
  return recipientReservations;
}

async function renderReservationsList() {
  const container = document.getElementById("reservations-cards-list");
  if (!container) return;

  try {
    const recipientData = await waitForRecipientData();
    const reservationDetails =
      await recipientData.getMyReservationDetails();

    recipientReservations = reservationDetails
      .filter(item => item.donation)
      .map(item => ({
        ...mapFirestoreDonation(item.donation),
        status: "Pending",
      }));
  } catch (error) {
    console.error("Could not load reservations:", error);
    recipientReservations = [];
  }
  
  const allReserved = getReservedDonations();
  
  // Apply filters
  let filtered = allReserved.filter(d => {
    // Search match
    if (reservationsFilters.search) {
      const q = reservationsFilters.search.toLowerCase();
      const nameMatch = d.foodName && d.foodName.toLowerCase().includes(q);
      const donorMatch = d.donorName && d.donorName.toLowerCase().includes(q);
      const statusMatch = d.status && d.status.toLowerCase().includes(q);
      if (!nameMatch && !donorMatch && !statusMatch) return false;
    }
    
    // Status match
    if (reservationsFilters.status !== "all") {
      let currentStatus = d.status;
      if (currentStatus === "Reserved") currentStatus = "Pending"; // fallback
      if (currentStatus !== reservationsFilters.status) return false;
    }
    
    // Category match
    if (reservationsFilters.category !== "all") {
      if (d.foodCategory !== reservationsFilters.category) return false;
    }
    
    // Date match (approx check on expiration or date formatted check)
    if (reservationsFilters.date) {
      const qDate = reservationsFilters.date.toLowerCase();
      const dateStr = d.foodExpiry || "";
      if (!dateStr.toLowerCase().includes(qDate)) return false;
    }
    
    return true;
  });
  
  // Update showing count
  const countLabel = document.getElementById("showing-reservations-count");
  if (countLabel) {
    countLabel.textContent = `Showing ${filtered.length} reservations`;
  }
  
  // Render
  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state-container">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--ink-faint)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin: 0 auto 12px; display: block;">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
        </svg>
        <p>No reservations at this time. Go to Available Food to reserve items!</p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = filtered.map(d => {
    // Map category
    let catClass = "produce";
    if (d.foodCategory === "Bakery") catClass = "bakery";
    else if (d.foodCategory === "Dairy") catClass = "dairy";
    else if (d.foodCategory === "Prepared meals") catClass = "prepared";
    else if (d.foodCategory === "Packaged goods") catClass = "packaged";
    else if (d.foodCategory === "Meat & seafood") catClass = "meat";
    
    // Use fallback photos
    let photoSrc = "../Donor/mock_apples.jpg";
    if (d.photos && d.photos.length > 0) {
      photoSrc = d.photos[0];
    } else {
      if (d.foodCategory === "Bakery") photoSrc = "../Donor/mock_bread.jpg";
      else if (d.foodCategory === "Produce" && d.foodName.toLowerCase().includes("tomato")) photoSrc = "../Donor/mock_tomatoes.jpg";
    }
    
    const donor = d.donorName || "Green Valley Farms";
    
    // Status cycle mapping
    let currentStatus = d.status || "Pending";
    if (currentStatus === "Reserved") currentStatus = "Pending";
    let statusClass = currentStatus.toLowerCase().replace(/\s+/g, "");
    
    // Format reserve/submit date
    const dateFormatted = d.date ? formatDate(d.date) : "Aug 20, 2025";
    
    return `
      <div class="food-card" data-id="${d.id}">
        <div class="food-card-img">
          <img src="${photoSrc}" alt="${d.foodName}" onerror="this.src='../Donor/mock_apples.jpg'">
        </div>
        <div class="food-card-content">
          <div class="food-card-top">
            <h3 class="food-card-title">${escapeHtml(d.foodName)}</h3>
            <span class="food-card-category ${catClass}">${d.foodCategory}</span>
          </div>
          <div class="food-card-donor">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 3.5 2 7a7 7 0 0 1-7 7h-3"></path>
            </svg>
            Donated by: ${escapeHtml(donor)}
          </div>
        </div>
        <div class="food-card-details" style="flex-direction: row; width: 62%; gap: 16px; border-left: 1px dashed var(--kraft-line); padding-left: 20px;">
          <div style="flex: 1; display: flex; flex-direction: column; gap: 12px; justify-content: center;">
            <div class="info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 8v4l3 3"></path>
              </svg>
              <span>Quantity: <strong class="qty-badge" style="background:#EAF0EB; color:#345D42;">${d.foodQty} ${d.foodUnit}</strong></span>
            </div>
            <div class="info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
              <span>Reserved on: <strong>${dateFormatted}</strong></span>
            </div>
          </div>
          
          <div style="flex: 1.1; display: flex; flex-direction: column; gap: 12px; justify-content: center;">
            <div class="info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="10" r="3"></circle>
                <path d="M12 21c-3.6-3.8-6-7.2-6-11a6 6 0 1 1 12 0c0 3.8-2.4 7.2-6 11z"></path>
              </svg>
              <span>Pickup: <strong>${escapeHtml(d.pickupAvail)}</strong></span>
            </div>
            <div class="info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
              </svg>
              <span>Status: <span class="status-badge ${statusClass}">${currentStatus}</span></span>
            </div>
          </div>
          
          <div style="display: flex; flex-direction: column; gap: 8px; align-items: stretch; justify-content: center; width: 150px;">
            <button class="btn-view-details" onclick="showReservationDetails('${d.id}')" style="width: 100%; justify-content: center;">
              View Details
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
            </button>
            <button class="btn btn-secondary btn-chat-partner" onclick="openChatWithReservation('${d.id}')" style="padding: 10px 16px; font-size: 0.85rem; font-weight: 600; display: inline-flex; align-items: center; justify-content: center; gap: 6px; border: 1px solid var(--kraft-line); border-radius: 6px; cursor: pointer; transition: all 0.2s; background: #FFF;">
              <i class="fa-solid fa-comment"></i>
              Chat with Donor
            </button>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function showReservationDetails(id) {
  const donations = recipientReservations;
  const d = donations.find(d => d.id === id);
  if (d) {
    document.getElementById("modal-food-name").textContent = d.foodName || "Reservation Details";
    document.getElementById("modal-category").textContent = d.foodCategory || "N/A";
    document.getElementById("modal-qty").textContent = `${d.foodQty || 0} ${d.foodUnit || ""}`;
    document.getElementById("modal-donor").textContent = d.donorName || "Green Valley Farms";
    
    // Status style inside modal
    let currentStatus = d.status || "Pending";
    if (currentStatus === "Reserved") currentStatus = "Pending";
    const modalStatus = document.getElementById("modal-status");
    modalStatus.textContent = currentStatus;
    modalStatus.className = "status-badge " + currentStatus.toLowerCase().replace(/\s+/g, "");
    
    document.getElementById("modal-storage").textContent = d.storageReq || "Ambient";
    document.getElementById("modal-pickup-instructions").textContent = d.pickupInstructions || "No pickup instructions provided.";
    
    const notesRow = document.getElementById("modal-notes-row");
    if (d.specialNotes) {
      notesRow.style.display = "block";
      document.getElementById("modal-notes").textContent = d.specialNotes;
    } else {
      notesRow.style.display = "none";
    }
    
    document.getElementById("res-detail-modal").style.display = "flex";
  }
}

function closeResDetailModal() {
  document.getElementById("res-detail-modal").style.display = "none";
}

function applyReservationsFilters(event) {
  event.preventDefault();
  reservationsFilters.search = document.getElementById("res-filter-search").value;
  reservationsFilters.status = document.getElementById("res-filter-status").value;
  reservationsFilters.category = document.getElementById("res-filter-category").value;
  reservationsFilters.date = document.getElementById("res-filter-date").value;
  renderReservationsList();
}

function resetReservationsFilters() {
  document.getElementById("form-reservations-filters").reset();
  reservationsFilters = {
    search: "",
    status: "all",
    category: "all",
    date: ""
  };
  renderReservationsList();
}

// =========================================================
// RECIPIENT PICKUP SCHEDULE CONTROLLERS (PHASE 3)
// =========================================================
async function renderPickupSchedule() {
  try {
    const recipientData = await waitForRecipientData();
    const reservationDetails =
      await recipientData.getMyReservationDetails();

    recipientReservations = reservationDetails
      .filter(item => item.donation)
      .map(item => ({
        ...mapFirestoreDonation(item.donation),
        status: "Pending",
      }));
  } catch (error) {
    console.error("Could not load pickup schedule:", error);
    recipientReservations = [];
  }

  const allReserved = getReservedDonations();
  
  // Group into Upcoming, Pending, Transit, Completed
  const upcomingList = allReserved.filter(d => d.status === "Confirmed" || d.status === "Ready for Pickup" || d.status === "In Transit");
  const pendingList = allReserved.filter(d => d.status === "Pending" || d.status === "Reserved");
  const transitList = allReserved.filter(d => d.status === "In Transit");
  const completedList = allReserved.filter(d => d.status === "Completed");
  
  // Update stats counters
  const elUpcoming = document.getElementById("sched-stat-upcoming");
  const elPending = document.getElementById("sched-stat-pending");
  const elTransit = document.getElementById("sched-stat-transit");
  const elCompleted = document.getElementById("sched-stat-completed");
  
  if (elUpcoming) elUpcoming.textContent = upcomingList.length;
  if (elPending) elPending.textContent = pendingList.length;
  if (elTransit) elTransit.textContent = transitList.length;
  if (elCompleted) elCompleted.textContent = completedList.length;
  
  // Render Upcoming List
  const upcomingWrapper = document.getElementById("list-upcoming-pickups");
  if (upcomingWrapper) {
    if (upcomingList.length === 0) {
      upcomingWrapper.innerHTML = `
        <div class="empty-state-container" style="border: 1px dashed #A5D6A7; background: #F1F8E9; padding: 24px; text-align: center; border-radius: 12px;">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#388E3C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin: 0 auto 12px; display: block;">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
          <h4 style="margin: 0 0 6px; font-size: 0.95rem; font-weight: 700; color: var(--ink);">No upcoming pickups scheduled.</h4>
          <p style="margin: 0; font-size: 0.85rem; color: var(--ink-soft);">Once a pickup is scheduled, it will appear here.</p>
        </div>
      `;
    } else {
      upcomingWrapper.innerHTML = upcomingList.map(d => renderPickupCard(d)).join("");
    }
  }
  
  // Render Pending List
  const pendingWrapper = document.getElementById("list-pending-pickups");
  if (pendingWrapper) {
    if (pendingList.length === 0) {
      pendingWrapper.innerHTML = `
        <div class="empty-state-container" style="border: 1px dashed #FFCC80; background: #FFF8E1; padding: 24px; text-align: center; border-radius: 12px;">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#E65100" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin: 0 auto 12px; display: block;">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          <h4 style="margin: 0 0 6px; font-size: 0.95rem; font-weight: 700; color: var(--ink);">No pending pickup requests.</h4>
          <p style="margin: 0; font-size: 0.85rem; color: var(--ink-soft);">Any pickup requests waiting to be scheduled will appear here.</p>
        </div>
      `;
    } else {
      pendingWrapper.innerHTML = pendingList.map(d => renderPickupCard(d)).join("");
    }
  }
  
  // Render Completed List
  const completedWrapper = document.getElementById("list-completed-pickups");
  if (completedWrapper) {
    if (completedList.length === 0) {
      completedWrapper.innerHTML = `
        <div class="empty-state-container" style="border: 1px dashed #A5D6A7; background: #F1F8E9; padding: 24px; text-align: center; border-radius: 12px;">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#1B5E20" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin: 0 auto 12px; display: block;">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
          <h4 style="margin: 0 0 6px; font-size: 0.95rem; font-weight: 700; color: var(--ink);">No completed pickups yet.</h4>
          <p style="margin: 0; font-size: 0.85rem; color: var(--ink-soft);">Your completed pickups will be shown here.</p>
        </div>
      `;
    } else {
      completedWrapper.innerHTML = completedList.map(d => renderPickupCard(d)).join("");
    }
  }
}

function renderPickupCard(d) {
  let catClass = "produce";
  if (d.foodCategory === "Bakery") catClass = "bakery";
  else if (d.foodCategory === "Dairy") catClass = "dairy";
  else if (d.foodCategory === "Prepared meals") catClass = "prepared";
  else if (d.foodCategory === "Packaged goods") catClass = "packaged";
  else if (d.foodCategory === "Meat & seafood") catClass = "meat";
  
  let photoSrc = "../Donor/mock_apples.jpg";
  if (d.photos && d.photos.length > 0) {
    photoSrc = d.photos[0];
  } else {
    if (d.foodCategory === "Bakery") photoSrc = "../Donor/mock_bread.jpg";
    else if (d.foodCategory === "Produce" && d.foodName.toLowerCase().includes("tomato")) photoSrc = "../Donor/mock_tomatoes.jpg";
  }
  
  const donor = d.donorName || "Green Valley Farms";
  
  let currentStatus = d.status || "Pending";
  if (currentStatus === "Reserved") currentStatus = "Pending";
  let statusClass = currentStatus.toLowerCase().replace(/\s+/g, "");
  
  return `
    <div class="food-card" data-id="${d.id}" style="margin-bottom: 12px;">
      <div class="food-card-img">
        <img src="${photoSrc}" alt="${d.foodName}" onerror="this.src='../Donor/mock_apples.jpg'">
      </div>
      <div class="food-card-content">
        <div class="food-card-top">
          <h3 class="food-card-title">${escapeHtml(d.foodName)}</h3>
          <span class="food-card-category ${catClass}">${d.foodCategory}</span>
        </div>
        <div class="food-card-donor">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 3.5 2 7a7 7 0 0 1-7 7h-3"></path>
          </svg>
          Donated by: ${escapeHtml(donor)}
        </div>
      </div>
      <div class="food-card-details" style="flex-direction: row; width: 62%; gap: 16px; border-left: 1px dashed var(--kraft-line); padding-left: 20px;">
        <div style="flex: 1; display: flex; flex-direction: column; gap: 12px; justify-content: center;">
          <div class="info-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M12 8v4l3 3"></path>
            </svg>
            <span>Quantity: <strong class="qty-badge" style="background:#EAF0EB; color:#345D42;">${d.foodQty} ${d.foodUnit}</strong></span>
          </div>
          <div class="info-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
            <span>Pickup Date: <strong>${d.foodExpiry ? formatDate(d.foodExpiry) : "Aug 25, 2025"}</strong></span>
          </div>
        </div>
        
        <div style="flex: 1.1; display: flex; flex-direction: column; gap: 12px; justify-content: center;">
          <div class="info-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="10" r="3"></circle>
              <path d="M12 21c-3.6-3.8-6-7.2-6-11a6 6 0 1 1 12 0c0 3.8-2.4 7.2-6 11z"></path>
            </svg>
            <span>Pickup: <strong>${escapeHtml(d.pickupAvail)}</strong></span>
          </div>
          <div class="info-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M12 8v4l3 3"></path>
            </svg>
            <span>Status: <span class="status-badge ${statusClass}">${currentStatus}</span></span>
          </div>
        </div>
        
        <div style="display: flex; align-items: center; justify-content: flex-end;">
          <button class="btn-view-details" onclick="showReservationDetails('${d.id}')">
            View Details
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>
        </div>
      </div>
    </div>
  `;
}

// =========================================================
// RECIPIENT PROFILE, SETTINGS & LOGOUT CONTROLLERS (PHASE 4)
// =========================================================
async function populateProfileFields() {
  try {
    const recipientData = await waitForRecipientData();
    const userProfile = await recipientData.getCurrentUserProfile();

    if (userProfile?.profile) {
      state.recipientType = userProfile.profile.recipientType || state.recipientType;
      state.org = userProfile.profile.org || state.org || {};
      state.contact = userProfile.profile.contact || state.contact || {};
      state.capacity = userProfile.profile.capacity || state.capacity || {};

      const avatarUrl = userProfile.profile.avatarUrl || "";
      if (avatarUrl) {
        state.profilePhoto = avatarUrl;
        state.avatarDataUrl = avatarUrl;
      }
    }

    if (userProfile?.displayName && !state.contact?.ctName) {
      if (!state.contact) state.contact = {};
      state.contact.ctName = userProfile.displayName;
    }
  } catch (error) {
    console.error("Could not load recipient profile:", error);
  }

  if (!state.org) state.org = {};
  if (!state.contact) state.contact = {};
  if (!state.capacity) state.capacity = {};

  document.getElementById("prof-org-name").value = state.org.orgName || "";

  const typeName = RECIPIENT_TYPES.find(t => t.id === state.recipientType)?.name || "Food Pantry";
  document.getElementById("prof-recipient-type").value = typeName;

  document.getElementById("prof-org-address").value = state.org.orgAddress || "";
  document.getElementById("prof-org-license").value = state.org.orgLicense || "";
  document.getElementById("prof-org-years").value = state.org.orgYears || "";
  document.getElementById("prof-org-website").value = state.org.orgWebsite || "";

  document.getElementById("prof-ct-name").value = state.contact.ctName || "";
  document.getElementById("prof-ct-title").value = state.contact.ctTitle || "";
  document.getElementById("prof-ct-phone").value = state.contact.ctPhone || "";
  document.getElementById("prof-ct-email").value = state.contact.ctEmail || "";
  document.getElementById("prof-ct-method").value = state.contact.ctMethod || "Email";

  const cats = state.capacity.foodCategories || [];
  document.querySelectorAll('input[name="profFoodCategories"]').forEach(cb => {
    cb.checked = cats.includes(cb.value);
  });

  normalizeRecipientAvatarState();
  const imgUrl = state.profilePhoto || "default_avatar.jpg";
  updateAvatarPreviews(imgUrl);

  hydrateDropdownLabels();
}

function hydrateDropdownLabels() {
  const elName = document.getElementById("dropdown-donor-name");
  const elType = document.getElementById("dropdown-donor-type");
  
  if (elName) elName.textContent = state.contact.ctName || "Sarah Jenkins";
  if (elType) elType.textContent = (state.org.orgName || "Hope Food Pantry") + " / " + (state.contact.ctTitle || "Coordinator");
}

function updateAvatarPreviews(imgUrl) {
  const ids = ["profile-view-avatar", "profile-edit-avatar-preview", "header-avatar", "mobile-header-avatar"];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.style.backgroundImage = `url('${imgUrl}')`;
    }
  });
}

async function handleProfilePhotoChange(event) {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const { uploadProfileImage } = await import("../cloudinaryUpload.js?v=20260823a");
    const imageUrl = await uploadProfileImage(file);

    state.profilePhoto = imageUrl;
    localStorage.setItem("recipient_onboarding_state", JSON.stringify(state));
    updateAvatarPreviews(imageUrl);
  } catch (error) {
    console.error("Could not upload recipient profile photo:", error);
    alert(error.message || "Profile photo could not be uploaded.");
    event.target.value = "";
  }
}

async function saveProfileChanges(event) {
  event.preventDefault();

  state.org.orgName = document.getElementById("prof-org-name").value;
  state.org.orgAddress = document.getElementById("prof-org-address").value;
  state.org.orgLicense = document.getElementById("prof-org-license").value;
  state.org.orgYears = document.getElementById("prof-org-years").value;
  state.org.orgWebsite = document.getElementById("prof-org-website").value;

  state.contact.ctName = document.getElementById("prof-ct-name").value;
  state.contact.ctTitle = document.getElementById("prof-ct-title").value;
  state.contact.ctPhone = document.getElementById("prof-ct-phone").value;
  state.contact.ctEmail = document.getElementById("prof-ct-email").value;
  state.contact.ctMethod = document.getElementById("prof-ct-method").value;

  const checkedCats = [];
  document.querySelectorAll('input[name="profFoodCategories"]:checked').forEach(cb => {
    checkedCats.push(cb.value);
  });
  state.capacity.foodCategories = checkedCats;

  try {
    const recipientData = await waitForRecipientData();

    await recipientData.saveUserProfile({
      displayName: state.contact.ctName || state.org.orgName,
      profile: {
        recipientType: state.recipientType,
        org: state.org,
        contact: state.contact,
        capacity: state.capacity,
        avatarUrl: state.profilePhoto || "",
      },
    });

    localStorage.setItem("recipient_onboarding_state", JSON.stringify(state));

    hydrateDropdownLabels();
    const imgUrl = state.profilePhoto || "default_avatar.jpg";
    updateAvatarPreviews(imgUrl);

    alert("Profile changes saved successfully!");
    showDashboardTab("dashboard");
  } catch (error) {
    console.error("Could not save recipient profile:", error);
    alert(error.message || "Profile could not be saved.");
  }
}

function populateSettingsFields() {
  if (!state.settings) {
    state.settings = {
      notifyEmail: true,
      notifySms: true
    };
  }
  
  document.getElementById("set-notify-email").checked = state.settings.notifyEmail;
  document.getElementById("set-notify-sms").checked = state.settings.notifySms;
  
  // Clear password inputs
  document.getElementById("set-pass-current").value = "";
  document.getElementById("set-pass-new").value = "";
  document.getElementById("set-pass-confirm").value = "";
  
  const hint = document.getElementById("set-pass-hint");
  if (hint) hint.hidden = true;
}

async function saveSettingsChanges(event) {
  event.preventDefault();

  if (!state.settings) state.settings = {};
  state.settings.notifyEmail = document.getElementById("set-notify-email").checked;
  state.settings.notifySms = document.getElementById("set-notify-sms").checked;

  const currentPassInput = document.getElementById("set-pass-current").value;
  const newPassInput = document.getElementById("set-pass-new").value;
  const confirmPassInput = document.getElementById("set-pass-confirm").value;
  const hint = document.getElementById("set-pass-hint");

  const passwordChangeRequested =
    currentPassInput || newPassInput || confirmPassInput;

  if (passwordChangeRequested) {
    if (!currentPassInput) {
      if (hint) {
        hint.textContent = "Enter your current password.";
        hint.hidden = false;
      }
      return;
    }

    if (newPassInput.length < 8) {
      if (hint) {
        hint.textContent = "New password must be at least 8 characters long.";
        hint.hidden = false;
      }
      return;
    }

    if (newPassInput !== confirmPassInput) {
      if (hint) {
        hint.textContent = "Passwords do not match.";
        hint.hidden = false;
      }
      return;
    }
  }

  try {
    const recipientData = await waitForRecipientData();

    if (passwordChangeRequested) {
      await recipientData.changePassword(
        currentPassInput,
        newPassInput
      );
    }

    await recipientData.saveUserSettings(state.settings);

    localStorage.setItem("recipient_onboarding_state", JSON.stringify(state));

    if (hint) hint.hidden = true;

    document.getElementById("set-pass-current").value = "";
    document.getElementById("set-pass-new").value = "";
    document.getElementById("set-pass-confirm").value = "";

    alert(
      passwordChangeRequested
        ? "Password and settings saved successfully!"
        : "Settings preferences saved successfully!"
    );

    showDashboardTab("dashboard");
  } catch (error) {
    console.error("Could not save recipient settings:", error);

    if (hint && error?.code === "auth/invalid-credential") {
      hint.textContent = "Current password is incorrect.";
      hint.hidden = false;
      return;
    }

    if (hint && error?.code === "auth/wrong-password") {
      hint.textContent = "Current password is incorrect.";
      hint.hidden = false;
      return;
    }

    alert(error.message || "Settings could not be saved.");
  }
}

async function logoutUser() {
  sessionStorage.removeItem("nourishshare_verified_workspace");
  try {
    if (!window.NourishShareRecipientData?.logout) {
      throw new Error(
        "Logout service is not available."
      );
    }

    await window.NourishShareRecipientData.logout();

    localStorage.removeItem(
      "recipient_onboarding_state"
    );

    window.location.href =
      "../../public/login.html";
  } catch (error) {
    console.error("Could not log out:", error);
    alert("Could not log out. Please try again.");
  }
}

// Update initialization to load saved onboarding state & dropdown labels on start
const originalInit = init;
init = function() {
  const savedState = localStorage.getItem("recipient_onboarding_state");
  if (savedState) {
    try {
      Object.assign(state, JSON.parse(savedState));
      // Update dropdown labels & avatars on boot if session is already active
      hydrateDropdownLabels();
      normalizeRecipientAvatarState();
      updateAvatarPreviews(state.profilePhoto || "default_avatar.jpg");
    } catch (e) {
      console.error("Error loading recipient onboarding state:", e);
    }
  }
  originalInit();

  // Hydrate the current Firestore profile on every authenticated boot.
  // This keeps dashboard/header presentation in sync even before
  // the user opens the Profile tab.
  void (async () => {
    try {
      const recipientData = await waitForRecipientData();
      const userProfile = await recipientData.getCurrentUserProfile();

      if (!userProfile?.profile) return;

      state.recipientType =
        userProfile.profile.recipientType ||
        state.recipientType;

      state.org =
        userProfile.profile.org ||
        state.org ||
        {};

      state.contact =
        userProfile.profile.contact ||
        state.contact ||
        {};

      state.capacity =
        userProfile.profile.capacity ||
        state.capacity ||
        {};

      const avatarUrl =
        userProfile.profile.avatarUrl || "";

      if (avatarUrl) {
        state.profilePhoto = avatarUrl;
        state.avatarDataUrl = avatarUrl;
      }

      if (userProfile.displayName && !state.contact?.ctName) {
        if (!state.contact) state.contact = {};
        state.contact.ctName = userProfile.displayName;
      }

      localStorage.setItem(
        "recipient_onboarding_state",
        JSON.stringify(state)
      );

      normalizeRecipientAvatarState();
      hydrateDropdownLabels();

      updateAvatarPreviews(
        state.profilePhoto || "default_avatar.jpg"
      );
    } catch (error) {
      console.error(
        "Could not hydrate recipient profile on startup:",
        error
      );
    }
  })();
};


// =========================================================
// CHICAGO FOOD ACCESS MAP
// =========================================================

let foodAccessMap = null;
let foodResearchLayer = null;
let foodDonationLayer = null;
let chicagoResearchLocations = null;
let currentResearchMapFilter = "all";

function normalizeMapText(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[.,#]/g, "")
    .replace(/\s+/g, " ");
}

async function loadChicagoResearchLocations() {
  if (chicagoResearchLocations) {
    return chicagoResearchLocations;
  }

  const response = await fetch(
    "./data/chicago-food-access.json"
  );

  if (!response.ok) {
    throw new Error(
      `Chicago map data failed to load (${response.status}).`
    );
  }

  chicagoResearchLocations = await response.json();
  return chicagoResearchLocations;
}

function ensureFoodAccessMap() {
  const container =
    document.getElementById("food-access-map");

  if (!container) return null;

  if (!window.L) {
    throw new Error("Leaflet map library is unavailable.");
  }

  if (foodAccessMap) {
    return foodAccessMap;
  }

  foodAccessMap = L.map(
    "food-access-map",
    { scrollWheelZoom: false }
  ).setView(
    [41.83, -87.69],
    11
  );

  L.tileLayer(
    "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
    }
  ).addTo(foodAccessMap);

  foodResearchLayer =
    L.layerGroup().addTo(foodAccessMap);

  foodDonationLayer =
    L.layerGroup().addTo(foodAccessMap);

  document
    .querySelectorAll("[data-map-filter]")
    .forEach(button => {
      button.addEventListener("click", () => {
        currentResearchMapFilter =
          button.dataset.mapFilter || "all";

        document
          .querySelectorAll("[data-map-filter]")
          .forEach(item => {
            item.classList.toggle(
              "active",
              item === button
            );
          });

        renderResearchMapMarkers();
      });
    });

  return foodAccessMap;
}

function renderResearchMapMarkers() {
  if (
    !foodResearchLayer ||
    !Array.isArray(chicagoResearchLocations)
  ) {
    return;
  }

  foodResearchLayer.clearLayers();

  chicagoResearchLocations
    .filter(location =>
      currentResearchMapFilter === "all" ||
      location.type === currentResearchMapFilter
    )
    .forEach(location => {
      const latitude = Number(location.latitude);
      const longitude = Number(location.longitude);

      if (
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude)
      ) {
        return;
      }

      const isPantry =
        location.type === "food_pantry";

      const marker = L.circleMarker(
        [latitude, longitude],
        {
          radius: 6,
          color: isPantry ? "#315d87" : "#a96520",
          weight: 2,
          fillColor: isPantry ? "#4678a5" : "#d88a35",
          fillOpacity: 0.88
        }
      );

      const typeLabel =
        isPantry ? "Food Pantry" : "Grocery Store";

      const ratingText = location.rating
        ? `<p>Rating: ${escapeHtml(location.rating)}</p>`
        : "";

      marker.bindPopup(`
        <div class="food-map-popup">
          <h3>${escapeHtml(location.name)}</h3>
          <p class="food-map-popup-type">${typeLabel}</p>
          <p>${escapeHtml(location.communityArea)}</p>
          <p>${escapeHtml(location.address)}</p>
          ${ratingText}
        </div>
      `);

      marker.addTo(foodResearchLayer);
    });
}

function resolveDonationMapPoint(donation) {
  const latitude =
    Number(donation.pickupLocation?.latitude);

  const longitude =
    Number(donation.pickupLocation?.longitude);

  if (
    Number.isFinite(latitude) &&
    Number.isFinite(longitude)
  ) {
    return {
      latitude,
      longitude,
      address:
        donation.pickupAddress ||
        donation.pickupLocation?.address ||
        ""
    };
  }

  if (!Array.isArray(chicagoResearchLocations)) {
    return null;
  }

  const donationAddress =
    normalizeMapText(donation.pickupAddress);

  const donorName =
    normalizeMapText(donation.donorName);

  const match =
    chicagoResearchLocations.find(location => {
      const addressMatches =
        donationAddress &&
        normalizeMapText(location.address) ===
          donationAddress;

      const nameMatches =
        donorName &&
        normalizeMapText(location.name) ===
          donorName;

      return addressMatches || nameMatches;
    });

  if (!match) {
    return null;
  }

  return {
    latitude: Number(match.latitude),
    longitude: Number(match.longitude),
    address:
      donation.pickupAddress ||
      match.address ||
      ""
  };
}

function createLiveDonationMapIcon() {
  return L.divIcon({
    className: "food-map-live-marker",
    html: '<span class="food-map-live-pin"></span>',
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    popupAnchor: [0, -13]
  });
}

function renderLiveDonationMapMarkers(donations) {
  if (!foodDonationLayer) {
    return 0;
  }

  foodDonationLayer.clearLayers();

  let plotted = 0;

  donations.forEach(donation => {
    const point =
      resolveDonationMapPoint(donation);

    if (
      !point ||
      !Number.isFinite(point.latitude) ||
      !Number.isFinite(point.longitude)
    ) {
      return;
    }

    plotted += 1;

    const marker = L.marker(
      [point.latitude, point.longitude],
      {
        icon: createLiveDonationMapIcon(),
        zIndexOffset: 1000
      }
    );

    const quantityText = [
      donation.foodQty,
      donation.foodUnit
    ]
      .filter(Boolean)
      .join(" ");

    const quantityLine = quantityText
      ? `<p><strong>Quantity:</strong> ${escapeHtml(quantityText)}</p>`
      : "";

    const addressText = point.address
      ? `<p><strong>Pickup:</strong> ${escapeHtml(point.address)}</p>`
      : "";

    const availabilityText =
      donation.pickupAvail
        ? `<p><strong>Available:</strong> ${escapeHtml(donation.pickupAvail)}</p>`
        : "";

    const donationId =
      JSON.stringify(String(donation.id));

    marker.bindPopup(`
      <div class="food-map-popup">
        <h3>${escapeHtml(donation.foodName || "Available Food")}</h3>
        <p class="food-map-popup-type">Available Donation</p>
        <p>${escapeHtml(donation.donorName || "Donor Organization")}</p>
        ${quantityLine}
        ${addressText}
        ${availabilityText}

        <button
          type="button"
          class="food-map-reserve-btn"
          onclick='reserveFoodItem(${donationId})'
        >
          Reserve Donation
        </button>
      </div>
    `);

    marker.addTo(foodDonationLayer);
  });

  return plotted;
}

async function renderFoodAccessMap(donations = []) {
  const status =
    document.getElementById("food-map-status");

  try {
    await loadChicagoResearchLocations();

    const map = ensureFoodAccessMap();

    if (!map) return;

    renderResearchMapMarkers();

    const liveCount =
      renderLiveDonationMapMarkers(donations);

    if (status) {
      status.textContent =
        `${chicagoResearchLocations.length} research locations | ` +
        `${liveCount} live donation` +
        `${liveCount === 1 ? "" : "s"}`;
    }

    setTimeout(() => {
      map.invalidateSize();
    }, 50);

  } catch (error) {
    console.error(
      "Could not render Chicago Food Access Map:",
      error
    );

    if (status) {
      status.textContent =
        "Map temporarily unavailable.";
    }
  }
}


init();

// =========================================================
// SFRN CHAT SYSTEM CODE (RECIPIENT LOGIC)
// =========================================================
let activeConvoId = null;
let chatSearchQuery = "";
let firestoreChatMessages = [];

function getChatCurrentUser() {
  const onboardingState = JSON.parse(localStorage.getItem("recipient_onboarding_state") || "{}");
  return {
    email: onboardingState.account?.accEmail || onboardingState.contact?.ctEmail || "sarah@hopefoodpantry.org",
    name: onboardingState.org?.orgName || "Hope Food Pantry",
    role: "Recipient"
  };
}

function loadAllConversations() {
  const user = getChatCurrentUser();
  if (!user) return [];

  const conversations = [];
  const donations = recipientReservations;
  const messages = [...JSON.parse(localStorage.getItem("sfrn_chat_messages") || "[]"), ...firestoreChatMessages];

  // 1. Admin Support conversation
  conversations.push({
    id: `convo-admin-${user.email}`,
    partnerName: "Nourish & Share Admin",
    partnerEmail: "admin@nourishshare.org",
    partnerRole: "Admin",
    context: "Support Ticket"
  });

  // 2. Reservation-linked chats
  donations.forEach(d => {
    if (d.id) {
      conversations.push({
        id: `convo-donor-recipient-${d.id}`,
        partnerName: d.donorName || "Donor",
        partnerEmail: d.donorEmail || "donor@nourishshare.org",
        partnerRole: "Donor",
        context: `Regarding: ${d.foodName}`,
        photo: d.photoDataUrl || ""
      });
    }
  });

  // Populate last message details for each convo
  conversations.forEach(c => {
    const convoMsgs = messages.filter(m => m.convoId === c.id);
    if (convoMsgs.length > 0) {
      const last = convoMsgs[convoMsgs.length - 1];
      c.lastMsgText = last.text;
      c.lastMsgTime = last.timestamp;
    } else {
      c.lastMsgText = "No messages yet.";
      c.lastMsgTime = 0;
    }
  });

  // Sort conversations by last message timestamp (most recent first)
  conversations.sort((a, b) => b.lastMsgTime - a.lastMsgTime);

  return conversations;
}

function renderConversations() {
  const deck = document.getElementById("conversations-deck");
  if (!deck) return;

  const user = getChatCurrentUser();
  const convos = loadAllConversations();
  
  let filtered = convos.filter(c => {
    const nameMatch = c.partnerName.toLowerCase().includes(chatSearchQuery.toLowerCase());
    const roleMatch = c.partnerRole.toLowerCase().includes(chatSearchQuery.toLowerCase());
    const contextMatch = c.context.toLowerCase().includes(chatSearchQuery.toLowerCase());
    return nameMatch || roleMatch || contextMatch;
  });

  if (filtered.length === 0) {
    deck.innerHTML = `<div style="padding:24px; text-align:center; color:var(--ink-faint);">No conversations found.</div>`;
    return;
  }

  const readStatus = JSON.parse(localStorage.getItem("sfrn_chat_read_status") || "{}");

  deck.innerHTML = filtered.map(c => {
    const timeStr = c.lastMsgTime > 0 ? formatChatTime(c.lastMsgTime) : "";
    const activeClass = c.id === activeConvoId ? "active" : "";
    
    const lastRead = readStatus[c.id]?.[user.email] || 0;
    const isUnread = c.lastMsgTime > lastRead && c.lastMsgTime > 0;
    const unreadDot = isUnread ? `<span class="convo-unread"></span>` : "";

    const initials = c.partnerName.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
    const avatarHtml = c.photo 
      ? `<div class="convo-avatar" style="background-image: url('${c.photo}')"></div>`
      : `<div class="convo-avatar" style="display:flex; align-items:center; justify-content:center; background:#EAF0EB; color:var(--blue-dark); font-weight:700; font-family:var(--font-display);">${initials}</div>`;

    return `
      <div class="convo-item ${activeClass}" onclick="selectConversation('${c.id}')">
        ${avatarHtml}
        <div class="convo-info">
          <div class="convo-meta">
            <span class="convo-name">${c.partnerName}</span>
            <span class="convo-time">${timeStr}</span>
          </div>
          <div class="convo-preview-row">
            <span class="convo-preview">${c.lastMsgText}</span>
            ${unreadDot}
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function selectConversation(convoId) {
  activeConvoId = convoId;
  const user = getChatCurrentUser();
  const convos = loadAllConversations();
  const convo = convos.find(c => c.id === convoId);
  
  if (!convo) return;

  document.getElementById("chat-empty-state").style.display = "none";
  document.getElementById("chat-active-panel").style.display = "flex";

  document.getElementById("chat-conversations-list").classList.add("hidden-mobile");
  document.getElementById("chat-active-window").classList.add("active-mobile");

  document.getElementById("active-partner-name").textContent = convo.partnerName;
  document.getElementById("active-partner-role").textContent = convo.partnerRole;
  document.getElementById("active-context").textContent = convo.context;

  const initials = convo.partnerName.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
  const avatarContainer = document.getElementById("active-partner-avatar");
  if (convo.photo) {
    avatarContainer.style.backgroundImage = `url('${convo.photo}')`;
    avatarContainer.innerHTML = "";
  } else {
    avatarContainer.style.backgroundImage = "none";
    avatarContainer.style.display = "flex";
    avatarContainer.style.alignItems = "center";
    avatarContainer.style.justifyContent = "center";
    avatarContainer.style.background = "#EAF0EB";
    avatarContainer.style.color = "var(--blue-dark)";
    avatarContainer.style.fontWeight = "700";
    avatarContainer.innerHTML = initials;
  }

  const readStatus = JSON.parse(localStorage.getItem("sfrn_chat_read_status") || "{}");
  if (!readStatus[convoId]) readStatus[convoId] = {};
  readStatus[convoId][user.email] = Date.now();
  localStorage.setItem("sfrn_chat_read_status", JSON.stringify(readStatus));

  renderMessages();
  renderConversations();
}

function renderMessages() {
  const container = document.getElementById("chat-messages-scroll");
  if (!container || !activeConvoId) return;

  const user = getChatCurrentUser();
  const allMessages = [...JSON.parse(localStorage.getItem("sfrn_chat_messages") || "[]"), ...firestoreChatMessages];
  const convoMsgs = allMessages.filter(m => m.convoId === activeConvoId);

  if (convoMsgs.length === 0) {
    container.innerHTML = `<div style="padding:24px; text-align:center; color:var(--ink-faint);">No messages yet. Say hello!</div>`;
    return;
  }

  container.innerHTML = convoMsgs.map(m => {
    const isSent = m.senderEmail === user.email;
    const wrapperClass = isSent ? "sent" : "received";
    const timeStr = formatChatMessageTime(m.timestamp);

    return `
      <div class="msg-wrapper ${wrapperClass}">
        <div class="msg-bubble">${escapeHtml(m.text)}</div>
        <span class="msg-time">${timeStr}</span>
      </div>
    `;
  }).join("");

  container.scrollTop = container.scrollHeight;
}

async function sendChatMessage(event) {
  if (event) event.preventDefault();
  const input = document.getElementById("chat-message-input");
  if (!input || !input.value.trim() || !activeConvoId) return;

  const user = getChatCurrentUser();
  const text = input.value.trim();

  if (activeConvoId.startsWith("convo-donor-recipient-")) {
    const donationId = activeConvoId.replace("convo-donor-recipient-", "");

    try {
      const recipientData = await waitForRecipientData();
      await recipientData.sendConversationMessage({
        conversationId: donationId,
        senderName: user.name,
        senderRole: user.role,
        senderEmail: user.email,
        text,
      });

      const messages =
        await recipientData.getConversationMessages(donationId);

      firestoreChatMessages = messages.map(message => ({
        ...message,
        convoId: activeConvoId,
      }));

      input.value = "";
      renderMessages();
      renderConversations();
      return;
    } catch (error) {
      console.error("Could not send reservation message:", error);
      alert(error.message || "Message could not be sent.");
      return;
    }
  }

  const allMessages = JSON.parse(localStorage.getItem("sfrn_chat_messages") || "[]");
  const newMsg = {
    id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    convoId: activeConvoId,
    senderEmail: user.email,
    senderName: user.name,
    senderRole: user.role,
    text,
    timestamp: Date.now()
  };

  allMessages.push(newMsg);
  localStorage.setItem("sfrn_chat_messages", JSON.stringify(allMessages));
  input.value = "";
  renderMessages();
  renderConversations();
}

function handleChatSearch() {
  const input = document.getElementById("chat-convo-search");
  chatSearchQuery = input ? input.value : "";
  renderConversations();
}

function goBackToConversations() {
  document.getElementById("chat-conversations-list").classList.remove("hidden-mobile");
  document.getElementById("chat-active-window").classList.remove("active-mobile");
}

function formatChatTime(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  const isYesterday = new Date(now.setDate(now.getDate() - 1)).toDateString() === date.toDateString();

  if (isToday) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } else if (isYesterday) {
    return "Yesterday";
  } else {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }
}

function formatChatMessageTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

// Background sync loop for real-time updates
async function refreshActiveReservationChat() {
  if (!activeConvoId?.startsWith("convo-donor-recipient-")) return;

  const donationId = activeConvoId.replace("convo-donor-recipient-", "");

  try {
    const recipientData = await waitForRecipientData();
    const messages = await recipientData.getConversationMessages(donationId);

    firestoreChatMessages = messages.map(message => ({
      ...message,
      convoId: activeConvoId,
    }));
  } catch (error) {
    console.error("Could not refresh reservation chat:", error);
  }
}

setInterval(async () => {
  const chatTab = document.getElementById("screen-chat-tab");
  if (chatTab && chatTab.classList.contains("active")) {
    if (activeConvoId) {
      await refreshActiveReservationChat();
      renderMessages();
    }
    renderConversations();
  }
}, 3000);

async function openChatWithReservation(donationId) {
  const convoId = `convo-donor-recipient-${donationId}`;

  try {
    const recipientData = await waitForRecipientData();
    const messages =
      await recipientData.getConversationMessages(donationId);

    firestoreChatMessages = messages.map(message => ({
      ...message,
      convoId,
    }));
  } catch (error) {
    console.error("Could not load reservation chat:", error);
    alert(error.message || "Chat could not be loaded.");
    return;
  }

  showDashboardTab("chat");
  selectConversation(convoId);
}

function seedDemoMessages() {
  if (localStorage.getItem("sfrn_chat_messages")) return;
  
  const messages = [];
  const now = Date.now();
  
  // 1. Recipient Support Convo Seed
  messages.push({
    id: "seed-msg-1",
    convoId: "convo-admin-sarah@hopefoodpantry.org",
    senderEmail: "admin@nourishshare.org",
    senderName: "Nourish & Share Admin",
    senderRole: "Admin",
    text: "Welcome to the Nourish & Share network! Let us know if you have any questions about reserving food.",
    timestamp: now - 3600000 * 2
  });
  messages.push({
    id: "seed-msg-2",
    convoId: "convo-admin-sarah@hopefoodpantry.org",
    senderEmail: "sarah@hopefoodpantry.org",
    senderName: "Hope Food Pantry",
    senderRole: "Recipient",
    text: "Thank you! The platform has been really easy to use so far.",
    timestamp: now - 3600000
  });
  messages.push({
    id: "seed-msg-3",
    convoId: "convo-admin-sarah@hopefoodpantry.org",
    senderEmail: "admin@nourishshare.org",
    senderName: "Nourish & Share Admin",
    senderRole: "Admin",
    text: "Great to hear! We are here to support your community mission.",
    timestamp: now - 1800000
  });

  // 2. Donor Support Convo Seed
  messages.push({
    id: "seed-msg-4",
    convoId: "convo-admin-contact@freshmart.com",
    senderEmail: "admin@nourishshare.org",
    senderName: "Nourish & Share Admin",
    senderRole: "Admin",
    text: "Thank you for listing your fresh surplus food on the network! Let us know if you need help with pickup coordinates.",
    timestamp: now - 3600000 * 3
  });

  // 3. Dynamic Reservation-linked Convo Seed
  const donations = JSON.parse(localStorage.getItem("donor_donations") || "[]");
  donations.forEach(d => {
    if (d.reserved && d.reservedBy) {
      const convoId = `convo-donor-recipient-${d.id}`;
      messages.push({
        id: `seed-msg-res-1-${d.id}`,
        convoId: convoId,
        senderEmail: d.reservedBy,
        senderName: d.recipientName || "Recipient",
        senderRole: "Recipient",
        text: `Hello! We've successfully reserved the "${d.foodName}". We are planning to pick it up during the specified window. Does that work for you?`,
        timestamp: now - 3600000
      });
      messages.push({
        id: `seed-msg-res-2-${d.id}`,
        convoId: convoId,
        senderEmail: d.donorEmail || "contact@freshmart.com",
        senderName: d.donorName || "Fresh Mart",
        senderRole: "Donor",
        text: `Hi! Yes, that works perfectly. The crates are packaged and labeled. See you soon!`,
        timestamp: now - 1800000
      });
    }
  });

  localStorage.setItem("sfrn_chat_messages", JSON.stringify(messages));
}






// =========================================================
// VERIFIED LOGIN ROUTING
// =========================================================
(async function enterVerifiedRecipientWorkspace() {
  const requestedRole =
    new URLSearchParams(window.location.search).get("verified");

  if (requestedRole !== "recipient") return;

  try {
    const recipientData = await waitForRecipientData();
    const profile = await recipientData.getCurrentUserProfile();

    if (
      !profile ||
      profile.role !== "recipient" ||
      profile.accountStatus !== "active"
    ) {
      throw new Error("This account is not an active recipient.");
    }

    document.body.classList.add("dashboard-mode");
    initDashboardNavigation();
    showDashboardTab("dashboard");

    history.replaceState(
      {},
      "",
      window.location.pathname
    );
  } catch (error) {
    console.error(
      "Could not open verified recipient workspace:",
      error
    );
    alert(
      `Could not open recipient dashboard: ${error.message}`
    );
  }
})();
