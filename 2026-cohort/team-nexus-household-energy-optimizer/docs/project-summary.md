# Household Energy Efficiency Optimizer: Project Summary

**Team Nexus Collaborative** | UN SDG 7: [Affordable and Clean Energy](https://www.un.org/sustainabledevelopment/energy/)

**Live site**: [tenant-power-tracker.onrender.com](https://tenant-power-tracker.onrender.com/) (Render free tier, allow about a minute for a cold start)

This summary covers research, solution, and implementation plan. Feature detail, setup instructions, and the demo and campaign videos are in the [project README](../README.md).

---

## 1. Research

**Problem.** Apartment tenants lack clear, actionable metrics to calculate and reduce their personal energy footprints without expensive hardware. Existing tools assume either appliance-level data renters don't have, or physical sensors they can't install.

**Method.** 15-minute informal interviews, July 25–28, 2026, with renters who pay their own utility bills, conducted by Sehr Abrar (UX/UI Lead). Questions covered what drives their bill, whether they'd tried to cut usage before, what would make an energy "score" trustworthy, and how they'd prefer to enter usage data. Full notes and the five resulting personas are in [user-research.md](./user-research.md).

**Findings.**

- **Nobody tracks appliance hours.** No interviewee could estimate daily AC, laundry, or entertainment hours. Manual kWh entry is a non-starter; lifestyle-style questions are answerable.
- **Score trust depends on explanation**, not the number alone.
- **Motivation splits into two currencies**, money and environmental impact. The product has to speak to both without making users pick a mode.
- **Effort tolerance is low.** Convenience beats precision for this audience.
- **Shared and family living complicates attribution.** Usage isn't wholly "mine," so the tool has to work off personal habits rather than assumed full control.

---

## 2. Solution

A web app where tenants set appliance usage with sliders to get a **Personalized Energy Score (1–100)**, explore what-if savings scenarios, and receive targeted tips, all benchmarked against real EIA.gov appliance data instead of live hardware readings.

Each finding maps to a shipped decision:

| Finding | Design decision |
|---|---|
| Nobody tracks appliance hours | Per-appliance sliders for 11 appliances, not manual kWh entry |
| Trust needs explanation | Score breakdown shown beside the score itself |
| Two competing motivations | Tips carry both cost and carbon framing |
| Low effort tolerance | Top 3 "energy hog" detection instead of category-by-category review |
| Shared living complicates attribution | Baselines framed around personal habits, not full-household control |

---

## 3. Implementation Plan

**Stack.** React + TypeScript (Vite) frontend, Flask backend, both deployed on Render. The core kWh, cost, and carbon math is written once in TypeScript and mirrored in Python, so `/api/simulate` returns the same numbers the UI computes. System diagram and the client-side vs. server-side split are in [architecture.md](./architecture.md).

**Data.** 11 appliances with wattage and default daily hours cleaned from EIA.gov (`data/eia_appliances.csv`), 3 synthetic baseline profiles modeled on typical usage by home size, and a 15-region table of electricity rates and carbon intensity. Methodology, and what changed between the original draft and the shipped schema, is in [data-sources.md](./data-sources.md).

**Ownership.** Four disciplines, one per Scholar. Ashenafi Mekonnen Demssie (Cybersecurity) ran the dependency audit, input validation review, and security CI. Peace Kahunde (Data Analytics) handled dataset cleaning, baseline profiles, and the calculation functions. Priscilla Gyepi-Garbrah (Digital Marketing) owned launch messaging and produced two video commercials. Sehr Abrar (UX Design and Full-Stack) ran the user research and built the input flow, layout, integration, and deployment. Contacts are in the [README](../README.md).

**Timeline.** Kickoff slipped to July 25, compressing the build into roughly three weeks: scope and dataset cleaning (Jul 25–27), usage simulator and score logic (Jul 28–31), savings visualizer, tips, UI polish and security review (Aug 1–7), deployment, documentation and campaign videos (Aug 8–11), final testing and submission (Aug 12–14).

**Risks and mitigations.**

| Risk | Mitigation |
|---|---|
| Roughly three weeks for a cross-functional MVP | Scoped hard to an MVP checklist; the campaign was held to two commercials rather than a multi-channel launch |
| Render cold starts can read as a broken site during grading | Documented in the README; the recorded walkthrough doesn't depend on a live load |
| Synthetic baseline profiles may not generalize to every household | Underlying appliance figures grounded in EIA.gov; framing validated against real renter interviews |
| Known CVEs in backend dependencies | Patched via `pip-audit`, with a CI check guarding against regressions ([security-audit-2026-08.md](./security-audit-2026-08.md)) |
| No accounts or persistent storage | Intentionally out of MVP scope, documented as a future idea rather than a silent gap |

**Status.** As of August 11, 2026 the project is complete. Every MVP checklist item is done, the frontend runs on live backend data rather than mocks, dependencies are audited and patched, and the 3:30 demo walkthrough and two campaign commercials are linked in the README.  

**Grow with Google resources used.** Applied Digital Skills; Google Cybersecurity, Data Analytics, Digital Marketing, and UX Design Professional Certificates.
