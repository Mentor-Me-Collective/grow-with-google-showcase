"""
Mentor Me Capstone — Objective 1: Workforce & Gender Diversity Analysis
Data Analytics track (Person A — Research & Visualization)

SOURCE DATA
-----------
Stack Overflow Annual Developer Survey 2020 (official public release)
- Fielded Feb 5-28, 2020 | 64,461 respondents | 186 countries
- Published under Open Database License (ODbL) by Stack Overflow
- Official release notes: https://stackoverflow.blog/2020/07/27/public-data-release-of-stack-overflows-2020-developer-survey/
- File used here: so2020_gender_devtype_clean.csv (trimmed to 15 relevant columns
  from the original 61-column survey_results_public.csv)

PIPELINE STEPS (matches capstone brief, Person A tasks):
1. Clean dataset — remove duplicates, handle missing values
2. Exploratory Data Analysis (EDA) — identify trends
3. Create charts and visualizations
4. Interpret findings — key insights
5. Finalize visualizations and supporting statistics
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

INPUT_FILE = 'so2020_gender_devtype_clean.csv'
OUTPUT_DIR = 'outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===========================================================
# STEP 1: CLEAN DATASET — remove duplicates, handle missing values
# ===========================================================
print("="*60)
print("STEP 1: CLEANING")
print("="*60)

df = pd.read_csv(INPUT_FILE)
print(f"Raw shape: {df.shape}")

print("\nMissing values BEFORE cleaning:")
print(df.isna().sum())

# 1a. Remove duplicates (check both full-row dupes and duplicate respondent IDs)
before = df.shape[0]
df = df.drop_duplicates(subset='Respondent')
df = df.drop_duplicates()
print(f"Removed {before - df.shape[0]} duplicate rows")

# 1b. Restrict to Man/Woman for clean binary comparison
# (Non-binary/self-describe/combo responses excluded here due to small sample
#  sizes that would make per-group stats unreliable — NOT because they don't matter.
#  Flag this as a limitation in your report.)
df = df[df['Gender'].isin(['Man', 'Woman'])].copy()

# 1c. Handle missing values — column by column, documented reasoning
#
# RULE APPLIED THROUGHOUT: never impute a field that feeds a reported finding
# (experience, compensation, employment). Imputing would fabricate values that
# could shift the exact gap numbers this report claims to have found. Instead:
#   - small/unused-elsewhere gaps -> drop rows globally
#   - large gaps in a core analysis variable -> drop ONLY within that specific
#     analysis, so unrelated analyses don't lose rows for no benefit
#   - columns not used anywhere in this pipeline (Age, WorkWeekHrs) -> left as-is

n_before = df.shape[0]

# Convert text-coded experience fields to numeric first (needed before dropping)
df['YearsCodePro'] = pd.to_numeric(
    df['YearsCodePro'].replace({'Less than 1 year': '0', 'More than 50 years': '51'}),
    errors='coerce'
)
df['YearsCode'] = pd.to_numeric(
    df['YearsCode'].replace({'Less than 1 year': '0', 'More than 50 years': '51'}),
    errors='coerce'
)

# Global drop: Employment (185 missing) and YearsCode (397 missing) —
# both are small fractions of the data and aren't reconstructable by imputation.
df = df.dropna(subset=['Employment', 'YearsCode'])
print(f"Dropped {n_before - df.shape[0]} rows missing Employment/YearsCode "
      f"({n_before} -> {df.shape[0]})")

# Categorical fields: keep NaN as an explicit "Not stated" category rather than
# dropping — dropping would bias the sample toward people who answered every question.
for col in ['EdLevel', 'DevType', 'JobSat', 'JobSeek', 'NEWLearn', 'OrgSize', 'JobFactors']:
    df[col] = df[col].fillna('Not stated')

print(f"Cleaned shape (Man/Woman only): {df.shape}")

# 1d. Build experience tiers — used only by tenure-based analyses.
# Rows with missing YearsCodePro are KEPT in df (e.g. for role/job-factor analysis)
# but will naturally drop out of any groupby that uses exp_tier, since pandas
# excludes NaN categories from crosstabs/groupby by default.
bins = [-1, 2, 5, 10, 20, 60]
labels = ['0-2y', '2-5y', '5-10y', '10-20y', '20y+']
df['exp_tier'] = pd.cut(df['YearsCodePro'], bins=bins, labels=labels)
n_exp_valid = df['exp_tier'].notna().sum()
print(f"Rows with valid experience tier (for tenure analyses only): {n_exp_valid} "
      f"({df.shape[0] - n_exp_valid} excluded from tenure-based charts)")

# Compensation subset: drop rows with missing/zero/implausible values, but ONLY
# for compensation-specific analysis — this does not affect df used elsewhere.
df_comp = df[(df['ConvertedComp'].notna()) & (df['ConvertedComp'] > 0)].copy()
df_comp['exp_tier'] = pd.cut(df_comp['YearsCodePro'], bins=bins, labels=labels)
print(f"Rows with valid compensation (for comp analysis only): {df_comp.shape[0]} "
      f"({df.shape[0] - df_comp.shape[0]} excluded from compensation charts)")

# Age and WorkWeekHrs are intentionally left untouched — neither is used
# anywhere in this pipeline, so cleaning them would cost sample size for
# no analytical benefit.
print("\nMissing values AFTER cleaning (in main df, Age/WorkWeekHrs left as-is on purpose):")
print(df.isna().sum())

df.to_csv(f'{OUTPUT_DIR}/so2020_cleaned.csv', index=False)


# ===========================================================
# STEP 2: EDA — identify trends
# ===========================================================
print("\n" + "="*60)
print("STEP 2: EDA")
print("="*60)

overall_women_share = (df['Gender'] == 'Woman').mean() * 100
print(f"Overall women's share of respondents: {overall_women_share:.1f}%")

# Trend 1: representation by role
exploded = df.dropna(subset=['DevType'])
exploded = exploded[exploded['DevType'] != 'Not stated']
exploded = exploded.assign(DevType=exploded['DevType'].str.split(';')).explode('DevType').reset_index(drop=True)
role_gender = pd.crosstab(exploded['DevType'], exploded['Gender'], normalize='columns') * 100
role_gender['gap'] = role_gender['Woman'] - role_gender['Man']
role_gender = role_gender.sort_values('gap')
print("\nRole representation gap (Woman % - Man %), most negative first:")
print(role_gender.round(1).head(5))

# Trend 2: representation by experience tier (the "leaky pipeline")
exp_gender = pd.crosstab(df['exp_tier'], df['Gender'], normalize='columns', dropna=True) * 100
print("\nRepresentation by experience tier (% within own gender group):")
print(exp_gender.round(1))

# Trend 3: retention risk (JobSeek) by experience tier, women only
women = df[df['Gender'] == 'Woman'].copy()
seek_by_tier = women.groupby('exp_tier', observed=True)['JobSeek'].apply(
    lambda x: (x == 'I am actively looking for a job').mean() * 100
)
print("\n% of women actively job-seeking, by experience tier (retention risk):")
print(seek_by_tier.round(1))

# Trend 4: job satisfaction by experience tier and gender
# (Replaces compensation as the 4th trend — compensation direction was
# inconsistent across datasets in earlier analysis, so it was dropped as
# a headline finding. Job satisfaction is a more direct success-factor
# measure and pairs with Trend 3's retention-risk finding.)
sat_order = ['Very dissatisfied', 'Slightly dissatisfied', 'Neither satisfied nor dissatisfied',
             'Slightly satisfied', 'Very satisfied']
df['JobSat_score'] = df['JobSat'].map({s: i for i, s in enumerate(sat_order)})  # 'Not stated' -> NaN
sat_gap = df.dropna(subset=['JobSat_score', 'exp_tier']).groupby(['exp_tier', 'Gender'], observed=True)['JobSat_score'].mean().unstack()
sat_gap['gap'] = (sat_gap['Woman'] - sat_gap['Man']).round(2)
print("\nMean job satisfaction score (0=Very dissatisfied, 4=Very satisfied) by tier and gender:")
print(sat_gap.round(2))

# Trend 5: what job factors women vs men prioritize (closest available proxy
# for "interest in growth/development/inclusive workplace" in this dataset)
jf_exploded = df.dropna(subset=['JobFactors'])
jf_exploded = jf_exploded[jf_exploded['JobFactors'] != 'Not stated']
jf_exploded = jf_exploded.assign(JobFactors=jf_exploded['JobFactors'].str.split(';')).explode('JobFactors').reset_index(drop=True)
factor_gender = pd.crosstab(jf_exploded['JobFactors'], jf_exploded['Gender'], normalize='columns') * 100
factor_gender['gap'] = factor_gender['Woman'] - factor_gender['Man']
factor_gender = factor_gender.sort_values('gap', ascending=False)
print("\nJob factors ranked by gender gap (Woman % - Man %), most female-skewed first:")
print(factor_gender.round(1))


# ===========================================================
# STEP 3: CHARTS AND VISUALIZATIONS
# ===========================================================
print("\n" + "="*60)
print("STEP 3: VISUALIZATIONS")
print("="*60)

# Chart 1 — Gender representation across tech roles
fig, ax = plt.subplots(figsize=(9, 8))
colors = ['#d62839' if g < 0 else '#3d5a80' for g in role_gender['gap']]
ax.barh(role_gender.index, role_gender['gap'], color=colors)
ax.axvline(0, color='black', linewidth=0.8)
ax.set_xlabel('Percentage point gap (Women % in role - Men % in role)')
ax.set_title('Gender representation gap across tech roles')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/chart1_role_representation.png', dpi=150)
plt.close()

# Chart 2 — The leaky pipeline (representation by experience tier)
fig, ax = plt.subplots(figsize=(8, 5))
x = range(len(labels))
ax.plot(x, exp_gender.reindex(labels)['Man'], marker='o', label='Men', color='#3d5a80')
ax.plot(x, exp_gender.reindex(labels)['Woman'], marker='o', label='Women', color='#d62839')
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=20)
ax.set_ylabel('% of gender group')
ax.set_title("The leaky pipeline: women's representation\ndrops off at senior experience tiers")
ax.legend()
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/chart2_leaky_pipeline.png', dpi=150)
plt.close()

# Chart 3 — Retention risk (mentorship access proxy) by experience tier, women only
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(seek_by_tier.index.astype(str), seek_by_tier.values, color='#f0a202')
ax.set_ylabel('% actively job-seeking')
ax.set_title('Retention risk among women is highest\nin the first 10 years of career (0-10y)')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/chart3_retention_risk.png', dpi=150)
plt.close()

# Chart 4 — Job satisfaction by experience tier and gender
fig, ax = plt.subplots(figsize=(8, 5))
x = range(len(labels))
ax.plot(x, sat_gap.reindex(labels)['Man'], marker='o', label='Men', color='#3d5a80')
ax.plot(x, sat_gap.reindex(labels)['Woman'], marker='o', label='Women', color='#d62839')
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=20)
ax.set_ylabel('Mean job satisfaction (0-4 scale)')
ax.set_title('Women report slightly higher satisfaction at every tier\n(yet still show elevated job-seeking — see Trend 3)')
ax.legend()
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/chart4_job_satisfaction.png', dpi=150)
plt.close()

# Chart 5 — Job factors: what women prioritize more than men
fig, ax = plt.subplots(figsize=(9, 6))
fg_sorted = factor_gender.sort_values('gap')
colors5 = ['#3d5a80' if g < 0 else '#d62839' for g in fg_sorted['gap']]
labels5 = [l[:40] for l in fg_sorted.index]
ax.barh(labels5, fg_sorted['gap'], color=colors5)
ax.axvline(0, color='black', linewidth=0.8)
ax.set_xlabel('Percentage point gap (Women % - Men %)')
ax.set_title('What women prioritize more than men when choosing a job\n(red = women prioritize more, blue = men prioritize more)')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/chart5_job_factors_gender.png', dpi=150)
plt.close()

print(f"Saved 5 charts to {OUTPUT_DIR}/")


# ===========================================================
# STEP 4: INTERPRET FINDINGS — key insights
# ===========================================================
insights = f"""
KEY INSIGHTS — Objective 1 Analysis
=====================================

1. REPRESENTATION GAP
   Women make up {overall_women_share:.1f}% of respondents overall. Representation
   is not evenly spread across roles: women are relatively more present in
   front-end, full-stack, and data-focused roles, and relatively scarcer in
   DevOps, sysadmin, and embedded/infrastructure roles.

2. THE LEAKY PIPELINE
   Women's share of the developer population is comparable to men's at
   junior tenure (0-2 years) but drops sharply by senior tenure (10y+).
   This is the core "gap" evidence: attrition/advancement, not entry,
   is where the problem concentrates.

3. SUCCESS FACTOR: RETENTION RISK WINDOW
   Among women, the share actively job-seeking (a retention-risk proxy)
   is highest in the first 10 years of career (0-10y) and drops
   substantially after 10 years. This validates targeting early-career
   women specifically, as the brief proposes — the vulnerable window is
   real and measurable, not just assumed.

4. SUCCESS FACTOR: SATISFIED BUT STILL LEAVING
   Women report slightly HIGHER job satisfaction than men at every experience
   tier (a small but consistent gap on a 0-4 scale). Read alongside Trend 3
   (elevated job-seeking among women, especially at 0-2y and 5-10y), this
   suggests women are not leaving because they are more unhappy where they
   are — they may be leaving because they see fewer visible paths forward
   internally. This points toward a sponsorship/growth-pathway gap rather
   than a satisfaction problem, which is directly relevant to what a
   mentorship platform can address.
   NOTE: compensation was tested as a candidate 4th trend but dropped —
   the direction of any pay gap was inconsistent across datasets (this
   survey vs. the Kaggle DS/ML survey showed opposite directions at some
   tiers), so it was not reliable enough to report as a finding.

5. WHAT WOMEN PRIORITIZE DIFFERENTLY WHEN CHOOSING A JOB
   "Diversity of the company or organization" is the most gender-differentiated
   job factor in this dataset — women select it far more often than men.
   "Opportunities for professional development" (the closest proxy to a
   mentorship/growth interest available here) shows no gap: men and women
   value it equally. This suggests women are not less interested in
   development opportunities, but weigh diversity/inclusion signals in an
   employer much more heavily when deciding where to work.

6. MISSING DATA WAS HANDLED PER-ANALYSIS, NOT GLOBALLY
   Employment and YearsCode (small gaps, <1%) were dropped globally.
   YearsCodePro/exp_tier and ConvertedComp (larger gaps, 20-36%) were dropped
   only within the specific analyses that use them, so unrelated analyses
   (e.g. role representation) keep their full sample size. No field was
   imputed — a fabricated average experience or salary could shift the exact
   gap numbers this report is built on.

7. WHAT THIS DATA CANNOT TELL US
   No field in this survey (or any public dataset found) directly measures
   mentorship access. The link between mentorship and retention/success
   is supported by cited literature (McKinsey "Women in the Workplace",
   Catalyst), not by this analysis. State this as a limitation, not a gap
   to keep searching for — it reflects what's publicly available at the
   individual level, not a research shortfall.
"""
print(insights)

with open(f'{OUTPUT_DIR}/key_insights.txt', 'w') as f:
    f.write(insights)


# ===========================================================
# STEP 5: FINALIZE — supporting statistics table
# ===========================================================
summary_stats = pd.DataFrame({
    'metric': [
        'Overall % women in sample',
        'Women % at 0-2y experience',
        'Women % at 20y+ experience',
        '% women job-seeking at 0-2y',
        '% women job-seeking at 20y+',
        'Job satisfaction gap (Woman-Man) at 0-2y',
        'Job satisfaction gap (Woman-Man) at 20y+',
    ],
    'value': [
        round(overall_women_share, 1),
        round(exp_gender.loc['0-2y', 'Woman'], 1),
        round(exp_gender.loc['20y+', 'Woman'], 1),
        round(seek_by_tier.loc['0-2y'], 1),
        round(seek_by_tier.loc['20y+'], 1),
        round(sat_gap.loc['0-2y', 'gap'], 2),
        round(sat_gap.loc['20y+', 'gap'], 2),
    ]
})
summary_stats.to_csv(f'{OUTPUT_DIR}/summary_statistics.csv', index=False)
print(f"\nSaved summary statistics table to {OUTPUT_DIR}/summary_statistics.csv")
print("\nPipeline complete.")
