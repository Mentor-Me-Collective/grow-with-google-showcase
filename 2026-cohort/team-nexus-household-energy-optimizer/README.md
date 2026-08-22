# Household Energy Efficiency Optimizer

## Team Nexus Collaborative
***UN SDG 7**: [Affordable and Clean Energy](https://www.un.org/sustainabledevelopment/energy/)*  
***Project Topic**: Household Energy Efficiency Optimizer*

**Live Site**: [tenant-power-tracker.onrender.com](https://tenant-power-tracker.onrender.com/) (if the page looks stuck loading, give it about a minute to spin back up)

---

## Table of Contents
| | |
|---|---|
| [1. Problem Statement](#1-problem-statement) | [2. Proposed Solution](#2-proposed-solution) |
| [3. MVP Feature Checklist](#3-mvp-feature-checklist) | [4. Grow with Google Resources Used](#4-grow-with-google-resources-used) |
| [5. Tech Stack](#5-tech-stack) | [6. Project Structure](#6-project-structure) |
| [7. Setup / Run Instructions](#7-setup--run-instructions) | [8. Project Timeline](#8-project-timeline) |
| [9. Risks & Mitigations](#9-risks--mitigations) | [10. Security Considerations](#10-security-considerations) |
| [11. Future Ideas](#11-future-ideas) | [12. Team Members](#12-team-members) |
| [13. Demo](#13-demo) | [14. License](#14-license) |

---

## 1. Problem Statement

Apartment tenants lack clear, actionable metrics to calculate and reduce their personal energy footprints without expensive hardware.

---

## 2. Proposed Solution

A web app where tenants input basic appliance usage or sample bill data to get a **Personalized Energy Score**, explore "What-If" savings scenarios via sliders, and receive automated, personalized tips, all benchmarked against real-world EIA.gov data instead of live hardware readings.

---

## 3. MVP Feature Checklist

**Phase 1: Data & Baseline Logic**
- [x] Cleaned EIA.gov appliance dataset (CSV/JSON) - `data/eia_appliances.csv`, served via `/api/appliances` and `/api/simulator/appliances`
- [x] 3–5 synthetic tenant baseline profiles modeled on typical usage by home size - `data/tenant_profiles.json` (1-Bed / 2-Bed / 3-Bed), served via `/api/simulator/baseline-profiles`
- [x] Core calculation functions: kWh, cost, carbon footprint - implemented in `frontend/src/lib/calculations.ts` (drives the live simulator) with a matching Python port in `backend/calculations.py` (served via `/api/simulate` for parity)

**Phase 2: Core App Features**
- [x] Usage Simulator: per-appliance sliders for 11 built-in appliances (fridge, AC, washer, TV, and more), plus the ability to add custom appliances
- [x] Savings Visualizer: bar chart, default usage vs. your scenario
- [x] Personalized Energy Score (1–100) vs. regional baseline
- [x] Top 3 "energy hog" detection with tailored tips

**Phase 3: Integration & Polish**
- [x] Basic cohesive UI (color palette, typography, metric cards)
- [x] Edge-case handling: 0 hrs / 24 hrs input doesn't crash or return negative numbers
- [x] README.md with install steps + requirements.txt
- [x] Security Considerations section

**Phase 4: Deployment**
- [x] Live public URL: Deployed on Render: [tenant-power-tracker.onrender.com](https://tenant-power-tracker.onrender.com/)
- [x] Risks & mitigations
- [x] Digital marketing campaign: strategy, target persona, and two video commercials, see [marketing-campaign.md](docs/marketing-campaign.md)
- [x] Demo video, see [Demo](#13-demo)

---

## 4. Grow with Google Resources Used

- Applied Digital Skills
- Google Cybersecurity Professional Certificate
- Google Data Analytics Professional Certificate
- Google Digital Marketing Professional Certificate
- Google UX Design Professional Certificate

---

## 5. Tech Stack

- **Frontend**: React + TypeScript (Vite), plain CSS with a shared color/typography system, [lucide-react](https://lucide.dev/) for icons
- **Backend**: Python + Flask
- **Data Sources**: [EIA.gov](https://www.eia.gov/) (appliance benchmarks); tenant baseline profiles are synthetic, modeled on typical usage by home size
- **Deployment**: Render (backend web service + frontend static site)
- **Tooling**: Git + GitHub for version control

---

## 6. Project Structure

```bash
team-nexus-household-energy-optimizer/
├── backend/          # Flask API: app.py, data.py, calculations.py, requirements.txt
├── data/             # Appliance, tenant-profile, and region datasets (CSV/JSON)
├── docs/             # written summary (PDF + markdown source), research, data, architecture, and security docs
├── frontend/         # React + TypeScript app (Vite): src/pages, src/components, src/lib
├── .gitignore        # Ignored files (env, deps, build output, etc.)
├── LICENSE           # MIT License
└── README.md         # Project overview and documentation
```

**Docs index:**

- **[project-summary.pdf](docs/project-summary.pdf)**: the 3-page written summary of research, solution, and implementation plan (markdown source: [project-summary.md](docs/project-summary.md))
- [user-research.md](docs/user-research.md): interview notes, key findings, and the five personas
- [marketing-campaign.md](docs/marketing-campaign.md): campaign strategy, goals and KPIs, target persona, and creative assets
- [design-system.md](docs/design-system.md): UI spec, color tokens, theming, text sizing, and accessibility
- [data-sources.md](docs/data-sources.md): dataset methodology and what changed from the original draft
- [architecture.md](docs/architecture.md): system diagram and the client-side vs. server-side split
- [security-audit-2026-08.md](docs/security-audit-2026-08.md): dependency vulnerability findings

---

## 7. Setup / Run Instructions

New to running a project locally? Here's what to install first:

- **[Python 3.9+](https://www.python.org/downloads/)**, needed to run the Flask backend
- **[Node.js 18+](https://nodejs.org/)** (npm comes bundled with it), needed to run the React frontend
- **[Git](https://git-scm.com/downloads)**, needed to clone this repository, if you haven't already

Once those are installed, open a terminal and clone the repo (skip this step if you already have the project folder):

```bash
git clone https://github.com/Mentor-Me-Collective/grow-with-google-showcase.git   # download the project files to your computer
cd grow-with-google-showcase/2026-cohort/team-nexus-household-energy-optimizer   # move into this project's folder
```

The backend and frontend run as two separate servers, so you'll want two terminal tabs/windows open at the same time, one for each set of steps below.

### Backend (Flask)

```bash
cd backend                          # move into the backend folder
python3 -m venv venv                # create an isolated Python environment for this project
source venv/bin/activate            # activate it (Windows: venv\Scripts\activate)
pip install -r requirements.txt     # install the Python packages the backend needs
cp .env.example .env                # copy the environment variable template to a real .env file
python app.py                       # start the Flask server
```

The API will run at `http://127.0.0.1:5050/api/health` (the root `/` just returns a small pointer message, no actual UI lives there).

### Frontend (React + TypeScript)

```bash
cd frontend         # move into the frontend folder (in your second terminal tab/window)
npm install          # download the JavaScript packages the frontend needs
cp .env.example .env # points the frontend at the backend above (VITE_API_URL)
npm run dev          # start the local development server
```

Vite will print a local URL in the terminal (typically `http://localhost:5173`), open it in your browser to view the app. The frontend fetches its appliance, baseline profile, and region data live from the backend started above, so both servers need to be running.

---

## 8. Project Timeline

**Submission Deadline: August 14, 2026**

Kickoff slipped to July 25, so the roadmap below is compressed.

| Phase | Timeline | Focus |
| ------ | -------- | ----- |
| Days 1–3 | July 25 – July 27 | Confirm MVP scope + tech stack, assign owners, start dataset cleaning & calc functions |
| Days 4–7 | July 28 – July 31 | Usage simulator + score logic in parallel |
| Days 8–14 | August 1 – August 7 | Simulator, savings visualizer, top-3 tips complete; UI polish & security review begin |
| Days 15–18 | August 8 – August 11 | Deployment, README finalized, two video commercials produced |
| Days 19–21 | August 12 – August 14 | Final testing, demo/pitch prep, submission |
| Post-submission | Launch – Launch + 90 days | Campaign execution: an educational email nurture sequence targeting 250 sign-ups at a 25% open rate and 5% CTR, plus the two commercials as organic social content (Instagram/TikTok/LinkedIn) targeting a 35% engagement lift and 300 qualified visits. Detail in [marketing-campaign.md](docs/marketing-campaign.md) |

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Compressed timeline (kickoff slipped to July 25, ~3 weeks for a cross-functional MVP) | Less room for polish or scope creep before the Aug 14 deadline | Scoped hard to an MVP checklist; stretch goals (ongoing campaign distribution) explicitly deprioritized behind core functionality. The campaign itself was scoped to two short-form commercials rather than a multi-channel launch, which kept it deliverable inside the window |
| Render free-tier cold starts | The live site can take up to a minute to respond after idling, which could read as broken during a live demo or grading pass | Documented clearly in the README and Demo section; recorded walkthrough video avoids relying on a cold live load |
| Synthetic, hand-modeled tenant baseline profiles (not a large real-world usage dataset) | Baseline comparisons may not generalize to every household | Grounded the underlying appliance data in EIA.gov figures (methodology in [data-sources.md](docs/data-sources.md)); validated framing (sliders over manual entry, dual cost/impact messaging) against real renter interviews, see [user-research.md](docs/user-research.md) |
| Vulnerable backend dependencies | Known CVEs in outdated packages | Audited with `pip-audit` and patched (Flask, flask-cors, python-dotenv bumped); added a CI security-check workflow to catch regressions |
| No account system or persistent storage | Can't support cross-session features like progress tracking (see Future Ideas) | Intentionally out of MVP scope; flagged as a documented future idea rather than a silent gap |

---

## 10. Security Considerations

- **No accounts, no persistent storage.** There's no login and nothing about a tenant's usage is stored server-side or in a database; the app is entirely session-based on the client.
- **Input validation, client and server side.** Hours-per-day values are clamped against min/max/NaN/negative input in both the frontend (`UsageSimulator.tsx`) and the backend (`clamp_hours` in `backend/calculations.py`), so malformed input can't crash the API or produce negative energy/cost figures. Wattage (1–10,000W) and quantity (1–20) are similarly clamped in the UI.
- **Unknown region/baseline IDs are rejected, not silently ignored.** `/api/simulate` returns a 400 for an unrecognized `region_id` or `baseline_id` instead of falling back quietly, so bad input surfaces as an error rather than a wrong answer.
- **CORS is intentionally open.** `CORS(app)` allows all origins, since this is a public, read-mostly API with no authenticated or user-specific data behind it; there's nothing sensitive a stricter policy would be protecting.
- **Dependency vulnerabilities audited and patched.** Scanned with `pip-audit`, 7 known CVEs found and fixed across Flask, flask-cors, and python-dotenv, full findings in [security-audit-2026-08.md](docs/security-audit-2026-08.md).
- **No secrets committed.** Real `.env` files are excluded via `.gitignore`; only `.env.example` placeholders are checked in. A `gitleaks` secret scan and `pip-audit` dependency check both run automatically in CI (`.github/workflows/security-check.yml`) on pushes and pull requests.

---

## 11. Future Ideas

- **Progress Tracking Over Time:** Save a user's score and scenarios across sessions and chart them on a trend line, not just a single snapshot. Eco-conscious and family personas specifically asked to see whether their habits are "working" over time, not just a one-off score.
- **Utility Bill Upload/OCR Parsing:** Let tenants upload a photo or PDF of an actual bill to auto-extract usage instead of relying only on sliders, closing the gap between the "sample bill data" idea in the problem statement and what's implemented today.
- **Multi-User/Household Accounts:** Research surfaced that students and families rarely control 100% of a household's usage. A shared household mode (e.g., splitting a score or bill across roommates) would address that attribution problem more directly than personal-habit framing alone.
- **Utility/Rebate Integration:** Surface region-specific utility rebate programs, time-of-use pricing, or renewable-energy plan options alongside the tips, so recommendations tie into real savings opportunities and not just generic advice.
- **Lightweight Gamification:** Badges or streaks for sustained improvement, plus an opt-in anonymous comparison against similar households in the same region, to reinforce the "trust the score" motivation without requiring account-heavy infrastructure.

---

## 12. Team Members

| Name | Role | Contact | MVP Responsibility |
|------|------|---------|---------------------|
| [Ashenafi Mekonnen Demssie](https://www.linkedin.com/in/ashenafi-mekonnen-demssie/)| Cybersecurity Lead | ashenafimekonnen600@gmail.com | Dependency vulnerability audit (pip-audit), secret-scan review, automated security CI via GitHub Actions, security audit documentation |
| [Peace Kahunde](https://www.linkedin.com/in/pkahunde) | Data Lead | peacek301@gmail.com | Dataset cleaning, baseline profiles, calculation functions |
| [Priscilla Gyepi-Garbrah](https://www.linkedin.com/in/priscilla-gyepi-garbrah-5190031ab/) | Digital Marketing Lead | gyepigarbrahpriscilla@gmail.com | Launch messaging and campaign strategy; scripted and created the two video commercials |
| [Sehr Abrar](https://www.linkedin.com/in/sehr-abrar/) | UX/UI Lead & Full-Stack/Integration | sehr.abrar1@gmail.com | Input flow, sliders/forms, layout, score feedback design; app structure, connecting calc logic to UI, deployment |

---

## 13. Demo

**Live App**: [tenant-power-tracker.onrender.com](https://tenant-power-tracker.onrender.com/)

> Hosted on Render's free tier, which spins down after inactivity, the first load after a period of idle time can take up to a minute while the server wakes back up. Subsequent loads are fast.

### Walkthrough

- **[Watch the demo walkthrough →](https://youtu.be/B45X0HwYUBw)**

### Marketing Campaign

Two short-form video commercials aimed at apartment tenants, both built on the same pitch: your energy usage is something you can see and keep track of, without buying any hardware.

- **[Commercial 1 →](https://drive.google.com/file/d/1Ocg_sx7XFVKKbQ6syr7kK6Z2tyGS-al6/view?usp=drive_link)**
- **[Commercial 2 →](https://drive.google.com/file/d/1_nsnz1r29N_yqFIGtG11OMvgQ4X0HxZH/view?usp=drive_link)**

The commercials are the lead creative for a wider campaign covering email and organic social, with a target persona, channel goals, and tracked KPIs. Full strategy in **[marketing-campaign.md](docs/marketing-campaign.md)** ([source document](https://docs.google.com/document/d/13jdbKRCzv_RQ6gSE9ZFAelCqxq3D7awzZk7DIsjNT7w/edit?tab=t.0)).

---

## 14. License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
