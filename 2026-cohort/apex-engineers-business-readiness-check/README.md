# Apex Engineers: Business Readiness Check

## UN Sustainable Development Goal

[Goal 9: Industry, Innovation, and Infrastructure](https://sdgs.un.org/goals/goal9)

## Problem Statement

Traditional mom-and-pop retail storefronts lack a simple, automated way to
assess and update their old administrative software.

## Overview

Apex Engineers is building a project to help small retail and e-commerce
businesses review the tools they use to run their business.

The Business Readiness Check focuses on four gaps supported by the team's
research: inventory synchronization, payments and checkout, customer email
capture, and online booking. It gives a non-technical owner a weighted risk
result and practical next steps in a few minutes.

Two optional, non-scored questions ask how the business manages operational
information and how often it repeats data entry. These answers personalize the
guidance for owner-operated and small-team workflows without changing the
research-derived score.

The project does not replace a point-of-sale system, process payments, schedule
appointments, or perform a formal security or compliance audit.

## How the Solution Works

1. The owner optionally enters a business name and type.
2. The owner can answer two optional questions about current administrative
   methods and repeated data entry.
3. The owner answers four scored questions with **Yes**, **No**, or **Not
   applicable**.
4. Python applies the research-derived question weights: 5, 4, 3, and 2.
5. The application calculates the applicable risk percentage.
6. Failed areas are ordered from highest to lowest weight.
7. The owner receives an area-by-area readiness breakdown and non-scored
   business-context guidance.
8. Python creates a phased modernization plan with security checks, success
   measures, and questions to ask software providers.
9. The owner can download the complete result as a plain-text report.

The risk categories are project-designed interpretation bands:

| Percentage | Result |
| ---: | --- |
| 0-24% | Low |
| 25-49% | Moderate |
| 50-74% | High |
| 75-100% | Critical |

These categories are not externally validated standards. **Not applicable**
answers are excluded from the denominator. If every area is not applicable,
the tool returns no score instead of reporting zero risk.

## Current Features

- Four-question Streamlit assessment.
- Two optional, non-scored questions about operational tools and repeated data
  entry.
- Weighted scoring with applicable-question handling.
- Highest-priority gap identification.
- Ordered modernization recommendations.
- Readiness status and explanation for every assessed area.
- This-week and 30-day modernization actions.
- Success measures, security checkpoints, and provider questions.
- Downloadable plain-text report containing the complete action plan.
- Input normalization, safe errors, a privacy notice, and a disclaimer.
- Automated tests for scoring, invalid input, priorities, and report output.

## Project Status

The expanded application is built, tested, and publicly deployed. All 22
automated tests pass. The mixed-answer assessment, optional business-context
flow, downloadable report, and mobile layout were verified in the deployed
environment. Team research, dashboard, workflow, cybersecurity materials, and
the final walkthrough video are complete.

## Team

- Ramya Kota - Data Analytics: dataset research and project tracking
- Dennys Antunish - IT Automation with Python: application, scoring logic,
  tests, deployment, and core documentation
- Sukanya Karri - Cybersecurity: cybersecurity review and NIST CSF 2.0-based
  recommendations
- Aishat Omolabake Ajibola - Advanced Data Analytics: Tableau dashboard and
  PACE workflow documentation

## Grow with Google Resources Used

- Google IT Automation with Python
- Python scripting and testing
- Git and GitHub collaboration
- Troubleshooting and secure automation practices

## Project Structure

```text
apex-engineers-business-readiness-check/
|-- app.py
|-- diagnostic.py
|-- styles.css
|-- .streamlit/
|   `-- config.toml
|-- requirements.txt
|-- README.md
|-- SECURITY.md
|-- LICENSE
|-- tests/
|   |-- test_app.py
|   `-- test_diagnostic.py
`-- docs/
    |-- Global Dataset.xlsx
    |-- Project Tracker and Raw Datasets.md
    |-- three-page-project-summary.md
    |-- Team_Apex_Engineers_PACE_Workflow_Implementation_Stages.md
    |-- Cybersecurity_Review_Report_md/
    |   |-- Cybersecurity_Review_Report.md
    |   `-- images/
    |-- Dashboard_Documentation/
    |   |-- Small Business Tech Stack Diagnostic Dashboard.md
    |   `-- img/
    `-- supporting CSV datasets
```

## Run Locally

Prerequisite: Python 3.10 or newer.

```bash
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Install the dependencies and start the application:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit will display the local application address in the terminal.

## Run the Tests

The test suite works with either command:

```bash
python -m unittest discover -s tests -v
python -m pytest -q
```

## Public Application

[Open the verified Business Readiness Check](https://business-readiness-check.onrender.com/)

The application is hosted as one Render Web Service from the `apex-engineers`
branch.

## Project Walkthrough Video

[Watch the final Apex Engineers project walkthrough on YouTube](https://www.youtube.com/watch?v=wgcjjEcuUVs)

## Supporting Project Materials

- [Three-page project summary](docs/three-page-project-summary.md)
- [Project tracker and raw dataset notes](docs/Project%20Tracker%20and%20Raw%20Datasets.md)
- [Global e-commerce dataset](docs/Global%20Dataset.xlsx)
- [Tableau dashboard documentation](docs/Dashboard_Documentation/Small%20Business%20Tech%20Stack%20Diagnostic%20Dashboard.md)
- [Interactive Tableau dashboard](https://public.tableau.com/views/SmallBusinessTech-StackDiagnosticToolbyTeamApexEngineer/SmallBusinessTech-StackDiagnosticTool)
- [PACE workflow implementation stages](docs/Team_Apex_Engineers_PACE_Workflow_Implementation_Stages.md)
- [Cybersecurity review report](docs/Cybersecurity_Review_Report_md/Cybersecurity_Review_Report.md)

## Research and Limitations

The diagnostic questions and weights come from the team's project report and
analysis of a global e-commerce dataset. Supporting articles and surveys were
used to frame the challenges of small retailers.

The dataset is an illustrative e-commerce case study. It does not prove that
every traditional storefront experiences the same rates or problems. The tool
therefore provides general guidance rather than guaranteed outcomes.

The two optional business-context questions are project-designed prompts. They
personalize guidance but do not add risk points or claim to be validated by the
dataset.

- [Project report and diagnostic criteria](https://docs.google.com/document/d/1OFAOKCO0PFtaKKfRQRJTysoO7rNMozFNBWTMYOUmOcI/edit)
- [MMC BUILD Project Outline](https://docs.google.com/document/d/1InNWpho03JfFCXKAuMmXqKNMXpoGoRerdZamuqvCQ2M/edit?tab=t.0)

## Future Ideas

- Optional inventory and customer-data file checks.
- More diagnostic areas, including accounting and shipping.
- Carefully researched vendor comparisons.
- User testing with small-business owners.

These ideas are outside the current release scope.

## License

This project is available under the [MIT License](LICENSE).
