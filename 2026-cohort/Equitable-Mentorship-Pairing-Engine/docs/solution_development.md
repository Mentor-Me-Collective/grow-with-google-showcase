# Solution Development — Equitable Mentorship Pairing Engine

## The problem this solves
Our data showed the skew isn't random: man→man pairings dominate (36.95%), woman→woman pairings are rare (11.54%), and the gap is statistically significant (χ² = 50,383.74, p ≈ 0). Informal, organic mentor-matching reproduces this pattern. The fix isn't "raise awareness" — it's removing the informal matching step entirely and replacing it with structured, criteria-based pairing.

## What we built
A rule-based mentor-mentee matching engine (`matching_engine.py`) that scores every possible mentor-mentee pair on three weighted factors, drawn directly from our findings:

| Factor | Weight | Why (grounded in our data) |
|---|---|---|
| Skill/topic overlap | 50% | Successful real-world pairs in our dataset cluster around shared research area — we treat this as the strongest predictor of a good match |
| Seniority gap | 30% | Our findings show early-career people rank mentor access highest (8.04 vs 9.84) — the engine prioritizes pairing juniors with meaningfully more senior mentors, not peers |
| Mentor availability/capacity | 20% | Prevents the same in-demand senior women from being over-matched, which would recreate the scarcity problem our data identified |

The engine deliberately does **not** use gender as a matching input. It's tracked only as an output metric — so the team (or a real deployment) can monitor whether pairing outcomes are becoming more equitable over time without letting gender drive who gets matched to whom. This directly answers our own limitation: the source dataset's *inferred* gender field has documented misclassification issues, so we don't want a live system depending on it for matching logic — only for measurement.

## How it works
1. Input: a CSV of mentees and a CSV of mentors, each with `id, name, skills (comma-separated), seniority_level (1-5), gender (optional, self-reported), capacity`
2. For every mentee, the engine scores all mentors with available capacity using the weighted formula above
3. Outputs the top-ranked mentor for each mentee, plus a full score matrix for manual review
4. Prints an equity summary: gender distribution of the resulting matches, so a program coordinator can see the outcome without gender being a matching input

## Why this is sustainable, not just a demo
- No proprietary data or paid API — runs on any CSV a program already collects during intake
- Self-reported fields only (per our own recommendation against inferred demographics)
- Capacity-aware, so it doesn't burn out the same few senior mentors
- The scoring weights are constants at the top of the script — a real program can tune them without touching logic

## Status and next step
This is a working MVP proving the matching logic end-to-end on synthetic data (see `sample_mentors.csv` / `sample_mentees.csv`). Lauren (IT Automation, Python) is best positioned to take this from script to a small runnable tool — e.g., a CLI or lightweight web form — before a real deployment, per the team's original role split.
