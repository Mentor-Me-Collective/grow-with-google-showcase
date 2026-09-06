# 🌟 Mentoring-Me — Equitable Mentorship Pairing & Career Growth Platform
> **Capstone Project — Team Prism-Strategists**  
> *Aligned with United Nations Sustainable Development Goal 5: Gender Equality (Target 5.5)*  
> *Developed as part of the Grow with Google Showcase (2026 Cohort)*

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Security](https://img.shields.io/badge/Auth-JWT%20%2B%202FA%20OTP-green.svg)]()
[![Grow with Google](https://img.shields.io/badge/Grow%20with%20Google-Capstone%20Showcase-4285F4.svg)](https://grow.google/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)

---

## 📌 1. What the Project Does (and Why It Matters)

### The Problem Statement
> *"Early-career women in technical fields face systemic isolation due to a lack of structured access to professional network matching."*

Women remain severely underrepresented across specialized technical domains (DevOps, Cloud Architecture, Systems Administration, and Data Engineering). Through empirical research on a benchmark dataset of **49,294 developers**, our team identified that the barrier is not initial entry, but rather **mid-career attrition and structural isolation**:

1. **The Retention Drop-off**: Women leave technical careers at two distinct milestone windows:
   - **Early-Career Transition (0–2 years)**: Juniors leaving due to isolation, onboarding hurdles, and imposter syndrome ($15.6\%$ active job-seeking flight risk).
   - **Mid-Career Plateau (5–10 years)**: Women leaving technical tracks due to a lack of senior sponsorship and visible promotion pathways.
2. **The "Job Satisfaction Paradox"**: Data proves women report slightly *higher* job satisfaction than men across all experience tiers ($+0.10$ to $+0.14$ on a $0\text{--}4$ scale). Women are **not** leaving because they dislike the work; they leave because they lack career sponsorship and upward mobility.
3. **Opaque & Arbitrary Matching**: Traditional mentorship initiatives rely on manual, arbitrary pairing or black-box algorithms that fail to account for multi-skill overlap, relatable seniority gaps, or diversity values.

---

### The Solution: Mentoring-Me
**Mentoring-Me** is a full-stack, data-grounded mentorship platform engineered to dismantle these barriers through an **explainable 5-factor matching algorithm**, **enterprise-grade cybersecurity**, and **continuous career advisory tools**.

#### 🔑 Key Capabilities:
* **Explainable 5-Factor Weighted Matching Model**:
  - **Role & Technical Alignment (30%)**: Jaccard similarity over multi-skill sets ($\frac{|A \cap B|}{|A \cup B|}$).
  - **Relatable Experience Gap (25%)**: Peaked scoring function prioritizing a relatable $2\text{--}10$ year seniority window (near-peer sponsorship).
  - **Retention-Risk Career-Stage Priority (20%)**: Direct algorithmic boost for $0\text{--}2\text{y}$ and $5\text{--}10\text{y}$ candidates.
  - **Goals & Workplace Culture Alignment (15%)**: Alignment across stated priorities (diversity signals, flexible schedules).
  - **Practical & Logistics Fit (10%)**: Organizational scale alignment.
* **Transparent Compatibility Breakdown**: Interactive UI bar charts showing users exactly *why* a pair was recommended.
* **D&I Allyship Boost**: $+10\%$ algorithmic priority for mentors registered as Diversity Allies.
* **Consumer-Grade Security**: Mandatory **Double Authentication (2FA)** with 6-digit email OTPs, Bcrypt password hashing, and JWT session tokens.
* **Direct Messaging & 1-Click Scheduling**: Real-time messaging with unread badges, one-click Google Calendar sync, and standard `.ics` invite generation for 25-minute introductory syncs.
* **External Discovery Hub**: Zero-dependency LinkedIn Boolean Deep Link Generator, GitHub REST search, and ORCID public researcher directory integration.
* **AI Career Advisor**: Personalized career roadmap generator and CV analyzer powered by Google Gemini AI.

---

## 👥 2. Cross-Functional Cohort & Grow with Google Resources Used

This project directly synthesizes skills, toolsets, and best practices acquired across four distinct **Grow with Google** learning tracks:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           TEAM PRISM-STRATEGISTS (COHORT SHOWCASE)                     │
├──────────────────────────┬───────────────────────────────┬──────────────────────────────┤
│ Scholar                  │ Grow with Google Track        │ Project Contribution & Role  │
├──────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 📊 Amanda Malahlela      │ Data Analytics Track          │ Objective 1: EDA & Insights  │
│ 🛡️ Seuna Christina       │ Cybersecurity Track           │ Objective 3: Platform & 2FA  │
│ ⚙️ Medha Yasa            │ IT Automation with Python     │ Backend API, CI/CD & Testing │
│ 📈 Martha Afful          │ Advanced Data Analytics Track │ Objective 2: Matching Model  │
└──────────────────────────┴───────────────────────────────┴──────────────────────────────┘
```

### 🎓 How Each Grow with Google Resource Was Leveraged:

#### 1. Google Data Analytics Professional Certificate — Amanda Malahlela
* **Applied Competencies**: Exploratory Data Analysis (EDA), data cleaning methodologies, spreadsheet modeling, and visualization design.
* **Implementation in Project**: Cleaned the Stack Overflow Developer Survey ($64,461 \rightarrow 49,294$ valid records), defined the non-imputation policy to prevent artificial skewing of gender gap statistics, and generated the five core publication charts (`chart1` through `chart5`) diagnosing the representation gap, leaky pipeline, and retention risk windows.

#### 2. Google Cybersecurity Professional Certificate — Seuna Christina
* **Applied Competencies**: Threat modeling, access control, identity and access management (IAM), cryptography, and security logging.
* **Implementation in Project**: Designed the security and authorization architecture:
  * Mandatory **Two-Factor Authentication (2FA)** via cryptographic 6-digit email OTPs.
  * Secure password hashing using **Bcrypt** with salt rounds.
  * Stateless **JWT Bearer Token** session management.
  * Defense against user enumeration attacks on authentication endpoints.
  * Relational **Security Audit Logging** tracking all login attempts, OTP challenges, and role changes.

#### 3. Google IT Automation with Python Professional Certificate — Medha Yasa
* **Applied Competencies**: Python automation scripting, REST API development, testing suites, system environment orchestration, and containerization.
* **Implementation in Project**: Built the automation and service layer:
  * **FastAPI REST Backend** with automated relational database migrations and mock data seeding (`seed.py`).
  * Automated **`.ics` calendar invite generator** and dynamic Google Calendar URL crafter for instant meeting bookings.
  * Automated testing pipeline with **23+ unit and integration tests** validating authentication, messaging, and outreach APIs.
  * Multi-container orchestration using **Docker** and **Docker Compose**.

#### 4. Google Advanced Data Analytics Professional Certificate — Martha Afful
* **Applied Competencies**: Advanced statistical modeling, algorithmic scoring formulation, multi-attribute similarity metrics, and empirical benchmarking.
* **Implementation in Project**: Engineered the matching algorithm and validation suite:
  * Formulated the **5-Factor Weighted Scoring Model** using set-theoretic **Jaccard Similarity** and non-linear peaked tenure curves.
  * Conducted formal **empirical benchmarking against a random baseline**, demonstrating an **$+80.6\%$ performance improvement**.
  * Executed scarcity stress-testing (50-mentor pool) to prove model robustness under constrained supply.

#### 5. Additional Google Resources Leveraged:
* **Google Digital Garage & Applied Digital Skills**: User-centric interface design, project communication, and workflow planning.
* **Google Gemini AI (Google AI Studio)**: Integrated to power the intelligent in-app Career Roadmap and resume analysis features.
* **Google Cloud & Material Design Guidelines**: Applied to the Streamlit UI layout and responsive CSS theme.

---

## 📊 3. Empirical Data & Algorithm Performance

Validated against the cleaned **Stack Overflow 2020 Developer Survey (49,294 respondents)**:

| Metric | Result | Benchmark Significance |
| :--- | :---: | :--- |
| **Top-Match Mean Compatibility Score** | **0.921 (92.1%)** | Consistently delivers "Strong" compatibility recommendations |
| **Improvement over Random Baseline** | **+80.6%** | Outperforms random assignment ($0.510$) by $>80\%$ |
| **Strong Match Coverage (50-mentor scarce pool)** | **63.0%** | High match quality even with early-stage, limited mentor supply |
| **Score Standard Deviation** | **0.063** | Discriminating, non-uniform scoring distribution |
| **Weak Matches under Scarcity** | **0.0%** | Gracefully degrades without delivering incompatible pairings |

---

## 🏛️ 4. Architecture & Repository Structure

```
mentor_me_capstone/
├── analysis/                      # Track: Data Analytics (Objective 1)
│   ├── objective1_full_pipeline.py# End-to-end cleaning & EDA pipeline
│   ├── chart1_role_representation.png # Role distribution gap
│   ├── chart2_leaky_pipeline.png  # Tenure attrition curve
│   ├── chart3_retention_risk.png  # Flight-risk window bar chart
│   ├── chart4_job_satisfaction.png# Satisfaction paradox comparison
│   ├── chart5_job_factors_gender.png  # D&I values divergence
│   ├── summary_statistics.csv     # Extracted numerical benchmarks
│   └── key_insights.txt           # Analytical synthesis
├── data/
│   └── so2020.csv                 # Cleaned benchmark dataset (49,294 rows)
├── diagrams/
│   ├── architecture_diagram.png   # Full-stack system topology
│   └── flowchart_matching_algorithm.png # Mathematical matching flow
├── matching/                      # Track: Advanced Data Analytics & Software Track
│   ├── app.py                     # Streamlit Consumer-Grade Web UI
│   ├── matching_algorithm_v1.py   # 5-factor weighted algorithm implementation
│   ├── evaluate_matching_algorithm.py # Accuracy & random baseline benchmarking
│   ├── test_matching_scenarios.py # 5 edge-case scenario tests
│   ├── matching_algorithm_methodology.md # Mathematical justification
│   ├── deployment_and_api_guide.md# Complete deployment manual
│   └── backend/                   # FastAPI REST Backend Service
│       ├── main.py                # REST endpoints, routers & middleware
│       ├── auth.py                # JWT, Bcrypt, 2FA OTP & email dispatch
│       ├── database.py            # SQLAlchemy database engine session
│       ├── models.py              # Relational database models
│       ├── schemas.py             # Pydantic data schemas
│       ├── seed.py                # Database population script
│       ├── profile_evaluator.py   # Scoring & profile evaluation
│       ├── linkedin_client.py     # Boolean Deep Link Generator
│       ├── github_client.py       # GitHub REST API client
│       ├── orcid_client.py        # ORCID researcher client
│       └── test_*.py              # 11 comprehensive backend test suites
├── docker-compose.yml             # Container orchestration
├── Procfile / railway.json        # Production PaaS configurations
└── README.md                      # Project documentation
```

---

## 🚀 5. Setup & Run Instructions

### Option A: Live Interactive Cloud Deployment
Access the live platform directly in your browser:  
👉 **[https://mentoring-me.streamlit.app](https://mentoring-me.streamlit.app)**

---

### Option B: Running Locally (Step-by-Step)

#### 1. Clone the Repository:
```bash
git clone https://github.com/Mentor-Me-Collective/grow-with-google-showcase.git
cd grow-with-google-showcase/matching
```

#### 2. Configure Python Virtual Environment:
```bash
# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

#### 3. Start the FastAPI Backend:
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
*Interactive Swagger API Docs will be available at:* `http://127.0.0.1:8000/docs`

#### 4. Launch the Streamlit Frontend:
In a second terminal window (with virtual environment activated):
```bash
streamlit run app.py
```
*Open your browser at:* `http://localhost:8501`

---

### Option C: Running with Docker Compose
Run both the frontend and backend in isolated containers with a single command:
```bash
docker-compose up --build
```
* **Frontend Web App**: `http://localhost:8501`
* **Backend API Docs**: `http://localhost:8000/docs`

---

### 🧪 Running the Automated Verification Suite
To execute the automated test suites covering 2FA, JWT authentication, in-app messaging, algorithm edge cases, and external outreach:
```bash
cd matching
pytest backend/ test_matching_scenarios.py -q
```

To run the algorithmic evaluation benchmark against the random baseline:
```bash
python evaluate_matching_algorithm.py
```

---

## 🔮 6. Future Ideas — Breadcrumbs for the Next Cohort!

To future Grow with Google Scholars building on this foundation, here are five high-impact expansion pathways:

1. **Outcome-Based Reinforcement & Supervised Weight Tuning**:
   - *The Idea*: Transition from our explainable rule-based weighted model to an **online learning / bandit model** once real users submit 6-month satisfaction ratings.
   - *How to Start*: Use the existing `MentorshipNote` and `Match` models to add a post-session rating column (`rating: 1-5`), then train a gradient-boosted ranker against those outcome labels.

2. **"Flash Mentorship" & Emergency PR Reviews**:
   - *The Idea*: Not every pairing requires a 6-month commitment. Many early-career women need a 15-minute emergency architecture review or pull request critique before a big sprint deadline.
   - *How to Start*: Add a "Flash Match" queue endpoint that matches available mentors in real-time based on active status and immediate GitHub issue tags.

3. **B2B Corporate DEI & Sponsorship Dashboard**:
   - *The Idea*: Enterprises want to fund and support internal female mentorship cohorts. Build an enterprise portal where corporate DEI leaders can sponsor licenses, view anonymized retention telemetry, and measure employee promotion velocity.
   - *How to Start*: Extend the `User.role` enum to include `ENTERPRISE_ADMIN`, and create an aggregated metrics page tracking cohort retention rates.

4. **WebRTC Video & Audio Rooms directly in the Browser**:
   - *The Idea*: While our platform automates Google Calendar sync and `.ics` files, embedding live, secure peer-to-peer WebRTC video rooms directly inside the Streamlit/FastAPI portal would eliminate external app switching entirely.

5. **Cross-Organizational "Peer Circles" (Group Mentorship)**:
   - *The Idea*: In specialized domains like DevOps or Embedded Systems where senior women are scarce, create 1-to-many "Circle Mentorship" pods where one senior mentor supports 4–6 early-career women simultaneously.

---

## 📄 7. Open-Source License

This project is licensed under the **MIT License** — feel free to fork, adapt, and build upon our work!

```
MIT License

Copyright (c) 2026 Team Prism-Strategists (Grow with Google Showcase)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

*Made with 💜 by **Team Prism-Strategists** for the **Grow with Google Showcase**.*
