# Recipient Onboarding Structure — Reference Document
## Surplus Food Redistribution Network (Private Recipient Website)

This document captures the agreed recipient onboarding flow, recipient types, and field-level decisions — mirroring the donor reference doc. **Already built — this is the reference record.**

---

## 1. Recipient Onboarding Flow

```
Recipient
 ↓
Choose recipient type
 ↓
[Food Pantry / Soup Kitchen / School Meal Program / Community Organization / Regional Food Bank]
 ↓
Organization information
 ↓
Contact information
 ↓
Capacity information (profile/capacity — NOT a live reservation)
 ↓
Account credentials
 ↓
Review & submit
 ↓
Account created
 ↓
Pending Verification screen
 ↓
Recipient Dashboard
```

Same flow applies to **all five recipient types** — no separate registration paths, just conditional fields inside the "Organization information" step.

---

## 2. Recipient Types (All Live in MVP)

Same treatment as donors: unlike the original documentation (which scoped only Food Pantry for MVP and treated the rest as future expansion), this build includes **all five types as active recipient categories from launch**:

1. Food Pantry
2. Soup Kitchen
3. School Meal Program
4. Community Organization
5. Regional Food Bank

---

## 3. Organization Information — Shared Core + Type-Specific Fields

**Design approach:** one reusable form component, with a small set of conditional fields shown based on the recipient type selected in the previous step — same pattern as the donor build.

### Shared Core Fields (all recipient types)
- Organization Name
- Recipient Type *(auto-filled from previous step)*
- Address
- Registration / Nonprofit Number (for admin verification)
- Years in Operation *(optional)*
- Website *(optional)*

### Type-Specific Fields

| Recipient Type | Extra Field(s) |
|---|---|
| Food Pantry | Households served weekly, Distribution model (Walk-in / Pre-scheduled pickup / Home delivery / Mixed) |
| Soup Kitchen | Meals served per day, Service days/hours |
| School Meal Program | Number of students served, School/district name |
| Community Organization | Organization mission/type, Nonprofit status |
| Regional Food Bank | Service area, Number of partner organizations |

---

## 4. Contact Information Step

**Decision:** Same as donor — the contact person is the same person creating the account (single login, single primary contact — no multi-user org accounts at MVP stage).

### Fields
- Contact Person Name
- Job Title / Role (e.g., "Pantry Coordinator," "Program Director")
- Phone Number
- Email *(becomes the login email — see Account Credentials below)*
- Preferred Contact Method (Phone / Email / In-app Messages)

---

## 5. "Capacity Information" at Signup — Clarified Scope

Mirrors the donor build's "Donation Information" distinction. This step is **profile/capacity information**, not an actual reservation.

| | Signup: "Capacity Information" | Post-Login: "Reserve Food" / "Available Food" screen |
|---|---|---|
| Purpose | Describes the recipient's general receiving capability | Claims a specific, real donation listing |
| Contains | Food categories most needed, people served weekly, receiving frequency, general pickup/receiving availability, storage/refrigeration capability | Specific food item, quantity, pickup time, donor details |
| When filled | Once, during registration (editable later via Profile) | Every time a reservation is made |
| Used for | Helping donors/admins understand recipient capacity ahead of time | Actual, time-sensitive redistribution transaction |

### Fields for Signup "Capacity Information" Step
- Food categories most needed (produce, bakery, dairy, prepared meals, packaged goods, meat & seafood)
- Estimated people served weekly
- How often the org can receive donations (Daily / Weekly / Occasional)
- General pickup / receiving availability window
- Storage / refrigeration availability on-site (Yes / No / Limited)

---

## 6. Account Credentials Step

### Fields
- Email *(auto-filled from Contact Information, editable if a different login email is preferred)*
- Password
- Confirm Password
- Terms of Service / Privacy Policy agreement checkbox *(required)*

---

## 7. Account Created → Verification State

**Decision:** Same verification-before-access model as donors. New accounts land in a **Pending Verification** state, not full dashboard access.

### Flow
```
Review & Submit
 ↓
Account Created
 ↓
Pending Verification screen
 (org can log in, view status, edit profile —
  cannot reserve food until approved)
 ↓
Admin Approves
 ↓
Full Recipient Dashboard unlocked
```

### Pending Verification Screen — Contents
- Status message (e.g., "Your account is under review")
- Editable organization profile while waiting
- No access to: Browsing available donations, Reserving food, Messaging donor organizations
- Notification sent automatically ("Account Approved") when admin approves

---

## 8. Open Items for Future Decisions
- Whether multi-user org accounts (separate login vs. contact person) should be added post-MVP
- Verification requirements per recipient type (e.g., does School Meal Program need district authorization documentation?)
- Whether "Capacity Information" profile data should pre-fill filters on the "Available Food" browsing screen
