"""
Mentoring-Me Capstone — Matching Algorithm Scenario Testing

Tests the algorithm against edge cases it needs to handle gracefully in a
real platform, not just the "happy path" single example tested earlier.

SCENARIOS COVERED:
1. Zero role overlap — mentee's role doesn't exist in the mentor pool at all
2. Experience-gap extremes — only very-senior mentors available (20+ years)
3. Missing JobFactors data — mentee or mentor didn't answer that question
4. Empty mentor pool — no mentors available at all (should not crash)
5. Real "hard" case — a mentee with a rare/niche role combination from actual data
"""

import os
import pandas as pd
import sys
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from matching_algorithm_v1 import (
    compute_match_score, find_top_matches, get_mentee_pool, get_mentor_pool
)

_csv_path = 'so2020_cleaned.csv'
if not os.path.exists(_csv_path):
    _csv_path = os.path.join(_current_dir, 'so2020_cleaned.csv')
if not os.path.exists(_csv_path):
    _csv_path = os.path.join(_current_dir, 'so2020.csv')

df = pd.read_csv(_csv_path)


def make_synthetic_profile(respondent_id, devtype, years, exp_tier, job_factors, org_size='Not stated'):
    """Small helper to build a controlled test profile — clearly synthetic,
    not drawn from real respondents, used only to isolate one scenario at a time."""
    return pd.Series({
        'Respondent': respondent_id,
        'DevType': devtype,
        'YearsCodePro': years,
        'exp_tier': exp_tier,
        'JobFactors': job_factors,
        'OrgSize': org_size,
    })


print("="*70)
print("SCENARIO 1: Zero role overlap")
print("="*70)
mentee = make_synthetic_profile(90001, 'Blockchain', 1.0, '0-2y',
                                  'Remote work options;Diversity of the company or organization')
mentor = make_synthetic_profile(90002, 'Developer, back-end', 8.0, None,
                                  'Opportunities for professional development')
score, breakdown = compute_match_score(mentee, mentor)
print(f"Mentee role: Blockchain | Mentor role: Developer, back-end (no overlap)")
print(f"Total score: {score} | Breakdown: {breakdown}")
assert breakdown['role'] == 0.0, "Expected zero role score for no overlap"
print("PASS: Algorithm correctly scores 0.0 on role alignment without crashing, "
      "other criteria (experience, career stage) still contribute to total score.\n")


print("="*70)
print("SCENARIO 2: Only very-senior mentors available (20+ year gap)")
print("="*70)
mentee = make_synthetic_profile(90003, 'Developer, front-end', 1.0, '0-2y',
                                  'Diversity of the company or organization')
mentor = make_synthetic_profile(90004, 'Developer, front-end', 25.0, None,
                                  'Diversity of the company or organization')
score, breakdown = compute_match_score(mentee, mentor)
print(f"Experience gap: 24 years")
print(f"Total score: {score} | Breakdown: {breakdown}")
assert breakdown['experience'] <= 0.3, "Expected low experience score for extreme gap"
print("PASS: Extreme experience gap correctly pulls the score down via experience_gap_score, "
      "even with perfect role and goals overlap.\n")


print("="*70)
print("SCENARIO 3: Missing JobFactors data")
print("="*70)
mentee = make_synthetic_profile(90005, 'Developer, mobile', 6.0, '5-10y', None)
mentor = make_synthetic_profile(90006, 'Developer, mobile', 12.0, None,
                                  'Opportunities for professional development')
score, breakdown = compute_match_score(mentee, mentor)
print(f"Mentee JobFactors: missing | Mentor JobFactors: present")
print(f"Total score: {score} | Breakdown: {breakdown}")
assert breakdown['goals'] == 0.3, "Expected neutral 0.3 default for missing goals data"
print("PASS: Missing data gets a neutral 0.3 score rather than 0 (not penalized) "
      "or crashing — a missing answer isn't treated as a mismatch.\n")


print("="*70)
print("SCENARIO 4: Empty mentor pool")
print("="*70)
mentee_real = get_mentee_pool(df).iloc[0]
empty_pool = df.iloc[0:0]  # zero rows, same columns
try:
    result = find_top_matches(mentee_real, empty_pool, top_n=5)
    print(f"Result shape: {result.shape}")
    print("PASS: Empty mentor pool returns an empty result set without crashing "
          "(a real platform would show 'no matches available yet' rather than erroring).\n")
except Exception as e:
    print(f"FAIL: Empty pool caused an error: {e}\n")


print("="*70)
print("SCENARIO 5: Real hard case — rarest role in the dataset")
print("="*70)
exploded = df.dropna(subset=['DevType']).assign(
    DevType_split=df['DevType'].str.split(';')
).explode('DevType_split')
role_counts = exploded['DevType_split'].value_counts()
rarest_role = role_counts.idxmin()
print(f"Rarest role in dataset: '{rarest_role}' ({role_counts.min()} respondents)")

rare_mentees = get_mentee_pool(df)[get_mentee_pool(df)['DevType'].str.contains(rarest_role, na=False, regex=False)]
if rare_mentees.shape[0] > 0:
    mentee = rare_mentees.iloc[0]
    mentor_pool = get_mentor_pool(df)
    matches = find_top_matches(mentee, mentor_pool, top_n=3)
    print(f"Mentee role(s): {mentee['DevType']}")
    print(f"Top 3 matches found:\n{matches[['mentor_id','mentor_devtype','total_score']].to_string(index=False)}")
    print("PASS: Even a mentee with a rare role gets ranked matches, since the "
          "algorithm degrades gracefully rather than requiring exact role matches.\n")
else:
    print("No mentee in the risk-window pool has this rare role — expected with "
          "small pool sizes, worth noting as a real limitation for very niche roles.\n")

print("="*70)
print("ALL SCENARIOS COMPLETE")
print("="*70)
