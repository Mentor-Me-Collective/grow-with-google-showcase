# 🔄 Data Handoff Guide

## Biodiversity & Native Planting Planner

**Team:** Vanguard Strategists

## 1. Pipeline

```text
Raw Sources
     ↓
Raw Data
     ↓
Cleaning
     ↓
Standardization
     ↓
Integration
     ↓
Feature Engineering
     ↓
Validation
     ↓
Application Dataset
     ↓
Recommendation Engine
     ↓
Streamlit Application
     ↓
Live Deployment
```

## 2. Application Dataset

```text
data/processed/plants_app.csv
```

Contains plant information and recommendation features required by the application.

## 3. State Dataset

```text
data/processed/plant_states.csv
```

Connects plant IDs to native-state relationships.

## 4. Runtime Dependency

The application must retain these processed datasets after migration. Removing them will prevent the application from loading its data.

## 5. User Input

```text
State
Sunlight
Water
Pollinator
```

Examples:

```text
Full Sun → supports_full_sun
Low Water → supports_low_water
Bee → supports_bee_observed
```

## 6. Recommendation Flow

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
Final Recommendations
```

## 7. Validation Checklist

```text
[ ] Required files exist
[ ] Required columns exist
[ ] plant_id values are present
[ ] State relationships are valid
[ ] Recommendation fields contain expected values
[ ] Plant names are available where expected
[ ] Image URLs are valid where available
[ ] No unexpected schema changes exist
```

## 8. Deployment Handoff

The validated application and processed datasets are deployed through Streamlit.

**Live application:** https://biodiversityplanner.streamlit.app/

## 9. Handoff Principle

```text
External Sources
      ↓
Data Processing
      ↓
Validated Processed Data
      ↓
Application
      ↓
Deployment
```
