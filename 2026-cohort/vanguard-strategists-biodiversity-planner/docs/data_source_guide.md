# 📊 Data Source Guide

## Biodiversity & Native Planting Planner

**Team:** Vanguard Strategists

## 1. Source Overview

| Source | Primary Purpose |
|---|---|
| Missouri Botanical Garden | Native plant distribution |
| Lady Bird Johnson Wildflower Center | Plant and gardening characteristics |
| USDA PLANTS Database | Botanical taxonomy |
| Pollinator Interaction Dataset | Pollinator observations |
| iNaturalist API | Plant images |

## 2. Missouri Botanical Garden

Contributes plant distribution and native-status relationships represented through `plant_id` and `native_state`.

## 3. Lady Bird Johnson Wildflower Center

Contributes gardening characteristics including sunlight, water, soil, moisture, pH, maintenance, bloom characteristics, and plant type.

## 4. USDA PLANTS Database

Supports botanical taxonomy and standardized plant identification.

## 5. Pollinator Interaction Dataset

Provides observed relationships between plants and pollinator groups.

Application fields include:

```text
supports_bee_observed
supports_butterfly_observed
supports_hummingbird_observed
supports_moth_observed
supports_fly_observed
supports_beetle_observed
supports_wasp_observed
```

## 6. iNaturalist

Used for plant image sourcing. Current project documentation records **894 out of 997 species (89.7%)** with image coverage.

## 7. Data Integration

```text
Native Distribution
        +
Gardening Characteristics
        +
Taxonomy
        +
Pollinator Data
        +
Image Metadata
        ↓
Integrated Plant Dataset
```

## 8. Data Quality

The project considers completeness, consistency, validity, uniqueness, referential integrity, and image availability.

## 9. Attribution

The project acknowledges the organizations and contributors whose public data and resources support this educational project. Applicable source licensing and attribution requirements should be followed.
