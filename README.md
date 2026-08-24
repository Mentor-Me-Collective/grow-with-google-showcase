🚲 Dublin South Mobility Project: Hyperlocal Micro-Mobility Planner

📌 Project Overview

This project develops a Hyperlocal Micro-Mobility Planner and spatial intelligence framework designed to evaluate and enhance active travel connectivity across South Dublin, Ireland. By leveraging OpenStreetMap (OSM) data and local transit datasets, this repository automates the extraction, cleaning, and filtering of spatial networks to analyze how suburban residential communities interface with high-frequency light rail (Luas Green Line) transit anchors.

Study Area: Dundrum to Sandyford, Dublin
(Bounding Box: 53.300 N, -6.180 E, 53.250 S, -6.270 W).

🌍 Project Alignment: UN Sustainable Development Goal 11
This project directly addresses UN SDG 11: Sustainable Cities and Communities, specifically Target 11.2, which aims to provide access to safe, affordable, accessible, and sustainable transport systems for all by 2030.
By transforming complex geospatial graph networks into actionable business intelligence, this project provides municipal planners with an empirical roadmap to convert car-dominated suburban corridors into safe, accessible active travel networks.
Identifies Infrastructure Gaps: Highlights residential zones falling completely outside 5-minute (400m) and 10-minute (800m) walking catchments.
Promotes Transport Equity: Merges spatial geometry with population data to prioritize underserved communities.
Bridges the "Last-Mile": Provides actionable insights to connect suburban neighbourhoods to primary transit hubs.

Problem Statement & Solution
The Problem: Commuters lack safe, connected data pathways to combine walking, cycling, and public transit. Heavy car-centric infrastructure—most notably the M50 Motorway and arterial multi-lane roads like the R113—physically cuts off neighbourhoods, creating severe high-friction choke points and forcing commuters into private cars.

The Solution: A Python-driven spatial analytics pipeline combined with an interactive Tableau BI dashboard. The framework models true network isochrones (400m–3km), applies an algorithmic 0–100 Street Corridor Safety Score across 88,168 network segments, and overlays CSO Census Demographics to isolate friction bottlenecks.

🎯 Key Findings & Performance Metrics
53,112 Residents live within a 10-minute (3km) cycling catchment of the target stations. 
12,289 Residents live within a 10-minute (800m) walking catchment.
88,168 Street Segments were evaluated and scored.
37.9% of the supporting street network is classified as high-risk (scoring 0–49) for vulnerable commuters.
2,063 Vulnerable Commuters are trapped across 12 distinct high-friction residential pockets, which require immediate infrastructure intervention.

🛠️ Tech Stack
Python 3.x
GeoPandas & Pandas: Spatial data manipulation and filtering
OSMnx: Querying and downloading OpenStreetMap street networks
Shapely: Geometric operations
Jupyter Notebook: Interactive data pipeline
Tableau: Interactive BI dashboard visualization

📂 Repository Structure
To run this project locally, ensure your folders are structured as follows.(Note: Raw data files are not tracked in this repository due to size; please place them in the `raw` folder before running).
dublin_mobility_project/
│
├── Data/
│   ├── Raw/                                        # Original datasets (Not tracked in Git)
│   │   ├── cso_small_area_boundaries.geojson       
│   │   ├── dublin_active_travel.geojson            
│   │   ├── dublin_cycle_infrastructure.csv         
│   │   ├── dublin_street_edges.geojson             
│   │   ├── dublin-metropolitan-area-existing-protected-cycle-infrastructure-2025/
│   │   ├── routes.txt                              
│   │   ├── stops.txt                               
│   │   └── Small_Area_National_Statistical_Boundaries_2022_Ungeneralised_view_-4936014253783534521
│   │
│   └── Processed/                                  # Cleaned data, analytics, and model outputs
│       ├── Dublin_cycle_network.geojson
│       ├── Dublin_demographics_sa2022.geojson
│       ├── Dublin_luas_stops.geojson
│       ├── Isochrone_cycle_1500m.geojson           
│       ├── Isochrone_cycle_3000m.geojson           
│       ├── Isochrone_walk_400m.geojson             
│       ├── Isochrone_walk_800m.geojson             
│       ├── Osm_corridor_edges.geojson
│       ├── Osm_corridor_edges_tagged.geojson
│       ├── Osm_corridor_nodes.geojson
│       ├── Osm_corridor_safety_scored.geojson      
│       ├── Phase5_high_friction_neighborhoods.csv  
│       ├── Processed_dublin_cycle_infrastructure.geojson
│       ├── Processed_dublin_protected_cycle_infrastructure.geojson
│       ├── Processed_gtfs_routes.csv
│       ├── Processed_gtfs_stops_dundrum.geojson
│       ├── Processed_luas_5_stations.geojson
│       ├── Small_areas_combined_infrastructure_distances.csv
│       └── Top_10_active_travel_priority_areas.csv 
│
├── notebooks/
│   └── dublin_mobility_analysis.ipynb              # Main data processing pipeline
│
├── docs/
│   └── dublin_south_mobility_summary.pdf           # Short written summary (Max 3 pages)
│
└── README.md

📺 Project Walkthrough & Documentation
Project Presentation Video:[Watch 7-Minute Project Walkthrough](https://drive.google.com/file/d/1AEvxQTEv16UegufNxVXVlRy3DjNDKHy9/view?usp=sharing)
Written Summary: See the `docs/` folder for the 3-page research and implementation plan summary.
