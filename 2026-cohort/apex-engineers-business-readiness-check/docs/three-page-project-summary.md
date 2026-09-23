# Three-Page Project Summary: Research, Solution, and Implementation Plan

**Team:** Apex Engineers

**UN SDG:** [Goal 9: Industry, Innovation, and Infrastructure](https://sdgs.un.org/goals/goal9)

**Live application:** [Business Readiness Check](https://business-readiness-check.onrender.com/)

**Walkthrough:** [Apex Engineers project walkthrough](https://youtu.be/oV8M_N_13U4)

## Problem and Research

Traditional small retailers can depend on disconnected administrative tools and
manual processes. These gaps can make it harder to maintain accurate inventory,
offer convenient checkout options, retain customer contact information, and
support online appointment booking. The project aligns with UN Sustainable
Development Goal 9 by helping small businesses assess and strengthen their
digital infrastructure.

The team cleaned and reviewed a global e-commerce dataset containing
transactions, customers, inventory, products, marketing, and supplier-cost
information. The project report identified four operational pain points:

1. Inventory records that are not synchronized between a physical point of sale
   and an online store.
2. Checkout friction when digital wallets or guest checkout are unavailable.
3. Customer profiles that cannot support follow-up because email information is
   missing or unverified.
4. Manual scheduling that does not allow customers to book online at any time.

Within the analyzed dataset, the team report recorded 12% of the catalog as at
risk of stockouts, more than 10,000 digital-wallet transactions, and 8.65% of
customer profiles with missing or unverified email addresses. It also identified
Health & Beauty as a high-revenue category where online scheduling could reduce
service friction. These findings informed the diagnostic areas but do not prove
that every small retailer experiences the same conditions.

Supporting articles and small-business surveys helped frame the broader problem.
The e-commerce dataset is an illustrative case study, not a representative
sample of every mom-and-pop storefront. The project therefore does not claim
that every traditional business experiences the same rates or outcomes.

## Solution

The Business Readiness Check is a Python and Streamlit web application. It asks
one question for each of the four pain points. A business owner answers Yes, No,
or Not applicable.

The questions use the weights defined in the team report:

- Inventory synchronization: 5.
- Payments and checkout: 4.
- Customer email capture: 3.
- Online booking: 2.

A No answer adds the question's full weight. A Yes answer adds zero points. A
Not applicable answer is excluded from both the score and the maximum applicable
points. The application divides earned risk points by applicable points and
converts the result to a percentage.

The interface labels the result Low, Moderate, High, or Critical. These bands
are project-designed interpretation categories rather than externally validated
standards. If every answer is Not applicable, the application returns no score
instead of presenting a misleading zero-risk result.

Two optional questions ask how the owner manages orders, inventory, and customer
information and how often information is copied between systems. These prompts
better represent the manual and fragmented workflows described in the problem
statement. They personalize the recommendations but do not affect the weighted
score and are not presented as dataset-validated diagnostic criteria.

Failed areas are ordered by weight. The application explains the highest
priority and gives every area a Ready, Needs attention, or Not applicable
status. It then creates project-designed this-week and 30-day actions, success
measures, security checkpoints, and questions the owner can ask software
providers. The downloadable plain-text report contains the same breakdown and
plan. The result is intended to start a modernization conversation. It is not a
formal technology, financial, compliance, or cybersecurity audit.

## Implementation Plan

### Steps and Timeline

1. **Week 1 — Plan:** Confirm the problem statement and SDG alignment, assign
   team roles, identify data sources, and establish the GitHub and Drive
   workspaces.
2. **Week 2 — Analyze:** Clean and review the selected e-commerce dataset,
   identify the four operational pain points, and define the weighted diagnostic
   logic.
3. **Week 3 — Construct:** Build the Python scoring module and Streamlit
   interface, prepare the Tableau dashboard, and review the application against
   the team's security guidance.
4. **Week 4 — Execute:** Test the application, verify the public deployment,
   complete the documentation and written summary, and record the walkthrough.

### Resources

The team used Python, Streamlit, Pytest, GitHub, Render, Tableau, Google Sheets,
Google Drive, the selected e-commerce dataset, the team project report, and
public small-business and cybersecurity research. The application intentionally
avoids a database and external service integrations so it can remain small,
explainable, and practical within the Build Phase timeline.

### Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| The dataset does not represent every mom-and-pop store. | Present it as an illustrative case study and avoid universal claims. |
| Scope growth delays the working solution. | Keep accounts, uploads, vendor comparisons, and live integrations outside the first release. |
| Assessment answers expose sensitive information. | Use fixed choices, limit optional text, avoid intentional persistence, and warn users not to enter sensitive data. |
| Local behavior differs from the public deployment. | Run automated tests and repeat the assessment and download checks on Render at desktop and mobile widths. |

### Technical Implementation

The scoring rules are separated from the Streamlit interface in
`diagnostic.py`. This module defines the questions and provides functions for
answer validation, scoring, risk classification, priority ordering, readiness
breakdowns, action-plan generation, text normalization, and report generation.
Separating these rules keeps the central logic understandable and testable.

`app.py` provides one user journey: read the privacy notice, optionally identify
the business, answer the questions, generate the result, review recommendations,
and download the report. The first version does not use authentication, a
database, file uploads, external APIs, or actual business-system integrations.

Automated tests cover all-Yes and all-No results, mixed weights, Not applicable
handling, all-not-applicable behavior, priority ordering, readiness statuses,
action-plan ordering, visible risk labels, missing and invalid answers,
optional-text normalization, and report consistency. The final test suite
contains 22 automated tests.

The public Render deployment was verified at desktop and mobile widths. A mixed
assessment produced 8 of 12 applicable risk points, a 66.7% High-risk result,
inventory synchronization as the highest priority, matching business-context
guidance, and a complete downloadable report. No browser errors appeared during
the deployed check.

The security approach minimizes collected information. Business details are
optional and length-limited, answers use fixed choices, report text is
normalized, and responses are not intentionally stored after the active
session. The application warns users not to enter passwords, payment-card data,
customer records, or other sensitive information.

## Outcome and Next Steps

The project turns the team's analysis into a small, explainable automation tool
that a non-technical owner can use in a few minutes. It now connects the score
to a practical modernization sequence instead of stopping at a diagnostic
label. The public application, source code, tests, documentation, security note,
MIT license, and team walkthrough video are complete.

Future work could add optional data-file checks, accounting and shipping
questions, researched vendor comparisons, and user testing. Those features
remain outside the current build so the submitted application stays focused,
testable, and clear about its evidence limits.

## Sources

- [Project report and diagnostic criteria](https://docs.google.com/document/d/1OFAOKCO0PFtaKKfRQRJTysoO7rNMozFNBWTMYOUmOcI/edit)
- [MMC BUILD Project Outline](https://docs.google.com/document/d/1InNWpho03JfFCXKAuMmXqKNMXpoGoRerdZamuqvCQ2M/edit?tab=t.0)
- [UN Sustainable Development Goal 9](https://sdgs.un.org/goals/goal9)
- [Deployed Business Readiness Check](https://business-readiness-check.onrender.com/)
