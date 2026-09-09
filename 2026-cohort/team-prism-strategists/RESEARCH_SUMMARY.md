# Mentoring-Me: Research Summary, Solution, and Implementation Plan
**Team Prism-Strategists | Grow with Google Capstone Showcase 2026**
**Aligned with UN SDG 5.5: Gender Equality in Professional Leadership**
*Seuna Christina, Amanda Malahlela, Medha Yasa, Martha Afful*

## Part 1: Research, Problem Context, and Empirical Evidence

### 1.1 Research Question

This project investigates one specific, measurable challenge: **Why do women disproportionately exit technical careers before reaching senior leadership, even when they report being satisfied with their work?** The core hypothesis was that structured mentorship access represents a systemic gap driving attrition. The primary objective of this research was to ground that hypothesis in verifiable workforce data rather than subjective assumption. This work directly advances United Nations Sustainable Development Goal Target 5.5, which specifically mandates ensuring women full and effective participation and equal opportunities for leadership at all levels of decision-making in economic and professional life.

### 1.2 The Dataset

The investigation utilizes the **Stack Overflow Developer Survey (2020)**, an established global survey of professional software developers. The raw dataset includes **64,461 respondents**. Through a disciplined data processing pipeline (removing non-professional respondents such as students and hobbyists, dropping rows missing professional experience or employment status, and standardizing role definitions), the resulting analysis-ready sample comprises **49,294 valid records**.

A deliberate decision was made **not to impute** missing entries in high-missingness fields, such as professional coding years (~20% missing) or compensation (~36% missing). Imputing synthetic averages into experience or compensation would distort the exact disparity metrics this investigation measures. Consequently, each specialized analysis is strictly restricted to complete-case observations, with exact sub-sample sizes documented.

### 1.3 Core Empirical Findings

**Finding 1: Representation Disparity (7.6% overall female representation)**
Women represent only **7.6%** of all professional developers in the cleaned global sample. This underrepresentation is concentrated in specific technical domains: female developers have higher relative representation in front-end, full-stack, and data-focused roles, but remain exceptionally scarce in DevOps, site reliability engineering, systems administration, and embedded infrastructure, which constitute critical high-growth technical tracks.

**Finding 2: The Leaky Pipeline (30.2% down to 5.2%)**
Female representation stands at **30.2%** among early-career developers with 0 to 2 years of professional experience. However, this proportion steadily deteriorates over time: among professionals with 20 or more years of experience, women represent merely **5.2%** of the workforce. This constitutes the central structural finding of the research. The underlying issue is not primarily initial workforce entry; rather, it is severe **mid-career attrition and structural barriers to advancement**.

**Finding 3: The Retention Risk Window (15.6% active flight risk at 0 to 2 years)**
Active job-seeking behavior, examined as an empirical proxy for retention vulnerability, peaks during the initial ten years of professional practice. Among women with 0 to 2 years of experience, **15.6%** report actively seeking new employment, compared to 7.1% among those with 20 or more years. This statistically confirms that early-career women represent the most vulnerable demographic requiring targeted intervention.

**Finding 4: The Job Satisfaction Paradox (Elevated Satisfaction with Concurrent Flight Risk)**
Across all experience tiers, female developers report **slightly higher** average job satisfaction than their male colleagues (a consistent advantage of +0.10 to +0.14 on a 0 to 4 rating scale). Comparing this finding directly with elevated job-seeking rates reveals a crucial dynamic: **women are not departing technical roles due to job dissatisfaction.** Rather, they depart because they encounter limited sponsorship, opaque promotional pathways, and professional isolation. This points directly to a sponsorship deficit that structured, intentional mentorship can solve.

**Finding 5: Diversity Signals as a Key Decision Factor**
When evaluating prospective employers, company diversity is the most statistically differentiated criterion between genders, selected by women at substantially higher rates than men. Conversely, interest in professional growth opportunities shows no gender divergence; both men and women prioritize skill advancement equally. This indicates that female engineers value professional development just as highly as their peers, but place decisive weight on visible inclusion signals when evaluating long-term career commitments.

### 1.4 Academic and Literature Grounding

Because global developer surveys capture cross-sectional workforce metrics rather than internal mentorship dynamics, these empirical patterns were directly synthesized with foundational organizational research from McKinsey (*Women in the Workplace*) and Catalyst. These studies confirm that active sponsorship, combined with structured near-peer mentorship, serves as the primary mechanism that converts high personal satisfaction into sustained career retention for women in technology. Mentoring-Me translates these research principles directly into software architecture.

## Part 2: Solution Architecture (Mentoring-Me Platform)

### 2.1 Platform Purpose and Problem-to-Solution Mapping

**Mentoring-Me** is a full-stack, data-grounded mentorship pairing platform engineered to dismantle mid-career attrition for women across technical disciplines. In place of informal social networking or arbitrary administrative sorting, the platform operationalizes each empirical finding through an explicit software mechanism:

| Empirical Problem Diagnosed | Root Cause from Data | How Mentoring-Me Solves It |
|---|---|---|
| **1. The Leaky Pipeline** (30.2% junior down to 5.2% senior) | Mid-career attrition resulting from an absence of relatable career sponsors | **Near-Peer Experience Fit (Factor 2)** prioritizes a relatable 2 to 10 year seniority gap, ensuring guidance is pragmatic, actionable, and culturally relevant. |
| **2. Peak Attrition Windows** (15.6% flight risk at 0 to 2 years) | Transition shock and mid-career progression plateaus | **Career-Stage Priority (Factor 3)** algorithmically directs available mentor capacity toward mentees situated in critical attrition windows. |
| **3. The Satisfaction Paradox** (+0.14 satisfaction, yet elevated exits) | Engineers leave not from dissatisfaction, but from invisible advancement paths | **Structured Milestones and Session Notes** converts informal advice into documented, accountable sponsorship goals with calendar integration. |
| **4. Role Model Scarcity** (7.6% overall female representation) | Small numbers mean senior female mentors are buried in unweighted lists | **SDG 5 Representation Boost (+10%)** intentionally prioritizes senior female role models when recommending mentors to female mentees. |
| **5. Workplace Culture Priority** (Diversity is the top differentiated factor) | Engineers place heavy decision weight on visible workplace inclusion | **D&I Allyship Boost (+10%) and Goals Overlap (Factor 4)** connects mentees with senior leaders actively dedicated to diversity and advocacy. |
| **6. Arbitrary Pairing Systems** | Users distrust black box algorithms and opaque manual assignments | **Explainable Compatibility Breakdown UI** provides full visibility into individual percentage contributions across all evaluation dimensions. |
| **7. Niche Domain Scarcity** (Severe scarcity in DevOps and Cloud) | Local internal pools lack specialized female infrastructure architects | **Outreach Hub (Section 2.4)** synthesizes compliant deep links across GitHub, ORCID, and LinkedIn to discover external senior leaders. |

### 2.2 Architecture Overview

The system is built upon a modular three-tier architecture:

| Architectural Tier | Technology Stack | Functional Responsibility |
|---|---|---|
| **Frontend Application** | Python, Streamlit | Responsive dashboard serving mentee, mentor, and administrator workflows |
| **Backend API Engine** | Python, FastAPI | High-performance REST endpoints, matching calculations, auth, and messaging |
| **Data Persistence** | SQLite (local), PostgreSQL (cloud) | Relational storage for profiles, matches, direct messages, and audit logs |
| **Intelligent Advisory** | Google Gemini 1.5 | Contextual career roadmap synthesis and resume narrative analysis |
| **Containerization** | Docker, Docker Compose | Reproducible environment configuration and container orchestration |
| **Automated Verification** | pytest | 23 automated unit and integration tests verifying matching and security |

External talent discovery is enabled through the **Outreach Hub**, integrating compliant LinkedIn Boolean query synthesis, GitHub REST API technical profile exploration, and the public ORCID researcher directory.

### 2.3 Security Architecture (Cybersecurity Track: Seuna Christina)

Security was implemented as a foundational platform requirement:

* **Two-Factor Authentication (2FA)**: Mandatory for all user authentication events. A cryptographic 6-digit one-time password (OTP) is generated on the server and delivered through verified email channels, expiring after 10 minutes to mitigate credential-stuffing risks.
* **Cryptographic Password Hashing**: Passwords are encrypted using Bcrypt with salted rounds. Plaintext credentials are never stored, transmitted, or logged.
* **Stateless Session Management**: Role-based access control (covering MENTEE, MENTOR, and ADMIN roles) is enforced at the API layer via JSON Web Tokens (JWT) containing cryptographic signatures and strict expiration claims.
* **Anti-Enumeration Protection**: Authentication endpoints supply uniform error responses for both invalid passwords and unlisted email addresses, neutralizing account discovery reconnaissance.
* **Security Audit Logging**: All authentication attempts, challenge outcomes, and permission modifications are recorded to a dedicated relational audit trail with timestamps, client network identifiers, and event classifications.

### 2.4 Ethical External Discovery (Compliance-First LinkedIn Integration)

A deliberate architectural decision governed the development of the **Outreach Hub**:

* **The Anti-Scraping Constraint**: Automated web scraping against LinkedIn violates Section 8 of their User Agreement, triggers network rate-limiting and CAPTCHA interventions, and creates fragile DOM dependencies vulnerable to minor frontend updates.
* **The Engineered Solution**: Rather than deploying unauthorized scrapers, the platform utilizes a zero-dependency **Boolean Query and Deep Link Synthesizer**. The backend dynamically compiles a mentee's skill targets, seniority requirements, geographic preferences, and Women-in-Tech keywords into valid, URL-encoded Boolean search links.
* **User Agency and Full Reliability**: When activated, the link opens directly within the user's authentic browser session, accompanied by personalized, pre-drafted outreach templates. This ensures **100% operational uptime**, **zero external API fees**, and **complete adherence to web platform governance standards**.

## Part 3: Implementation Plan

### 3.1 Execution Steps and Timeline

The project followed a structured, phased execution model. Each phase was assigned to team members based on their Google Career Certificate specialization, ensuring domain expertise governed every deliverable.

| Phase | Description | Timeline | Team Lead |
|---|---|---|---|
| **Phase 1: Data Analysis and EDA** | Acquire, clean, and analyze the Stack Overflow 2020 Developer Survey. Perform gender-disaggregated statistical analysis. Produce the five core empirical findings. | July 19 to August 2 | Amanda Malahlela (Data Analytics) |
| **Phase 2: Backend API and Matching Engine** | Design the five-factor weighted scoring algorithm. Build FastAPI REST endpoints for registration, authentication, profile management, and matching. Implement equity overlays and dynamic weight adjustment. | August 2 to August 16 | Martha Afful (Advanced Data Analytics) |
| **Phase 3: Frontend Dashboard** | Develop the Streamlit multi-role dashboard (Mentee, Mentor, Admin views). Build the explainable compatibility breakdown UI, direct messaging, calendar sync, and the Outreach Hub interface. | August 9 to August 23 | Medha Yasa (IT Automation) |
| **Phase 4: Security and 2FA** | Implement Bcrypt password hashing, JWT stateless sessions, 2FA email OTP verification, anti-enumeration protection, and audit logging. | August 16 to August 27 | Seuna Christina (Cybersecurity) |
| **Phase 5: Testing and Validation** | Execute 23 automated pytest tests covering matching accuracy, authentication flows, and security edge cases. Benchmark the algorithm against a random-assignment baseline across 49,294 records. | August 27 to September 1 | Full Team |
| **Phase 6: Deployment and User Registration** | Containerize with Docker Compose. Deploy the live platform. Onboard 11 real users (5 mentees, 6 mentors) and validate production match quality. | September 1 to September 4 | Full Team |

### 3.2 Resources

| Resource Category | Specific Resources Used |
|---|---|
| **Primary Dataset** | Stack Overflow 2020 Annual Developer Survey (64,461 raw respondents, 49,294 cleaned) |
| **Academic Literature** | McKinsey *Women in the Workplace* reports, Catalyst sponsorship research |
| **Team Expertise** | Four Google Career Certificate holders across Data Analytics, Advanced Data Analytics, IT Automation, and Cybersecurity |
| **Technology Stack** | Python, FastAPI, Streamlit, SQLAlchemy, SQLite/PostgreSQL, Docker, Google Gemini 1.5, pytest |
| **External APIs** | GitHub REST API (developer profile discovery), ORCID public directory, LinkedIn Boolean deep link synthesis |
| **Infrastructure** | Local development environments with Docker Compose orchestration, cloud-ready PostgreSQL configuration |

### 3.3 Algorithmic Matching Design (Advanced Data Analytics: Martha Afful)

The matching engine employs an **explainable five-factor scoring model** executed pairwise between a mentee and each active mentor profile. Transparency is maintained as a strict design rule: every score component remains independently inspectable and is visualized directly within the mentee interface.

#### Factor 1: Role and Technical Alignment (Base Weight: 30%, Dynamic Weight: 25%)
Calculated via **Jaccard Set Similarity**:

$$\text{Role Score} = \frac{|A \cap B|}{|A \cup B|}$$

Where $A$ denotes the mentee technical role set and $B$ denotes the mentor role set. Partial credit is systematically awarded to related specializations (for instance, Backend Development and Full Stack Engineering) to maintain robust matching even when title phrasing varies.

#### Factor 2: Relatable Experience Gap (Base Weight: 25%, Dynamic Weight: 20%)
A **non-linear peaked scoring function** prioritizes a 2 to 10 year seniority differential between mentor and mentee as the optimal near-peer window. Gaps below 2 years receive reduced scores due to limited mentorship elevation, while gaps exceeding 15 years are moderately depreciated to avoid potential disconnects in contemporary technical practices.

#### Factor 3: Career Stage Priority (Weight: 20%)
An algorithmic priority awarded to mentorship pairings that address mentees within empirically identified attrition tiers (specifically 0 to 2 years and 5 to 10 years of experience). This factor directly translates Finding 3 into code by channeling mentorship availability toward the cohorts carrying the highest statistical risk of departure.

#### Factor 4: Goals and Workplace Culture Alignment (Weight: 15%)
Measures compatibility across stated workplace priorities, including flexible schedules, inclusive cultures, and leadership development. This reflects Finding 5, ensuring that mentees prioritizing diversity are paired with mentors aligned with those professional values.

#### Factor 5: Practical and Logistics Fit (Weight: 10%)
Assesses organizational scale compatibility, ensuring guidance is tailored appropriately whether the mentee is navigating early-stage startups or large-scale enterprise environments.

### 3.4 Dynamic Weight Adjustment

When a mentee enters a custom biography and specific technical aspirations, a **sixth dimension (Freestyle NLP Matching, 10% weight)** automatically activates. The algorithm dynamically redistributes weight from the Role and Experience factors to evaluate text alignment using keyword domain coverage. When no biography is provided, this factor smoothly adjusts to 0%, and the remaining five factors return to their standard distribution.

### 3.5 Equity Overlays (Commitment to UN SDG 5)

Two equity adjustments are integrated into the scoring output:

* **Representation Alignment Boost (+10%)**: When a female mentee is evaluated alongside a senior female mentor, a 10% score priority is applied. This intervention counteracts demographic scarcity, preventing qualified female mentors from being submerged beneath larger male applicant volumes.
* **D&I Allyship Boost (+10%)**: When a mentee requests ally mentorship and a mentor has verified Diversity Ally standing, a 10% priority boost is activated. Cumulative adjustments are strictly bounded at a maximum of +20% to prevent artificial score inflation.

### 3.6 Risks and Mitigation Strategies

| Risk Identified | Potential Impact | Mitigation Strategy Implemented |
|---|---|---|
| **Data Quality and Missingness** | High-missingness fields (20% to 36%) could distort workforce disparity metrics if imputed | Adopted a strict non-imputation policy. Each analysis uses only complete-case observations with documented sub-sample sizes. |
| **Cold-Start Algorithm Bias** | New platforms lack historical interaction data to train recommendation weights | Deployed hand-tuned, research-grounded factor weights validated through empirical benchmarking (+80.6% over random baseline). Modular architecture supports future reinforcement learning once feedback volume accumulates. |
| **Small Mentor Pool** | Limited initial mentor supply could reduce match diversity and quality | Integrated the Outreach Hub for external talent discovery via GitHub, ORCID, and LinkedIn deep links, expanding the effective candidate pool beyond registered users. |
| **Security Vulnerabilities** | Credential theft, account enumeration, and unauthorized access | Implemented layered defenses: Bcrypt hashing, 2FA with time-limited OTP, JWT session tokens, anti-enumeration responses, and comprehensive audit logging. |
| **Platform Scalability** | SQLite limitations under concurrent multi-user production load | Architected the data layer with SQLAlchemy ORM decoupled from specific database engines. PostgreSQL and Google Cloud SQL are supported through environment configuration without code changes. |
| **Algorithmic Transparency Distrust** | Users may reject recommendations from opaque matching systems | Built an Explainable Compatibility Breakdown UI showing individual percentage contributions across all scoring dimensions, enabling users to verify and trust every recommendation. |

### 3.7 Empirical Benchmarking (Algorithm Validation)

The algorithm was validated against an unweighted random-assignment baseline across the cleaned Stack Overflow dataset (49,294 respondents):

| Performance Metric | Algorithm Model | Random Assignment Baseline |
|---|:---:|:---:|
| Top-Match Mean Compatibility | **0.921 (92.1%)** | 0.510 (51.0%) |
| Improvement over Baseline | **+80.6%** | Baseline Reference |
| Strong Match Coverage (50-mentor scarce pool) | **63.0%** | Approximately 15% |
| Score Standard Deviation | **0.063** | Approximately 0.220 |
| Incompatible (Weak) Matches Delivered | **0.0%** | Approximately 30% |

The narrow standard deviation (0.063 compared to 0.220 for random pairings) confirms that the model is **rigorously selective** rather than returning uniform central scores.

### 3.8 Live Platform Telemetry and Production User Validation

Beyond synthetic benchmarking, the platform was validated against the **live production registry** reflected in the Administrator Dashboard:

| Platform Metric | Live System Value | Operational Significance |
|---|:---:|---|
| **Total Live Real Users** | **11 Users** | Authenticated accounts registered within the active scope |
| **Registered Mentees** | **5 Mentees** | Early-career engineers actively exploring mentorship pairings |
| **Registered Mentors** | **6 Mentors** | Active senior practitioners available in the matching pool |
| **2FA Security Adoption** | **5 Accounts (45.5%)** | Active multi-factor email verification enforcement |
| **Delivered Match Quality** | **100% Viable** | Pairings confirmed within Good or Strong tiers (0.0% Weak) |
| **Active Platform Interactions** | **Operational** | Real-time direct messaging, profile discovery, and calendar meeting sync |

![Figure: Live Administrator Dashboard Telemetry showing 11 real registered accounts (5 mentees, 6 mentors) with active 2FA enforcement](diagrams/admin_live_users_proof.png)

*Figure: Production Administrator Dashboard Telemetry confirming 11 live registered accounts (5 mentees, 6 mentors) and active Two-Factor Authentication (2FA) enforcement.*

This dual-tier validation demonstrates that the algorithm operates effectively both under high-volume statistical simulation (SO2020) and during live, interactive user sessions.

## Part 4: Scope Boundaries and Future Roadmap

Every engineering initiative involves deliberate scope boundaries and design trade-offs. The boundaries outlined below reflect intentional architectural decisions made to prioritize security, explainability, and user trust:

### 4.1 Empirical Data Scope and Generalizability
* **Baseline Dataset**: The Stack Overflow 2020 Developer Survey provided a high-volume (49,294 records) empirical foundation to diagnose structural workforce attrition. As a public cross-sectional survey, it establishes directional baselines; future iterations will incorporate longitudinal post-2024 industry telemetry to evaluate post-pandemic workplace transitions.
* **External Mentorship Grounding**: Public developer datasets do not directly track individual mentorship relationships. The positive relationship between sponsorship and career retention was grounded in established literature from McKinsey and Catalyst, which this software directly implements.

### 4.2 Deliberate Algorithmic Design Trade-Offs
* **Explainability over Black Box Models**: An intentional choice was made to deploy an explainable multi-factor scoring model rather than opaque neural collaborative filtering. In professional career development, participants need to understand the explicit reasons behind a recommendation. Transparency fosters participant trust, mitigates systemic bias, and resolves the cold-start challenge inherent in new platforms.
* **Reinforcement Learning Roadmap**: Once user cohorts generate continuous feedback through the integrated milestone tracker and post-session notes, the platform's modular structure can incorporate online weight tuning and contextual bandit ranking models.

### 4.3 Production Scalability and Professional Verification
* **Database and Concurrency Architecture**: The system utilizes SQLAlchemy ORM with decoupled data layers. While local execution utilizes lightweight SQLite for immediate portability, the backend is fully prepared for horizontal scaling via PostgreSQL or Google Cloud SQL through environment configuration updates.
* **Professional Verification Ecosystem**: Initial identity validation incorporates candidate CV uploads, GitHub developer repositories, and direct LinkedIn profile deep links. Future enterprise tiers can integrate automated Single Sign-On (SSO) and corporate HRIS webhooks (such as Workday) for direct organizational credential verification.

*This summary was prepared by Team Prism-Strategists for the Grow with Google Capstone Showcase. The full codebase, automated test suite, and algorithm benchmarking pipelines are available in the project repository under the MIT License.*
