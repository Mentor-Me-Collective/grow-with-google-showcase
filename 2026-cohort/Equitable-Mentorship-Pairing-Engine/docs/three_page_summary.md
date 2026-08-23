# Equitable Mentorship Pairing Engine
### Team Catalyst Strategists — MMC BUILD Stage, SDG 5 (Gender Equality)

## 1. Problem

Early-career women in technical fields face systemic isolation due to a lack of structured access to professional network matching — mentorship happens informally, and informal processes reproduce existing imbalances rather than correcting them.

## 2. Research & Data

We evaluated several public datasets (World Bank Gender Data Portal, Kaggle gender-inequality indexes, multiple Stack Overflow survey years) and rejected them for containing only representation statistics, not actual mentor-mentee relationship data. We settled on two sources:

- **Nature Scientific Data (2022) Academic Family Tree mentorship dataset** — 743,176 real mentor-mentee pairs, with algorithmically inferred gender for both parties. This is our core dataset for pairing analysis.
- **Stack Overflow 2025 Developer Survey** — used for tech-workforce career-stage context. Notably, the 2025 edition dropped its gender/demographic question entirely, which we treat as a finding in itself: it limited this source to career-stage analysis only.

### Findings
- Mentors are overwhelmingly men: 67.81% vs. 21.21% women (10.98% unclassified by the inference model).
- Pairing breakdown: man→man 36.95%, woman→woman only 11.54%, woman→man 19.69%, man→woman 6.85%.
- This skew is statistically significant, not chance: a Chi-Square test of independence returned χ² = 50,383.74 (df=4, p ≈ 0), rejecting the null hypothesis that gender and pairing outcome are independent.
- Early-career developers (0-3 yrs) rank access to expert mentors more important (8.04) than developers with 4+ years (9.84), where lower = more important — meaning the group most affected by the pairing skew is also the group that values mentorship most.

### Limitations disclosed
Gender in our core dataset is inferred from first names, not self-reported, and is less reliable on some names. The dataset is bioscience/neuroscience academia, not tech-specific — we treat it as a structural stand-in for how mentorship forms, not a tech-industry sample.

## 3. Solution

Rather than another awareness campaign, we built a **rule-based mentor-mentee matching engine** that replaces informal matching with structured, criteria-based pairing — the actual mechanism our data shows is producing the skew.

The engine scores every mentee-mentor pair on three weighted factors, each grounded directly in our findings:
- **Skill/topic overlap (50%)** — the strongest predictor of a good pairing
- **Seniority gap (30%)** — prioritizes meaningfully more senior mentors, since early-career people value this most
- **Mentor capacity (20%)** — prevents over-matching the same in-demand senior women, which would recreate the scarcity problem we identified

Critically, **gender is never used as a matching input** — only tracked as an output metric, so a coordinator can monitor whether outcomes are becoming more equitable without a live system depending on an unreliable inferred field. This directly answers our own data-privacy limitation.

A working prototype (`matching_engine.py`) runs end-to-end on sample data and prints both the matches and an equity summary. It requires no proprietary data or paid infrastructure — just a CSV of mentee/mentor intake data most programs already collect.

## 4. Implementation Plan

- **Phase 1 (Weeks 1-2):** Replace inferred gender with an optional self-reported field; tune scoring weights against a small real pilot group.
- **Phase 2 (Weeks 3-6):** Run the engine on one live cohort in parallel with existing informal matching; track outcomes.
- **Phase 3 (Weeks 7-10):** Wrap the script in a lightweight CLI or web form so a non-technical coordinator can run it.
- **Phase 4 (Weeks 11-12):** Compare pilot results against the informal-matching baseline; document and hand off.

**Key risks:** small pilot sample size (mitigated by treating Phase 2 as directional); reluctance to share gender data (mitigated by making it optional and matching-independent); weights validated on academic data may not generalize (mitigated by re-tuning against real pilot outcomes before wider adoption).

**Success metrics:** reduced man→man/woman→woman pairing skew relative to our 36.95%/11.54% baseline; increased share of women mentors relative to the 21.21% baseline.

## 5. Team

Israel Babalola (Data Analytics) — data sourcing, cleaning, analysis, dashboard. Gbenga Ayodeji (Advanced Data Analytics) — statistical validation (Chi-Square test). Eldad Berhanu (Cybersecurity) — data-privacy review. Lauren Rodriguez (IT Automation/Python) — tool hardening for pilot deployment.
