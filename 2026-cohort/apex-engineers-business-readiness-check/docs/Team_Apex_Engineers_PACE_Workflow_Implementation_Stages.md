# Team - Apex Engineers

**UN SDG Goal:** Goal 9: Industry, Innovation, and Infrastructure

**Project Topic:** Small Business Tech-Stack Diagnostic Tool

**Implemented Solution:** Business Readiness Check

**Problem Statement:** Traditional mom-and-pop retail storefronts lack a simple, automated path to audit and modernize their legacy administrative software.

---

## Project Questions & Considerations

## PACE: Plan Stage

### **What does "tech-stack diagnostic" mean for our specific project — what exactly are we building?**
Build a Python and Streamlit diagnostic tool for small-business owners. This
tool evaluates four operational areas to calculate a weighted risk score,
identify the highest-priority technology gap, and generate a practical
modernization roadmap with general security checkpoints.

### **What does success look like for this tool, and how will we know if it actually solves the problem statement?**
- **Closing the Knowledge Gap:** Transitioning users from uncertainty ("I don't know what's out there") to actionable, personalized recommendations ("Here is what I should use").
- **High Usability:** Enabling non-technical small business owners to receive a comprehensive diagnostic in under two minutes without requiring technical fluency or exposure to jargon.
- **Actionable Modernization:** Moving beyond static information to clear, prioritized modernization decisions that address the specific identified "Fragmentation Tax" risks.
- **Validation:** Success is validated when the user successfully identifies their highest-priority technical gap and receives a concrete, step-by-step path to resolution.

### **Who are we assuming the end user is? Does that change what we build?**
The end user is the store owner. This decision directly informs our build strategy: we must prioritize a minimalist, jargon-free, and intuitive interface that requires zero technical fluency, rather than a more complex tool that would necessitate professional training or multi-client management features.

### **What categories of "legacy administrative software" should the diagnostic cover?**
- Inventory
- Email
- Payment
- Booking

### **What is each team member's role and primary deliverable for our four tracks (Advanced Data Analytics, Data Analytics, IT Automation with Python, and Cybersecurity)?**
- **Ramya Kota** (Data Analytics) — Sourcing and cleaning datasets, performing exploratory data analysis, and constructing and maintaining the project tracking log.
- **Aishat Omolabake Ajibola** (Advanced Data Analytics) — Developing data visualization dashboards, generating analytical reports, and constructing the comprehensive PACE documentation workflow.
- **Dennys Antunish** (IT Automation with Python) — Designing and developing the Streamlit diagnostic tool, managing the GitHub repository, and handling code deployment/pushes.
- **Sukanya Karri** (Cybersecurity) — Reviewing the tool's security and privacy
  considerations, preparing recommended safeguards and a security roadmap, and
  mapping those recommendations to the NIST CSF 2.0 reference framework.

### **What are the team's shared/collaborative responsibilities?**
All team members are responsible for participating in the weekly progress meetings, contributing to the final recorded walkthrough, and ensuring individual code/documentation merges cleanly into the main repository.

### **What is the project timeline?**
Project Timeline – 4 weeks
- **Week 1:** Identifying business needs, defining project scope, data sourcing, project framework design, team roles, and GitHub repository setup.
- **Week 2:** Exploratory Data Analysis (EDA), cleaning datasets, and developing the core scoring/diagnostic logic.
- **Week 3:** Integrating scoring logic into Streamlit, finalizing the Tableau
  dashboard UI, and reviewing the project against security practices and the
  NIST CSF 2.0 reference framework.
- **Week 4:** Final testing, bug fixing, documentation completion, recording walkthrough video, and project submission (Deadline: August 14).

### **What is the logical build order — which pieces block others, and who is waiting on whom?**
- **Data Foundation:** Sourcing of raw datasets (Ramya Kota & Aishat Omolabake Ajibola).
- **Analysis:** Data cleaning, Exploratory Data Analysis (EDA), and identification of the four key pain points (Ramya Kota).
- **Visualization & Reporting:** Building the Tableau dashboard and generating the comprehensive project report (Aishat Omolabake Ajibola).
- **Technical Development:** Development of the Streamlit diagnostic tool
  (Dennys Antunish) and review against security practices and the NIST CSF 2.0
  reference framework (Sukanya Karri).

### **Where will we source data — do we use publicly available datasets (Kaggle, Data.gov, SBA/other small-business surveys), collect our own via a short survey, or simulate representative data? What are the tradeoffs?**
We used a global e-commerce dataset sourced by Ramya Kota. The data underwent
cleaning, deduplication, and formatting, followed by exploratory analysis to
identify relevant operational indicators.

### **What tools/platforms will we standardize on (GitHub repo structure, branch naming, communication channel, file-sharing/notebook environment) so our work merges cleanly?**
- **Version Control (GitHub):** Shared `apex-engineers` branch in the team fork;
  final pull request targets the MMC repository's `main` branch and remains
  open for review.
- **Repository Structure:** Project-root Python and Streamlit files, `/tests`
  for automated checks, and `/docs` for datasets, images, analysis, and reports.
- **Communication:** Slack for daily operational updates and coordination; Google Meet for bi-weekly status syncs.
- **File-sharing:** Google Drive for all shared documentation and project logs.

### **What is our internal check-in cadence between now and August 14 (e.g. weekly syncs, mid-point review), and how will we track progress and flag delays early?**
- **Bi-Weekly Syncs:** Every Tuesday and Sunday for strategic progress review.
- **Daily Standups:** Brief daily Slack status updates for the final week.
- **Tracking:** Centralized Project Tracker (Google Sheet) with status indicators (Green/Yellow/Red).
- **Delay Protocol:** If a task is blocked for >24 hours, it is flagged in the Slack channel for immediate team re-evaluation.

### **What does each person need from the others to start their piece of the work today?**
- **Ramya Kota and Aishat Omolabake Ajibola:** Finalizing and sharing the cleaned dataset and core insights to ensure alignment.
- **Dennys Antunish:** Needs the identified pain points and logic derived from the data analysis to build the diagnostic tool.
- **Sukanya Karri:** Needs the defined operational scope and business context to map NIST CSF 2.0 security requirements and vulnerability assessments.

### **What are the possible risks and mitigation strategies?**
- **Risk:** Data quality issues in public datasets. **Mitigation:** Rigorous data cleaning and standardization.
- **Risk:** Overly complex tool UI. **Mitigation:** Focus on a minimalist, jargon-free Streamlit interface.
- **Risk:** Security and data privacy vulnerabilities. **Mitigation:** Use
  in-memory processing to avoid intentionally persisting user information,
  prohibit PII or payment credential collection, and use NIST CSF 2.0 as a
  reference when documenting additional safeguards.

## PACE: Analyze Stage

### **Will the data we source (real or self-collected) be sufficient to build a credible diagnostic, or will we need to supplement/simulate additional data?**
The global e-commerce dataset provides an illustrative baseline for examining
inventory, payment, customer, and service-related indicators. It does not
directly measure a business's software maturity or prove that legacy software
caused an observed outcome. The diagnostic logic is therefore stress-tested
with predefined answer combinations, including fully enabled, fully manual,
mixed, invalid, and not-applicable cases.

### **What variables/fields do we need in our dataset to score a business's tech-stack maturity (e.g. software used per category, age of system, manual vs. digital processes, budget, and staff size)?**
We need categories covering Payments (digital wallet support), Inventory (automation level), Email capture status, and Booking.

### **How will we define and weight a "diagnostic score" — what makes one business more in need of modernization than another?**
The score is calculated based on the presence/absence of automation across four pillars: Payments, Inventory, Marketing, and Service/Booking. Weights are assigned based on revenue impact (e.g., Inventory has higher weights due to direct revenue loss).

### **What does a summary of our dataset look like once collected — sample size, ranges, any gaps or unusual patterns we should flag before building on top of it?**
The dataset includes thousands of transaction and customer records. Indicators
include unverified customer emails and inventory and payment patterns. Booking
need is a project assumption for service-oriented businesses rather than a
field directly measured by the dataset.

### **What assumptions are we making about small businesses that we should validate against the data rather than guess?**
We assume manual processes can contribute to inefficiency. The dataset
illustrates operational indicators, but it does not establish that disconnected
software caused lost revenue or customer friction. The tool therefore provides
general guidance rather than a causal or externally validated assessment.

### **What are the key assumptions made in the analysis?**
1. **Data Representation:** The provided tables are assumed to accurately represent the complete operational history and current inventory levels of the business.
2. **Inventory Risk:** Products with stock levels at or below the reorder point are assumed to be at immediate risk of stockouts if manual updates are delayed.
3. **Ghost Customer Reachability:** Customers with `email_verified == 'FALSE'` are assumed to be unreachable by automated email marketing engines due to incomplete or unverified contact data.
4. **Service Component:** The 'Beauty & Health' category is assumed to contain products or consultations that would benefit directly from integrated service scheduling.

## PACE: Construct Stage

### **What specific features, testing protocols, and output requirements define the project's final build?**
During the Construct stage, we build the Python Streamlit application using the four weighted assessment questions, scoring logic, recommendations, and downloadable report. We then test each feature, correct problems, and confirm that the application works on both desktop and mobile devices.

### **How will the scoring logic be integrated, and who owns that integration step to ensure nothing falls through the cracks?**
Integration is handled by the IT Automation lead (Dennys Antunish). The scoring
functions remain in the separate `diagnostic.py` module and are imported into
the Streamlit interface in `app.py`.

## PACE: Execute Stage

### **What is the minimum viable version of the diagnostic tool we can demo, and what would be "stretch" additions if time allows?**
MVP: Four scored technology questions plus two optional, non-scored
business-context questions. The tool calculates a weighted risk score and
creates a downloadable plain-text roadmap.

### **What format will the final output take for a small-business user?**
A web-based interactive tool providing a score and an actionable, prioritized roadmap, including recommended next steps, a modernization action plan, how to measure progress, questions to ask providers, and security checkpoints.

### **What do we still need to investigate or validate before we consider the tool ready to demo?**
Input validation, incomplete and invalid answers, scoring edge cases, and
report generation are covered by 22 automated tests. The application does not
use a database or intentionally retain assessment answers after the active
session. The final walkthrough video is complete and its verified public link
is included in the README.

### **What does the README need to cover so anyone (including graders) can run/view the project easily? And, who is responsible for it?**
The README must cover: problem statement, solution summary, instructions to run or view the project, and the walkthrough video link. Responsibility: Collaborative team effort, with Dennys Antunish responsible for technical coordination and final assembly.

### **Who is responsible for the recorded walkthrough, and what should it show in under 5 minutes?**
All team members are responsible for the recording of the walkthrough video, which will be compiled and edited by Dennys Antunish.

### **Who is responsible for writing the short written summary (max 3 pages) of the research, solution, and implementation plan?**
The final Markdown summary is stored in `docs/three-page-project-summary.md`. All team
members are responsible for reviewing it and confirming that their work is
represented accurately.

### **What would the team folders on GitHub entail?**
- Project root — Streamlit application, scoring logic, styles, configuration,
  requirements, README, license, and security guidance
- `/tests` — automated application and diagnostic tests
- `/docs` — documentation, screenshots, datasets, source links, analysis, and
  supporting write-ups

### **What is our plan for the final week — buffer time for integration, testing, and polishing the submission before the August 14 deadline?**
Final code review, security audit of the deployment process (HTTPS/TLS verification), and final polish of the user dashboard interface.
