process.env.FIRESTORE_EMULATOR_HOST = "127.0.0.1:8080";
process.env.FIREBASE_AUTH_EMULATOR_HOST = "127.0.0.1:9099";
process.env.GCLOUD_PROJECT = "beacon-food-network";

const admin = require("../functions/node_modules/firebase-admin");

admin.initializeApp({
  projectId: "beacon-food-network",
});

const auth = admin.auth();
const db = admin.firestore();

const PASSWORD = "TeamBeacon2026!";

async function ensureUser({
  email,
  role,
  displayName,
  organizationId,
  organizationName,
  profile = {},
}) {
  let user;

  try {
    user = await auth.getUserByEmail(email);
    console.log(`Auth user already exists: ${email}`);
  } catch (error) {
    if (error.code !== "auth/user-not-found") {
      throw error;
    }

    user = await auth.createUser({
      email,
      password: PASSWORD,
      displayName,
    });

    console.log(`Created Auth user: ${email}`);
  }

  await db.collection("users").doc(user.uid).set({
    role,
    accountStatus: "active",
    displayName,
    organizationId,
    profile,
  });

  await db.collection("organizations").doc(organizationId).set({
    name: organizationName,
    type: role,
    verificationStatus: "approved",
    createdBy: user.uid,
  });

  return user;
}


function createDemoAvatar(initials, background) {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
      <rect width="256" height="256" rx="128" fill="${background}"/>
      <text
        x="128"
        y="144"
        text-anchor="middle"
        font-family="Arial, Helvetica, sans-serif"
        font-size="88"
        font-weight="700"
        fill="#ffffff"
      >${initials}</text>
    </svg>
  `;

  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

async function main() {
  const donor = await ensureUser({
    email: "donor-a@example.com",
    role: "donor",
    displayName: "Jordan Lee",
    organizationId: "donor-org-test",
    organizationName: "Beacon Fresh Market",
    profile: {
      donorType: "grocery",
      business: {
        bizName: "Beacon Fresh Market",
        bizAddress: "121 N LaSalle St, Chicago, IL 60602",
        bizLicense: "DEMO-CHICAGO-001",
        bizWebsite: "https://example.org/beacon-fresh-market",
        bizYears: "8",
      },
      contact: {
        ctName: "Jordan Lee",
        ctTitle: "Food Recovery Coordinator",
        ctEmail: "donor-a@example.com",
        ctPhone: "(312) 555-0142",
        ctMethod: "email",
      },
      donation: {
        donFrequency: "Weekly",
        donStorage: "Refrigerated and dry storage",
        donWindow: "Weekdays, 2 PM - 6 PM",
        foodCategories: ["produce", "bakery", "dairy"],
      },
      avatarUrl: createDemoAvatar("BF", "#2f6f4e"),
    },
  });

  const recipient = await ensureUser({
    email: "recipient-a@example.com",
    role: "recipient",
    displayName: "Maya Brooks",
    organizationId: "recipient-org-test",
    organizationName: "Westside Community Pantry",
    profile: {
      recipientType: "pantry",
      org: {
        orgName: "Westside Community Pantry",
        orgAddress: "4133 W Madison St, Chicago, IL 60624",
        orgLicense: "DEMO-CHICAGO-002",
        orgWebsite: "https://example.org/westside-community-pantry",
        orgYears: "12",
      },
      contact: {
        ctName: "Maya Brooks",
        ctTitle: "Pantry Coordinator",
        ctEmail: "recipient-a@example.com",
        ctPhone: "(773) 555-0186",
        ctMethod: "email",
      },
      capacity: {
        capFrequency: "Daily",
        capServed: "150 households per week",
        capStorage: "Refrigerated, frozen, and shelf-stable",
        capWindow: "Monday - Friday, 9 AM - 5 PM",
        foodCategories: ["produce", "bakery", "dairy"],
      },
      avatarUrl: createDemoAvatar("WC", "#416b78"),
    },
  });

  let adminUser;

  try {
    adminUser = await auth.getUserByEmail("admin-a@example.com");
    console.log("Auth user already exists: admin-a@example.com");
  } catch (error) {
    if (error.code !== "auth/user-not-found") {
      throw error;
    }

    adminUser = await auth.createUser({
      email: "admin-a@example.com",
      password: PASSWORD,
      displayName: "Alex Morgan",
    });
  }

  await db.collection("users").doc(adminUser.uid).set({
    role: "admin",
    accountStatus: "active",
    displayName: "Alex Morgan",
    profile: {
      title: "Platform Administrator",
    },
  });

  await db.collection("donations").doc("test-bakery-box").set({
    organizationId: "donor-org-test",
    createdBy: donor.uid,
    status: "available",
    title: "Fresh Produce Rescue Box",
    description: [
      "Category: produce",
      "Expiry: Same day",
      "Pickup address: 121 N LaSalle St, Chicago, IL 60602",
      "Pickup availability: Today, 2 PM - 5 PM",
      "Instructions: Check in at the front desk for pickup.",
    ].join("\n"),
    quantity: "4 boxes",
    photos: [],
    pickupAddress: "121 N LaSalle St, Chicago, IL 60602",
    pickupLocation: {
      address: "121 N LaSalle St, Chicago, IL 60602",
      latitude: 41.8837,
      longitude: -87.6324,
      displayName: "121 N LaSalle St, Chicago, IL 60602",
      source: "Demo seed",
    },
  });

  console.log("");
  console.log("Emulator seed complete.");
  console.log(`Donor: donor-a@example.com / ${PASSWORD}`);
  console.log(`Recipient: recipient-a@example.com / ${PASSWORD}`);
  console.log(`Admin: admin-a@example.com / ${PASSWORD}`);
  console.log(`Donor UID: ${donor.uid}`);
  console.log(`Recipient UID: ${recipient.uid}`);
  console.log("Donation: Fresh Produce Rescue Box");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Seed failed:");
    console.error(error);
    process.exit(1);
  });