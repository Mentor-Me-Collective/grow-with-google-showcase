# Equitable Mentorship Pairing Engine

**Team:** Catalyst Strategists: Israel Babalola (Data Analytics), Eldad Berhanu (Cybersecurity), Lauren Rodriguez (IT Automation with Python), Gbenga Ayodeji (Advanced Data Analytics)
**UN SDG Goal:** Goal 5, Gender Equality

## What this project does

Early-career women in technical fields face systemic isolation due to a lack of structured access to professional network matching. This project analyzes real mentorship data to quantify that gap and inform the design of a fairer, structured mentor-matching engine.

## Grow with Google resources used

Data Analytics Grow with Google Track (Career Certificate), applied via Python/pandas analysis and Tableau Public visualization.

## Data sources

- [Academic mentorship dataset](https://doi.org/10.5281/zenodo.4917086) — 743,000+ real mentor-mentee pairs (Nature Scientific Data, 2022)
- [Stack Overflow 2025 Developer Survey](https://www.kaggle.com/datasets/edoardogalli/stack-overflow-annual-developer-survey-2025)

## Setup / run instructions

Open `src/Equitable_Mentorship_Pairing_Engine.ipynb` in Google Colab or Kaggle. Attach the mentorship dataset files and the Stack Overflow survey as inputs, then run all cells top to bottom.

## Findings

- **Mentors are overwhelmingly men.** 67.81% of mentors are men vs. 21.21% women (10.98% of names unclassified by the gender-inference model).
- **The gender-pairing pattern is statistically significant, not random.** A Chi-Square test of independence on the pairing data returned p ≈ 0.0000 (chi2 = 50,383.74, df = 4), rejecting the null hypothesis that gender and mentor/mentee pairing are independent.
- **Early-career developers value mentorship access more.** "Expert mentors" ranks 8.04 in importance for developers with 0–3 years of experience, vs. 9.84 for 4+ years (lower = more important, Stack Overflow 2025).
- The 2025 Stack Overflow survey no longer includes a gender question, so it was used only for career-stage context, not representation figures.

## Recommendations

- Weight topic/skill similarity between mentor and mentee in the matching logic, since successful real pairs show this pattern naturally.
- Don't rely on informal, organic introductions to fill mentor roles for women — the data shows that process already produces a skewed, non-random outcome.
- Target mentor recruiting specifically at senior women, since they're the scarce side of the pairing, not the mentees.
- Make demographic fields in the matching engine self-reported and optional, rather than inferred, given the documented misclassification issues in the source data.

## Limitations

Gender in the mentorship dataset is inferred from first names by a model, not self-reported. The dataset itself comes from bioscience/neuroscience academia, not the tech industry, so it's a structural stand-in for how mentorship relationships form rather than a tech-specific sample.

## Future ideas

Build a small synthetic or short-survey dataset of real tech-specific matching attributes (skills, goals, seniority gap) no public dataset currently records actual tech-industry mentor-match outcomes.
