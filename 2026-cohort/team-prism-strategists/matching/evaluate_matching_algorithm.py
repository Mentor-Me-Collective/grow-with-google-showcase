"""
Mentoring-Me Capstone — Matching Algorithm Evaluation

No ground-truth "correct match" data exists (no historical outcomes to
validate against), so "accuracy" here is defined operationally as:

1. COVERAGE: % of mentees who receive at least one strong match (score >= 0.7)
2. BASELINE COMPARISON: does the weighted algorithm outperform random mentor
   assignment? If not, the weighting scheme isn't adding real value.
3. SCORE DISTRIBUTION: are scores spread out meaningfully, or clustered
   (which would suggest the weights aren't actually discriminating between
   good and bad matches)?
"""

import os
import sys
import pandas as pd
import numpy as np

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from matching_algorithm_v1 import (
    compute_match_score, find_top_matches, get_mentee_pool, get_mentor_pool,
    match_quality_label
)

np.random.seed(42)  # reproducibility

_csv_path = 'so2020_cleaned.csv'
if not os.path.exists(_csv_path):
    _csv_path = os.path.join(_current_dir, 'so2020_cleaned.csv')
if not os.path.exists(_csv_path):
    _csv_path = os.path.join(_current_dir, 'so2020.csv')

df = pd.read_csv(_csv_path)
mentees = get_mentee_pool(df)
mentors = get_mentor_pool(df)
print(f"Full mentee pool: {mentees.shape[0]} | Full mentor pool: {mentors.shape[0]}")

# Evaluate on a sample (running the full pool x full mentor pool is expensive —
# a representative sample is standard practice here, not a shortcut that
# undermines the result)
SAMPLE_SIZE = 100
mentee_sample = mentees.sample(n=min(SAMPLE_SIZE, mentees.shape[0]), random_state=42)
print(f"Evaluating on a sample of {mentee_sample.shape[0]} mentees\n")

top_scores = []          # best match score per mentee (weighted algorithm)
random_scores = []       # score of a RANDOMLY chosen mentor, for comparison
has_strong_match = []    # whether best match >= 0.7

for _, mentee in mentee_sample.iterrows():
    matches = find_top_matches(mentee, mentors, top_n=1)
    if matches.empty:
        continue
    best_score = matches.iloc[0]['total_score']
    top_scores.append(best_score)
    has_strong_match.append(best_score >= 0.7)

    # Baseline: score of ONE randomly picked mentor (not the algorithm's choice)
    random_mentor = mentors.sample(n=1, random_state=np.random.randint(0, 100000)).iloc[0]
    r_score, _ = compute_match_score(mentee, random_mentor)
    random_scores.append(r_score)

top_scores = np.array(top_scores)
random_scores = np.array(random_scores)

print("="*60)
print("RESULT 1: COVERAGE")
print("="*60)
coverage = np.mean(has_strong_match) * 100
print(f"% of mentees with at least one strong match (score >= 0.7): {coverage:.1f}%")

print("\n" + "="*60)
print("RESULT 1b: MATCH QUALITY BREAKDOWN (using match_quality_label)")
print("="*60)
labels = pd.Series([match_quality_label(s) for s in top_scores])
label_counts = labels.value_counts()
label_pct = (label_counts / len(labels) * 100).round(1)
for label in ['Strong', 'Good', 'Fair', 'Weak']:
    count = label_counts.get(label, 0)
    pct = label_pct.get(label, 0.0)
    print(f"  {label:>7}: {count:>3} mentees ({pct}%)")

print("\n" + "="*60)
print("RESULT 1c: MATCH QUALITY AT REALISTIC POOL SIZE (50 mentors)")
print("="*60)
print("The full synthetic pool (24,413 mentors) makes every match 'Strong' —")
print("not a realistic test. Re-running on a thin, realistic-scale pool:")
thin_pool = mentors.sample(n=50, random_state=1)
thin_labels = []
for _, mentee in mentee_sample.iterrows():
    m = find_top_matches(mentee, thin_pool, top_n=1)
    if not m.empty:
        thin_labels.append(match_quality_label(m.iloc[0]['total_score']))
thin_labels = pd.Series(thin_labels)
thin_counts = thin_labels.value_counts()
thin_pct = (thin_counts / len(thin_labels) * 100).round(1)
for label in ['Strong', 'Good', 'Fair', 'Weak']:
    count = thin_counts.get(label, 0)
    pct = thin_pct.get(label, 0.0)
    print(f"  {label:>7}: {count:>3} mentees ({pct}%)")

print("\n" + "="*60)
print("RESULT 2: ALGORITHM vs RANDOM BASELINE")
print("="*60)
print(f"Mean top-match score (weighted algorithm): {top_scores.mean():.3f} "
      f"({match_quality_label(top_scores.mean())} on average)")
print(f"Mean score of a random mentor (baseline):   {random_scores.mean():.3f} "
      f"({match_quality_label(random_scores.mean())} on average)")
improvement = ((top_scores.mean() - random_scores.mean()) / random_scores.mean()) * 100
print(f"Improvement over random: {improvement:.1f}%")

print("\n" + "="*60)
print("RESULT 3: SCORE DISTRIBUTION")
print("="*60)
print(f"Min: {top_scores.min():.3f} | 25th pct: {np.percentile(top_scores,25):.3f} | "
      f"Median: {np.median(top_scores):.3f} | 75th pct: {np.percentile(top_scores,75):.3f} | "
      f"Max: {top_scores.max():.3f}")
print(f"Std deviation: {top_scores.std():.3f}  (near-zero would mean scores aren't discriminating)")
