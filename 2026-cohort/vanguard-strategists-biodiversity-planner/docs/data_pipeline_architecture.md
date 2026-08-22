# 🏗️ Data Pipeline Architecture

## Biodiversity & Native Planting Planner

**Team:** Vanguard Strategists  
**Program:** Grow with Google BUILD Stage  
**SDG:** Goal 15 — Life on Land

## 1. High-Level Architecture

```text
┌─────────────────────────────┐
│      External Sources       │
├─────────────────────────────┤
│ Missouri Botanical Garden   │
│ Lady Bird Johnson WFC       │
│ USDA PLANTS Database        │
│ Pollinator Dataset          │
│ iNaturalist API             │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       Raw Data Layer        │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│      Cleaning Layer         │
├─────────────────────────────┤
│ Duplicate Removal           │
│ Missing-Value Handling      │
│ Name Standardization        │
│ Type Conversion             │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│   Integration & Processing  │
├─────────────────────────────┤
│ Taxonomy Resolution         │
│ Dataset Integration         │
│ State Relationships         │
│ Pollinator Aggregation      │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│    Feature Engineering      │
├─────────────────────────────┤
│ Sunlight Features           │
│ Water Features              │
│ Pollinator Features         │
│ Bloom Features              │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│      Data Validation        │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│      Processed Data         │
├─────────────────────────────┤
│ plants_master.csv           │
│ plants_app.csv              │
│ plant_states.csv            │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│    Recommendation Engine    │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│    Streamlit Application    │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│      Live Deployment        │
└─────────────────────────────┘
```

## 2. Feature Engineering

### Sunlight

```text
supports_full_sun
supports_part_shade
supports_shade
```

### Water

```text
supports_low_water
supports_medium_water
supports_high_water
```

### Pollinators

```text
supports_bee_observed
supports_butterfly_observed
supports_hummingbird_observed
supports_moth_observed
supports_fly_observed
supports_beetle_observed
supports_wasp_observed
```

## 3. Validation

Processed data is reviewed for completeness, consistency, validity, uniqueness, relationship integrity, and expected field types.

## 4. Processed Data Layer

The application relies primarily on:

```text
data/processed/plants_app.csv
data/processed/plant_states.csv
```

The broader development workflow also produces `plants_master.csv` and a data-quality report.

## 5. Recommendation Layer

```text
Selected State
      ↓
Native Plant IDs
      ↓
Sunlight Match
      ↓
Water Match
      ↓
Pollinator Match
      ↓
Recommendations
```

## 6. Presentation Layer

The Streamlit application handles:

- User input
- Dataset loading
- Recommendation filtering
- Plant results
- Plant details
- Image display
- Empty-result handling
- Responsive presentation

## 7. Deployment

The completed application is deployed through Streamlit.

**Live application:** https://biodiversityplanner.streamlit.app/

## 8. Architecture Principle

```text
Data Layer
    ↓
Validated Dataset
    ↓
Recommendation Layer
    ↓
Presentation Layer
    ↓
Deployment
```

## 9. Future Architecture

```text
Scheduled Data Collection
          ↓
Automated Cleaning
          ↓
Automated Integration
          ↓
Automated Validation
          ↓
Dataset Versioning
          ↓
Application Update
```
