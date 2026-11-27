# ShiftBridge Frontend Overview

The ShiftBridge frontend is a **React + TypeScript** single-page application (SPA) styled with **Tailwind CSS** and **Lucide React** icons. It provides an interactive, role-based interface for workers and managers to view weekly schedules, chat with an AI scheduling assistant, and approve shift change proposals.

---

## Tech Stack

- **Framework:** React (with Hooks)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Icons:** `lucide-react`
- **State & Routing:** Local React state + `window.history.pushState` / `popstate` (for `/login` and `/dashboard`)
- **Authentication:** JWT stored in `localStorage` (`jwt`)

---

## Application Architecture (`App.tsx`)

`App.tsx` serves as the root controller, managing:

- **Authentication & Routing:** Checks for a `jwt` in `localStorage` on mount, fetches the current user via `api.getMe(token)`, and routes between `/login` (`AuthCard`) and `/dashboard`.
- **Role Detection:** Determines whether the logged-in user is a `manager` or `worker` (currently based on `user.id.startsWith('m')`).
- **Global State:** Holds `workers`, `schedule` (`ShiftInfo[]`), and `aiProposals` (`ProposalType[]`), fetched in parallel when entering the dashboard.
- **Resizable Layout:** Implements a split-pane desktop layout with a draggable vertical resizer (`chatWidth` clamped between `300px` and `750px`) separating the left `SidebarChat` and the right `CalendarGrid`.

---

## Key Components

### 1. `AuthCard.tsx`

- Renders the login screen with email and password inputs.
- Submits credentials to `api.login()`, stores the returned `access_token` in `localStorage`, and triggers `onLogin()`.
- Displays loading states and inline error messages.

### 2. `Header.tsx`

- Sticky top navigation bar displaying the **ShiftBridge** brand, the logged-in user's avatar, name, role badge (`Manager` or `Worker`), and a logout button.

### 3. `SidebarChat.tsx`

- **Dual-Tab Interface:**
  - **Chat Sidebar** (workers only): Allows workers to chat with the ShiftBridge AI assistant (`api.sendMessage()`), auto-scrolls to new messages, auto-resizes the textarea (1–5 rows), and renders inline `ProposalCard` components when the AI generates a shift proposal.
  - **Proposals Tab**: Lists all pending proposals (`api.getProposals()`) for both workers and managers.
- **Approval Syncing:** Handles `handleApproveProposal()`—if a proposal is fully approved (`result.deleted === true`), it removes the proposal from the list and updates `schedule` in `App.tsx` with `result.new_shift`. If partially approved, it updates the proposal's approval flags in place.

### 4. `ProposalCard.tsx`

- Displays a single shift change proposal, comparing **Current** vs. **Proposed** day, start time, and length, along with any optional `note`.
- Shows manager/worker approval status and an **Approve** button if the current user's role hasn't approved yet.

### 5. `CalendarGrid.tsx`

- **7-Day Schedule Table:** Displays Monday–Sunday shifts alongside weekly total hours (`totalHours / maxHours`) with color-coded hour badges.
- **Role-Based Views:**
  - **Worker View:** Shows only the logged-in worker's personal weekly schedule.
  - **Manager View:** Shows all staff (excluding the manager) with filters for **Worker**, **Search Query** (name/role/department), and **Role** (`Senior RN`, `Charge Nurse`, `RN`, `LPN`, `Support Specialist`).
- **Shift States:** Visually distinguishes between `off`, standard roster shifts, and AI-updated shifts (`updated` / `updatedByAi`). Clicking any cell opens a bottom `ShiftDetailBar` with full shift details.

---

## API Integration (`services/api.ts`)

All backend communication is centralized in `api.ts`, targeting `http://localhost:8000`:

- **Auth (`/auth`):** `login()`, `getMe()`
- **Data (`/data`):** `getWorkers()`, `getSchedule()`, `getProposals()`, `approveProposal()`
- **Chat (`/chat`):** `sendMessage()`

Protected requests automatically attach the `Authorization: Bearer <jwt>` header using `api.getToken()`.
