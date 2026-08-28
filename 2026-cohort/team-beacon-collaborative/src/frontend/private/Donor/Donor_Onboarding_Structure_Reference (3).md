# Donor Onboarding Structure — Reference Document
## Surplus Food Redistribution Network (Private Donor Website)

This document captures the agreed donor onboarding flow, donor types, and field-level decisions to guide future build work. **Not yet implemented — reference only.**

---

## 1. Donor Onboarding Flow

```
Donor
 ↓
Choose donor type
 ↓
[Grocery Store / Restaurant / Bakery / Farm / Food Manufacturer / Supermarket / Community Organization]
 ↓
Business information
 ↓
Contact information
 ↓
Donation information (profile/capacity — NOT a live listing)
 ↓
Account credentials
 ↓
Review & submit
 ↓
Account created
 ↓
Donor dashboard
```

This same flow applies to **all seven donor types** — no separate registration paths, just conditional fields inside the "Business information" and "Donation information" steps.

---

## 2. Donor Types (All Live in MVP)

Unlike the original documentation (which scoped only Grocery Store for MVP and treated the rest as future expansion), this build includes **all seven types as active donor categories from launch**:

1. Grocery Store
2. Restaurant
3. Bakery
4. Farm
5. Food Manufacturer
6. Supermarket
7. Community Organization (as a donor)

---

## 3. Business Information — Shared Core + Type-Specific Fields

**Design approach:** one reusable form component, with a small set of conditional fields shown based on the donor type selected in the previous step. Avoids duplicating seven separate forms.

### Shared Core Fields (all donor types)
- Business / Organization Name
- Business Type *(auto-filled from previous step)*
- Address
- Business License / Registration Number (for admin verification)
- Years in Operation *(optional)*
- Website *(optional)*

### Type-Specific Fields

| Donor Type | Extra Field(s) |
|---|---|
| Grocery Store | Store size, number of locations |
| Supermarket | Store size, number of locations |
| Restaurant | Cuisine type, seating capacity |
| Bakery | Products typically made |
| Farm | Type of produce grown, seasonal availability |
| Food Manufacturer | Product categories, production scale |
| Community Organization | Organization mission/type, nonprofit status |

---

## 4. "Donation Information" at Signup — Clarified Scope

This step is **profile/capacity information**, not an actual food listing.

| | Signup: "Donation Information" | Post-Login: "Donate Food" screen |
|---|---|---|
| Purpose | Describes the donor's general donation capability | Publishes a specific, real donation |
| Contains | Expected food categories, donation frequency, general pickup availability, storage/refrigeration capability | Food name, quantity, expiration date, specific pickup window, images |
| When filled | Once, during registration (editable later via Profile) | Every time a new donation is created |
| Used for | Helping admins/recipients understand donor capacity ahead of time; can pre-fill defaults on future donation forms | Actual, time-sensitive redistribution transaction |

### Suggested Fields for Signup "Donation Information" Step
- Typical food categories expected to donate (produce, bakery, dairy, prepared meals, etc.)
- Estimated donation frequency (daily / weekly / occasional)
- General pickup availability window (e.g., weekday mornings)
- Storage / refrigeration availability (relevant for perishables)

---

## 5. Contact Information Step

**Decision:** The contact person is the same person creating the account (single login, single primary contact — no multi-user org accounts at MVP stage).

### Fields
- Contact Person Name
- Job Title / Role (e.g., "Store Manager," "Owner")
- Phone Number
- Email *(this becomes the login email — see Account Credentials below)*
- Preferred Contact Method (Phone / Email / In-app Messages)

**Rationale:** Most donor organizations (bakeries, farms, single-location stores) won't have a separate admin setting up accounts on someone else's behalf. A single point of contact simplifies verification and keeps communication unambiguous. Multi-user org accounts can be considered as a future enhancement.

---

## 6. Account Credentials Step

### Fields
- Email *(auto-filled from Contact Information, editable if a different login email is preferred — e.g., a shared inbox like donations@business.com)*
- Password
- Confirm Password
- Terms of Service / Privacy Policy agreement checkbox *(required)*

**Rationale:** Reusing the contact email by default reduces friction while still allowing overrides. Two-factor authentication is not included at MVP but is a reasonable future enhancement (aligns with "Account Security" mentioned under Settings in the original documentation).

---

## 7. Account Created → Verification State

**Decision:** New accounts are created in a **Pending Verification** state, not full dashboard access. This matches the original documentation's verification-before-access model (Chapters 12.2, 12.6, 16.4).

### Updated Flow
```
Review & Submit
 ↓
Account Created
 ↓
Pending Verification screen
 (org can log in, view status, edit profile —
  cannot post donations until approved)
 ↓
Admin Approves
 ↓
Full Donor Dashboard unlocked
```

### Pending Verification Screen — Suggested Contents
- Status message (e.g., "Your account is under review")
- Estimated review timeframe (if applicable)
- Editable profile/business info while waiting
- No access to: Donate Food, Messages, Pickup Scheduling
- Notification sent automatically ("Account Approved") when admin approves — ties into the platform's existing Notification Module

**Rationale:** Since donors coordinate real food handoffs with recipient organizations, verification protects the trust model the whole platform depends on. Immediate unrestricted access would undermine that.

---

## 8. Open Items for Future Decisions
- Whether Recipient onboarding needs a parallel structure (Food Pantry now; Soup Kitchen, School Meal Program, Community Org, Regional Food Bank per original doc — status TBD per your build)
- Verification requirements per donor type (e.g., does Community Organization need nonprofit documentation upload?)
- Whether "Donation Information" profile data should pre-fill the "Donate Food" form fields
- Whether multi-user org accounts (separate login vs. contact person) should be added post-MVP
