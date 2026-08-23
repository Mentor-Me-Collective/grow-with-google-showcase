# Equitable Mentorship Pairing Engine
### Team Catalyst Strategists — SDG 5: Gender Equality

## Problem Statement
Early-career women in technical fields face systemic isolation due to a
lack of structured access to professional network matching.

## Solution Summary
We analyzed 743,000+ real mentor-mentee pairs and found the pairing gap
is statistically significant, not random (Chi-Square p ≈ 0). In response,
we built a rule-based matching engine that scores mentee-mentor pairs on
skill overlap, seniority gap, and mentor capacity — replacing informal
matching with structured pairing. Gender is tracked only as an output
metric, never used as a matching input.

See `docs/three_page_summary.md` for the full write-up and
`docs/implementation_plan.md` for the rollout plan.

## How to Run
```bash
cd src
python matching_engine.py sample_mentees.csv sample_mentors.csv
```

## Video Walkthrough
🎥 [Watch the 5-minute walkthrough](https://drive.google.com/file/d/18fcxdS8UqP1PByCkSDSmnylo3npE2x91/view?usp=drive_link)

## Team
Israel Babalola, Gbenga Ayodeji, Eldad Berhanu, Lauren Rodriguez
