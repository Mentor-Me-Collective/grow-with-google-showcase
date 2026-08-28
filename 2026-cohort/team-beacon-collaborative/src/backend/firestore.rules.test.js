const fs = require("fs");
const path = require("path");

const {
  initializeTestEnvironment,
  assertSucceeds,
  assertFails,
} = require("@firebase/rules-unit-testing");

const {
  doc,
  getDoc,
  setDoc,
  updateDoc,
  runTransaction,
} = require("firebase/firestore");

const PROJECT_ID = "beacon-food-network";

let testEnv;

// --------------------------------------------------
// ATOMIC RESERVATION HELPER
// --------------------------------------------------

async function reserveDonation(
  db,
  donationId,
  recipientOrganizationId,
  recipientUserId
) {
  const donationRef = doc(
    db,
    "donations",
    donationId
  );

  const reservationRef = doc(
    db,
    "reservations",
    donationId
  );

  return runTransaction(db, async (transaction) => {
    const donationSnapshot =
      await transaction.get(donationRef);

    if (!donationSnapshot.exists()) {
      throw new Error("Donation does not exist");
    }

    transaction.update(
      donationRef,
      {
        status: "reserved",
      }
    );

    transaction.set(
      reservationRef,
      {
        donationId,
        recipientOrganizationId,
        createdBy: recipientUserId,
        status: "active",
      }
    );
  });
}

// --------------------------------------------------
// TEST DATA
// --------------------------------------------------

async function seedTestData() {
  await testEnv.withSecurityRulesDisabled(
    async (context) => {
      const db = context.firestore();

      // USERS

      await setDoc(
        doc(db, "users", "admin-test"),
        {
          role: "admin",
          accountStatus: "active",
          displayName: "Admin Test",
          organizationId: "platform-admin",
        }
      );

      await setDoc(
        doc(db, "users", "donor-a-test"),
        {
          role: "donor",
          accountStatus: "active",
          displayName: "Donor A",
          organizationId: "donor-org-a",
        }
      );

      await setDoc(
        doc(db, "users", "donor-b-test"),
        {
          role: "donor",
          accountStatus: "active",
          displayName: "Donor B",
          organizationId: "donor-org-b",
        }
      );

      await setDoc(
        doc(db, "users", "recipient-a-test"),
        {
          role: "recipient",
          accountStatus: "active",
          displayName: "Recipient A",
          organizationId: "recipient-org-a",
        }
      );

      await setDoc(
        doc(db, "users", "recipient-b-test"),
        {
          role: "recipient",
          accountStatus: "active",
          displayName: "Recipient B",
          organizationId: "recipient-org-b",
        }
      );

      await setDoc(
        doc(db, "users", "suspended-donor-test"),
        {
          role: "donor",
          accountStatus: "suspended",
          displayName: "Suspended Donor",
          organizationId: "donor-org-a",
        }
      );

      // ORGANIZATIONS

      await setDoc(
        doc(
          db,
          "organizations",
          "donor-org-a"
        ),
        {
          name: "Donor Organization A",
          type: "donor",
          verificationStatus: "approved",
          createdBy: "donor-a-test",
        }
      );

      await setDoc(
        doc(
          db,
          "organizations",
          "donor-org-b"
        ),
        {
          name: "Donor Organization B",
          type: "donor",
          verificationStatus: "approved",
          createdBy: "donor-b-test",
        }
      );

      await setDoc(
        doc(
          db,
          "organizations",
          "recipient-org-a"
        ),
        {
          name: "Recipient Organization A",
          type: "recipient",
          verificationStatus: "approved",
          createdBy: "recipient-a-test",
        }
      );

      await setDoc(
        doc(
          db,
          "organizations",
          "recipient-org-b"
        ),
        {
          name: "Recipient Organization B",
          type: "recipient",
          verificationStatus: "approved",
          createdBy: "recipient-b-test",
        }
      );

      // AVAILABLE DONATION

      await setDoc(
        doc(
          db,
          "donations",
          "donation-a-001"
        ),
        {
          organizationId: "donor-org-a",
          createdBy: "donor-a-test",
          status: "available",
          title: "Fresh Produce Box",
          description:
            "Mixed surplus fruits and vegetables",
          quantity: "10 boxes",
        }
      );

      // EXISTING RESERVED DONATION

      await setDoc(
        doc(
          db,
          "donations",
          "donation-reserved-001"
        ),
        {
          organizationId: "donor-org-a",
          createdBy: "donor-a-test",
          status: "reserved",
          title: "Reserved Produce",
          description:
            "Already reserved by Recipient A",
          quantity: "2 boxes",
        }
      );

      await setDoc(
        doc(
          db,
          "reservations",
          "donation-reserved-001"
        ),
        {
          donationId: "donation-reserved-001",
          recipientOrganizationId:
            "recipient-org-a",
          createdBy: "recipient-a-test",
          status: "active",
        }
      );

      // RESERVED DONATION WITH NO RESERVATION
      // Used only to prove invalid reservation
      // creation is rejected.

      await setDoc(
        doc(
          db,
          "donations",
          "donation-unavailable-001"
        ),
        {
          organizationId: "donor-org-a",
          createdBy: "donor-a-test",
          status: "reserved",
          title: "Unavailable Donation",
          description:
            "Used for negative security testing",
          quantity: "1 box",
        }
      );
    }
  );
}

// --------------------------------------------------
// TEST RUNNER
// --------------------------------------------------

async function runTests() {
  try {
    testEnv =
      await initializeTestEnvironment({
        projectId: PROJECT_ID,

        firestore: {
          host: "127.0.0.1",
          port: 8080,

          rules: fs.readFileSync(
            path.join(
              __dirname,
              "..",
              "..",
              "firestore.rules"
            ),
            "utf8"
          ),
        },
      });

    await testEnv.clearFirestore();
    await seedTestData();

    console.log(
      "\nRunning Firestore security tests...\n"
    );

    // --------------------------------------------------
    // AUTH CONTEXTS
    // --------------------------------------------------

    const adminDb =
      testEnv
        .authenticatedContext("admin-test")
        .firestore();

    const donorADb =
      testEnv
        .authenticatedContext("donor-a-test")
        .firestore();

    const donorBDb =
      testEnv
        .authenticatedContext("donor-b-test")
        .firestore();

    const recipientADb =
      testEnv
        .authenticatedContext(
          "recipient-a-test"
        )
        .firestore();

    const recipientBDb =
      testEnv
        .authenticatedContext(
          "recipient-b-test"
        )
        .firestore();

    const suspendedDonorDb =
      testEnv
        .authenticatedContext(
          "suspended-donor-test"
        )
        .firestore();

    const attackerDb =
      testEnv
        .authenticatedContext(
          "attacker-test"
        )
        .firestore();

    const unauthenticatedDb =
      testEnv
        .unauthenticatedContext()
        .firestore();

    // --------------------------------------------------
    // BASIC READ ACCESS
    // --------------------------------------------------

    await assertSucceeds(
      getDoc(
        doc(
          adminDb,
          "users",
          "donor-a-test"
        )
      )
    );

    console.log(
      "PASS: Admin can read another user's profile"
    );

    await assertSucceeds(
      getDoc(
        doc(
          donorADb,
          "donations",
          "donation-a-001"
        )
      )
    );

    console.log(
      "PASS: Approved donor can read donations"
    );

    await assertSucceeds(
      getDoc(
        doc(
          recipientADb,
          "donations",
          "donation-a-001"
        )
      )
    );

    console.log(
      "PASS: Approved recipient can read donations"
    );

    await assertFails(
      getDoc(
        doc(
          unauthenticatedDb,
          "donations",
          "donation-a-001"
        )
      )
    );

    console.log(
      "PASS: Unauthenticated user cannot read donations"
    );

    // --------------------------------------------------
    // EXISTING RESERVATION ACCESS
    // --------------------------------------------------

    await assertSucceeds(
      getDoc(
        doc(
          recipientADb,
          "reservations",
          "donation-reserved-001"
        )
      )
    );

    console.log(
      "PASS: Recipient A can read its own reservation"
    );

    await assertFails(
      getDoc(
        doc(
          recipientBDb,
          "reservations",
          "donation-reserved-001"
        )
      )
    );

    console.log(
      "PASS: Recipient B cannot read Recipient A's reservation"
    );

    // --------------------------------------------------
    // CROSS-ORG DONATION WRITE
    // --------------------------------------------------

    await assertFails(
      updateDoc(
        doc(
          donorBDb,
          "donations",
          "donation-a-001"
        ),
        {
          title: "Unauthorized Edit",
        }
      )
    );

    console.log(
      "PASS: Donor B cannot modify Donor A's donation"
    );

    // --------------------------------------------------
    // VALID DONOR CREATE
    // --------------------------------------------------

    await assertSucceeds(
      setDoc(
        doc(
          donorADb,
          "donations",
          "donation-atomic-001"
        ),
        {
          organizationId: "donor-org-a",
          createdBy: "donor-a-test",
          status: "available",
          title: "Bakery Surplus",
          description:
            "Bread and pastries",
          quantity: "6 boxes",
        }
      )
    );

    console.log(
      "PASS: Approved Donor A can create a donation"
    );

    // --------------------------------------------------
    // ATOMIC RESERVATION SUCCESS
    // --------------------------------------------------

    await assertSucceeds(
      reserveDonation(
        recipientADb,
        "donation-atomic-001",
        "recipient-org-a",
        "recipient-a-test"
      )
    );

    console.log(
      "PASS: Recipient A can atomically reserve an available donation"
    );

    // Verify both halves actually committed.

    const reservedDonationSnapshot =
      await getDoc(
        doc(
          recipientADb,
          "donations",
          "donation-atomic-001"
        )
      );

    if (
      reservedDonationSnapshot.data().status
      !== "reserved"
    ) {
      throw new Error(
        "Atomic reservation failed to mark donation reserved"
      );
    }

    const reservationSnapshot =
      await getDoc(
        doc(
          recipientADb,
          "reservations",
          "donation-atomic-001"
        )
      );

    if (
      reservationSnapshot.data().createdBy
      !== "recipient-a-test"
    ) {
      throw new Error(
        "Atomic reservation created incorrect ownership"
      );
    }

    console.log(
      "PASS: Atomic reservation committed both linked document changes"
    );

    // --------------------------------------------------
    // DOUBLE-BOOKING ATTEMPT
    // --------------------------------------------------

    await assertFails(
      reserveDonation(
        recipientBDb,
        "donation-atomic-001",
        "recipient-org-b",
        "recipient-b-test"
      )
    );

    console.log(
      "PASS: Recipient B cannot reserve a donation already reserved by Recipient A"
    );

    // --------------------------------------------------
    // STANDALONE RESERVATION MUST FAIL
    // --------------------------------------------------

    await assertSucceeds(
      setDoc(
        doc(
          donorADb,
          "donations",
          "donation-standalone-001"
        ),
        {
          organizationId: "donor-org-a",
          createdBy: "donor-a-test",
          status: "available",
          title: "Standalone Test Donation",
          description:
            "Used to test atomic enforcement",
          quantity: "3 boxes",
        }
      )
    );

    await assertFails(
      setDoc(
        doc(
          recipientADb,
          "reservations",
          "donation-standalone-001"
        ),
        {
          donationId:
            "donation-standalone-001",
          recipientOrganizationId:
            "recipient-org-a",
          createdBy: "recipient-a-test",
          status: "active",
        }
      )
    );

    console.log(
      "PASS: Reservation cannot be created without reserving donation in same atomic operation"
    );

    // --------------------------------------------------
    // STANDALONE DONATION RESERVE MUST FAIL
    // --------------------------------------------------

    await assertFails(
      updateDoc(
        doc(
          recipientADb,
          "donations",
          "donation-standalone-001"
        ),
        {
          status: "reserved",
        }
      )
    );

    console.log(
      "PASS: Recipient cannot reserve donation status without creating matching reservation"
    );

    // --------------------------------------------------
    // NON-ADMIN ORGANIZATION UPDATE
    // --------------------------------------------------

    await assertFails(
      updateDoc(
        doc(
          donorADb,
          "organizations",
          "donor-org-a"
        ),
        {
          verificationStatus: "approved",
        }
      )
    );

    console.log(
      "PASS: Non-admin cannot update organization verification"
    );

    // --------------------------------------------------
    // SUSPENDED USER
    // --------------------------------------------------

    await assertFails(
      setDoc(
        doc(
          suspendedDonorDb,
          "donations",
          "suspended-donation-001"
        ),
        {
          organizationId: "donor-org-a",
          createdBy:
            "suspended-donor-test",
          status: "available",
          title: "Blocked Donation",
          description:
            "Should not be allowed",
          quantity: "1 box",
        }
      )
    );

    console.log(
      "PASS: Suspended donor cannot create donations"
    );

    // --------------------------------------------------
    // USER CANNOT CLAIM APPROVED ORG
    // --------------------------------------------------

    await assertFails(
      setDoc(
        doc(
          attackerDb,
          "users",
          "attacker-test"
        ),
        {
          role: "donor",
          accountStatus: "active",
          displayName: "Attacker",
          organizationId: "donor-org-a",
        }
      )
    );

    console.log(
      "PASS: User cannot attach themselves to another approved organization"
    );

    // --------------------------------------------------
    // ORGANIZATION CANNOT SELF-APPROVE
    // --------------------------------------------------

    await assertFails(
      setDoc(
        doc(
          attackerDb,
          "organizations",
          "attacker-org"
        ),
        {
          name: "Attacker Organization",
          type: "donor",
          verificationStatus: "approved",
          createdBy: "attacker-test",
        }
      )
    );

    console.log(
      "PASS: Organization cannot self-approve during creation"
    );

    // --------------------------------------------------
    // MISSING DONATION RESERVATION
    // --------------------------------------------------

    await assertFails(
      setDoc(
        doc(
          recipientADb,
          "reservations",
          "does-not-exist"
        ),
        {
          donationId: "does-not-exist",
          recipientOrganizationId:
            "recipient-org-a",
          createdBy: "recipient-a-test",
          status: "active",
        }
      )
    );

    console.log(
      "PASS: Recipient cannot reserve a missing donation"
    );

    // --------------------------------------------------
    // NON-AVAILABLE DONATION RESERVATION
    // --------------------------------------------------

    await assertFails(
      setDoc(
        doc(
          recipientADb,
          "reservations",
          "donation-unavailable-001"
        ),
        {
          donationId:
            "donation-unavailable-001",
          recipientOrganizationId:
            "recipient-org-a",
          createdBy: "recipient-a-test",
          status: "active",
        }
      )
    );

    console.log(
      "PASS: Recipient cannot reserve a non-available donation"
    );

    // --------------------------------------------------
    // DONATION OWNERSHIP IMMUTABILITY
    // --------------------------------------------------

    await assertFails(
      updateDoc(
        doc(
          donorADb,
          "donations",
          "donation-a-001"
        ),
        {
          organizationId: "donor-org-b",
        }
      )
    );

    console.log(
      "PASS: Donor cannot change donation organization ownership"
    );

    await assertFails(
      updateDoc(
        doc(
          donorADb,
          "donations",
          "donation-a-001"
        ),
        {
          createdBy: "donor-b-test",
        }
      )
    );

    console.log(
      "PASS: Donor cannot change donation creator ownership"
    );

    // --------------------------------------------------
    // RESERVATION OWNERSHIP IMMUTABILITY
    // --------------------------------------------------

    await assertFails(
      updateDoc(
        doc(
          recipientADb,
          "reservations",
          "donation-reserved-001"
        ),
        {
          recipientOrganizationId:
            "recipient-org-b",
        }
      )
    );

    console.log(
      "PASS: Recipient cannot change reservation organization ownership"
    );

    await assertFails(
      updateDoc(
        doc(
          recipientADb,
          "reservations",
          "donation-reserved-001"
        ),
        {
          donationId:
            "donation-unavailable-001",
        }
      )
    );

    console.log(
      "PASS: Recipient cannot change reservation donation ownership"
    );

    await assertFails(
      updateDoc(
        doc(
          recipientADb,
          "reservations",
          "donation-reserved-001"
        ),
        {
          createdBy: "recipient-b-test",
        }
      )
    );

    console.log(
      "PASS: Recipient cannot change reservation creator ownership"
    );

    // --------------------------------------------------
    // USER PROFILE UPDATE PERMISSIONS
    // --------------------------------------------------

    await assertSucceeds(
      updateDoc(
        doc(
          donorADb,
          "users",
          "donor-a-test"
        ),
        {
          displayName: "Updated Donor A",
          profile: {
            contact: {
              name: "Updated Donor A",
            },
          },
        }
      )
    );

    console.log(
      "PASS: User can update own display name and profile"
    );

    await assertSucceeds(
      updateDoc(
        doc(
          donorADb,
          "users",
          "donor-a-test"
        ),
        {
          "profile.settings": {
            notifyEmail: true,
            notifySms: false,
          },
        }
      )
    );

    console.log(
      "PASS: User can update own nested profile settings"
    );

    await assertFails(
      updateDoc(
        doc(
          donorADb,
          "users",
          "donor-a-test"
        ),
        {
          role: "admin",
        }
      )
    );

    console.log(
      "PASS: User cannot change own role"
    );

    await assertFails(
      updateDoc(
        doc(
          donorADb,
          "users",
          "donor-a-test"
        ),
        {
          accountStatus: "suspended",
        }
      )
    );

    console.log(
      "PASS: User cannot change own account status"
    );

    await assertFails(
      updateDoc(
        doc(
          donorADb,
          "users",
          "donor-a-test"
        ),
        {
          organizationId: "donor-org-b",
        }
      )
    );

    console.log(
      "PASS: User cannot change own organization"
    );

    // --------------------------------------------------
    // CONVERSATION ACCESS
    // --------------------------------------------------

    await assertSucceeds(
      setDoc(
        doc(
          recipientADb,
          "conversations",
          "donation-reserved-001"
        ),
        {
          donationId: "donation-reserved-001",
          donorUid: "donor-a-test",
          recipientUid: "recipient-a-test",
          participants: [
            "donor-a-test",
            "recipient-a-test",
          ],
        }
      )
    );

    console.log(
      "PASS: Approved recipient can create valid donation conversation"
    );

    await assertSucceeds(
      getDoc(
        doc(
          donorADb,
          "conversations",
          "donation-reserved-001"
        )
      )
    );

    await assertSucceeds(
      getDoc(
        doc(
          recipientADb,
          "conversations",
          "donation-reserved-001"
        )
      )
    );

    console.log(
      "PASS: Conversation participants can read conversation"
    );

    await assertFails(
      getDoc(
        doc(
          recipientBDb,
          "conversations",
          "donation-reserved-001"
        )
      )
    );

    console.log(
      "PASS: Nonparticipant cannot read conversation"
    );

    // --------------------------------------------------
    // MESSAGE ACCESS
    // --------------------------------------------------

    await assertSucceeds(
      setDoc(
        doc(
          recipientADb,
          "messages",
          "message-test-001"
        ),
        {
          conversationId: "donation-reserved-001",
          senderUid: "recipient-a-test",
          senderName: "Recipient A",
          senderRole: "Recipient",
          senderEmail: "recipient-a@example.com",
          text: "Security test message",
          timestamp: Date.now(),
        }
      )
    );

    console.log(
      "PASS: Conversation participant can create message"
    );

    await assertSucceeds(
      getDoc(
        doc(
          donorADb,
          "messages",
          "message-test-001"
        )
      )
    );

    console.log(
      "PASS: Conversation participant can read message"
    );

    await assertFails(
      getDoc(
        doc(
          recipientBDb,
          "messages",
          "message-test-001"
        )
      )
    );

    console.log(
      "PASS: Nonparticipant cannot read message"
    );

    await assertFails(
      setDoc(
        doc(
          recipientBDb,
          "messages",
          "message-test-002"
        ),
        {
          conversationId: "donation-reserved-001",
          senderUid: "recipient-b-test",
          senderName: "Recipient B",
          senderRole: "Recipient",
          senderEmail: "recipient-b@example.com",
          text: "Unauthorized message",
          timestamp: Date.now(),
        }
      )
    );

    console.log(
      "PASS: Nonparticipant cannot create conversation message"
    );

    console.log(
      "\nAll current security tests passed.\n"
    );
  } catch (error) {
    console.error(
      "\nTEST FAILURE:"
    );

    console.error(error);

    process.exitCode = 1;
  } finally {
    if (testEnv) {
      await testEnv.cleanup();
    }
  }
}

runTests();
