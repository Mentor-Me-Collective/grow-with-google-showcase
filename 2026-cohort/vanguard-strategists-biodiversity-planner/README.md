# 🌱 Biodiversity & Native Planting Planner

### UN Sustainable Development Goal 15 — Life on Land

**Team:** Vanguard Strategists  
**Program:** Grow with Google BUILD Stage  
**Project Topic:** Biodiversity & Native Planting Planner

> 🌐 **[Launch the Live Application](https://biodiversityplanner.streamlit.app/)**

## 🌿 Project Overview

The Biodiversity & Native Planting Planner is a data-driven web application that helps urban gardeners discover native plants suitable for their growing conditions while supporting local biodiversity and pollinators.

Users can select:
- 📍 U.S. state
- ☀️ Sunlight availability
- 💧 Water availability
- 🦋 Preferred pollinator

The application uses processed plant and native-state datasets to identify plants that match the selected conditions.

## 🎯 Problem Statement

Urban gardeners often lack simple, automated tools that help them identify native plant species suitable for their local gardening conditions while supporting local pollinator populations.

## 💡 Our Solution

We combined plant distribution, gardening characteristics, taxonomy, pollinator observations, and image information into application-ready datasets.

```text
User selects gardening conditions
            ↓
Recommendation engine
            ↓
Native-state filtering
            ↓
Sunlight + water + pollinator filtering
            ↓
Matching native plants
            ↓
Plant information and images
```

## 👥 Team — Vanguard Strategists

| Team Member | Grow with Google Track | Role |
|---|---|---|
| **Ayotomiwa Omojola** | Data Analytics | **Data Analytics & UI/UX Design** |
| **Hanan Kassim** | Advanced Data Analytics | **Advanced Data Analytics** |
| **Adrian Denis** | IT Automation with Python | **Application Development & Automation** |
| **Favour Asomba** | Cybersecurity | **Cybersecurity** |

### Ayotomiwa Omojola — Data Analytics & UI/UX Design

- Data sourcing and preparation
- Data cleaning and standardization
- Dataset integration
- Feature engineering
- Data validation
- Application-ready dataset preparation
- UI/UX design and refinement
- User-flow and information-hierarchy improvements
- Responsive interface considerations for desktop and mobile

### Hanan Kassim — Advanced Data Analytics

- Data analysis
- Dataset validation
- Analytical review
- Data quality support

### Adrian Denis — IT Automation & Application Development

- Recommendation engine
- Python/Streamlit application development
- Application logic
- User-input filtering
- Data-to-interface integration
- Application deployment

### Favour Asomba — Cybersecurity

- Security considerations
- Input validation review
- Repository security
- Deployment/security review

## ✨ Key Features

- 📍 Native plant recommendations by U.S. state
- ☀️ Sunlight-based filtering
- 💧 Water-availability filtering
- 🦋 Pollinator-based filtering
- 🌿 Detailed plant information
- 🖼️ Plant images where available
- 📱 Responsive interface
- 🚀 Deployed Streamlit application

## 🧠 Recommendation Engine

The current recommendation engine uses deterministic rule-based filtering rather than machine learning.

```text
Selected State
      ↓
Find native plant IDs
      ↓
Match sunlight requirement
      ↓
Match water requirement
      ↓
Match preferred pollinator
      ↓
Return matching plants
```

## 📊 Data Sources

| Source | Purpose |
|---|---|
| Missouri Botanical Garden | Native plant distribution |
| Lady Bird Johnson Wildflower Center | Gardening characteristics |
| USDA PLANTS Database | Botanical taxonomy |
| Pollinator Interaction Dataset | Pollinator observations |
| iNaturalist API | Plant images |

See [`docs/data_source_guide.md`](docs/data_source_guide.md).

## 🔄 Data Pipeline

```text
Raw Data
   ↓
Cleaning
   ↓
Standardization
   ↓
Feature Engineering
   ↓
Taxonomy Resolution
   ↓
Pollinator Aggregation
   ↓
Coverage Validation
   ↓
plants_master.csv
   ↓
plants_app.csv
   ↓
Recommendation Engine
   ↓
Streamlit Application
```

## 🗂️ Application Datasets

### `plants_master.csv`
Complete integrated dataset containing merged source data, taxonomy, gardening information, and pollinator observations.

### `plants_app.csv`
Application-ready dataset containing recommendation features, display information, and plant image information.

The project documentation records image coverage of **894 out of 997 species (89.7%)**.

### `plant_states.csv`
Normalized lookup table connecting plant IDs to native U.S. states.

### `data_quality_report.csv`
Validation summary produced during the data-processing workflow.

## 🛠️ Technologies

- Python
- Pandas
- NumPy
- Streamlit
- Jupyter Notebook
- iNaturalist API
- Git
- GitHub

## 🚀 Live Application

**[🌱 Open Biodiversity & Native Planting Planner](https://biodiversityplanner.streamlit.app/)**

The Streamlit application has been deployed for public demonstration.

## 🖥️ Application Workflow

```text
Open Application
      ↓
Select State
      ↓
Select Sunlight
      ↓
Select Water
      ↓
Select Preferred Pollinator
      ↓
Generate Recommendations
      ↓
Explore Native Plant Results
```

## 🚀 Getting Started Locally(How to Run)

### 1. Clone the repository

```bash
git clone https://github.com/Jolitomi/Biodiversity_Planner.git
cd Biodiversity_Planner
```

### 2. Create a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

From the repository root:

```bash
streamlit run src/app.py
```

> The application depends on the processed datasets in `data/processed/`. Do not remove those files when migrating or deploying the application.

## Video Walkthrough
[Watch the demo](https://app.screencastify.com/watch/kv8Tq2aVjOVxSOWOnJHw)

## 📁 Showcase Project Structure

```text
biodiversity-native-planting-planner/
│
├── README.md
├── src/
│   └── app.py
├── data/
│   └── processed/
│       ├── plants_app.csv
│       └── plant_states.csv
├── docs/
│   ├── project_documentation.md
│   ├── data_source_guide.md
│   ├── data_dictionary.md
│   ├── data_handoff.md
│   └── data_pipeline_architecture.md
└── LICENSE
```

## 📱 UI/UX

The interface was refined with a focus on:
- Clear visual hierarchy
- Simple user input
- Compact recommendation presentation
- Readability of plant information
- Responsive behavior across desktop and mobile screens
- Reducing unnecessary vertical scrolling

UI/UX refinement was a cross-functional contribution alongside the project's data and engineering work.

## 🌍 UN SDG 15 — Life on Land

This project supports **UN Sustainable Development Goal 15: Life on Land** by encouraging biodiversity-conscious planting and making native plant information more accessible.

## Implementation Plan

**Steps & Timeline**
1. **Data Foundation (Completed)** — Source, clean, and validate the master dataset
2. **Application Build (Completed)** — Build the Streamlit recommendation app and app-facing dataset
3. **Deployment (Completed)** — Deploy publicly via Streamlit; document local run steps
4. **Documentation & Submission (Completed)** — Finalize README, summary, and walkthrough video
5. **Post-submission Expansion (Planned)** — Broaden species coverage, add ML-based ranking, mobile polish

**Resources**
- Open datasets: Missouri Botanical Garden, Lady Bird Johnson Wildflower Center, USDA PLANTS, iNaturalist
- Python/Pandas/NumPy for data processing, Streamlit for the front end
- Team coverage across Data Analytics & UX, Advanced Data Analytics, App Dev & Automation, and Cybersecurity
- Streamlit Community Cloud for hosting

**Risks & Mitigations**
| Risk | Mitigation |
|---|---|
| Incomplete/inconsistent source data | Data quality report flags gaps; dataset scoped to well-documented species |
| Recommendations miss edge-case growing conditions | Filtering logic is transparent and explainable, tunable as more data is validated |
| Hosted app downtime / free-tier limits | Local run instructions documented as fallback |
| Security exposure on a public-facing app | Dedicated cybersecurity review of input handling and deployment config |
| Scope creep past deadline | Feature set limited to rule-based engine now; ML ranking deferred to "What's Next" |

## 🔮 What's Next

Potential future improvements include:
- ⭐ Recommendation ranking
- 🗺️ Interactive maps
- 📍 County-level recommendations
- 🌸 Seasonal planting recommendations
- 🐝 Expanded pollinator coverage
- 🌎 Expanded geographic coverage
- 📊 Biodiversity impact indicators
- 🔎 More advanced plant search

## 📚 Documentation

- [Project Documentation](docs/project_documentation.md)
- [Data Source Guide](docs/data_source_guide.md)
- [Data Dictionary](docs/data_dictionary.md)
- [Data Handoff Guide](docs/data_handoff.md)
- [Data Pipeline Architecture](docs/data_pipeline_architecture.md)

## 📜 License

This project is developed for educational purposes as part of the Grow with Google BUILD Stage.

Users should comply with the applicable licensing, attribution, and usage requirements of each external source.

## 🙏 Acknowledgements

We acknowledge:
- Missouri Botanical Garden
- Lady Bird Johnson Wildflower Center
- United States Department of Agriculture (USDA)
- Pollinator dataset contributors
- iNaturalist

## 🌱 Project Status

- ✅ Dataset sourcing completed
- ✅ Data cleaning completed
- ✅ Feature engineering completed
- ✅ Taxonomy integration completed
- ✅ Pollinator aggregation completed
- ✅ Master dataset completed
- ✅ Application dataset completed
- ✅ Plant image integration completed
- ✅ UI/UX refinement completed
- ✅ Streamlit application developed
- ✅ Application deployed
- 🚀 **Live application available**

---

**Vanguard Strategists**  
*Biodiversity & Native Planting Planner*
