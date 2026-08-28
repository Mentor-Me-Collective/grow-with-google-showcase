# Household Energy Efficiency Optimizer — Project Summary

**Team:** Quantum Alliance
**UN SDG Goal:** Goal 7 — Affordable and Clean Energy
**Program:** Mentor Me Collective × Grow with Google BUILD Stage

---

## 1. Research & Problem Grounding

### Problem Statement

Apartment tenants lack clear, actionable metrics to calculate and reduce their personal energy footprint without expensive hardware. Unlike homeowners, renters typically cannot install smart meters, solar panels, or whole-home energy monitors and utility bills give them a single monthly total with no breakdown of which appliances or habits are driving that cost. This leaves tenants unable to make informed, low-cost decisions about where to cut usage.

### Why This Matters (SDG 7 Alignment)

Goal 7 calls for affordable, reliable, and sustainable energy for all. A significant and growing share of the U.S. population rents rather than owns, and rental housing is systematically underserved by existing energy-efficiency tools, most of which assume homeownership (e.g., recommending insulation upgrades or appliance replacement, which tenants cannot act on). A tool that works within a tenant's  constraints- no hardware, no ownership of the appliances, no ability to renovate closes a  gap in who gets to participate in energy efficiency.

### Data Sources

The project grounds its estimates in reference data drawn from:

- **ENERGY STAR Product Finder** — typical appliance wattage and efficiency ratings, used to estimate power draw per appliance type.
- **EIA RECS (Residential Energy Consumption Survey)** — used to derive approximate average monthly household electricity consumption by housing type (studio, apartment, condo, multi-family), giving each user a benchmark to compare against.
- **User-entered data** — housing type, appliance ownership, and usage patterns, collected directly from the tenant to personalize the estimate.

For this MVP, appliance wattage and benchmark figures are representative reference values rather than exact per-model ENERGY STAR/EIA measurements — a deliberate scope decision to prioritize a working, testable pipeline within the project timeline. This is documented transparently in the codebase (`load_reference_data.py`, `README.md`) rather than presented as more precise than it is.

---

## 2. Solution Summary

### What We Built

A working, end-to-end application that lets a tenant:

1. Enter their housing type and size
2. Add each appliance they own, with quantity and daily usage hours
3. Receive an estimated **monthly energy usage (kWh)**, **cost (USD)**, and **carbon footprint (kg CO2e)**
4. See how their usage compares to a benchmark for similar households
5. Get an **efficiency score and label**, plus **rule-based, explainable recommendations** (e.g., flagging appliances responsible for a large share of usage, or unusually long daily usage hours)
6. Save estimates over time to track progress

### Architecture

```
User
  │
  ▼
Input Form (Streamlit dashboard)
  │
  ▼
SQLite Database (5 tables, normalized to 3NF)
  │
  ▼
Python Analytics Pipeline
  ├── Energy Calculation
  ├── Cost Calculation
  ├── Carbon Calculation
  ├── Energy Efficiency Score
  └── Recommendations
  │
  ▼
Streamlit Dashboard
```

### Key Design Decisions

- **Normalized SQL schema (3NF):** appliance specs and housing-type benchmarks live in their own reference tables, populated once, rather than being duplicated per household. This keeps the database consistent and makes it easy to update reference data without touching user records.
- **Optional fields with safe defaults:** electricity rate and carbon emission factor are optional at the database level (not every tenant knows their exact rate), with fallback default values applied in the analytics layer so the app never crashes on missing input while still using the tenant's own figures whenever provided.
- **Historical tracking:** each estimate is saved with a timestamp, so a tenant can track whether their usage is trending up or down over time, not just see a single snapshot.
- **Rule-based, explainable recommendations:** rather than a black-box model, the recommendation engine uses transparent thresholds (e.g., "flag any appliance responsible for ≥20% of total usage") so a tenant can understand *why* a suggestion was made.

### Sustainability & Practicality

The solution requires no hardware purchase, no landlord permission, and no technical expertise beyond answering simple form questions directly matching the constraint tenants actually face. It runs entirely on free, open tools (Python, SQLite, Streamlit), so it has no ongoing cost to operate or scale.

---

## 3. Implementation Plan

### Steps Taken

| Phase | Work |
|---|---|
| 1. Data Dictionary | Defined and iterated on the full set of fields, types, sources, and units needed, incorporating team review feedback (added cost/carbon/quantity/timestamp fields; scoped out a stretch-goal field) |
| 2. SQL Schema Design | Designed a normalized (3NF) schema with primary/foreign keys, constraints, and indexes |
| 3. Database & Reference Data | Built the SQLite database and loaded ENERGY STAR/EIA-derived reference data |
| 4. Python Analytics Pipeline | Built the energy/cost/carbon calculation engine, efficiency scoring, and recommendation logic |
| 5. Integration Testing | Ran the full pipeline end-to-end with real function calls (not just code review) to catch integration bugs before they reached users |
| 6. Dashboard | Built a Streamlit interface exposing the full workflow: household input → appliance entry → analysis → recommendations → historical tracking |
| 7. Security Review | Reviewed input validation, SQL query safety, database/secrets handling, and confirmed no unnecessary personal data is collected |
| 8. Bug Fixes | Identified and fixed a crash affecting tenants who leave electricity rate/carbon factor blank, and a dashboard crash on a deprecated Streamlit API call |

### Timeline

The team worked from the BUILD stage kickoff through the submission deadline. The SQL schema and Python analytics development ran concurrently with defined checkpoints to confirm the pieces integrated correctly.

### Resources Used

- **Team:** cross-functional cohort spanning Data Analytics, Cybersecurity, and IT Automation tracks
- **Tools:** Python 3, SQLite, Streamlit, GitHub (fork + pull request workflow)
- **Data:** ENERGY STAR and EIA RECS as reference sources

### Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Crash for tenants who skip optional fields (electricity rate, carbon factor) | Added fallback default values in the analytics layer; confirmed via direct testing |
| SQL injection | All queries use parameterized statements throughout; verified in code review |
| Committing sensitive/generated files (e.g., local database) to version control | Added `.gitignore` rules; removed a previously-committed database file |
| Reference data precision | Documented transparently as representative MVP values rather than exact measurements, so the limitation is visible rather than hidden |
| Compressed timeline / parallel work causing integration mismatches | Ran actual end-to-end tests (not just code review) against the real database and dashboard before finalizing, catching two real bugs before submission |
| No authentication (anyone can view any household record) | Acceptable for a local MVP demo; documented as a known limitation for any future multi-user deployment |

### MVP Limitations (Known & Documented)

- No authentication/authorization — appropriate for a local demo, not a multi-user production deployment
- No encryption at rest for the local database, acceptable given no personally identifying information is stored
- Reference data (wattages, benchmarks) are representative estimates, not exact per-model or per-region figures
- This is a manual code review process, not an automated security scan
