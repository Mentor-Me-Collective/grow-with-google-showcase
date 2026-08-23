# Data Dictionary — Native Plant / Pollinator Dataset

Project: Catalyst Architects — Grow with Google Capstone
Purpose: Recommend native plant species to urban gardeners to support local pollinators (SDG 15: Life on Land)

## Columns

| Column | Type | Description | Example |
|---|---|---|---|
| species_id | text | Unique ID for the row (just increment: 001, 002, ...) | 001 |
| common_name | text | Common/everyday plant name | Purple Coneflower |
| scientific_name | text | Latin binomial — use USDA PLANTS as the authority for spelling | Echinacea purpurea |
| native_range | text | State(s) or county(ies) where the species is native, scoped to your chosen region | Maryland |
| bloom_start | text | Month bloom period begins | June |
| bloom_end | text | Month bloom period ends | August |
| sun_needs | text | One of: full sun / part sun / shade | full sun |
| soil_type | text | One of: well-drained / clay / sandy / loamy | well-drained |
| moisture | text | One of: dry / medium / wet | medium |
| pollinators_supported | text | Comma-separated list, e.g. bees, butterflies, hummingbirds, moths | bees, butterflies |
| hardiness_zones | text | USDA zone range | 3-8 |
| source | text | Which database this row came from (primary source) | USDA PLANTS |
| source_url | text | Direct link to the record, for verification later | |
| notes | text | Anything you had to guess, reconcile, or flag for review | scientific name differs on BONAP, used USDA spelling |

## Standardized value lists (use these exact words so filtering works cleanly)

**sun_needs:** full sun, part sun, shade
**soil_type:** well-drained, clay, sandy, loamy
**moisture:** dry, medium, wet

## Sourcing priority
1. Pollinator Partnership regional guide — use as your starting species list (pre-vetted pollinator matches)
2. USDA PLANTS Database — confirm native status + scientific name spelling (authority for naming)
3. BONAP — confirm county-level native range (more precise than USDA's state-level data)
4. iNaturalist/GBIF — optional, to verify a species has actually been observed in your region

## Row completion rule
A row isn't "done" until it can answer all four core questions:
1. Is it native to the chosen region?
2. What growing conditions does it need?
3. When does it bloom?
4. Which pollinators does it support?

If any of the four is missing, leave a note in the `notes` column and flag it for follow-up rather than guessing.
