Gig Worker Contract Safety Tracker

A web & mobile platform helping independent freelancers securely manage contracts, invoices, payment milestones, and project records — reducing wage theft and improving payment visibility.

Built by Nova Collaborative as part of Mentor Me Collective's Grow with Google Program, 2026 Cohort — BUILD Stage.

Problem Statement

Freelancers and gig economy participants lack basic central tracking systems to securely log client invoices and prevent wage theft.

What it does (and why it matters)

87.3% of employed Nigerians are self-employed, and most freelance work happens outside platforms like Upwork or Fiverr, where payment protection doesn't exist. Freelancers routinely lose payment records, face delayed invoices, and have no centralized way to track contracts, milestones, or disputes.

This MVP gives freelancers one place to:

Securely store and version-control contracts

Create and track invoices linked to real projects

Monitor payment status (Pending, Paid, Overdue)

Track project milestones and deadlines

Export contracts and payment history as evidence during disputes


This project aligns with UN Sustainable Development Goal 8: Decent Work and Economic Growth.

Solution Summary

Our research (World Bank, Nigerian Bureau of Statistics, ILO, and a team-collected freelancer survey) confirmed nonpayment and wage theft as a widespread, largely untracked problem for off-platform freelancers. We translated each research finding directly into a product requirement — full detail in docs/problem-statement-kpi-framework.docx.

The MVP centers on a single dashboard giving freelancers real-time visibility into what they're owed, what's overdue, and a documented paper trail for disputes — measured against a Payment Health metric benchmarked against our own researched wage-theft baseline.

How to run / view this project

Live application: https://nova-contract-safety-tracker-896952476797.europe-west2.run.app

Dashboard design (interactive prototype): src/dashboard.jsx

Recorded walkthrough (max 5 min): Watch Walkthrough Video https://drive.google.com/file/d/18EdQBvKedtPDG9aPp6dD5dE78wU-0pGL/view?usp=drivesdk

Project Charter: docs/project-charter.pdf


Grow with Google resources used

Google Data Analytics Professional Certificate (Chinazo Ezenwata) — used to ground the problem statement in real data and define our KPI/success metrics framework

Google Project Management Professional Certificate (Temitope Ogunkunle) — used to produce the Project Charter, Communication Plan, Stakeholder Analysis, Project Schedule, Work Breakdown Structure, Sprint Backlog, Product Backlog, Gantt Chart, and project documentation, planning, execution, and monitoring

Google UX Design Certificate (Idinmachukwu Onuegbu) — used to research user pain points and create user stories, personas, and the product interface design

Google Cybersecurity Professional Certificate (John Adepoju) — used to define security requirements, identify security threats, and flag database issues to be rectified

Google IT Support Professional Certificate (Gabriella Idehen) — used to collaborate on User Acceptance Testing requirements and data standardization


Team — Nova Collaborative

Name	Grow with Google Track	Project Role

Temitope Ogunkunle	Project Management	Coordination
Idinmachukwu Onuegbu	UX Design	Design / UX
Gabriella Idehen	IT Support	Backend / Infrastructure
John Adepoju	Cybersecurity	Security / Auth
Chinazo Ezenwata	Data Analytics	Data & Insights


What's in this branch

docs/project-charter.pdf — Project Charter (scope, objectives, risks, success metrics)

docs/problem-statement-kpi-framework.docx — Problem Statement & KPI Framework

docs/product-backlog.pdf — Product Backlog

docs/sprint-backlog.docx — Sprint Backlog

docs/wbs.pdf — Work Breakdown Structure (WBS)

docs/stakeholder-analysis.pdf — Stakeholder Analysis

docs/risk-register.xlsx — Risk Register

docs/issues-log.xlsx — Issues Log

docs/team-communication-meeting-plan.docx — Team Communication & Meeting Plan

docs/project-schedule.pdf — Project Schedule

docs/security-requirements.docx — Product Security Requirements Document

docs/identified-security-issues.docx — Identified Security Issues

docs/uat-requirements.pdf — User Acceptance Testing (UAT) Requirements

docs/meeting-notes.pdf — Meeting Notes

docs/final-evaluation.pdf — Final Project Evaluation

src/dashboard.jsx — Dashboard design (freelancer-facing real-time payment tracking view)

src/contract_screens/ — Figma UI/UX design exports


Future Ideas

Native mobile app (iOS/Android)

Payment gateway integration (Paystack, Flutterwave)

Integration with Upwork/Fiverr for auto-synced contracts

AI-assisted contract review


License

MIT
