# Braid (EMPE) — project summary

**Team Quantum Solvers** · UN SDG 5, Gender Equality · MMC × Grow with Google, 2026 cohort
Benardette Xetsa Setutsinam Afi Gati · Eulleria Gitau · Jeff Mbita · Omogbolaga Daramola

---

## 1. Research

**Problem statement.** *Early-career women in technical fields face systemic isolation due to a lack of structured access to professional network matching.* We kept this unchanged for the duration of the project.

The evidence is consistent across sources. Women are **35% of STEM graduates** globally — a figure largely unmoved for a decade — and **26% of the data and AI workforce** (UNESCO, 2025). In Sub-Saharan Africa the disparity is sharper: for every 100 men with spreadsheet skills, roughly **40–44 women** have equivalent proficiency. Fewer than a quarter of tertiary students in Africa study STEM, and in 17 of 21 countries with sex-disaggregated data, women are **16% or less** of STEM graduates (UN OSAA, 2026).

Connectivity compounds the gap. The mobile internet gender gap in Sub-Saharan Africa was **26% in 2025**, leaving roughly **230 million women** in the region offline (GSMA, 2026) at a time when professional networking is increasingly digital.

Crucially, the UN analysis names causes we can build against: **limited exposure, insufficient role models, and weak mentorship networks.** It identifies mentorship as a primary mechanism connecting education to professional careers. The World Bank's Africa Gender Innovation Lab, across 100+ impact evaluations in 30 countries, reinforces that structural barriers respond to deliberate, evidence-based intervention.

**So why has mentorship not already closed this gap?** Our research pointed at the operations, not the intent. Most programmes run on informal networks and manual pairing. Informal networking structurally advantages people who already have access — the opposite of what a widening intervention requires. Manual matching in a spreadsheet stops scaling at roughly thirty participants, precisely when a programme begins to matter. Both failure modes are administrative, and administrative problems are tractable.

We scoped accordingly. Braid does not attempt to solve gender inequality in STEM. It addresses a narrower, addressable question: **when a programme allocates scarce mentor hours, can that allocation be transparent, scalable, and equity-aware by construction?**

## 2. Solution

Braid is a working platform for organisations running structured mentorship programmes, covering the full lifecycle: programme creation → onboarding → information collection → matching configuration → matching run → review → publication → engagement → monitoring → reporting.

A coordinator defines a programme and builds its application form. Applicants complete it. The coordinator sets matching criteria — which questions matter, how much, and which are non-negotiable — then starts a **matching run**, reviews the proposal, and publishes. Published matches become **strands**: one-to-one or group relationships with messaging, milestones and progress tracking.

**The design decision that defines the project.** Braid began as compatibility-based mentor *discovery*: browse recommended mentors, request one. During design we concluded that discovery reproduces the original inequity. Browsing rewards confidence, free time, and knowing what to look for — the very advantages the target user lacks. We changed the model to **cohort-wide allocation with coordinator review**, so the person who most needs a mentor does not have to know how to go looking for one.

**The matching engine** runs in five separated stages, each independently inspectable:

- **Normalisation** projects form answers into a fixed typed shape, so an arbitrary form structure never reaches matching, reporting or export.
- **Eligibility** applies hard constraints — role compatibility, shared skill, a three-hour timezone band, conflict-of-interest separation. A failing pair is removed entirely rather than scored low, because a heavy weight can be overridden by a strong score elsewhere and a hard constraint cannot.
- **Fit** scores pair quality 0–1 across coordinator-weighted fields, using Jaccard overlap for options and closeness for numeric answers, with each field marked `similar` or `complementary`. The total divides by the weight *actually used*, so no pair is penalised for questions neither person was asked.
- **Priority** scores how much difference the structured route makes to a given mentee, from fields flagged `equity`. This is deliberately not merit and not charity: a woman with two mentors and a strong network loses less by waiting a round than one with neither, so the same mentor hour produces more for the second. Kept strictly separate from fit — merging them makes outcomes unexplainable.
- **Global assignment** builds a cost matrix over every eligible pair and solves the whole cohort at once via the Hungarian algorithm (`scipy.optimize.linear_sum_assignment`), subject to capacity caps, a coverage floor, and bounded priority weighting.

That last stage is the substantive contribution. Greedy matching — walk the list, assign each mentee her best available mentor — makes a locally sensible choice every time and produces a worse cohort, because early picks consume options later mentees needed more. Solving globally avoids that. The engineering is a well-understood problem class; **the objective function is where the argument sits.** Maximising a plain sum always permits sacrificing the tail, and the tail is exactly who the project is for — hence the coverage floor and the priority term.

**Equity is an input, not a report.** Priority enters the function the solver minimises. The review screen shows coverage, mentor load against capacity, and match quality *per priority band* **above** the pair list, because a list of names hides whether a run was fair and a single average cannot answer the question either. Demographic reporting counts only participants who gave explicit consent and suppresses any group of three or fewer, stating how many were withheld — a fairness dashboard that re-identifies the two women in a cohort has protected nobody.

**A human publishes.** Draft matches are reversible and nothing reaches a participant until a coordinator presses publish. Mentorship is a human relationship; the algorithm supports the decision rather than making it.

## 3. Implementation

**Approach.** Agile MVP delivery over four weeks, 15 July – 14 August 2026, in five phases: initiation and discovery; product and system design; platform development; testing and optimisation; demonstration and delivery. Governance used a full WBS, RACI matrix, Gantt chart and a 12-item risk register, all included in this folder.

**Cross-functional contribution.** Project Management owned planning, requirements and testing oversight. Data Analytics owned compatibility factors, the scoring model and evaluation metrics. Cybersecurity owned authentication, privacy, access control and security review. IT Automation with Python owned the full-stack build — backend and frontend, APIs, matching engine and integration.

**Architecture.** A monorepo with a single OpenAPI contract read by both sides: FastAPI, SQLAlchemy, Alembic and PostgreSQL on the backend with NumPy and SciPy for matching; Next.js, TypeScript, Tailwind and React Query on the frontend. Frontend types are generated from the contract, so client and server cannot drift. Role lives on participation rather than account, because the same person is a mentee in one programme and a mentor in another.

The hardest constraint was that **the application form is unknown when the code is written.** The solution is dynamic at the edge, fixed at the core: forms are versioned JSON with stable per-question identifiers, so renaming a question does not orphan existing answers; publishing creates a new version and submitted applications keep the version they answered; normalisation then projects flagged fields into a fixed typed table that everything downstream reads.

**Delivered.** All 60 operations in the contract are implemented against the real backend — 49 paths, 33 frontend pages, 54 Python modules. Type checking, ESLint and Ruff all pass clean. An end-to-end run on a seeded 22-participant cohort produced 9 matches at 64.3% coverage with the fairness summary populated across all three priority bands, published successfully to the participant side.

One validation finding is worth recording. The fairness panel showed a mentor at load 4 against capacity 3. Investigation confirmed the run assigned her **zero** new mentees; the excess was pre-existing seed data and the capacity clamp had correctly reduced her remaining places to zero. The engine refused to over-assign. Coverage below 100% is likewise correct behaviour — it reflects real mentor scarcity, and those mentees enter an unmatched queue with reason codes rather than being force-matched to someone unsuitable.

**Known limitations**, stated plainly: there is no skill taxonomy yet, so the shared-skill constraint compares raw strings and a hyphen can prevent a valid match; sessions carry no dates and check-ins are messages rather than recorded answers, so both are reported as empty with an on-page explanation rather than filled with plausible-looking charts; there is no upload endpoint or mail provider; and the system is validated at cohort scale, not load-tested. The charter's 50% administrative-reduction target is an objective, not a measured result — verifying it requires a live programme.

**Next.** A canonical skill taxonomy with a coordinator review queue is the highest-value improvement, followed by dated sessions, structured check-ins, and swap/lock/re-run controls on the review screen.

---

**References.** GSMA (2026) *The mobile gender gap report 2026*; UNESCO (2025) *Closing the digital divide for women and girls in Africa through education*; UN OSAA (2026) *The power of mentorship*; World Bank (n.d.) *Africa Gender Innovation Lab*.
