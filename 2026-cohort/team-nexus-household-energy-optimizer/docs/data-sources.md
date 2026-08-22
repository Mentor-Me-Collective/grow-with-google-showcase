# Data Sources & Methodology

How each dataset in `data/` was built, and what changed between Peace's original drafts and what's shipped. Written mainly so the assumptions behind the numbers aren't lost, since a couple of them (usage frequency, cost) didn't carry over into the final CSV schema.

---

## Appliance Dataset (`data/eia_appliances.csv`)

Wattage and typical daily-usage figures for 11 common household appliances, adapted from EIA.gov-style residential appliance energy benchmarks and compiled by Peace (Data Lead).

### Original draft

Peace's first pass included per-appliance monthly kWh/cost estimates and a `Notes` column explaining the usage assumption behind each `Hours_Per_Day` figure:

| Appliance | Watts | Hours/Day | Monthly kWh | Monthly Cost | Notes |
|---|---|---|---|---|---|
| Refrigerator | 150 | 24 | 108 | $12.96 | Runs 24/7 |
| Air Conditioner | 1200 | 4 | 144 | $17.28 | Average 4hrs/day |
| Television | 120 | 4 | 14.4 | $1.73 | Average 3hrs/day |
| Laptop | 60 | 4 | 7.2 | $0.86 | Average 4hrs/day |
| Washing Machine | 500 | 1 | 15 | $1.80 | 3 loads per week |
| Clothes Dryer | 3000 | 1 | 90 | $10.80 | 2 loads per week |
| Gaming Console | 160 | 2 | 9.6 | $1.15 | Average 2hrs/day |
| LED Lights | 10 | 5 | 1.5 | $0.18 | Per bulb, 4–6 bulbs per home |
| Microwave | 1000 | 0.25 | 7.5 | $0.90 | 15min/day |
| Dishwasher | 1200 | 1 | 36 | $4.32 | Once per day |
| Router | 10 | 24 | 7.2 | $0.86 | Runs 24/7 |

### What changed for the shipped version

The `Watts` and `Hours_Per_Day` values above carried over **unchanged** into `data/eia_appliances.csv`, every figure matches exactly. What differs:

- **Columns renamed**: `Watts` → `Avg_Watts`, `Hours_Per_Day` → `Default_Hours_Per_Day`, to match what `backend/calculations.py` and `backend/data.py` key off of.
- **`Category` added** (Kitchen, HVAC, Laundry, Entertainment, Office, Lighting), wasn't in Peace's draft; added so the simulator can group appliances, color-code them, and pick relevant tips.
- **`Monthly_kWh` / `Monthly_Cost` dropped, not lost**: these were computed at a single implied electricity rate. The shipped app is region-aware (`data/regions.json`, 15 regions with different `rate_per_kwh`), so a hardcoded cost column would be wrong for 14 of the 15 regions. Cost and kWh are now computed live per region instead of stored statically.
- **`Notes` dropped from the CSV, preserved above**: not used anywhere in code, but this is the context for *why* each default-hours number is what it is (e.g., the washing machine's `1 hr/day` default represents "3 loads per week" divided out, not a literal daily habit). Kept here so that reasoning isn't lost.

---

## Tenant Baseline Profiles (`data/tenant_profiles.json`)

Three synthetic profiles (1-Bed / 2-Bed / 3-Bed) giving typical per-appliance hours for each home size, used as the comparison baseline for the Personalized Energy Score.

**These are hand-modeled, not derived from an external dataset.** The profiles were built by reasoning from the appliance dataset above (e.g., a 3-Bed House gets a clothes dryer and gaming console a 1-Bed Apartment doesn't, and a higher AC default hours to reflect more square footage) rather than sourced from an external usage dataset.

---

## Regional Rate & Carbon Table (`data/regions.json`)

Electricity rate (`rate_per_kwh`) and carbon intensity (`carbon_lbs_per_kwh`) across 15 regions (6 US regions plus 9 countries), used to make the simulator's cost/carbon math region-aware instead of US-only.

These are approximate, team-compiled figures reflecting each region's general rate and grid mix (e.g., hydro-heavy regions like Norway and the Pacific Northwest carry a low carbon factor; coal-heavy regions like South Africa and the Midwest carry a high one) rather than pulled from a single cited dataset. Treat them as directionally representative, not as an authoritative utility-rate feed.
