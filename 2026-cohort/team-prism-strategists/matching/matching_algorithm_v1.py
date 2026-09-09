"""
Mentoring-Me Capstone — Matching Algorithm & Methodology
Weighted Scoring Model v1

APPROACH: Rule-based weighted scoring (see research notes in report — chosen
over collaborative filtering / ML classification because there is no
historical match-outcome data to learn from, and a transparent, explainable
score is more defensible for a capstone review than a black-box model).

IMPORTANT — ON THE MENTOR/MENTEE DATA USED HERE:
No public dataset labels anyone as a "mentor" or "mentee" — that field does
not exist anywhere. The Stack Overflow 2020 survey is being used here purely
as a source of SYNTHETIC CANDIDATE PROFILES to test the algorithm's logic
before real platform data exists (this mirrors the "limited availability of
real mentorship datasets" risk named in the capstone brief). The "mentor
pool" below is built with a simple proxy rule (YearsCodePro >= 5) — this is
an assumption made for testing purposes only, NOT a claim that these
respondents are actual mentors. In the real platform, mentor/mentee pools
would come from explicit self-selection at sign-up ("I want a mentor" /
"I want to be a mentor"), not an experience-level filter. The scoring logic
itself (role overlap, experience gap, career-stage priority, goals
alignment) is designed to work identically once real self-selected data
replaces this synthetic pool — only the data source changes.

CRITERIA AND WEIGHTS (grounded in Objective 1 findings):
1. Role/skill alignment       — 30%  (Chart 1: gap is role-specific, not generic)
2. Experience gap             — 25%  (Chart 2: pipeline breaks matter more than raw seniority)
3. Career-stage priority      — 20%  (Chart 3: two retention-risk windows, 0-2y and 5-10y)
4. Goals/values alignment     — 15%  (Chart 5: JobFactors overlap reflects real stated priorities)
5. Practical fit              — 10%  (org size / logistics — lower weight, secondary to substance)
"""

import os
import pandas as pd
import numpy as np

# ===========================================================
# STEP 1: Load real profiles from the cleaned dataset (robust path lookup)
# ===========================================================
_base_dir = os.path.dirname(os.path.abspath(__file__))
_candidate_paths = [
    os.path.join(_base_dir, 'so2020_cleaned.csv'),
    os.path.join(_base_dir, '..', 'data', 'so2020_cleaned.csv'),
    os.path.join(_base_dir, '..', 'so2020_cleaned.csv'),
    'so2020_cleaned.csv'
]

df = pd.DataFrame()
for _p in _candidate_paths:
    if os.path.exists(_p):
        try:
            df = pd.read_csv(_p)
            break
        except Exception:
            pass

def get_mentee_pool(df):
    """
    SYNTHETIC mentee pool for testing: women in the two high-retention-risk
    windows identified in Objective 1 (0-2y, 5-10y). In production this
    pool would be built from platform sign-ups where users self-select
    "I want a mentor" — not derived from survey data.
    """
    return df[(df['Gender'] == 'Woman') & (df['exp_tier'].isin(['0-2y', '5-10y']))].dropna(subset=['DevType'])

def get_mentor_pool(df):
    """
    SYNTHETIC mentor pool for testing: proxy rule of 5+ years experience,
    NOT a claim that these respondents are actual mentors. In production
    this pool would come from users self-selecting "I want to be a mentor"
    at sign-up.
    """
    return df[df['YearsCodePro'] >= 5].dropna(subset=['DevType'])


# ===========================================================
# STEP 2: Scoring functions for each criterion
# ===========================================================

def role_alignment_score(mentee_devtype, mentor_devtype):
    """Jaccard overlap between the two multi-select DevType sets. 0-1 scale."""
    mentee_roles = set(mentee_devtype.split(';'))
    mentor_roles = set(mentor_devtype.split(';'))
    if not mentee_roles or not mentor_roles:
        return 0.0
    intersection = len(mentee_roles & mentor_roles)
    union = len(mentee_roles | mentor_roles)
    return intersection / union if union > 0 else 0.0


def experience_gap_score(mentee_years, mentor_years):
    """
    Peaks at a 3-10 year gap (meaningfully senior but still relatable).
    Too small a gap = not enough to teach. Too large = less relatable/available.
    Returns 0-1.
    """
    gap = mentor_years - mentee_years
    if gap < 2:
        return 0.2  # not enough seniority difference
    elif 2 <= gap <= 10:
        return 1.0  # ideal range
    elif 10 < gap <= 15:
        return 0.6  # still useful, less relatable
    else:
        return 0.3  # very large gap, may feel distant


def career_stage_priority_score(mentee_exp_tier):
    """
    Weight based on retention-risk findings (Chart 3): 0-2y and 5-10y are
    the two vulnerable windows and get the highest priority score.
    """
    priority_map = {
        '0-2y': 1.0,
        '5-10y': 0.9,
        '2-5y': 0.5,
        '10-20y': 0.3,
        '20y+': 0.2,
    }
    return priority_map.get(mentee_exp_tier, 0.3)


def goals_alignment_score(mentee_factors, mentor_factors):
    """Jaccard overlap between JobFactors selections. 0-1 scale."""
    if pd.isna(mentee_factors) or pd.isna(mentor_factors):
        return 0.3  # neutral default when data is missing, not zero (don't penalize missingness)
    mentee_set = set(mentee_factors.split(';'))
    mentor_set = set(mentor_factors.split(';'))
    if not mentee_set or not mentor_set:
        return 0.3
    intersection = len(mentee_set & mentor_set)
    union = len(mentee_set | mentor_set)
    return intersection / union if union > 0 else 0.3


def practical_fit_score(mentee_org, mentor_org):
    """Same org-size bracket = more relatable day-to-day work context."""
    if pd.isna(mentee_org) or pd.isna(mentor_org) or mentee_org == 'Not stated' or mentor_org == 'Not stated':
        return 0.5  # neutral default
    return 1.0 if mentee_org == mentor_org else 0.4


# ===========================================================
# STEP 3: Combine into the weighted match score
# ===========================================================
WEIGHTS = {
    'role': 0.30,
    'experience': 0.25,
    'career_stage': 0.20,
    'goals': 0.15,
    'practical': 0.10,
}

def compute_match_score(mentee, mentor, weights=None):
    w = weights if weights is not None else WEIGHTS
    scores = {
        'role': role_alignment_score(mentee['DevType'], mentor['DevType']),
        'experience': experience_gap_score(mentee['YearsCodePro'], mentor['YearsCodePro']),
        'career_stage': career_stage_priority_score(mentee['exp_tier']),
        'goals': goals_alignment_score(mentee['JobFactors'], mentor['JobFactors']),
        'practical': practical_fit_score(mentee['OrgSize'], mentor['OrgSize']),
    }
    total = sum(scores[k] * w.get(k, WEIGHTS.get(k, 0)) for k in scores)
    return round(total, 3), scores


# ===========================================================
# STEP 4: Run on real sampled profiles — find top mentor matches
# ===========================================================
def find_top_matches(mentee, mentor_pool, top_n=5, weights=None):
    """
    Returns the top N mentors by total_score.

    TIE-BREAKER: when two or more mentors have equal total_score (common with
    multi-select categorical fields — many respondents share the same role/
    factor combinations), ties are broken by preferring the SMALLEST
    experience gap. Rationale: among equally well-matched mentors on paper,
    the one closer in career stage is likely more relatable and more
    realistically available/responsive than someone much further ahead.
    """
    results = []
    for _, mentor in mentor_pool.iterrows():
        if mentor['Respondent'] == mentee['Respondent']:
            continue
        score, breakdown = compute_match_score(mentee, mentor, weights=weights)
        exp_gap = mentor['YearsCodePro'] - mentee['YearsCodePro']
        results.append({
            'mentor_id': mentor['Respondent'],
            'mentor_devtype': mentor['DevType'],
            'mentor_years': mentor['YearsCodePro'],
            'experience_gap': exp_gap,
            'total_score': score,
            **{f'{k}_score': v for k, v in breakdown.items()}
        })
    results_df = pd.DataFrame(results)
    if results_df.empty:
        # No mentors available — return an empty result with the expected
        # columns rather than crashing, so the platform can show a clean
        # "no matches available yet" state instead of an error.
        return pd.DataFrame(columns=['mentor_id', 'mentor_devtype', 'mentor_years',
                                      'experience_gap', 'total_score', 'role_score',
                                      'experience_score', 'career_stage_score',
                                      'goals_score', 'practical_score'])
    # Primary sort: total_score descending. Secondary sort (tie-breaker):
    # experience_gap ascending (smaller gap wins among ties).
    results_df = results_df.sort_values(['total_score', 'experience_gap'], ascending=[False, True])
    return results_df.head(top_n)


def match_quality_label(score):
    """
    Converts a raw score into an interpretable confidence label.

    WHY THIS MATTERS (found during evaluation): the algorithm always returns
    a "top match" even when the mentor pool is thin and nothing scores well
    (e.g. mean score of just 0.73 at a realistic 50-mentor pool size vs 0.92
    at a synthetic 24,000-mentor pool). Presenting a 0.45 and a 0.95 match
    identically would mislead users. This label makes match confidence
    explicit so the platform can be honest about weak matches instead of
    dressing them up as strong ones.
    """
    if score >= 0.7:
        return 'Strong'
    elif score >= 0.55:
        return 'Good'
    elif score >= 0.4:
        return 'Fair'
    else:
        return 'Weak'


def get_match_recommendation(mentee, mentor_pool, top_n=5, strong_threshold=0.7):
    """
    Wraps find_top_matches with quality labels and a fallback message.
    This is the main entry point a real platform would call.
    """
    matches = find_top_matches(mentee, mentor_pool, top_n=top_n)
    if matches.empty:
        return {
            'matches': matches,
            'message': "No mentors are currently available. We'll notify you as new mentors join."
        }

    matches = matches.copy()
    matches['quality'] = matches['total_score'].apply(match_quality_label)

    best_score = matches.iloc[0]['total_score']
    if best_score < strong_threshold:
        message = (
            f"We found some possible matches, but none are a strong fit yet "
            f"(best available: {match_quality_label(best_score)}, score {best_score:.2f}). "
            f"This usually means the mentor pool doesn't yet have someone in your "
            f"specific role or experience range — consider checking back as more "
            f"mentors join, or broadening your role preferences."
        )
    else:
        message = f"Found {(matches['total_score'] >= strong_threshold).sum()} strong match(es)."

    return {'matches': matches, 'message': message}


if __name__ == '__main__':
    mentees = get_mentee_pool(df)
    mentors = get_mentor_pool(df)
    print(f"Mentee pool: {mentees.shape[0]} | Mentor pool: {mentors.shape[0]}")

    # Test on one real sample mentee
    sample_mentee = mentees.iloc[0]
    print(f"\nSample mentee (Respondent {sample_mentee['Respondent']}):")
    print(f"  Role(s): {sample_mentee['DevType']}")
    print(f"  Experience: {sample_mentee['YearsCodePro']} years ({sample_mentee['exp_tier']})")
    print(f"  Priorities: {sample_mentee['JobFactors']}")

    top_matches = find_top_matches(sample_mentee, mentors, top_n=5)
    print(f"\nTop 5 mentor matches:")
    print(top_matches.to_string(index=False))
