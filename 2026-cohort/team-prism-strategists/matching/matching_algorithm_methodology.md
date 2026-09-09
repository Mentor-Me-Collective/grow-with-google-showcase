# Mentoring-Me — Matching Algorithm & Methodology

## 1. Research: Approaches Considered

Three broad approaches were evaluated before selecting a method:

| Approach | How it works | Suitability for this project |
|---|---|---|
| **Collaborative filtering** | Learns from historical match outcomes ("mentees like you succeeded with mentors like this") | Not viable — no historical mentorship-outcome data exists to learn from (a cold-start problem) |
| **ML classification/regression** | Trains a model to predict match success from labeled examples | Not viable for the same reason — no labeled "this match worked" data is available at this stage |
| **Rule-based weighted scoring** | Defines explicit criteria, assigns weights, computes a transparent score per mentor-mentee pair | **Selected.** Requires no historical data, produces an explainable score a reviewer or user can audit, and can be tuned directly as new evidence becomes available |

A content-based similarity measure (Jaccard overlap) was used *within* the weighted model for multi-select fields (role, job priorities), rather than as a standalone method — this combines the interpretability of rule-based scoring with a principled way to compare categorical, multi-valued profile data.

## 2. Matching Criteria and Weighted Scoring Model

Criteria were not chosen arbitrarily — each is grounded directly in a finding from the Objective 1 data analysis.

| Criterion | Weight | Basis in Objective 1 findings |
|---|---|---|
| Role/skill alignment | 30% | The representation gap is role-specific, not uniform across tech (Chart 1) — DevOps, sysadmin, and embedded roles show the widest gaps, so role-accurate matching matters more than generic "tech" matching |
| Experience gap | 25% | The pipeline breaks at specific tenure transitions (Chart 2), not gradually — a mentor 2-10 years ahead is more relatable and realistic than a purely maximal seniority gap |
| Career-stage priority | 20% | Retention risk has two distinct peaks, at 0-2y and 5-10y (Chart 3) — mentees in these windows are prioritized over lower-risk tenure bands |
| Goals/values alignment | 15% | Women and men show measurable differences in job priorities, particularly around workplace diversity signals (Chart 5) — overlap here reflects genuine stated compatibility, not assumption |
| Practical fit | 10% | Lower weight — logistics (organization size) matter but should not override substantive fit |

**Scoring mechanics:**
- Role and goals alignment use **Jaccard similarity** (intersection ÷ union) over multi-select survey fields, so partial overlap is rewarded rather than requiring an exact match
- Experience gap uses a **peaked scoring function**: a 2-10 year gap scores 1.0, extending outward penalizes gaps that are too small (insufficient seniority to mentor) or too large (over 15 years, likely less relatable/available)
- Career-stage priority uses a **direct lookup** against the two empirically-identified risk windows
- All five component scores are combined via `total = Σ(component_score × weight)`, producing one number between 0 and 1

## 3. Data Used to Build and Test the Algorithm

**Important limitation, stated explicitly:** no public dataset labels individuals as "mentor" or "mentee" — this field does not exist anywhere. The Stack Overflow 2020 Developer Survey (49,294 cleaned respondents; see Data Analytics section) was used to generate **synthetic candidate profiles** for testing the algorithm's logic prior to real platform data existing. This mirrors the "limited availability of real mentorship datasets" risk identified in the project brief.

- **Synthetic mentee pool:** women in the two high-retention-risk experience tiers (0-2y, 5-10y) — 1,495 profiles
- **Synthetic mentor pool:** respondents with 5+ years of professional experience, used as a testing proxy — 24,413 profiles

In production, both pools would instead be built from explicit user self-selection at sign-up ("I want a mentor" / "I want to be a mentor"). The scoring logic itself does not change — only the data source would.

## 4. Testing and Refinement

Five scenarios were used to stress-test the algorithm against realistic edge cases, not just a single favorable example:

| Scenario | Result |
|---|---|
| Zero role overlap between mentee and mentor | Score correctly degrades (0.5) rather than zeroing out entirely — other criteria still contribute |
| Extreme experience gap (24 years) | Correctly penalized (experience component drops to 0.3) even with perfect role/goals alignment |
| Missing goals data (`JobFactors` unanswered) | Assigned a neutral default (0.3) rather than penalized as a mismatch or causing an error |
| **Empty mentor pool** | **A genuine bug was found**: the algorithm crashed with a `KeyError` on `total_score` when no mentors were available. Fixed to return a clean empty result instead. |
| Real respondent with a rare role combination | Still produced ranked, sensible matches — the algorithm degrades gracefully on genuinely thin real data, not just synthetic edge cases |

A **tie-breaker rule** was also added: when total scores tie (common with categorical multi-select fields, since many respondents share standard combinations), the mentor with the smaller experience gap is ranked first, making results deterministic rather than arbitrary.

All scenarios were re-run after each change to confirm fixes worked and no prior behavior regressed.

## 5. Evaluation

Because no historical match-outcome data exists, "accuracy" was evaluated operationally along three dimensions, using a sample of 100 real synthetic mentee profiles:

**a) Algorithm vs. random baseline** — the strongest evidence of validity, since it isolates the weighting scheme's actual contribution:
- Mean top-match score (weighted algorithm): **0.921**
- Mean score of a randomly assigned mentor: **0.510**
- **Improvement over random: 80.6%**

**b) Coverage and match quality at realistic scale** — the full synthetic pool (24,413 mentors) produced 100% "Strong" matches, but this is an artifact of pool size, not evidence of algorithm quality on its own. Re-testing against a realistic early-platform pool size (50 mentors) gave a more honest picture:

| Mentor pool size | Strong | Good | Fair/Weak |
|---|---|---|---|
| 50 (realistic, early-platform) | 63% | 37% | 0% |
| 24,413 (synthetic, unrealistic) | 100% | 0% | 0% |

No mentee received a Fair or Weak match even at the thin pool size — the algorithm degrades gracefully under scarcity rather than producing poor matches, but match *quality* at launch will be bottlenecked by mentor supply rather than by the matching logic itself. This is a concrete, evidence-based product recommendation: **an active mentor-recruitment strategy is a prerequisite for match quality, not a separate concern from the algorithm.**

**c) Score distribution** — median 0.925, standard deviation 0.063 across the full-scale test, confirming scores are discriminating between candidates rather than clustering uninformatively at one value.

## 6. Improvement: Match Quality Transparency

Evaluation revealed that the algorithm always returns a "top match" regardless of how weak it is — a 0.45 in a thin pool and a 0.95 in a rich pool would look identical in format. Two additions address this directly:

- **`match_quality_label()`** — converts raw scores into interpretable tiers (Strong ≥0.7, Good ≥0.55, Fair ≥0.4, Weak <0.4)
- **`get_match_recommendation()`** — the production entry point, which attaches quality labels and, when the best available match falls below the "Strong" threshold, returns an honest message explaining the likely cause (limited mentor pool for that specific role/tenure) with a concrete next step, rather than silently presenting a weak match as if it were confident

This was a direct, evidence-driven refinement — not a generic feature addition — made in response to the pool-size sensitivity found during evaluation.

## 7. Limitations

- **No ground-truth validation is possible yet.** Without historical match-outcome data, "accuracy" is necessarily proxy-based (baseline comparison, coverage, distribution) rather than a measure of whether matches actually succeed in practice.
- **Synthetic mentor/mentee pools are a testing stand-in**, not real platform data. Real self-selected sign-up data may differ meaningfully in composition from a general developer survey.
- **Compensation was tested and excluded** as a matching criterion; its direction was inconsistent across datasets during the Objective 1 analysis and was judged too unreliable to weight in the algorithm.
- **Weights (30/25/20/15/10%) were set based on the strength of evidence in Objective 1, not through formal optimization** (e.g. grid search against labeled outcomes) — appropriate given the absence of outcome data, but worth revisiting once real usage data exists.

## 8. Future Work

Once the platform has real mentor sign-ups and, eventually, match-outcome data (satisfaction ratings, continued engagement), the rule-based model could be extended with a collaborative-filtering or supervised-learning layer trained on that outcome data — the weighted scoring model here would remain a strong, explainable baseline to compare any future model against.

## 9. Direct LinkedIn Deep Link Generator: Zero-Dependency External Discovery

### What is the Direct LinkedIn Deep Link Generator?
A **LinkedIn Deep Link** is a dynamically constructed URL that opens LinkedIn’s official search engine with pre-filled, Boolean-optimized filters based on a mentee’s exact profile attributes and goals (*Target Role, Country, Skills, Seniority, and Mentorship keywords*).

Instead of relying on fragile, rate-limited, or deprecated third-party search APIs (or scrapers that risk violating terms of service), the system generates a smart, one-click deep link that takes the user directly to live, matching mentor candidates across LinkedIn’s global network of 1B+ professionals.

### Key Architectural Advantages
1. **Resilience & Zero Deprecation Risk**: Avoids reliance on third-party APIs (e.g. Proxycurl, Google Custom Search API quotas) that can be deprecated, blocked, or altered.
2. **Real-Time Global Reach**: Taps directly into live, active LinkedIn member data rather than cached or static datasets.
3. **Boolean Search Precision**: Translates mentee profile preferences into structured Boolean search syntax (`AND`, `OR`, quoted phrases, location scoping, seniority keywords, and mentorship tokens).
4. **SDG 5 Equity & Representation**: Supports an optional Women in Tech / Diversity mode (`"women in tech" OR "female leader" OR "women who code"`) to connect early-career women with senior female mentors and leaders.
5. **Integrated Outreach Crafter**: Provides character-counted LinkedIn Connection Notes (strictly `<= 300` characters to adhere to LinkedIn's connection request limits) and InMail/direct message templates for high-conversion outreach.

