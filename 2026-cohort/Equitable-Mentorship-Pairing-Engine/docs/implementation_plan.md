# Implementation Plan — Equitable Mentorship Pairing Engine

## Goal
Move from analysis + prototype to a pilot-ready tool a real mentorship program (starting with MMC itself) could run.

## Phased timeline

**Phase 1 — Foundation (Weeks 1-2)**
- Replace inferred-gender fields with a short, optional, self-reported intake form (name, skills, seniority, goals, gender — optional)
- Finalize the scoring weights in `matching_engine.py` against a small real pilot group instead of synthetic data
- Resources: 1 data analyst (weight tuning), 1 Python dev (form + data pipeline)

**Phase 2 — Pilot (Weeks 3-6)**
- Run the engine on one live cohort (e.g., the next MMC intake) alongside the existing informal matching process, without replacing it yet
- Track match outcomes and the equity summary output over the pilot period
- Resources: program coordinator access, 20-30 real mentor/mentee intake records

**Phase 3 — Tool hardening (Weeks 7-10)**
- Wrap the script in a lightweight interface (CLI or simple web form) so a non-technical coordinator can run it — natural extension of the current prototype
- Add basic validation (duplicate detection, missing-field handling)
- Resources: 1 Python/IT automation dev (Lauren's track)

**Phase 4 — Evaluation & handoff (Weeks 11-12)**
- Compare pilot-matched pairs against historically informal-matched pairs on the same equity metrics used in our analysis (mentor gender distribution, pairing skew)
- Document results and hand off to MMC or another sponsoring program for adoption decision

## Resources needed
- Program coordinator time to collect real intake data and run pilot cohort
- 1-2 developers to harden the script into a usable tool (Phase 3)
- No paid infrastructure required — runs locally on CSV input; can move to a simple hosted form later if adopted

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Low pilot participation / small sample size | Start with one cohort, not the full program; treat Phase 2 as directional, not conclusive |
| Self-reported gender field seen as intrusive or skipped | Make it explicitly optional; the engine works without it — gender is only used for the equity summary, never for matching |
| Scoring weights don't generalize outside academic mentorship data they were validated on | Re-tune weights against real pilot outcomes in Phase 1/2 rather than trusting the synthetic-data defaults long-term |
| Manual matching stays "easier" so the tool doesn't get adopted | Position Phase 2 as parallel-run, not replacement — let the equity summary make the case for itself before asking anyone to switch processes |
| Team members' availability after this cohort program ends | Document the handoff clearly (Phase 4) so the tool survives past the BUILD stage even if the team disbands |

## Success metrics
- Reduction in man→man / woman→woman pairing skew vs. the 36.95% / 11.54% baseline from our analysis
- Increase in women mentors matched relative to the 21.21% baseline
- Coordinator time-to-match decreases vs. informal process
