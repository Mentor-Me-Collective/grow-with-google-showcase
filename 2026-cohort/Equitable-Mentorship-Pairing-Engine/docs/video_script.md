# Video Walkthrough Script (target: 5 minutes)

**Format note:** record as a screen-share — Kaggle notebook, Tableau dashboard, and `matching_engine.py` running live. Assign parts to whoever's available; solo delivery works fine too. Timings are guides, not hard cuts.

---

### 1. Problem + team (0:00-0:45)
"We're Catalyst Strategists, working on SDG 5, Gender Equality. Our problem statement: early-career women in technical fields face systemic isolation due to a lack of structured access to professional network matching. Our team — [names + tracks] — split the work across data analysis, statistical validation, privacy review, and tooling."

### 2. Data & findings (0:45-2:00)
*[Screen: Kaggle notebook]*
"We grounded this in real data — 743,000+ real mentor-mentee pairs from an academic mentorship dataset, plus Stack Overflow's 2025 developer survey for career-stage context.

Three findings drove everything after this. One: mentors are overwhelmingly men — 68% versus 21% women. Two: this isn't random — a Chi-Square test confirms the pairing skew is statistically significant. Three: early-career developers value mentor access more than experienced ones — so the group most affected by the skew is the group that needs it most."

*[Screen: Tableau dashboard]*
"Here's that visualized — [briefly point at the three charts]."

### 3. Solution (2:00-3:30)
*[Screen: matching_engine.py running in terminal]*
"Instead of another awareness campaign, we built something that removes the informal matching step our data shows is causing the skew — a rule-based matching engine.

It scores every possible mentee-mentor pair on three factors pulled straight from our findings: skill overlap, seniority gap, and mentor capacity. Here it is running on sample data — [run the script live] — it outputs ranked matches and, importantly, an equity summary. Gender is never a matching input, only a tracked output — because our own data showed the gender field in typical datasets is inferred, not reliable enough to build matching logic on."

### 4. Implementation plan (3:30-4:30)
"This isn't just a demo. Our four-phase plan takes it from prototype to pilot: first, swap inferred gender for an optional self-reported field and tune the model on real data. Second, run it alongside a live cohort's existing process, not replacing it yet. Third, wrap it in a simple interface a coordinator can actually use. Fourth, measure results against the informal-matching baseline and hand it off.

Our main risks — small pilot samples, reluctance to share gender data, weights that don't generalize past academic data — each have a direct mitigation in the plan."

### 5. Close (4:30-5:00)
"That's Problem Grounding through real statistically-validated data, a working Solution that acts on our own findings, and an Implementation Plan to take it further. Everything — notebook, dashboard, engine code, and docs — is in this branch. Thanks for watching."

---

**Before recording:** cut anything if you're running long — Section 3 (Solution) is the one to protect, since it's the heaviest-weighted rubric category and the one you're proving exists for the first time on camera.
