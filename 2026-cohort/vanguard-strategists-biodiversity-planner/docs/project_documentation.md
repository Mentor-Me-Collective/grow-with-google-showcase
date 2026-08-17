# 🌱 Biodiversity & Native Planting Planner
## Project Documentation

**Team:** Vanguard Strategists  
**Program:** Grow with Google BUILD Stage  
**UN SDG:** Goal 15 — Life on Land  
**Live Application:** [https://biodiversityplanner.streamlit.app/](https://biodiversityplanner.streamlit.app/)

## 1. Project Background

Urban gardening can provide opportunities to support biodiversity, but selecting suitable native plants can be difficult because information about native distribution, growing requirements, taxonomy, and pollinator relationships is distributed across multiple sources.

The project combines these sources into structured datasets and presents the information through an interactive recommendation application.

## 2. Problem Statement

Urban gardeners lack simple, automated tools that help them identify native plant species suitable for their local gardening conditions while supporting local pollinator populations.

## 3. Project Goal

Provide a simple, practical tool that helps users discover native plants based on location and gardening conditions.

## 4. Objectives

1. Collect relevant plant and ecological data.
2. Clean and standardize information from multiple sources.
3. Integrate plant, distribution, taxonomy, and pollinator information.
4. Engineer application-ready recommendation features.
5. Validate processed datasets.
6. Build a deterministic recommendation engine.
7. Develop an interactive web application.
8. Refine UI/UX for desktop and mobile.
9. Deploy the application for public demonstration.
10. Support UN SDG 15.

## 5. User Flow

```text
State → Sunlight → Water → Preferred Pollinator → Recommendations
```

## 6. Recommendation Logic

A plant is considered a match when it satisfies the selected state, sunlight, water, and pollinator criteria.

## 7. UI/UX Contribution

UI/UX refinement focused on information hierarchy, user flow, compact results, readability, responsive behavior, mobile usability, and reducing unnecessary vertical scrolling.

## 8. Team Contributions

### Ayotomiwa Omojola — Data Analytics & UI/UX Design
Data sourcing, cleaning, standardization, integration, feature engineering, validation, application-ready datasets, UI/UX design, user-flow refinement, information hierarchy, and responsive interface considerations.

### Hanan Kassim — Advanced Data Analytics
Data analysis, dataset validation, analytical review, and data quality support.

### Adrian Denis — IT Automation & Application Development
Recommendation engine, Python/Streamlit application development, application logic, user-input filtering, data-to-interface integration, and deployment.

### Favour Asomba — Cybersecurity
Security considerations, input validation review, repository security, and deployment/security review.

## 9. Data Processing

The workflow includes source collection, cleaning, standardization, taxonomy resolution, dataset integration, pollinator aggregation, feature engineering, and validation.

## 10. Application Datasets

The application depends on:

```text
data/processed/plants_app.csv
data/processed/plant_states.csv
```

These files must remain available at runtime.

## 11. Deployment

The application is deployed using Streamlit.

**Live application:** [https://biodiversityplanner.streamlit.app/](https://biodiversityplanner.streamlit.app/)

## 12. Current Status

The main data pipeline, recommendation application, UI/UX refinement, and deployment have been completed.

## 13. Limitations

- U.S. state-level geographic scope.
- Some plant records may be incomplete.
- Image availability is not universal.
- Recommendations are deterministic rather than ranked.
- Results depend on underlying data quality.

## 14. Future Improvements

- Recommendation ranking
- Interactive maps
- County-level recommendations
- Seasonal planting guidance
- Expanded pollinator coverage
- Expanded geographic coverage
- Biodiversity impact indicators
- Advanced plant search

## 15. SDG 15 Alignment

The project supports **UN SDG 15 — Life on Land** by making native-plant information more accessible and encouraging biodiversity-conscious planting decisions.
