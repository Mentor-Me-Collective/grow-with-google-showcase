# Beacon Backend & Firebase Handoff

This folder contains the Firebase client initialization, authentication helpers, Firestore helpers, and Firestore Security Rules test suite for the Beacon Collaborative Nourish & Share project.

The project also uses Firebase Cloud Functions for server-side HTTP API routes. Cloud Functions are located in:

    functions/

---

## Architecture

The current MVP backend uses:

- Firebase Authentication for account identity
- Cloud Firestore for application data
- Firestore Security Rules for authorization and data isolation
- Firebase Cloud Functions for server-side HTTP API routes
- Firebase Emulator Suite for local integration testing

### Core Food Redistribution Flow

    Organization Registration
            |
            v
    verificationStatus = pending
            |
            v
    Admin Approval
            |
            v
    verificationStatus = approved
            |
            v
    Donor Creates Donation
            |
            v
    Recipient Views Available Donations
            |
            v
    Recipient Reserves Donation
            |
            v
    Donation: available -> reserved
            +
    Reservation Created Atomically

### Contact Flow

    Public Contact Form
            |
            v
    POST /contact
            |
            v
    Server-Side Validation
            |
            v
    contactMessages Collection
            |
            v
    Admin Dashboard / Admin API

The public Contact form does not write directly to Firestore.

---

## Client Firebase Files

### firebaseConfig.js

Initializes the Firebase Web App and exports:

- app
- auth
- db

Example:

    import { auth, db } from "./firebaseConfig.js";

### authHelpers.js

Provides Firebase Authentication helpers.

Available functions:

    loginWithEmail(auth, email, password)
    logout(auth)
    watchAuthState(auth, callback)

Example:

    import { auth } from "./firebaseConfig.js";

    import {
      loginWithEmail,
      logout,
      watchAuthState,
    } from "./authHelpers.js";

The public login page currently connects to these helpers through:

    src/frontend/public/auth-adapter.js

The adapter exposes:

    window.NourishShareAuth.signIn(...)

for the existing frontend login interface.

Post-login workspace routing remains dependent on the private/admin frontend being available.

### firebaseHelpers.js

Provides Firestore operations for the main application workflow.

Available functions include:

    getCurrentUserProfile(db, auth)

    createDonation(
      db,
      auth,
      {
        title,
        description,
        quantity,
      }
    )

    getAvailableDonations(db)

    reserveDonation(
      db,
      auth,
      donationId
    )

    getMyReservations(db, auth)

    approveOrganization(
      db,
      organizationId
    )

    rejectOrganization(
      db,
      organizationId
    )

Example:

    import {
      auth,
      db,
    } from "./firebaseConfig.js";

    import {
      createDonation,
      getAvailableDonations,
      reserveDonation,
    } from "./firebaseHelpers.js";

Frontend code should use these helpers instead of duplicating Firestore logic inside UI event handlers.

---

## Firestore Collections

### users

Document ID:

    Firebase Authentication UID

Expected fields:

    role
    accountStatus
    displayName
    organizationId

Supported application roles:

    admin
    donor
    recipient

Supported account states:

    active
    suspended
    deactivated

Example:

    users/{uid}

    role: "donor"
    accountStatus: "active"
    displayName: "Example Donor"
    organizationId: "organization-id"

### organizations

Expected fields:

    name
    type
    verificationStatus
    createdBy

Supported organization types:

    donor
    recipient

Verification states:

    pending
    approved
    rejected
    suspended

New organizations must begin with:

    verificationStatus: "pending"

Only an authenticated administrator may update organization verification state.

### donations

Expected fields:

    organizationId
    createdBy
    status
    title
    description
    quantity

Supported donation states:

    available
    reserved
    picked_up
    cancelled

Approved donors may create donations only for their own organization.

### reservations

Expected fields:

    donationId
    recipientOrganizationId
    createdBy
    status

Supported reservation states:

    active
    cancelled
    completed

### contactMessages

Contact messages are created through the server-side Contact API.

Expected fields:

    name
    email
    reason
    message
    status
    createdAt
    updatedAt

Contact status values:

    unread
    read
    resolved

New submissions always begin with:

    status: "unread"

createdAt and updatedAt are generated server-side.

Public users do not need an account to submit the Contact form.

Administrative retrieval and status changes require authenticated admin access.

---

## Atomic Reservation Rule

The reservation document ID must equal the donation document ID.

Example:

    donations/abc123
    reservations/abc123

Do not generate a separate reservation ID.

The reserveDonation() helper handles this automatically.

Reservation creation and donation status changes are performed together in a Firestore transaction:

    donation status:
    available -> reserved

and:

    matching reservation document created

Both operations succeed together or neither succeeds.

This prevents two recipients from successfully reserving the same donation.

---

## Contact HTTP API

The Contact API is implemented with Firebase Cloud Functions in:

    functions/index.js

Exported function:

    api

Local emulator base URL:

    http://127.0.0.1:5001/beacon-food-network/us-central1/api

The production base URL should be substituted after Cloud Functions deployment.

### POST /contact

Purpose:

Submit a public Contact form message.

Authentication:

None required.

Request:

    POST /contact
    Content-Type: application/json

Body:

    {
      "name": "Example Person",
      "email": "person@example.com",
      "reason": "General question",
      "message": "I would like more information."
    }

Server-side validation:

- name must be present and no more than 120 characters
- email must be a valid email address and no more than 254 characters
- reason must be present and no more than 120 characters
- message must contain 1 to 5000 characters

The API does not rely on browser-side validation as a security or data-integrity boundary.

Success:

    HTTP 201 Created

Example:

    {
      "ok": true,
      "message": "Your message has been received.",
      "id": "generated-firestore-document-id"
    }

Each submission receives a unique Firestore document ID.

The stored record includes:

    status: unread
    createdAt: server timestamp
    updatedAt: server timestamp

Validation error:

    HTTP 400 Bad Request

Example:

    {
      "ok": false,
      "error": "validation_error",
      "fields": {
        "email": "Enter a valid email address."
      }
    }

Internal server details are not returned to the client.

### GET /admin/contact-messages

Purpose:

Retrieve Contact messages for administrative review.

Authentication:

Required.

The request must contain a valid Firebase Authentication ID token:

    Authorization: Bearer <Firebase ID token>

The authenticated user must also have a Firestore user profile containing:

    role: "admin"
    accountStatus: "active"

Authentication alone is not sufficient.

Request:

    GET /admin/contact-messages
    Authorization: Bearer <token>

Success:

    HTTP 200 OK

Example:

    {
      "ok": true,
      "messages": [
        {
          "id": "message-id",
          "name": "Example Person",
          "email": "person@example.com",
          "reason": "General question",
          "message": "Example message",
          "status": "unread"
        }
      ]
    }

Messages are returned newest first.

The current endpoint returns up to 100 records.

Unauthorized / Forbidden:

    {
      "ok": false,
      "error": "forbidden"
    }

Unauthenticated users cannot retrieve Contact messages.

### PATCH /admin/contact-messages/{id}

Purpose:

Update the workflow status of a Contact message.

Authentication:

Required.

The same admin requirements used by the GET endpoint apply:

    valid Firebase ID token
    role = admin
    accountStatus = active

Request:

    PATCH /admin/contact-messages/{id}
    Authorization: Bearer <token>
    Content-Type: application/json

Body:

    {
      "status": "read"
    }

or:

    {
      "status": "resolved"
    }

Supported administrative updates:

    read
    resolved

The endpoint does not allow arbitrary field updates.

Success:

    {
      "ok": true,
      "id": "message-id",
      "status": "resolved"
    }

updatedAt is refreshed with a server timestamp.

Invalid status:

    {
      "ok": false,
      "error": "invalid_status"
    }

Missing message:

    {
      "ok": false,
      "error": "not_found"
    }

---

## Contact API Verification

The Contact API has been tested locally with the Firebase Emulator Suite.

Verified behaviors include:

- valid public Contact submission
- unique Firestore document creation
- server-side validation
- status initialized to unread
- createdAt and updatedAt server timestamps
- authenticated admin retrieval
- unauthenticated admin access blocked
- Contact status update to read
- Contact status update to resolved
- admin authorization using role = admin
- admin authorization using accountStatus = active

The local test setup used:

    Authentication Emulator: 127.0.0.1:9099
    Functions Emulator:      127.0.0.1:5001
    Firestore Emulator:      127.0.0.1:8080
    Emulator UI:             127.0.0.1:4000

---

## Security Enforcement

Frontend checks are provided for clearer UI errors, but the frontend is not the security boundary.

Firestore Security Rules enforce:

- authentication requirements
- active account requirements
- role-based access control
- organization verification
- organization ownership
- cross-organization isolation
- protected ownership fields
- admin-only organization verification
- reservation availability
- atomic reservation creation
- default deny for unmatched collections

The application should not rely on hiding buttons or pages as authorization.

The Contact API additionally performs server-side validation and server-side admin authorization through Firebase Cloud Functions.

---

## Security Tests

Security Rules tests are located in:

    firestore.rules.test.js

Run the Firestore emulator from the project root:

    firebase emulators:start --only firestore

Then, in another terminal:

    node src\backend\firestore.rules.test.js

The test suite covers successful operations and intentionally blocked operations, including:

- unauthenticated access
- role access
- organization boundaries
- suspended users
- organization self-approval attempts
- ownership-field changes
- invalid reservation creation
- atomic reservation behavior
- double-reservation attempts

PERMISSION_DENIED messages are expected during tests that intentionally verify blocked actions.

The important result is:

    All current security tests passed.

---

## Frontend Integration Notes

Use the exported helper functions instead of duplicating Firestore logic inside UI event handlers.

For example, a Reserve button should call:

    await reserveDonation(
      db,
      auth,
      donationId
    );

Do not separately:

1. create a reservation
2. update the donation

The helper already performs those operations atomically.

Likewise, donor listing creation should use:

    await createDonation(
      db,
      auth,
      {
        title,
        description,
        quantity,
      }
    );

Firestore Security Rules remain authoritative even when these helpers are used.

The public Contact form is connected through:

    src/frontend/public/contact.js

The current local Contact API URL is:

    http://127.0.0.1:5001/beacon-food-network/us-central1/api/contact

This URL should be changed to the deployed Cloud Functions URL before final production deployment.
