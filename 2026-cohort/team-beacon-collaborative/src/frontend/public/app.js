// ================= FOOD DONATION STATE =================
let foodDonations = [];

// Active filters
let currentCategory = "all";
let searchQuery = "";

// ================= DOM CONTENT INITIALIZATION =================
document.addEventListener("DOMContentLoaded", () => {
  initDesktopNav();
  initMobileDrawer();
  initMetricsCounter();
  initFoodFinder();
  initInteractiveMap();
  initFormsAndModals();
  initFormInstantValidation();
});

// ================= DESKTOP NAVIGATION =================
function initDesktopNav() {
  const navItems = document.querySelectorAll(".nav-links .nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", (e) => {
      // If it's the donate button, prevent default to open modal smoothly
      if (item.id === "open-donate-modal-btn") {
        e.preventDefault();
      }
    });
  });
}

// ================= MOBILE NAVIGATION DRAWER =================
function initMobileDrawer() {
  const menuBtn = document.getElementById("mobile-menu-btn");
  const closeBtn = document.getElementById("drawer-close-btn");
  const overlay = document.getElementById("mobile-drawer-overlay");
  const drawer = document.getElementById("mobile-drawer");
  const drawerLinks = document.querySelectorAll(".drawer-item");

  const toggleDrawer = (open) => {
    drawer.classList.toggle("open", open);
    overlay.classList.toggle("open", open);
    document.body.style.overflow = open ? "hidden" : "";
  };

  menuBtn.addEventListener("click", () => toggleDrawer(true));
  closeBtn.addEventListener("click", () => toggleDrawer(false));
  overlay.addEventListener("click", () => toggleDrawer(false));

  drawerLinks.forEach(link => {
    link.addEventListener("click", () => {
      drawerLinks.forEach(l => l.classList.remove("active"));
      link.classList.add("active");
      toggleDrawer(false);
    });
  });

}

// ================= ANIME METRICS COUNTER (SDG 2) =================
function initMetricsCounter() {
  const metrics = document.querySelectorAll(".metric-val");
  
  const options = {
    threshold: 0.5,
    rootMargin: "0px"
  };

  const observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const target = entry.target;
        const limit = parseInt(target.getAttribute("data-target"), 10);
        let count = 0;
        const speed = limit > 1000 ? 50 : 20;
        const step = Math.ceil(limit / speed);

        const updateCount = () => {
          count += step;
          if (count >= limit) {
            target.textContent = limit.toLocaleString();
          } else {
            target.textContent = count.toLocaleString();
            setTimeout(updateCount, 30);
          }
        };
        updateCount();
        observer.unobserve(target);
      }
    });
  }, options);

  metrics.forEach(metric => observer.observe(metric));
}

// ================= DYNAMIC FOOD FINDER GRID & FILTERING =================
async function initFoodFinder() {
  const grid = document.getElementById("food-listings-grid");
  const searchInput = document.getElementById("search-input");
  const filterPills = document.querySelectorAll("#category-filters .filter-pill");
  await loadAvailableDonations();

  // Search input event
  searchInput.addEventListener("input", (e) => {
    searchQuery = e.target.value.toLowerCase().trim();
    renderFoodCards();
  });

  // Filter pills
  filterPills.forEach(pill => {
    pill.addEventListener("click", () => {
      filterPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      currentCategory = pill.getAttribute("data-category");
      renderFoodCards();
    });
  });
}

async function loadAvailableDonations() {
  const data = window.NourishShareData;

  if (!data || typeof data.getAvailableDonations !== "function") {
    console.error("Donation data adapter is unavailable.");
    foodDonations = [];
    renderFoodCards();
    return;
  }

  try {
    const donations = await data.getAvailableDonations();
    foodDonations = donations.map(mapFirestoreDonationToCard);
  } catch (error) {
    console.error("Available donations could not be loaded.", error);
    foodDonations = [];
  }

  renderFoodCards();
}

function mapFirestoreDonationToCard(donation) {
  const descriptionFields = parseDonationDescription(donation.description || "");
  const category = descriptionFields.category || "other";
  const expiry = descriptionFields.expiry || "Availability not specified";

  return {
    id: donation.id,
    title: donation.title || "Untitled Donation",
    donor: "Community Donor",
    category,
    quantity: donation.quantity || "Quantity not specified",
    expiry: expiry.startsWith("Expires in ") ? expiry : `Expires in ${expiry}`,
    isUrgent: expiry.toLowerCase().includes("hour"),
    distance: "Pickup location available",
    address: descriptionFields.address || "Pickup location not specified",
    instructions: descriptionFields.instructions || "None provided",
    image: getCategoryPlaceholder(category)
  };
}

function parseDonationDescription(description) {
  const fields = {};

  description.split("\n").forEach(line => {
    const separatorIndex = line.indexOf(":");
    if (separatorIndex === -1) return;

    const label = line.slice(0, separatorIndex).trim().toLowerCase();
    const value = line.slice(separatorIndex + 1).trim();

    if (label === "category") {
      fields.category = value;
    } else if (label === "expiry") {
      fields.expiry = value;
    } else if (label === "pickup address") {
      fields.address = value;
    } else if (label === "instructions") {
      fields.instructions = value;
    }
  });

  return fields;
}
function renderFoodCards() {
  const grid = document.getElementById("food-listings-grid");
  grid.innerHTML = "";

  const filtered = foodDonations.filter(item => {
    const matchesCategory = currentCategory === "all" || item.category === currentCategory;
    const matchesSearch = item.title.toLowerCase().includes(searchQuery) ||
                          item.donor.toLowerCase().includes(searchQuery) ||
                          item.address.toLowerCase().includes(searchQuery);
    return matchesCategory && matchesSearch;
  });

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div class="empty-selection-state w-100" style="grid-column: 1 / -1;">
        <i class="fa-solid fa-cookie-bite"></i>
        <p>No food listings match your search criteria. Try selecting another filter or post a new donation!</p>
      </div>
    `;
    return;
  }

  filtered.forEach(item => {
    const card = document.createElement("div");
    card.className = "food-card glass-card";
    
    // Background placeholder or unsplash images
    const coverImage = item.image || "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=400&q=80";

    card.innerHTML = `
      <div class="food-card-header" style="background-image: linear-gradient(to bottom, rgba(0,0,0,0.15), rgba(0,0,0,0.65)), url('${coverImage}');">
        <span class="card-cat-badge ${item.category}">${item.category.toUpperCase()}</span>
        <span class="expiry-badge ${item.isUrgent ? 'urgent' : ''}">
          <i class="fa-solid fa-clock"></i> ${item.expiry}
        </span>
      </div>
      <div class="food-card-body">
        <h3>${item.title}</h3>
        <div class="donor-label">
          <i class="fa-solid fa-store"></i> <span>${item.donor}</span>
        </div>
        <div class="food-meta">
          <span><i class="fa-solid fa-cubes"></i> ${item.quantity}</span>
          <span><i class="fa-solid fa-map-pin"></i> ${item.distance}</span>
        </div>
        <div class="food-card-footer">
          <button class="btn btn-primary w-100 claim-trigger" data-id="${item.id}">
            <i class="fa-solid fa-circle-check"></i> Claim Food
          </button>
        </div>
      </div>
    `;
    grid.appendChild(card);
  });

  // Attach claim modal events
  document.querySelectorAll(".claim-trigger").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const donationId = btn.getAttribute("data-id");
      setupAndOpenClaimModal(donationId);
    });
  });
}

// ================= INTERACTIVE DISTRIBUTION MAP =================
function initInteractiveMap() {
  const pins = document.querySelectorAll(".map-pin");
  const detailPanel = document.getElementById("map-selection-detail");

  pins.forEach(pin => {
    pin.addEventListener("click", () => {
      pins.forEach(p => p.classList.remove("active"));
      pin.classList.add("active");

      const id = pin.getAttribute("data-id");
      const donation = foodDonations.find(item => item.id === id);

      if (donation) {
        detailPanel.innerHTML = `
          <div class="map-detail-card">
            <h4>${donation.title}</h4>
            <span class="category">${donation.category.toUpperCase()}</span>
            <div class="map-detail-meta">
              <div><i class="fa-solid fa-building"></i> <strong>Donor:</strong> ${donation.donor}</div>
              <div><i class="fa-solid fa-location-dot"></i> <strong>Location:</strong> ${donation.address}</div>
              <div><i class="fa-solid fa-clock"></i> <strong>Availability:</strong> ${donation.expiry}</div>
              <div><i class="fa-solid fa-box"></i> <strong>Quantity:</strong> ${donation.quantity}</div>
            </div>
            <button class="btn btn-secondary w-100 claim-trigger" data-id="${donation.id}">
              <i class="fa-solid fa-circle-check"></i> Claim Listing
            </button>
          </div>
        `;

        // Attach action events inside side panel claim buttons
        detailPanel.querySelector(".claim-trigger").addEventListener("click", () => {
          setupAndOpenClaimModal(donation.id);
        });
      } else {
        detailPanel.innerHTML = `
          <div class="empty-selection-state">
            <i class="fa-solid fa-circle-info"></i>
            <p>Donor node offline or claimed. Please select another active pin.</p>
          </div>
        `;
      }
    });
  });
}

// ================= FORMS & MODALS SYSTEM =================
function initFormsAndModals() {
  const openDonateBtn = document.getElementById("open-donate-modal-btn");
  const heroDonateBtn = document.getElementById("hero-donate-trigger");
  const closeDonateBtn = document.getElementById("close-donate-modal");
  const donateModal = document.getElementById("donate-modal");

  const closeClaimBtn = document.getElementById("close-claim-modal");
  const claimModal = document.getElementById("claim-modal");

  // Open Donate Modal
  const openDonate = () => openModal("donate-modal");
  if (openDonateBtn) openDonateBtn.addEventListener("click", openDonate);
  if (heroDonateBtn) heroDonateBtn.addEventListener("click", openDonate);
  const homeJoinDonateBtn = document.getElementById("home-join-donate");
  if (homeJoinDonateBtn) homeJoinDonateBtn.addEventListener("click", openDonate);

  // Close Donate Modal
  closeDonateBtn.addEventListener("click", () => closeModal("donate-modal"));
  closeClaimBtn.addEventListener("click", () => closeModal("claim-modal"));

  // Click outside to close modals
  window.addEventListener("click", (e) => {
    if (e.target === donateModal) closeModal("donate-modal");
    if (e.target === claimModal) closeModal("claim-modal");
  });

  // Handle donation submission
  const donateForm = document.getElementById("donate-food-form");
  donateForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = window.NourishShareData;

    if (!data || typeof data.createDonation !== "function") {
      showToastNotification(
        "Donation Unavailable",
        "The secure donation connection is not available right now."
      );
      return;
    }

    const itemName = document.getElementById("don-item-name").value;
    const category = document.getElementById("don-category").value;
    const quantity = document.getElementById("don-quantity").value;
    const expiry = document.getElementById("don-expiry").value;
    const address = document.getElementById("don-distance").value;
    const instructions = document.getElementById("don-instructions").value;

    const description = [
      `Category: ${category}`,
      `Expiry: ${expiry}`,
      `Pickup address: ${address}`,
      `Instructions: ${instructions || "None provided"}`
    ].join("\n");

    let createdDonation;

    try {
      createdDonation = await data.createDonation({
        title: itemName,
        description,
        quantity
      });
    } catch (error) {
      console.error("Donation creation failed.", error);

      showToastNotification(
        "Donation Not Created",
        error && error.message
          ? error.message
          : "We could not create this donation right now."
      );

      return;
    }

    showToastNotification(
      "Donation Created!",
      "Your surplus food is now listed for community pickup."
    );

    try {
      await loadAvailableDonations();
      closeModal("donate-modal");
      donateForm.reset();
      simulateSdgProgressUpdate();
    } catch (error) {
      console.error(
        "Donation was created, but the page could not fully refresh.",
        error
      );
    }
  });

  // Handle claim submission
  const claimForm = document.getElementById("claim-food-form");
  claimForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const claimId = claimForm.getAttribute("data-target-id");
    const data = window.NourishShareData;

    if (!data || typeof data.reserveDonation !== "function") {
      showToastNotification(
        "Claim Unavailable",
        "The secure reservation connection is not available right now."
      );
      return;
    }

    try {
      await data.reserveDonation(claimId);
      await loadAvailableDonations();

      closeModal("claim-modal");
      claimForm.reset();

      showToastNotification(
        "Claim Successful!",
        "The food items have been reserved. Safe journey to your pickup location!"
      );
    } catch (error) {
      console.error("Donation reservation failed.", error);

      showToastNotification(
        "Claim Not Completed",
        error && error.message
          ? error.message
          : "We could not reserve this donation right now."
      );
    }
  });
  // Handle partner registration submission
  const registerForm = document.getElementById("partner-registration-form");
  registerForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const orgName = document.getElementById("reg-org-name").value;
    registerForm.reset();
    showToastNotification("Registration Submitted!", `Welcome, ${orgName}! Our team is reviewing your credentials.`);
  });
}

function openModal(id) {
  document.getElementById(id).classList.add("open");
}

function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}

function setupAndOpenClaimModal(id) {
  const donation = foodDonations.find(item => item.id === id);
  if (!donation) return;

  document.getElementById("claim-title").textContent = donation.title;
  document.getElementById("claim-donor").textContent = `Donated by: ${donation.donor} (${donation.address})`;
  document.getElementById("claim-meta-expiry").innerHTML = `<i class="fa-solid fa-clock"></i> ${donation.expiry}`;
  document.getElementById("claim-meta-dist").innerHTML = `<i class="fa-solid fa-location-dot"></i> ${donation.distance}`;

  const claimForm = document.getElementById("claim-food-form");
  claimForm.setAttribute("data-target-id", id);

  openModal("claim-modal");
}

function getCategoryPlaceholder(cat) {
  switch (cat) {
    case "bakery":
      return "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=400&q=80";
    case "produce":
      return "https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&w=400&q=80";
    case "prepared":
      return "https://images.unsplash.com/photo-1546549032-9571cd6b27df?auto=format&fit=crop&w=400&q=80";
    default:
      return "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=400&q=80";
  }
}

// ================= FORM INSTANT VALIDATION FEEDBACK =================
function initFormInstantValidation() {
  const fields = [
    { id: "reg-org-name", condition: val => val.length > 2 },
    { id: "reg-email", condition: val => val.includes("@") && val.includes(".") },
  ];

  fields.forEach(field => {
    const el = document.getElementById(field.id);
    if (!el) return;

    el.addEventListener("input", () => {
      const parent = el.closest(".form-group");
      if (field.condition(el.value)) {
        parent.classList.add("success");
      } else {
        parent.classList.remove("success");
      }
    });
  });
}

// ================= INTERACTIVE TOAST NOTIFICATIONS =================
function showToastNotification(title, desc) {
  const toast = document.getElementById("success-toast");
  document.getElementById("toast-title").textContent = title;
  document.getElementById("toast-desc").textContent = desc;

  toast.classList.add("show");
  
  // Confetti Simulation (Leaf Confetti)
  createConfettiShower();

  setTimeout(() => {
    toast.classList.remove("show");
  }, 4000);
}

// Simulated SDG progress bar increments when donating
// Simulated SDG progress bar increments when donating
function simulateSdgProgressUpdate() {
  const progressFill = document.querySelector(".progress-bar-fill");
  const pctText = document.getElementById("goal-pct-val");

  if (!progressFill || !pctText) return;

  let currentPct = parseInt(pctText.textContent, 10);

  if (currentPct < 98) {
    currentPct += 2;
    progressFill.style.width = `${currentPct}%`;
    pctText.textContent = currentPct;
  }
}

// Leaf-themed CSS Confetti generator
function createConfettiShower() {
  const container = document.body;
  const leavesColors = ["#81c784", "#66bb6a", "#4caf50", "#388e3c", "#a5d6a7"];
  
  for (let i = 0; i < 30; i++) {
    const leaf = document.createElement("div");
    leaf.className = "css-confetti-leaf";
    leaf.style.left = `${Math.random() * 100}vw`;
    leaf.style.top = `-20px`;
    leaf.style.backgroundColor = leavesColors[Math.floor(Math.random() * leavesColors.length)];
    leaf.style.width = `${Math.random() * 10 + 6}px`;
    leaf.style.height = `${Math.random() * 14 + 10}px`;
    leaf.style.borderRadius = "0px 10px 0px 10px"; // leaf shape
    leaf.style.position = "fixed";
    leaf.style.zIndex = "9999";
    leaf.style.opacity = Math.random();
    leaf.style.transform = `rotate(${Math.random() * 360}deg)`;
    
    // Add leaf animation inline
    leaf.animate([
      { transform: `translate(0, 0) rotate(0deg)` },
      { transform: `translate(${Math.random() * 150 - 75}px, 105vh) rotate(${Math.random() * 720}deg)` }
    ], {
      duration: Math.random() * 2000 + 2000,
      easing: "ease-out"
    });

    container.appendChild(leaf);

    // Remove element after animation
    setTimeout(() => {
      leaf.remove();
    }, 4000);
  }
}
