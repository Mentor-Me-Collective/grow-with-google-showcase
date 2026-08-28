// =========================================================
// STATE
// =========================================================
const state = {
  donorType: null,
  business: {},
  contact: {},
  donation: {},
  account: {},
};

const STEP_ORDER = ["welcome", "type", "business", "contact", "donation", "account", "review", "pending"];
const STAMP_STEPS = ["type", "business", "contact", "donation", "account", "review"];
let currentStep = "welcome";

// =========================================================
// DONOR TYPES
// All seven are live in this build (not future-expansion-only).
// Each has an icon, short description, and a set of fields
// specific to how that org actually donates food.
// =========================================================
const DONOR_TYPES = [
  {
    id: "grocery",
    name: "Grocery Store",
    icon: "🛒",
    desc: "Produce, dairy, and packaged goods nearing sell-by date.",
    fields: [
      { id: "storeSize", label: "Store size", type: "select", options: ["Under 5,000 sq ft", "5,000–20,000 sq ft", "Over 20,000 sq ft"] },
      { id: "locations", label: "Number of locations", type: "number", placeholder: "e.g. 1" },
    ],
  },
  {
    id: "supermarket",
    name: "Supermarket",
    icon: "🏬",
    desc: "Larger-scale surplus across multiple departments.",
    fields: [
      { id: "storeSize", label: "Store size", type: "select", options: ["Under 20,000 sq ft", "20,000–50,000 sq ft", "Over 50,000 sq ft"] },
      { id: "locations", label: "Number of locations", type: "number", placeholder: "e.g. 3" },
    ],
  },
  {
    id: "restaurant",
    name: "Restaurant",
    icon: "🍽️",
    desc: "Prepared food and ingredients left at close of service.",
    fields: [
      { id: "cuisine", label: "Cuisine type", type: "text", placeholder: "e.g. Italian, casual dining" },
      { id: "seating", label: "Seating capacity", type: "number", placeholder: "e.g. 60" },
    ],
  },
  {
    id: "bakery",
    name: "Bakery",
    icon: "🥖",
    desc: "Bread and baked goods unsold at end of day.",
    fields: [
      { id: "products", label: "Products typically made", type: "text", placeholder: "e.g. Bread, pastries, cakes" },
    ],
  },
  {
    id: "farm",
    name: "Farm",
    icon: "🌾",
    desc: "Fresh, seasonal produce beyond market demand.",
    fields: [
      { id: "produceType", label: "Type of produce grown", type: "text", placeholder: "e.g. Leafy greens, root vegetables" },
      { id: "seasonality", label: "Seasonal availability", type: "text", placeholder: "e.g. May–October" },
    ],
  },
  {
    id: "manufacturer",
    name: "Food Manufacturer",
    icon: "🏭",
    desc: "Overruns, mislabeled batches, and short-dated stock.",
    fields: [
      { id: "productCategories", label: "Product categories", type: "text", placeholder: "e.g. Canned goods, snacks" },
      { id: "scale", label: "Production scale", type: "select", options: ["Small batch", "Mid-size", "Industrial"] },
    ],
  },
  {
    id: "community",
    name: "Community Organization",
    icon: "🤝",
    desc: "Surplus gathered through drives, events, or partners.",
    fields: [
      { id: "missionType", label: "Organization mission / type", type: "text", placeholder: "e.g. Neighborhood mutual aid" },
      { id: "nonprofitStatus", label: "Nonprofit status", type: "select", options: ["Registered nonprofit", "Fiscally sponsored", "Not incorporated"] },
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
  grid.innerHTML = DONOR_TYPES.map(t => `
    <button type="button" class="crate" data-id="${t.id}" onclick="selectDonorType('${t.id}')">
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
// DONOR TYPE SELECTION
// =========================================================
function selectDonorType(id) {
  state.donorType = id;
  document.querySelectorAll(".crate").forEach(el => {
    el.classList.toggle("selected", el.dataset.id === id);
  });
  document.getElementById("type-continue").disabled = false;

  const type = DONOR_TYPES.find(t => t.id === id);
  const tag = document.getElementById("rail-tag");
  tag.hidden = false;
  document.getElementById("rail-tag-value").textContent = type.name;
  document.getElementById("business-type-echo").textContent = type.name.toLowerCase();

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
  document.getElementById("form-business").addEventListener("submit", e => {
    e.preventDefault();
    state.business = Object.fromEntries(new FormData(e.target).entries());
    const type = DONOR_TYPES.find(t => t.id === state.donorType);
    type.fields.forEach(f => {
      const el = document.getElementById(`tf-${f.id}`);
      if (el) state.business[f.id] = el.value;
    });
    goTo("contact");
  });

  document.getElementById("form-contact").addEventListener("submit", e => {
    e.preventDefault();
    state.contact = Object.fromEntries(new FormData(e.target).entries());
    state.contact.ctMethod = document.querySelector('[data-name="ctMethod"]').dataset.value || "";
    document.getElementById("acc-email").value = state.contact.ctEmail || "";
    goTo("donation");
  });

  document.getElementById("form-donation").addEventListener("submit", e => {
    e.preventDefault();
    state.donation = Object.fromEntries(new FormData(e.target).entries());
    state.donation.foodCategories = getChipValues("food-categories");
    state.donation.donStorage = document.querySelector('[data-name="donStorage"]').dataset.value || "";
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
  const type = DONOR_TYPES.find(t => t.id === state.donorType);

  const blocks = [
    {
      title: "Donor type",
      step: "type",
      items: [["Organization type", type.name]],
    },
    {
      title: "Business information",
      step: "business",
      items: [
        ["Name", state.business.bizName],
        ["Address", state.business.bizAddress],
        ["License #", state.business.bizLicense],
        ["Years in operation", state.business.bizYears || "—"],
        ["Website", state.business.bizWebsite || "—"],
        ...type.fields.map(f => [f.label, state.business[f.id] || "—"]),
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
      title: "Donation profile",
      step: "donation",
      items: [
        ["Categories", (state.donation.foodCategories || []).join(", ") || "—"],
        ["Frequency", state.donation.donFrequency || "—"],
        ["Pickup window", state.donation.donWindow || "—"],
        ["Storage available", state.donation.donStorage || "—"],
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

    if (!window.NourishShareDonorData) {
      await import("./data-adapter.js?v=20260823f");
    }

    if (!window.NourishShareDonorData?.registerAccount) {
      throw new Error("Registration service is not available.");
    }

    await window.NourishShareDonorData.registerAccount({
      email,
      password,
      displayName:
        state.contact?.ctName ||
        state.business?.bizName ||
        "Donor",
      organizationName:
        state.business?.bizName ||
        "Donor Organization",
      profile: {
        donorType:
          state.donorType ||
          state.type ||
          "",
        business: state.business || {},
        contact: state.contact || {},
        donation: state.donation || {},
        avatarUrl: state.avatarDataUrl || "",
      },
    });

    localStorage.setItem(
      "donor_onboarding_state",
      JSON.stringify(state)
    );

    document.getElementById("pending-name").textContent =
      state.contact?.ctName || "there";

    document.getElementById("pending-org").textContent =
      state.business?.bizName || "your organization";

    document.getElementById("pending-email").textContent =
      email;

    goTo("pending");
  } catch (error) {
    console.error(
      "Could not submit donor application:",
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
  const target = document.getElementById(`screen-${step}`);
  if (target) target.classList.add("active");
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
// DONOR DASHBOARD BYPASS & ROUTING TRIGGERS (PHASE 1)
// =========================================================
async function bypassVerification() {
  // Hydrate Profile State
  await hydrateProfile();
  
  // Enter Dashboard View Mode (hides onboarding sidebars/stamps)
  document.body.classList.add("dashboard-mode");
  
  // Initialize Active Tabs & Listeners
  initDashboardNavigation();
  showDashboardTab("dashboard");
}

async function hydrateProfile() {
  let loadedFromFirestore = false;

  try {
    const donorData = await waitForDonorData();
    const userProfile = await donorData.getCurrentUserProfile();

    if (userProfile?.profile) {
      state.donorType = userProfile.profile.donorType || state.donorType;
      state.business = userProfile.profile.business || state.business || {};
      state.contact = userProfile.profile.contact || state.contact || {};
      state.donation = userProfile.profile.donation || state.donation || {};
      state.avatarDataUrl = userProfile.profile.avatarUrl || "";

      if (userProfile.displayName && !state.contact?.ctName) {
        if (!state.contact) state.contact = {};
        state.contact.ctName = userProfile.displayName;
      }

      localStorage.setItem("donor_onboarding_state", JSON.stringify(state));
      loadedFromFirestore = true;
    }
  } catch (error) {
    console.error("Could not load donor profile from Firestore:", error);
  }

  if (!loadedFromFirestore) {
    const savedState = localStorage.getItem("donor_onboarding_state");
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        Object.assign(state, parsed);
      } catch (e) {
        console.error("Error reading saved onboarding profile:", e);
      }
    }
  }

  if (!state.business || !state.business.bizName) {
    state.donorType = "grocery";
    state.business = {
      bizName: "Harvest Market",
      bizAddress: "742 Evergreen Terrace, Springfield",
      bizLicense: "LIC-77449911",
      bizYears: "4",
      bizWebsite: "www.harvestmarket.org",
      storeSize: "Under 5,000 sq ft",
      locations: "1"
    };
    state.contact = {
      ctName: "Marge Simpson",
      ctTitle: "General Manager",
      ctPhone: "555-0113",
      ctEmail: "marge.simpson@harvestmarket.org",
      ctMethod: "email"
    };
    state.donation = {
      foodCategories: ["Produce", "Bakery"],
      donFrequency: "Weekly",
      donWindow: "Tuesdays & Thursdays 10 AM - 2 PM",
      donStorage: "refrigerated"
    };
    state.account = {
      accEmail: "marge.simpson@harvestmarket.org"
    };
    state.avatarDataUrl = "";

    localStorage.setItem("donor_onboarding_state", JSON.stringify(state));
  }

  updateProfileUIPresentation();
}

function updateProfileUIPresentation() {
  const typeObj = DONOR_TYPES.find(t => t.id === state.donorType) || DONOR_TYPES[0];
  
  // Update Dropdown text details
  const dropName = document.getElementById("dropdown-donor-name");
  const dropType = document.getElementById("dropdown-donor-type");
  if (dropName) dropName.textContent = state.contact.ctName || "User Profile";
  if (dropType) dropType.textContent = typeObj.name || "Donor";
  
  // Update welcome hero section text
  const heroTitle = document.querySelector(".hero-title");
  if (heroTitle && state.contact.ctName) {
    heroTitle.innerHTML = `Welcome back, ${escapeHtml(state.contact.ctName)} 👋`;
  }
  
  // Sync avatars
  const avatarUrl = state.avatarDataUrl || "default_avatar.jpg";
  document.querySelectorAll(".nav-avatar-circle, #profile-view-avatar").forEach(el => {
    el.style.backgroundImage = `url('${avatarUrl}')`;
    el.style.backgroundSize = "cover";
    el.style.backgroundPosition = "center";
  });
}

function initDashboardNavigation() {
  // Wire desktop & mobile navigation clicks (except profile click box which toggles dropdown)
  document.querySelectorAll(".donor-nav-item").forEach(item => {
    if (item.id === "nav-profile-menu-trigger") return;
    
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

  // Wire profile dropdown trigger on desktop wood nav
  const profileTrigger = document.getElementById("nav-profile-menu-trigger");
  const dropdown = document.getElementById("profile-dropdown");
  if (profileTrigger && dropdown) {
    profileTrigger.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdown.classList.toggle("open");
    });
    
    // Close dropdown on click outside
    document.addEventListener("click", (e) => {
      if (!profileTrigger.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove("open");
      }
    });
  }

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
}

function showDashboardTab(tab) {
  // Hide all screens
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  
  // Show target tab screen
  const screen = document.getElementById(`screen-${tab}-tab`);
  if (screen) screen.classList.add("active");
  
  // Update nav highlight class globally across desktop/mobile nav elements
  document.querySelectorAll(".donor-nav-item").forEach(item => {
    item.classList.toggle("active", item.dataset.tab === tab);
  });

  // Re-render donations whenever My Donations tab or dashboard is shown
  if (tab === "donations" || tab === "dashboard") {
    renderMyDonations();
  }
  
  // Re-render pickup schedule when target is schedule or dashboard
  if (tab === "schedule" || tab === "dashboard") {
    renderPickupSchedule();
  }
  
  if (tab === "chat") {
    renderConversations();
  }
}

// =========================================================
// DONATE FOOD FORM CONTROLS & PHOTO UPLOADER (PHASE 1)
// =========================================================
function triggerPhotosInput() {
  const fileInput = document.getElementById("donate-photos-input");
  if (fileInput) fileInput.click();
}


let donationPhotoObserver = null;

function initDonationPhotoObserver() {
  const container =
    document.getElementById("donate-photo-previews");

  if (!container || donationPhotoObserver) return;

  donationPhotoObserver =
    new MutationObserver(() => {
      updateDonationPhotoUI();
    });

  donationPhotoObserver.observe(
    container,
    { childList: true }
  );

  updateDonationPhotoUI();
}

document.addEventListener(
  "DOMContentLoaded",
  initDonationPhotoObserver
);

let uploadPhotoCount = 0;

function handleNewPhotos(event) {
  const files = Array.from(event.target.files || []);

  if (files.length === 0) return;

  const previewsContainer =
    document.getElementById("donate-photo-previews");

  if (!previewsContainer) return;

  const addMoreBox =
    previewsContainer.querySelector(".add-more-box");

  const existingPhotos =
    previewsContainer.querySelectorAll(".preview-item").length;

  const availableSlots =
    Math.max(0, 5 - existingPhotos);

  if (availableSlots === 0) {
    alert("You can upload a maximum of 5 photos.");
    event.target.value = "";
    return;
  }

  const acceptedFiles = files
    .filter(file => file.type.startsWith("image/"))
    .slice(0, availableSlots);

  acceptedFiles.forEach(file => {
    uploadPhotoCount++;

    const photoId =
      `uploaded-photo-${uploadPhotoCount}`;

    const reader = new FileReader();

    reader.onload = function(e) {
      const previewItem =
        document.createElement("div");

      previewItem.className = "preview-item";
      previewItem.dataset.id = photoId;
      previewItem._uploadFile = file;

      previewItem.innerHTML = `
        <img src="${e.target.result}" alt="Selected donation photo">
        <span
          class="remove-btn"
          onclick="removePhoto('${photoId}')"
          title="Remove photo"
          aria-label="Remove ${file.name}"
        >&times;</span>
      `;

      previewsContainer.insertBefore(
        previewItem,
        addMoreBox
      );

      updateDonationPhotoUI();
    };

    reader.readAsDataURL(file);
  });

  if (files.length > acceptedFiles.length) {
    alert(
      "Only the first available photos were added. " +
      "A maximum of 5 images is allowed."
    );
  }

  // Allows choosing the same file again after removing it.
  event.target.value = "";
}

function updateDonationPhotoUI() {
  const container =
    document.getElementById("donate-photo-previews");

  const status =
    document.getElementById("donate-photo-status");

  if (!container) return;

  const photos =
    Array.from(container.querySelectorAll(".preview-item"));

  photos.forEach((photo, index) => {
    photo.classList.toggle(
      "primary-photo",
      index === 0
    );
  });

  if (status) {
    status.textContent =
      photos.length === 0
        ? "No photos selected"
        : `${photos.length} of 5 photo${photos.length === 1 ? "" : "s"} selected`;
  }

  const addMore =
    container.querySelector(".add-more-box");

  if (addMore) {
    addMore.style.display =
      photos.length >= 5 ? "none" : "flex";
  }
}


function removePhoto(id) {
  const previewsContainer = document.getElementById("donate-photo-previews");
  const itemToRemove = previewsContainer.querySelector(`[data-id="${id}"]`);
  if (itemToRemove) {
    itemToRemove.remove();
  }
}

async function submitDonationForm(event) {
  event.preventDefault();
  
  const form = document.getElementById("form-donate-food");
  if (!form) return;
  
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }
  
  // Collect all photos from the preview items (both mock and custom uploaded ones)
  const photoItems = Array.from(
    document.querySelectorAll(
      "#donate-photo-previews .preview-item"
    )
  );

  const photoUrls = [];

  if (photoItems.length > 0) {
    const { uploadProfileImage } =
      await import(
        "../cloudinaryUpload.js?v=20260823a"
      );

    for (const item of photoItems) {
      if (item._uploadFile) {
        const url =
          await uploadProfileImage(
            item._uploadFile
          );

        photoUrls.push(url);
        continue;
      }

      const existingUrl =
        item.querySelector("img")?.src;

      if (
        existingUrl &&
        existingUrl.startsWith("https://")
      ) {
        photoUrls.push(existingUrl);
      }
    }
  }
  
  // Get donor business name from onboarding state
  const onboarding = JSON.parse(localStorage.getItem("donor_onboarding_state") || "{}");
  const donorName = (onboarding.business && onboarding.business.bizName) || "Green Valley Farms";
  
  // Construct donation data object
  const donation = {
    id: "don-" + Date.now(),
    foodName: document.getElementById("food-name").value,
    foodCategory: document.getElementById("food-category").value,
    foodQty: parseFloat(document.getElementById("food-qty").value) || 0,
    foodUnit: document.getElementById("food-unit").value,
    foodExpiry: document.getElementById("food-expiry").value,
    foodDesc: document.getElementById("food-desc").value,
    pickupAvail: document.getElementById("pickup-avail").value,
    pickupInstructions: document.getElementById("pickup-instructions").value,
    storageReq: document.getElementById("storage-req").value,
    specialNotes: document.getElementById("special-notes").value,
    status: "Pending Review",
    date: new Date().toISOString(),
    photos: photoUrls,
    donorName: donorName
  };
  
  try {
    if (!window.NourishShareDonorData?.createDonation) {
      throw new Error("Donation service is not available.");
    }

    const description = [
      `Category: ${donation.foodCategory}`,
      `Expiry: ${donation.foodExpiry || "Not specified"}`,
      `Pickup availability: ${donation.pickupAvail || "Not specified"}`,
      `Pickup instructions: ${donation.pickupInstructions || "None"}`,
      `Storage requirements: ${donation.storageReq || "None"}`,
      `Description: ${donation.foodDesc || "None"}`,
      `Special notes: ${donation.specialNotes || "None"}`,
    ].join("\n");

    await window.NourishShareDonorData.createDonation({
      title: donation.foodName,
      description,
      quantity: `${donation.foodQty} ${donation.foodUnit}`.trim(),
        photos: photoUrls,
    });

    alert("Donation submitted successfully!");
  } catch (error) {
    console.error("Donation submission failed:", error);
    alert(error.message || "Donation could not be submitted.");
    return;
  }
  
  // Clear form fields
  form.reset();
  
  // Restore photo upload elements to default mock thumbnails
  const previewsContainer = document.getElementById("donate-photo-previews");
  previewsContainer.innerHTML = `
    <div class="preview-item mock" data-id="mock-apples">
      <img src="mock_apples.jpg" alt="Apples">
      <span class="remove-btn" onclick="removePhoto('mock-apples')">&times;</span>
    </div>
    <div class="preview-item mock" data-id="mock-bread">
      <img src="mock_bread.jpg" alt="Bread">
      <span class="remove-btn" onclick="removePhoto('mock-bread')">&times;</span>
    </div>
    <div class="preview-item mock" data-id="mock-tomatoes">
      <img src="mock_tomatoes.jpg" alt="Tomatoes">
      <span class="remove-btn" onclick="removePhoto('mock-tomatoes')">&times;</span>
    </div>
    <div class="add-more-box" onclick="triggerPhotosInput()">
      <span>+</span>
    </div>
  `;
  
  // Redirect to My Donations tab automatically
  showDashboardTab("donations");
}

// =========================================================
// MY DONATIONS RENDER, SEARCH, AND FILTERS (PHASE 1)
// =========================================================
let donorDonations = [];

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

  const statusMap = {
    available: "Approved",
    reserved: "Scheduled",
    picked_up: "Completed",
    cancelled: "Cancelled",
  };

  return {
    id: donation.id,
    foodName: donation.title || "Untitled Donation",
    foodCategory:
      getDescriptionField(donation.description, "Category") || "Other",
    foodQty: Number.isNaN(parsedQty) ? 0 : parsedQty,
    foodUnit: quantityParts.slice(1).join(" ") || "",
    foodExpiry:
      getDescriptionField(donation.description, "Expiry") ||
      "Not specified",
    foodDesc:
      getDescriptionField(donation.description, "Description"),
    pickupAvail:
      getDescriptionField(donation.description, "Pickup availability") ||
      "Not specified",
    pickupInstructions:
      getDescriptionField(donation.description, "Pickup instructions"),
    storageReq:
      getDescriptionField(donation.description, "Storage requirements"),
    specialNotes:
      getDescriptionField(donation.description, "Special notes"),
    status:
      statusMap[donation.status] ||
      donation.status ||
      "Approved",
    date: "",
    photos: Array.isArray(donation.photos) ? donation.photos : [],
  };
}
async function waitForDonorData() {
  if (!window.NourishShareDonorData) {
    await import("./data-adapter.js?v=20260823f");
  }

  if (!window.NourishShareDonorData) {
    throw new Error("Donation service failed to initialize.");
  }

  return window.NourishShareDonorData;
}

async function renderMyDonations() {
  try {
    const donorData = await waitForDonorData();
    const firestoreDonations =
      await donorData.getMyDonations();
    donorDonations =
      firestoreDonations.map(mapFirestoreDonation);
  } catch (error) {
    console.error("Could not load donor donations:", error);
    donorDonations = [];
  }
  const donations = donorDonations;
  
  // Calculate summary counts
  const totalCount = donations.length;
  const activeCount = donations.filter(d => ["Pending Review", "Approved", "Scheduled", "Picked Up"].includes(d.status)).length;
  const completedCount = donations.filter(d => d.status === "Completed").length;
  
  // Total weight in kg (summing up quantities labeled with 'kg' unit)
  let totalKg = 0;
  donations.forEach(d => {
    if (d.foodUnit === "kg") {
      totalKg += d.foodQty;
    }
  });
  
  // Update My Donations Summary widgets
  const totalValEl = document.getElementById("sum-total-donations");
  const activeValEl = document.getElementById("sum-active-donations");
  const completedValEl = document.getElementById("sum-completed-donations");
  const foodValEl = document.getElementById("sum-food-donated");
  
  if (totalValEl) totalValEl.textContent = totalCount;
  if (activeValEl) activeValEl.textContent = activeCount;
  if (completedValEl) completedValEl.textContent = completedCount;
  if (foodValEl) foodValEl.textContent = `${totalKg} kg`;
  
  // Sync dashboard page metrics too!
  const dashActiveEl = document.getElementById("stat-active-donations");
  const dashScheduledEl = document.getElementById("stat-scheduled-pickups");
  const dashFoodEl = document.getElementById("stat-food-donated");
  
  if (dashActiveEl) dashActiveEl.textContent = activeCount;
  if (dashScheduledEl) dashScheduledEl.textContent = donations.filter(d => d.status === "Scheduled").length;
  if (dashFoodEl) dashFoodEl.textContent = `${totalKg} kg`;
  
  filterAndSortDonations();
}

function filterAndSortDonations() {
  const donations = donorDonations;
  const searchQuery = (document.getElementById("donations-search")?.value || "").toLowerCase().trim();
  const filterStatus = document.getElementById("donations-filter-status")?.value || "All";
  const sortBy = document.getElementById("donations-sort")?.value || "Newest";
  
  let filtered = donations.filter(d => {
    // 1. Search filter
    const matchesSearch = d.foodName.toLowerCase().includes(searchQuery) || 
                          d.foodCategory.toLowerCase().includes(searchQuery) ||
                          (d.foodDesc || "").toLowerCase().includes(searchQuery);
    // 2. Status filter
    const matchesStatus = filterStatus === "All" || d.status === filterStatus;
    
    return matchesSearch && matchesStatus;
  });
  
  // 3. Sorting
  filtered.sort((a, b) => {
    const timeA = new Date(a.date).getTime();
    const timeB = new Date(b.date).getTime();
    return sortBy === "Newest" ? (timeB - timeA) : (timeA - timeB);
  });
  
  const listWrapper = document.getElementById("donations-list-wrapper");
  if (!listWrapper) return;
  
  if (filtered.length === 0) {
    listWrapper.innerHTML = `
      <div class="empty-state-card">
        <h3 class="empty-state-title">No donations yet</h3>
        <p class="empty-state-sub">Your surplus food can make a difference.</p>
        <button type="button" class="btn btn-empty-action" onclick="showDashboardTab('donate')">Donate Food</button>
      </div>
    `;
    return;
  }
  
  listWrapper.innerHTML = filtered.map(d => {
    const thumbnail = d.photos && d.photos.length > 0 ? d.photos[0] : "mock_apples.jpg";
    const badgeClass = `badge-${d.status.toLowerCase().replace(/\s+/g, "")}`;
    
    return `
      <div class="donation-row-card">
        <img class="donation-card-img" src="${thumbnail}" alt="${d.foodName}">
        <div class="donation-card-info">
          <h4 class="donation-card-title">${escapeHtml(d.foodName)}</h4>
          <p class="donation-card-sub">${d.foodQty} ${d.foodUnit} &bull; ${d.foodCategory}</p>
          <div class="donation-card-meta">
            <div class="meta-item">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
              <span>Best before: ${escapeHtml(d.foodExpiry)}</span>
            </div>
            <div class="meta-item">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
              <span>Pickup: ${escapeHtml(d.pickupAvail)}</span>
            </div>
          </div>
        </div>
        <div class="donation-card-actions">
          <span class="status-badge ${badgeClass}">
            <span class="badge-dot"></span>
            ${d.status}
          </span>
          <button type="button" class="btn btn-view-details" onclick="viewDonationDetails('${d.id}')">
            View Details
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>
        </div>
      </div>
    `;
  }).join("");
}

// =========================================================
// VIEW DETAILS MODAL TRIGGERS (PHASE 1)
// =========================================================
function viewDonationDetails(id) {
  const donations = donorDonations;
  const d = donations.find(item => item.id === id);
  if (!d) return;
  
  const modal = document.getElementById("details-modal");
  const modalTitle = document.getElementById("modal-food-name");
  const modalBody = document.getElementById("modal-details-body");
  
  if (modalTitle) modalTitle.textContent = d.foodName;
  
  // Render photo gallery
  let photoGalleryHtml = "";
  if (d.photos && d.photos.length > 0) {
    photoGalleryHtml = `
      <div class="detail-block span-2">
        <span class="detail-label">Uploaded Photos</span>
        <div class="modal-photo-gallery">
          ${d.photos.map(p => `<div class="modal-photo-item"><img src="${p}" alt="Photo"></div>`).join("")}
        </div>
      </div>
    `;
  }
  
  if (modalBody) {
    modalBody.innerHTML = `
      <div class="details-grid">
        <div class="detail-block">
          <span class="detail-label">Status</span>
          <span class="detail-value" style="font-weight: 700; color: var(--green-dark);">${d.status}</span>
        </div>
        <div class="detail-block">
          <span class="detail-label">Category</span>
          <span class="detail-value">${escapeHtml(d.foodCategory)}</span>
        </div>
        <div class="detail-block">
          <span class="detail-label">Quantity &amp; Unit</span>
          <span class="detail-value">${d.foodQty} ${d.foodUnit}</span>
        </div>
        <div class="detail-block">
          <span class="detail-label">Best Before Date</span>
          <span class="detail-value">${escapeHtml(d.foodExpiry)}</span>
        </div>
        <div class="detail-block">
          <span class="detail-label">Pickup Availability</span>
          <span class="detail-value">${escapeHtml(d.pickupAvail)}</span>
        </div>
        <div class="detail-block">
          <span class="detail-label">Storage Requirements</span>
          <span class="detail-value">${escapeHtml(d.storageReq)}</span>
        </div>
        <div class="detail-block span-2">
          <span class="detail-label">Pickup Instructions</span>
          <span class="detail-value">${escapeHtml(d.pickupInstructions || "—")}</span>
        </div>
        <div class="detail-block span-2">
          <span class="detail-label">Special Notes</span>
          <span class="detail-value">${escapeHtml(d.specialNotes || "—")}</span>
        </div>
        <div class="detail-block span-2">
          <span class="detail-label">Description</span>
          <span class="detail-value">${escapeHtml(d.foodDesc || "No description provided.")}</span>
        </div>
        ${photoGalleryHtml}
      </div>
    `;
  }
  
  if (modal) modal.classList.add("open");
}

function closeDetailsModal(event) {
  const modal = document.getElementById("details-modal");
  if (modal) modal.classList.remove("open");
}

// =========================================================
// PICKUP SCHEDULE LIST RENDER (PHASE 1)
// =========================================================
async function renderPickupSchedule() {
  try {
    const donorData = await waitForDonorData();
    const firestoreDonations =
      await donorData.getMyDonations();
    donorDonations =
      firestoreDonations.map(mapFirestoreDonation);
  } catch (error) {
    console.error("Could not load donor pickup schedule:", error);
    donorDonations = [];
  }

  const donations = donorDonations;
  
  // Categorize pickups by status groups
  const upcomingPickups = donations.filter(d => ["Scheduled", "Picked Up"].includes(d.status));
  const pendingPickups = donations.filter(d => ["Pending Review", "Approved"].includes(d.status));
  const completedPickups = donations.filter(d => d.status === "Completed");
  
  // Update Pickup Schedule Summary widgets
  const upcomingValEl = document.getElementById("sum-upcoming-pickups");
  const pendingValEl = document.getElementById("sum-pending-pickups");
  const completedValEl = document.getElementById("sum-completed-pickups");
  
  if (upcomingValEl) upcomingValEl.textContent = upcomingPickups.length;
  if (pendingValEl) pendingValEl.textContent = pendingPickups.length;
  if (completedValEl) completedValEl.textContent = completedPickups.length;
  
  // Inject pickup cards into each section container
  renderPickupSection("pickup-list-upcoming", upcomingPickups);
  renderPickupSection("pickup-list-pending", pendingPickups);
  renderPickupSection("pickup-list-completed", completedPickups);
}

function renderPickupSection(containerId, list) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  if (list.length === 0) {
    container.innerHTML = `<div style="font-size: 0.88rem; color: var(--ink-faint); padding: 12px 16px; background: var(--card); border: 1px dashed var(--kraft-line); border-radius: 12px; margin-bottom: 12px;">No pickups scheduled in this status.</div>`;
    return;
  }
  
  container.innerHTML = list.map(d => {
    const thumbnail = d.photos && d.photos.length > 0 ? d.photos[0] : "mock_apples.jpg";
    const badgeClass = `badge-${d.status.toLowerCase().replace(/\s+/g, "")}`;
    const storageBadgeHtml = getStorageBadgeHtml(d.storageReq);
    
    return `
      <div class="donation-row-card">
        <img class="donation-card-img" src="${thumbnail}" alt="${d.foodName}">
        
        <div class="pickup-card-grid">
          <!-- Col 1: Details -->
          <div class="pickup-card-details">
            <h4 class="donation-card-title">${escapeHtml(d.foodName)}</h4>
            <p class="donation-card-sub">${d.foodQty} ${d.foodUnit} &bull; ${d.foodCategory}</p>
            <div class="donation-card-meta" style="grid-template-columns: 1fr;">
              <div class="meta-item">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="16" y1="2" x2="16" y2="6"></line>
                  <line x1="8" y1="2" x2="8" y2="6"></line>
                  <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                <span>${escapeHtml(d.pickupAvail)}</span>
              </div>
              <div class="meta-item">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
                <span>Your Pickup Location</span>
              </div>
            </div>
          </div>
          
          <!-- Col 2: Instructions -->
          <div class="pickup-card-instructions">
            <span class="detail-label">Pickup Instructions</span>
            <p class="instruction-text">${escapeHtml(d.pickupInstructions || "No instructions provided.")}</p>
            <span class="detail-label">Storage Requirement</span>
            ${storageBadgeHtml}
          </div>
        </div>
        
        <div class="donation-card-actions">
          <span class="status-badge ${badgeClass}">
            <span class="badge-dot"></span>
            ${d.status}
          </span>
          ${d.status === "Scheduled" ? `
          <button type="button" class="btn btn-secondary btn-chat-partner" onclick="openChatWithReservation('${d.id}')" style="margin-right: 8px; padding: 6px 12px; font-size: 0.8rem; display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--kraft-line); background: #FFF;">
            <i class="fa-solid fa-comment"></i>
            Chat with Recipient
          </button>
          ` : ""}
          <button type="button" class="btn btn-view-details" onclick="viewDonationDetails('${d.id}')">
            View Details
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>
        </div>
      </div>
    `;
  }).join("");
}

function getStorageBadgeHtml(req) {
  const norm = (req || "").toLowerCase();
  if (norm.includes("refrigerated")) {
    return `
      <span class="storage-badge-pill" style="background: #EBF3FC; color: #1E4E79;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px; vertical-align: middle;">
          <line x1="2" y1="12" x2="22" y2="12"></line>
          <line x1="12" y1="2" x2="12" y2="22"></line>
          <path d="M20 16l-4-4 4-4"></path>
          <path d="M4 8l4 4-4 4"></path>
          <path d="M16 4l-4 4-4-4"></path>
          <path d="M8 20l4-4 4 4"></path>
        </svg>Refrigerated
      </span>
    `;
  } else if (norm.includes("frozen")) {
    return `
      <span class="storage-badge-pill" style="background: #E0F7FA; color: #006064;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px; vertical-align: middle;">
          <line x1="2" y1="12" x2="22" y2="12"></line>
          <line x1="12" y1="2" x2="12" y2="22"></line>
          <path d="M20 16l-4-4 4-4"></path>
          <path d="M4 8l4 4-4 4"></path>
          <path d="M16 4l-4 4-4-4"></path>
          <path d="M8 20l4-4 4 4"></path>
        </svg>Frozen
      </span>
    `;
  } else {
    // Ambient / Room Temperature
    return `
      <span class="storage-badge-pill" style="background: #FFF3E0; color: #E65100;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px; vertical-align: middle;">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
          <polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>Room Temperature
      </span>
    `;
  }
}

// =========================================================
// PROFILE EDITING & ACTIONS CONTROLLERS (PHASE 1)
// =========================================================
function openProfileTab() {
  // Hide dropdown overlay
  const dropdown = document.getElementById("profile-dropdown");
  if (dropdown) dropdown.classList.remove("open");
  
  // Close mobile drawer if open
  const drawer = document.getElementById("mobile-drawer");
  const overlay = document.getElementById("drawer-overlay");
  if (drawer) drawer.classList.remove("open");
  if (overlay) overlay.classList.remove("open");

  // Show profile tab screen
  showDashboardTab("profile");
  
  // Populate form fields
  document.getElementById("prof-biz-name").value = state.business.bizName || "";
  document.getElementById("prof-biz-address").value = state.business.bizAddress || "";
  document.getElementById("prof-biz-license").value = state.business.bizLicense || "";
  document.getElementById("prof-biz-years").value = state.business.bizYears || "";
  document.getElementById("prof-biz-website").value = state.business.bizWebsite || "";
  
  const typeObj = DONOR_TYPES.find(t => t.id === state.donorType) || DONOR_TYPES[0];
  document.getElementById("prof-donor-type").value = typeObj.name;
  
  document.getElementById("prof-ct-name").value = state.contact.ctName || "";
  document.getElementById("prof-ct-title").value = state.contact.ctTitle || "";
  document.getElementById("prof-ct-phone").value = state.contact.ctPhone || "";
  document.getElementById("prof-ct-email").value = state.contact.ctEmail || "";
  document.getElementById("prof-ct-method").value = state.contact.ctMethod || "email";
  
  document.getElementById("prof-don-storage").value = state.donation.donStorage || "ambient";
  document.getElementById("prof-don-frequency").value = state.donation.donFrequency || "";
  document.getElementById("prof-don-window").value = state.donation.donWindow || "";
  
  // Sync saved profile photo into the edit form preview
  const previewEl = document.getElementById("profile-edit-avatar-preview");
  if (previewEl) {
    const avatarUrl = state.avatarDataUrl || "default_avatar.jpg";
    previewEl.style.backgroundImage = `url('${avatarUrl}')`;
    previewEl.style.backgroundSize = "cover";
    previewEl.style.backgroundPosition = "center";
  }

  // Populate conditional fields
  renderEditProfileConditionalFields(typeObj);
}

function renderEditProfileConditionalFields(type) {
  const container = document.getElementById("profile-conditional-fields-container");
  if (!container) return;
  if (!type.fields || !type.fields.length) { container.innerHTML = ""; return; }
  
  container.innerHTML = `<div class="type-fields-label" style="margin-top: 16px; font-weight: 700; color: var(--green-dark);">Specific to ${type.name.toLowerCase()}s</div>` +
    type.fields.map(f => {
      const val = state.business[f.id] || "";
      if (f.type === "select") {
        return `
          <div class="field" style="margin-top: 12px;">
            <label for="tf-prof-${f.id}">${f.label}</label>
            <select id="tf-prof-${f.id}" name="${f.id}">
              <option value="" disabled>Select one</option>
              ${f.options.map(o => `<option ${o === val ? "selected" : ""}>${o}</option>`).join("")}
            </select>
          </div>`;
      }
      return `
        <div class="field" style="margin-top: 12px;">
          <label for="tf-prof-${f.id}">${f.label}</label>
          <input type="${f.type}" id="tf-prof-${f.id}" name="${f.id}" value="${escapeHtml(val)}" placeholder="${f.placeholder || ""}">
        </div>`;
    }).join("");
}

function openSettingsTab() {
  const dropdown = document.getElementById("profile-dropdown");
  if (dropdown) dropdown.classList.remove("open");
  
  const drawer = document.getElementById("mobile-drawer");
  const overlay = document.getElementById("drawer-overlay");
  if (drawer) drawer.classList.remove("open");
  if (overlay) overlay.classList.remove("open");

  showDashboardTab("settings");
}

async function saveDonorSettings() {
  const notifyEmail =
    document.getElementById(
      "set-notify-email"
    )?.checked ?? true;

  const notifySms =
    document.getElementById(
      "set-notify-sms"
    )?.checked ?? true;

  const currentPassword =
    document.getElementById(
      "set-pass-old"
    )?.value || "";

  const newPassword =
    document.getElementById(
      "set-pass-new"
    )?.value || "";

  const confirmPassword =
    document.getElementById(
      "set-pass-confirm"
    )?.value || "";

  try {
    if (
      !window.NourishShareDonorData
        ?.saveUserSettings
    ) {
      throw new Error(
        "Settings service is not available."
      );
    }

    await window.NourishShareDonorData
      .saveUserSettings({
        notifyEmail,
        notifySms,
      });

    const changingPassword =
      currentPassword ||
      newPassword ||
      confirmPassword;

    if (changingPassword) {
      if (!currentPassword) {
        throw new Error(
          "Enter your current password."
        );
      }

      if (newPassword.length < 8) {
        throw new Error(
          "New password must be at least 8 characters."
        );
      }

      if (newPassword !== confirmPassword) {
        throw new Error(
          "New passwords do not match."
        );
      }

      await window.NourishShareDonorData
        .changePassword(
          currentPassword,
          newPassword
        );

      document.getElementById(
        "set-pass-old"
      ).value = "";

      document.getElementById(
        "set-pass-new"
      ).value = "";

      document.getElementById(
        "set-pass-confirm"
      ).value = "";
    }

    alert("Settings updated successfully!");
  } catch (error) {
    console.error(
      "Could not save donor settings:",
      error
    );

    alert(
      error?.message ||
      "Could not save settings."
    );
  }
}

async function logoutUser() {
  sessionStorage.removeItem("nourishshare_verified_workspace");
  try {
    if (!window.NourishShareDonorData?.logout) {
      throw new Error(
        "Logout service is not available."
      );
    }

    await window.NourishShareDonorData.logout();

    localStorage.removeItem(
      "donor_onboarding_state"
    );

    window.location.href =
      "../../public/login.html";
  } catch (error) {
    console.error("Could not log out:", error);
    alert("Could not log out. Please try again.");
  }
}

async function handleProfilePhotoChange(event) {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const { uploadProfileImage } = await import("../cloudinaryUpload.js?v=20260823a");
    const imageUrl = await uploadProfileImage(file);

    state.avatarDataUrl = imageUrl;
    localStorage.setItem("donor_onboarding_state", JSON.stringify(state));
    updateProfileUIPresentation();

    const previewEl = document.getElementById("profile-edit-avatar-preview");
    if (previewEl) {
      previewEl.style.backgroundImage = `url('${imageUrl}')`;
    }
  } catch (error) {
    console.error("Could not upload donor profile photo:", error);
    alert(error.message || "Profile photo could not be uploaded.");
    event.target.value = "";
  }
}

async function saveProfileChanges(event) {
  event.preventDefault();

  const form = document.getElementById("form-edit-profile");
  if (!form) return;

  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  state.business.bizName = document.getElementById("prof-biz-name").value;
  state.business.bizAddress = document.getElementById("prof-biz-address").value;
  state.business.bizLicense = document.getElementById("prof-biz-license").value;
  state.business.bizYears = document.getElementById("prof-biz-years").value;
  state.business.bizWebsite = document.getElementById("prof-biz-website").value;

  state.contact.ctName = document.getElementById("prof-ct-name").value;
  state.contact.ctTitle = document.getElementById("prof-ct-title").value;
  state.contact.ctPhone = document.getElementById("prof-ct-phone").value;
  state.contact.ctEmail = document.getElementById("prof-ct-email").value;
  state.contact.ctMethod = document.getElementById("prof-ct-method").value;

  state.donation.donStorage = document.getElementById("prof-don-storage").value;
  state.donation.donFrequency = document.getElementById("prof-don-frequency").value;
  state.donation.donWindow = document.getElementById("prof-don-window").value;

  const typeObj = DONOR_TYPES.find(t => t.id === state.donorType) || DONOR_TYPES[0];
  if (typeObj.fields) {
    typeObj.fields.forEach(f => {
      const el = document.getElementById(`tf-prof-${f.id}`);
      if (el) {
        state.business[f.id] = el.value;
      }
    });
  }

  try {
    const donorData = await waitForDonorData();

    await donorData.saveUserProfile({
      displayName: state.contact.ctName || state.business.bizName,
      profile: {
        donorType: state.donorType,
        business: state.business,
        contact: state.contact,
        donation: state.donation,
        avatarUrl: state.avatarDataUrl || "",
      },
    });

    localStorage.setItem("donor_onboarding_state", JSON.stringify(state));
    updateProfileUIPresentation();

    alert("Profile saved successfully!");
    showDashboardTab("dashboard");
  } catch (error) {
    console.error("Could not save donor profile:", error);
    alert(error.message || "Profile could not be saved.");
  }
}

init();

// =========================================================
// SFRN CHAT SYSTEM CODE (DONOR LOGIC)
// =========================================================
let activeConvoId = null;
let chatSearchQuery = "";
let firestoreChatMessages = [];

function getChatCurrentUser() {
  const onboardingState = JSON.parse(localStorage.getItem("donor_onboarding_state") || "{}");
  return {
    email: onboardingState.account?.accEmail || onboardingState.contact?.ctEmail || "contact@freshmart.com",
    name: onboardingState.business?.bizName || "Fresh Mart",
    role: "Donor"
  };
}

function loadAllConversations() {
  const user = getChatCurrentUser();
  if (!user) return [];

  const conversations = [];
  const donations = donorDonations;
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
    const isOwnDonation = d.donorEmail === user.email || d.donorName === user.name;
    if (d.status === "Scheduled") {
      conversations.push({
        id: `convo-donor-recipient-${d.id}`,
        partnerName: d.recipientName || "Recipient",
        partnerEmail: d.reservedBy || "recipient@nourishshare.org",
        partnerRole: "Recipient",
        context: `Regarding: ${d.foodName}`,
        photo: d.recipientAvatar || ""
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
      : `<div class="convo-avatar" style="display:flex; align-items:center; justify-content:center; background:#EAF0EB; color:var(--green-dark); font-weight:700; font-family:var(--font-display);">${initials}</div>`;

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
    avatarContainer.style.color = "var(--green-dark)";
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
      const donorData = await waitForDonorData();
      await donorData.sendConversationMessage({
        conversationId: donationId,
        senderName: user.name,
        senderRole: user.role,
        senderEmail: user.email,
        text,
      });

      const messages =
        await donorData.getConversationMessages(donationId);

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
    const donorData = await waitForDonorData();
    const messages = await donorData.getConversationMessages(donationId);

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
    const donorData = await waitForDonorData();
    const messages =
      await donorData.getConversationMessages(donationId);

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
(async function enterVerifiedDonorWorkspace() {
  const requestedRole =
    new URLSearchParams(window.location.search).get("verified");

  if (requestedRole !== "donor") return;

  try {
    const donorData = await waitForDonorData();
    const profile = await donorData.getCurrentUserProfile();

    if (
      !profile ||
      profile.role !== "donor" ||
      profile.accountStatus !== "active"
    ) {
      throw new Error("This account is not an active donor.");
    }

    document.body.classList.add("dashboard-mode");
    initDashboardNavigation();
    showDashboardTab("dashboard");

    // Hydrate presentation after dashboard entry.
    void hydrateProfile();

    // Remove routing token from visible URL.
    history.replaceState(
      {},
      "",
      window.location.pathname
    );
  } catch (error) {
    console.error(
      "Could not open verified donor workspace:",
      error
    );
    alert(
      `Could not open donor dashboard: ${error.message}`
    );
  }
})();
