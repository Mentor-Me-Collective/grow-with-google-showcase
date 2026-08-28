2026-cohort/quantum-alliance-energy-optimizer/README.md
# Household Energy Efficiency Optimizer

**Team:** Quantum Alliance
**Program:** Mentor Me Collective x Grow with Google BUILD Stage — UN SDG Goal 7 (Affordable and Clean Energy)

## Problem
Apartment tenants lack clear, actionable metrics to calculate and reduce their personal energy footprint without expensive smart-meter hardware. This tool lets a user enter their housing type and appliances, then get an estimated monthly energy usage, cost, carbon footprint, and personalized recommendations — compared against typical usage for similar households.

## How It Works

```
User
  │
  ▼
Input Form (CLI / Streamlit)
  │
  ▼
SQLite Database
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
Dashboard
```

## Data Sources
- **ENERGY STAR Product Finder** — appliance wattage reference data
- **EIA RECS (Residential Energy Consumption Survey)** — housing-type benchmark averages
- **User-entered data** — household details and appliance ownership, for personalized estimates

Appliance wattages and benchmark kWh figures used in this MVP are representative reference values, not exact ENERGY STAR/EIA measurements — see `docs/SECURITY_REVIEW.md` and inline code comments for details.

## Database Schema

Normalized to 3NF across 5 tables:

- `households` — one row per user (housing type, size, electricity rate, carbon factor)
- `appliances` — reference table of appliance types and default wattage (populated once)
- `household_appliances` — junction table: what each household owns and how it's used
- `benchmarks` — reference table of average monthly kWh by housing type
- `usage_estimates` — calculated output per estimate run, timestamped for historical tracking

Full schema with constraints and design notes: `src/schema.sql`

## Setup & Usage

Requires Python 3 (no external packages needed for the core pipeline — uses the built-in `sqlite3` module).

```bash
# 1. Create the database and tables
python3 setup_db.py

# 2. Load reference data (ENERGY STAR appliances + EIA RECS benchmarks)
python3 load_reference_data.py

# 3. Run the app
python3 app.py
```

This walks you through entering your housing type, size, electricity rate, and appliances, then prints your estimated monthly usage, cost, and how you compare to similar households.

## Project Structure

```
src/
  schema.sql                — database schema (tables, constraints, indexes)
  setup_db.py                — creates the database from schema.sql
  load_reference_data.py     — loads ENERGY STAR + EIA RECS reference data
  database.py                — database connection/helper utilities
  energy_calculations.py     — kWh and cost calculation logic
  energy_efficiency.py       — efficiency score and labeling
  historical_tracking.py     — tracks estimates over time
  household_analysis.py      — main analysis pipeline, ties calculations together
  recommendations.py         — generates appliance/usage recommendations
docs/
  SECURITY_REVIEW.md         — cybersecurity review: input validation, SQL safety,
                                data handling, PII assessment, risks & mitigations
```

## Security & Privacy

No personally identifying information (name, email, address) is collected or stored — see `docs/SECURITY_REVIEW.md` for the full review, including SQL injection safety, database handling, and MVP-stage limitations.

## MVP Limitations

- Appliance wattages and benchmark values are representative estimates, not exact measurements — see reference data files for details.
- No authentication — this is a local, single-machine MVP, not a multi-user deployment.
- Carbon emission factors are user/region-configurable but default values are approximate.

## Team

Oluwaseyi Omisore · Nadya Teshome Abraha · Nora Chinyere Muoghalu · James Gitau · Sandra Ohenewaa Djan · Hemapriya Kanagala · Brian Mayora · Tolulope Fayemi 
