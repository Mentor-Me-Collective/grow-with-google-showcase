"""
AquaWatch Naija: Hyperlocal Water Quality Monitor Portal
=============================================================
UN SDG Goal 6: Clean Water and Sanitation

A public dashboard that lets community members view municipal water
testing results and safety warnings in one place.

Data source: nigeria_combined_water_data.csv

HOW TO RUN THIS APP
--------------------
1. Make sure you have Python installed.
2. Install the required libraries (only needs to be done once):
       pip install -r requirements.txt
3. Put this file (app.py) and "nigeria_combined_water_data.csv"
   in the SAME folder.
4. Open a terminal in that folder and run:
       streamlit run app.py
5. Your browser will open automatically at http://localhost:8501
"""

import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

# -----------------------------------------------------------------------
# PAGE CONFIG  (must be the first Streamlit command in the script)
# -----------------------------------------------------------------------
st.set_page_config(
    page_title="AquaWatch Naija",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------
# CSS: Award-style glassmorphism, with a light "HydraFlow" finish layered
# on top. Two blocks, same as the design draft: the first sets up the
# glass-card/tab/alert system, the second re-tints it toward a lighter,
# more legible palette so text stays readable against the aqua background.
# -----------------------------------------------------------------------
st.markdown(
    """
<style>
:root{
    --bg-blue:#082c57;
    --bg-cobalt:#0f4fbf;
    --bg-turq:#2ec4b6;
    --bg-mint:#9ce8d0;

    --glass:rgba(255,255,255,.72);
    --glass-strong:rgba(255,255,255,.84);
    --glass-border:rgba(255,255,255,.72);

    --mint:#40e0a2;
    --emerald:#17c77b;
    --cobalt:#1f6fff;
    --amber:#ffbf47;
    --danger:#ff4d63;

    --text:#10251b;
    --muted:rgba(16,37,27,.62);
    --dark:#0d2338;
}

/* ---------- Global ---------- */
html, body, [class*="css"]{
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
}

.stApp{
    background:
        radial-gradient(circle at 8% 12%, rgba(185,235,190,.55), transparent 28%),
        radial-gradient(circle at 88% 8%, rgba(124,207,235,.48), transparent 32%),
        linear-gradient(135deg, #c9e8d0 0%, #b9e3dc 42%, #9fd8ea 100%);
    color:#10251b;
}

.block-container{
    max-width:1500px;
    padding-top:1.25rem;
    padding-bottom:2.2rem;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"]{
    background:linear-gradient(
        180deg,
        rgba(255,255,255,.76),
        rgba(242,250,244,.64)
    );
    border-right:1px solid var(--glass-border);
    backdrop-filter:blur(14px);
}

section[data-testid="stSidebar"] *{
    color:#173321;
}

.sidebar-brand-stack{
    display:flex;
    flex-direction:column;
    align-items:flex-start;
    gap:8px;
    margin:0 0 22px;
}

.sidebar-logo-img{
    width:170px;
    height:auto;
    display:block;
}

.sidebar-sub{
    font-size:.85rem;
    font-weight:700;
    color:rgba(255,255,255,.68);
}

/* ---------- Hero ---------- */
.hero-wrap{
    display:flex;
    align-items:flex-end;
    justify-content:space-between;
    gap:24px;
    margin-bottom:20px;
}

.hero-kicker{
    display:inline-flex;
    align-items:center;
    gap:8px;
    padding:6px 10px;
    border-radius:999px;
    background:rgba(64,224,162,.12);
    border:1px solid rgba(64,224,162,.24);
    color:#b8ffe4;
    font-size:.74rem;
    font-weight:750;
    letter-spacing:.02em;
}

.hero-title{
    margin-top:11px;
    font-size:2.45rem;
    line-height:1.02;
    font-weight:850;
    letter-spacing:-.055em;
    color:#ffffff;
}

.hero-sub{
    margin-top:9px;
    max-width:760px;
    font-size:.98rem;
    color:var(--muted);
    line-height:1.55;
}

/* ---------- Glass card ---------- */
.glass-card{
    background:var(--glass);
    border:1px solid var(--glass-border);
    border-radius:16px;
    backdrop-filter:blur(10px);
    -webkit-backdrop-filter:blur(10px);
    box-shadow:
        0 14px 32px rgba(4,25,48,.18),
        inset 0 1px 0 rgba(255,255,255,.08);
}

/* ---------- KPI ---------- */
.kpi-card{
    min-height:155px;
    padding:20px 22px;
    position:relative;
    overflow:hidden;
}

.kpi-card:after{
    content:"";
    position:absolute;
    width:120px;height:120px;
    right:-35px;bottom:-50px;
    border-radius:50%;
    background:linear-gradient(145deg,rgba(64,224,162,.28),rgba(31,111,255,.22));
}

.kpi-label{
    color:rgba(255,255,255,.74);
    font-size:.79rem;
    font-weight:700;
    text-transform:uppercase;
    letter-spacing:.08em;
}

.kpi-value{
    margin-top:12px;
    font-size:2.45rem;
    line-height:1;
    font-weight:860;
    letter-spacing:-.05em;
    color:#ffffff;
}

.kpi-meta{
    margin-top:9px;
    font-size:.76rem;
    color:#c7f8e6;
    font-weight:700;
}

/* ---------- Safety banners ---------- */
/* alert-grid: same equal-height technique as action-grid below - CSS
   Grid stretches all 3 banners to match the tallest one's content,
   regardless of how much text each status has (Safe's copy is much
   shorter than Moderate/High Risk's, so without this the Safe banner
   renders visibly shorter than the other two). */
.alert-grid{
    display:grid;
    grid-template-columns:repeat(3, 1fr);
    gap:20px;
}

@media (max-width: 700px){
    .alert-grid{grid-template-columns:1fr;}
}

.alert-safe,
.alert-caution,
.alert-danger{
    border-radius:16px;
    padding:16px 18px;
    border:1px solid rgba(255,255,255,.2);
    backdrop-filter:blur(10px);
    display:flex;
    gap:13px;
    align-items:flex-start;
    box-shadow:0 10px 24px rgba(0,0,0,.12);
}

.alert-safe{
    background:linear-gradient(135deg,rgba(17,199,123,.26),rgba(21,153,101,.17));
}

.alert-caution{
    background:linear-gradient(135deg,rgba(255,152,0,.29),rgba(230,126,0,.16));
}

.alert-danger{
    background:linear-gradient(135deg,rgba(255,77,99,.34),rgba(179,21,50,.22));
    animation:dangerPulse 1.65s infinite;
}

@keyframes dangerPulse{
    0%,100%{
        box-shadow:0 0 0 0 rgba(255,77,99,.12),0 10px 24px rgba(0,0,0,.12);
    }
    50%{
        box-shadow:0 0 0 10px rgba(255,77,99,.03),0 10px 24px rgba(0,0,0,.16);
    }
}

.alert-icon{
    width:34px;height:34px;
    border-radius:12px;
    display:grid;place-items:center;
    background:rgba(255,255,255,.14);
    flex:0 0 auto;
}

.alert-title{
    font-size:.92rem;
    font-weight:850;
    color:white;
}

.alert-copy{
    margin-top:3px;
    color:rgba(255,255,255,.78);
    font-size:.77rem;
    line-height:1.45;
}

/* ---------- Section headers ---------- */
.section-title{
    font-size:1.06rem;
    font-weight:820;
    letter-spacing:-.02em;
    color:#fff;
    margin:10px 0 12px;
}

/* ---------- Custom tabs ---------- */
div[data-baseweb="tab-list"]{
    gap:10px;
    background:rgba(255,255,255,.08);
    border:1px solid rgba(255,255,255,.14);
    border-radius:16px;
    padding:7px;
    backdrop-filter:blur(10px);
}

button[data-baseweb="tab"]{
    height:44px;
    border-radius:12px !important;
    color:rgba(255,255,255,.72) !important;
    font-weight:750 !important;
    background:transparent !important;
}

button[data-baseweb="tab"][aria-selected="true"]{
    color:#fff !important;
    background:linear-gradient(135deg,rgba(31,111,255,.92),rgba(49,155,229,.82)) !important;
    box-shadow:0 8px 20px rgba(17,76,159,.25);
}

div[data-baseweb="tab-highlight"]{
    display:none;
}

/* ---------- Native widgets ---------- */
div[data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div,
.stTextInput input{
    border-radius:12px !important;
    border:1px solid rgba(255,255,255,.18) !important;
    background:rgba(255,255,255,.12) !important;
    color:white !important;
    backdrop-filter:blur(10px);
}

div[data-baseweb="select"] span{
    color:white !important;
}

.stMetric{
    background:rgba(255,255,255,.11);
    border:1px solid rgba(255,255,255,.16);
    border-radius:14px;
    padding:14px 16px;
}

[data-testid="stMetricLabel"]{
    color:rgba(255,255,255,.7);
}

[data-testid="stMetricValue"]{
    color:white;
}

/* ---------- Dataframe ---------- */
[data-testid="stDataFrame"]{
    background:rgba(255,255,255,.10);
    border:1px solid rgba(255,255,255,.16);
    border-radius:16px;
    overflow:hidden;
    backdrop-filter:blur(10px);
}

/* ---------- Action cards ---------- */
/* action-grid: CSS Grid (not st.columns) so all 4 cards are forced to the
   SAME height regardless of how much text each one holds. Grid rows size
   to their tallest cell and stretch every cell to fill it by default, so
   card 4 (the longest) sets the height and cards 1-3 match it exactly. */
.action-grid{
    display:grid;
    grid-template-columns:repeat(2, 1fr);
    gap:20px;
    max-width:1000px;
    margin:0 auto;
}

@media (max-width: 650px){
    .action-grid{grid-template-columns:1fr;}
}

.action-card{
    min-height:210px;
    padding:18px;
    display:flex;
    flex-direction:column;
}

.action-step{
    width:34px;height:34px;
    border-radius:11px;
    display:grid;place-items:center;
    font-weight:850;
    color:white;
    background:linear-gradient(145deg,var(--cobalt),var(--mint));
    box-shadow:0 8px 18px rgba(0,0,0,.14);
    flex-shrink:0;
}

.action-title{
    margin-top:13px;
    font-size:.94rem;
    font-weight:820;
    color:white;
    flex-shrink:0;
    line-height:1.25;
    white-space:nowrap;
}

.action-copy{
    margin-top:6px;
    font-size:.77rem;
    color:rgba(255,255,255,.72);
    line-height:1.5;
}

/* ---------- Breakdown cards ---------- */
.metric-mini{
    padding:18px;
    min-height:125px;
}

.metric-mini-label{
    color:rgba(255,255,255,.68);
    font-size:.76rem;
}

.metric-mini-value{
    margin-top:13px;
    font-size:1.75rem;
    font-weight:840;
    color:white;
}

.metric-mini-note{
    margin-top:4px;
    font-size:.7rem;
    color:#bcf7dc;
}

/* ---------- Misc ---------- */
hr{
    border-color:rgba(255,255,255,.12) !important;
}

#MainMenu{visibility:hidden;}
footer{visibility:hidden;}
header{background:transparent;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
/* HydraFlow-inspired light glass finish */
.hero-title,.section-title{color:#173321!important}
.hero-sub{color:#52685a!important}
.hero-kicker{color:#0b754b!important;background:rgba(255,255,255,.52)!important;border-color:rgba(16,120,75,.18)!important}
.kpi-card,.metric-mini,.action-card{
    background:rgba(255,255,255,.76)!important;
    border:1px solid rgba(255,255,255,.88)!important;
    box-shadow:0 18px 42px rgba(31,88,74,.10)!important;
}
.kpi-label,.metric-mini-label{color:#52685a!important}
.kpi-value,.metric-mini-value,.action-title{color:#14261a!important}
.kpi-meta,.metric-mini-note{color:#168b54!important}
.action-copy{color:#607064!important}
.alert-title,.alert-copy,.alert-icon{color:white!important}
.alert-safe{background:linear-gradient(135deg,#179b5b,#28bd78)!important}
.alert-caution{background:linear-gradient(135deg,#cc7a00,#ff9800)!important}
.alert-danger{background:linear-gradient(135deg,#d94752,#f0646e)!important}
button[data-baseweb="tab"]{color:#4e6657!important}
button[data-baseweb="tab"][aria-selected="true"]{
    color:white!important;
    background:linear-gradient(135deg,#15975a,#28c781)!important;
}
div[data-baseweb="tab-list"]{
    background:rgba(255,255,255,.62)!important;
    border-color:rgba(255,255,255,.78)!important;
}
div[data-baseweb="select"] > div,.stTextInput input{
    background:rgba(255,255,255,.78)!important;
    color:#173321!important;
    border-color:rgba(255,255,255,.90)!important;
}
div[data-baseweb="select"] span{color:#173321!important}
[data-testid="stMetricLabel"],[data-testid="stMetricValue"]{color:#173321!important}
.stMetric{background:rgba(255,255,255,.68)!important;border-color:rgba(255,255,255,.82)!important}
section[data-testid="stSidebar"] .sidebar-sub,
section[data-testid="stSidebar"] .stCaption{color:#607064!important}
</style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------
# SAFETY THRESHOLDS
# -----------------------------------------------------------------------
PH_MIN, PH_MAX = 6.5, 8.5          # Safe drinking water pH range
TURBIDITY_MAX = 5.0                # NTU  (WHO acceptable limit)
BACTERIA_MAX = 1000.0              # CFU/mL (simplified "high risk" cutoff)
CONTAMINANT_MAX = 7.0              # ppm (on this dataset's 0-10 scale)

# -----------------------------------------------------------------------
# RISK LEVEL COLORS (discrete: Green = Safe, Orange = Moderate, Red = High)
# -----------------------------------------------------------------------
# Colors are tied directly to the 3 Risk Level buckets, not a continuous
# score, so the legend, map dots, and table row shading always agree on
# exactly which of the 3 categories a given site falls into.
RISK_COLORS = {
    "Safe": (52, 168, 83),          # green
    "Moderate Risk": (255, 152, 0), # orange
    "High Risk": (234, 67, 53),     # red
}

# -----------------------------------------------------------------------
# NIGERIA COUNTRY OUTLINE (for the map's border layer)
# -----------------------------------------------------------------------
# Simplified single-polygon boundary (58 vertices), sourced from the
# public "johan/world.geo.json" country-boundaries dataset on GitHub.
# The "road" basemap draws every country's border/label at equal weight,
# which makes Nigeria hard to pick out from neighbors like Niger. This
# highlighted stroke is drawn on top so Nigeria reads as the one country
# that matters here, and the jittered region dots visibly sit inside it.
NIGERIA_BORDER_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "id": "NGA",
            "properties": {"name": "Nigeria"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [8.500288, 4.771983], [7.462108, 4.412108], [7.082596, 4.464689],
                    [6.698072, 4.240594], [5.898173, 4.262453], [5.362805, 4.887971],
                    [5.033574, 5.611802], [4.325607, 6.270651], [3.57418, 6.2583],
                    [2.691702, 6.258817], [2.749063, 7.870734], [2.723793, 8.506845],
                    [2.912308, 9.137608], [3.220352, 9.444153], [3.705438, 10.06321],
                    [3.60007, 10.332186], [3.797112, 10.734746], [3.572216, 11.327939],
                    [3.61118, 11.660167], [3.680634, 12.552903], [3.967283, 12.956109],
                    [4.107946, 13.531216], [4.368344, 13.747482], [5.443058, 13.865924],
                    [6.445426, 13.492768], [6.820442, 13.115091], [7.330747, 13.098038],
                    [7.804671, 13.343527], [9.014933, 12.826659], [9.524928, 12.851102],
                    [10.114814, 13.277252], [10.701032, 13.246918], [10.989593, 13.387323],
                    [11.527803, 13.32898], [12.302071, 13.037189], [13.083987, 13.596147],
                    [13.318702, 13.556356], [13.995353, 12.461565], [14.181336, 12.483657],
                    [14.577178, 12.085361], [14.468192, 11.904752], [14.415379, 11.572369],
                    [13.57295, 10.798566], [13.308676, 10.160362], [13.1676, 9.640626],
                    [12.955468, 9.417772], [12.753672, 8.717763], [12.218872, 8.305824],
                    [12.063946, 7.799808], [11.839309, 7.397042], [11.745774, 6.981383],
                    [11.058788, 6.644427], [10.497375, 7.055358], [10.118277, 7.03877],
                    [9.522706, 6.453482], [9.233163, 6.444491], [8.757533, 5.479666],
                    [8.500288, 4.771983],
                ]],
            },
        }
    ],
}


def risk_level_color(level: str) -> list:
    """Return the RGB color for a Risk Level bucket, used for the map dots."""
    return list(RISK_COLORS.get(level, (150, 150, 150)))


def highlight_risk(row):
    # Same discrete Green/Orange/Red colors as the map, applied as a light
    # background tint so a table row's shade always matches its risk bucket.
    r, g, b = RISK_COLORS.get(row["Risk Level"], (150, 150, 150))
    return [f"background-color: rgba({r}, {g}, {b}, 0.25)"] * len(row)


# -----------------------------------------------------------------------
# LOAD & PREPARE THE DATA
# -----------------------------------------------------------------------
# Resolved relative to THIS FILE's location (not the working directory).
# Streamlit Cloud's working directory is always the repo root, regardless
# of where app.py lives, so a bare filename breaks once app.py moves into
# a subfolder like src/. This works from the repo root or from inside src/.
CSV_FILE = Path(__file__).parent / "nigeria_combined_water_data.csv"


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    """Read the CSV and add a few helper columns used across the app."""
    df = pd.read_csv(path)

    # --- Build a single, easy-to-read Risk Level column -----------------
    # A site is flagged "High Risk" if 2+ readings breach a safety
    # threshold, "Moderate Risk" if exactly 1 breaches, else "Safe".
    #
    # Risk Level is graded ONLY on this specific water sample: pH,
    # Turbidity, Bacteria Count, and Contaminant Level (ppm). For the 9
    # Abuja / Benue South rows that have no numeric "Bacteria Count
    # (CFU/mL)" or "Contaminant Level (ppm)" reading, there's a single
    # supplementary signal that stands in for those two missing numeric
    # checks; it does NOT add extra checks for rows that already have
    # full numeric data:
    #
    # FIELD-REPORTED CONTAMINATION (9 Abuja / Benue South rows): these
    # rows have a qualitative field note in the separate "Contaminant
    # Level" TEXT column instead (e.g. "High (Coliforms up to 862
    # MPN/100mL)"). That severity word is mapped onto the same
    # breach-counting scheme used for the numeric thresholds, so those 9
    # sites are still screened on contamination severity rather than
    # being judged on pH/Turbidity alone.
    #
    # Disease Indicator / Risk (below) is a DELIBERATELY separate signal:
    # regional Cholera/Typhoid/Diarrheal case rates, not a water test
    # result, and is never folded into this breach count. The two are
    # allowed to disagree; see the caption on the dashboard for why.
    #
    # (Confirmed the field-note rows and the disease-case-rate rows never
    # overlap: the field-note rows are exactly the 9 rows missing disease
    # case-rate data, and vice versa.)
    FIELD_SEVERITY_BREACH_WEIGHT = {
        "extreme": 2,        # alone, enough to reach High Risk
        "very high": 2,      # alone, enough to reach High Risk
        "high": 1,
        "moderate-high": 1,
    }

    def field_reported_reasons(row):
        if pd.notna(row["Bacteria Count (CFU/mL)"]) and pd.notna(row["Contaminant Level (ppm)"]):
            return []  # real numeric readings exist for this row - nothing to fall back to
        note = row.get("Contaminant Level")
        if pd.isna(note) or not str(note).strip():
            return []
        severity_word = str(note).split("(")[0].strip().lower()
        weight = FIELD_SEVERITY_BREACH_WEIGHT.get(severity_word, 0)
        if weight == 0:
            return []
        # Just the severity tier (e.g. "Extreme", "Very High"), no raw
        # instrument readings, matching the plain style of every other
        # Risk Reason string ("High turbidity", "High bacteria count").
        # The full field note is still shown as-is in Disease Indicator /
        # Risk, so no detail is lost, just not duplicated here.
        label = f"Field-reported contamination: {severity_word.title()}"
        return [label] * weight

    def classify_risk(row):
        reasons = []
        if pd.notna(row["pH Level"]) and not (PH_MIN <= row["pH Level"] <= PH_MAX):
            reasons.append("pH out of safe range")
        if pd.notna(row["Turbidity (NTU)"]) and row["Turbidity (NTU)"] > TURBIDITY_MAX:
            reasons.append("High turbidity")
        if pd.notna(row["Bacteria Count (CFU/mL)"]) and row["Bacteria Count (CFU/mL)"] > BACTERIA_MAX:
            reasons.append("High bacteria count")
        if pd.notna(row["Contaminant Level (ppm)"]) and row["Contaminant Level (ppm)"] > CONTAMINANT_MAX:
            reasons.append("High contaminant level")
        reasons.extend(field_reported_reasons(row))

        # dict.fromkeys(...) de-dupes while keeping order, so a weight-2
        # reason reads once in the displayed Risk Reason text even though
        # it counts twice toward the High Risk threshold.
        display_reasons = list(dict.fromkeys(reasons))

        if len(reasons) >= 2:
            return "High Risk", "; ".join(display_reasons)
        elif len(reasons) == 1:
            return "Moderate Risk", reasons[0]
        else:
            return "Safe", "No thresholds breached"

    risk_results = df.apply(classify_risk, axis=1, result_type="expand")
    df["Risk Level"] = risk_results[0]
    df["Risk Reason"] = risk_results[1]

    # --- Fill blank Disease Indicator / Risk cells with a derived note ---
    # Only ~9 of 324 rows have a hand-written field note in this column
    # (from Abuja/Benue South site surveys); those are left untouched.
    #
    # IMPORTANT: Risk Level (above) and Disease Indicator / Risk (below)
    # are DELIBERATELY two separate signals, not one score:
    #   - Risk Level = whether THIS water sample breaches a chemistry/
    #     microbiology threshold (pH, Turbidity, Bacteria, Contaminant).
    #   - Disease Indicator / Risk = whether the surrounding REGION has
    #     elevated Cholera/Typhoid/Diarrheal case rates in the population.
    # A site's water can test clean today while its region still carries a
    # high disease burden from other causes (storage, distribution,
    # sanitation, a past outbreak), so these are allowed to disagree, and
    # the app.py caption below says so explicitly rather than implying a
    # single unified score. (We tried folding disease case-rates into Risk
    # Level directly and it back-fired: the dataset's Cholera/Typhoid
    # values don't sit on an absolute WHO alert scale the way the
    # thresholds assumed. For example, Typhoid tops out at 99 in this dataset, so
    # the ">= 100 = High" band could never fire, while Cholera's median of
    # 24 meant "% >= 10 = High" fired for 254 of 315 rows. Folding that
    # straight into Risk Level pushed 320 of 324 rows to High Risk,
    # destroying the dashboard's ability to distinguish sites at all.)
    #
    # For the text below, Cholera/Typhoid now use the SAME dataset-relative
    # approach already used for Diarrheal (90th/75th percentile of this
    # dataset) instead of a borrowed absolute epidemiological scale, so all
    # three diseases are judged consistently and the label actually varies
    # from region to region instead of saying "High Cholera" almost everywhere.
    cholera_p90 = df["Cholera Cases per 100,000 people"].quantile(0.90)
    cholera_p75 = df["Cholera Cases per 100,000 people"].quantile(0.75)
    typhoid_p90 = df["Typhoid Cases per 100,000 people"].quantile(0.90)
    typhoid_p75 = df["Typhoid Cases per 100,000 people"].quantile(0.75)
    diarrheal_p90 = df["Diarrheal Cases per 100,000 people"].quantile(0.90)
    diarrheal_p75 = df["Diarrheal Cases per 100,000 people"].quantile(0.75)

    def disease_indicator_note(row):
        original = row.get("Disease Indicator / Risk")
        if pd.notna(original) and str(original).strip():
            return original  # keep the real, field-observed note as-is

        candidates = []  # (severity_rank, label) - higher rank displayed first

        cholera = row.get("Cholera Cases per 100,000 people")
        if pd.notna(cholera):
            if cholera >= cholera_p90:
                candidates.append((2, "High incidence risk for Cholera"))
            elif cholera >= cholera_p75:
                candidates.append((1, "Moderate incidence risk for Cholera"))

        typhoid = row.get("Typhoid Cases per 100,000 people")
        if pd.notna(typhoid):
            if typhoid >= typhoid_p90:
                candidates.append((2, "High incidence risk for Typhoid"))
            elif typhoid >= typhoid_p75:
                candidates.append((1, "Moderate incidence risk for Typhoid"))

        diarrheal = row.get("Diarrheal Cases per 100,000 people")
        if pd.notna(diarrheal):
            if diarrheal >= diarrheal_p90:
                candidates.append((2, "High incidence risk for Diarrheal disease"))
            elif diarrheal >= diarrheal_p75:
                candidates.append((1, "Moderate incidence risk for Diarrheal disease"))

        if candidates:
            # Highest-severity reason wins; only that one is kept for display.
            _, top_label = max(candidates, key=lambda c: c[0])
            return top_label

        return "No elevated disease indicators recorded"

    df["Disease Indicator / Risk"] = df.apply(disease_indicator_note, axis=1)

    # --- Water Treatment Method: replace missing values with a clear label
    # (~98 of 324 rows have no treatment method recorded in the source data)
    df["Water Treatment Method"] = df["Water Treatment Method"].fillna("Data not provided")

    # --- Give every region an approximate map location -------------------
    # NOTE: The dataset doesn't include exact GPS coordinates, so we use
    # approximate central points for each region (for visualization
    # purposes only) and add a small random "jitter" so multiple test
    # sites in the same region don't sit on top of each other.
    region_coords = {
        "Abuja (FCT)": (9.0765, 7.3986),
        "Benue South": (7.1900, 8.1300),
        "Central": (9.5000, 7.6000),
        "North": (11.9964, 8.5920),
        "South": (4.8156, 7.0498),
        "East": (6.4500, 7.5000),
        "West": (7.3775, 3.9470),
    }
    rng = np.random.default_rng(42)  # fixed seed = same map every run
    lat_list, lon_list = [], []
    for region in df["Region"]:
        base_lat, base_lon = region_coords.get(region, (9.0820, 8.6753))  # Nigeria center fallback
        lat_list.append(base_lat + rng.uniform(-0.35, 0.35))
        lon_list.append(base_lon + rng.uniform(-0.35, 0.35))
    df["lat"] = lat_list
    df["lon"] = lon_list

    return df


try:
    data = load_data(CSV_FILE)
except FileNotFoundError:
    st.error(
        f" Could not find **{CSV_FILE}**. "
        "Please make sure it is in the same folder as app.py, then refresh this page."
    )
    st.stop()

# -----------------------------------------------------------------------
# SIDEBAR: BRAND + FILTERS
# -----------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand-stack">
            <img class="sidebar-logo-img"
                 src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAbgAAACrCAYAAAAU/4kyAADyoElEQVR42uy9d5xd13UdvNY+974yvWHQO0AQADvYJRIU1XvjQLIsWbHjyLEducYl/mINh44TxyWyoziJSxw7dmQZQ8exLPdYIijJtgpISRR7BUB0DIBpr9x7z97fH+fcNyAJUpQtUZT89o/zw4CYV+a8c85ua60NdK1rXeta17rWta51rWtd61rXuta1rnWta13rWte61rWuda1rXeta17rWta51rWtde26bnJwUAOyuRNe61rWude1bybqOrWtd61rXuvataa/84M9f9v73v78KM3YdXte61rWufeuY/JP8rWNZ8g2Tk2OLmy766xOvfvUkSNv9iU+47pboWte61rWug/vmtZ07CcAe3XrVDzRWbBprrLng37z6t3/3Tfte9rJiYu/erpPrWte61rVvAeM/yd/ZjLu+59ba6W97y5fG67WNo0O9Njtz8uC6L3/+6t8/8r7TuBUG0rrbo2td61rXuhncN4/t3Ssgdeaay95dHxnbjCIvqu1GNrRqzcYnV2/+FZmiTkxPS3drdK1rXeta18F9E5mFjPX7Jvt0fMWP1Sma0Gy+bckq+mY+tvxdb//on+2e3rPHd0uVXeta17rWdXDfRNnbtGDPHt9/6eXfZcvXbOnLF/JaNUlmqbKumrjhnprdXx/4r+//3V8ZmL53wiKysmtd61rXuvZNaP90shQzYudO65vvH6tfevnvDfRWewaY0YlIywzjSeIuH6jld6K2UtK09ch3bb5jYudOd9/0dLcX17Wuda1r3QzuRWzT0wLScOG2n6ouG1/VkzW8V4qC1uNEHlts4ZVjw8nKZjNf7Fv247s/8pGLpt/xDh+VTrrWta51rWtdB/citIm9Du94h1/zU790dbJ87ftreaMwgSQiIImeJMETjYw1Eb5j1YCeQqW3um7DL9MM9wVKQde61rWuda3r4F6MDg6gGWY37vxZHR1LEnr0VJxTRxYgHWhN0p5YWMQ7Vo4lVWPWGFv78ov+9OM/OL1nj8de6wJOuta1rnWt6+BeZLZ3r8OePX7oF353D9ZvekWlWCyqThxFQm+NJBytLmL75xpcmVb52mW9ydlGs+hZseJn1v7+/9mMCejkpHVLlV3rWte61nVwLxIzIyYmbP0PTg7l4xt+Lq1VtEcMqSMAUih0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"
                 alt="AquaWatch Naija logo" />
            <div class="sidebar-sub">Hyperlocal Water Quality Monitor</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Location Filters")

    # NOTE: the dataset's finest geographic grain is "Region" (there is no
    # LGA-level breakdown in this CSV), so filters are Region + Water
    # Source Type: the same two dimensions the underlying data supports.
    region_options = ["All Regions"] + sorted(data["Region"].dropna().unique().tolist())
    selected_region = st.selectbox("Region", region_options)

    source_options = ["All Water Source Types"] + sorted(data["Water Source Type"].dropna().unique().tolist())
    selected_source = st.selectbox("Water Source Type", source_options)

    st.markdown("---")
    st.caption(
        f"**Safety thresholds:** pH ({PH_MIN}–{PH_MAX}) and Turbidity (≤ {TURBIDITY_MAX} NTU) "
        "reflect WHO drinking water guidance on operational/acceptability parameters, not "
        "formal numeric guideline values the way WHO sets for specific health-based "
        f"contaminants. Bacteria (≤ {int(BACTERIA_MAX)} CFU/mL) and Contaminant Level "
        f"(≤ {CONTAMINANT_MAX} ppm) are dataset-calibrated cutoffs with no WHO basis at all "
        "since the source data doesn't identify which pathogen or contaminant was tested. "
        "For context, WHO's actual standard for E. coli is zero detectable presence in any "
        "100 mL sample. High Risk = 2+ thresholds breached, Moderate = 1, Safe = 0. For the "
        "9 Abuja/Benue South rows missing numeric Bacteria/Contaminant readings, a "
        "qualitative field note (e.g., \"Extreme\", \"High\") stands in, so those sites are "
        "still screened on contamination, not judged on pH/Turbidity alone."
    )

# Apply the filters
filtered = data.copy()
if selected_region != "All Regions":
    filtered = filtered[filtered["Region"] == selected_region]
if selected_source != "All Water Source Types":
    filtered = filtered[filtered["Water Source Type"] == selected_source]

total_samples = len(filtered)
safe_count = int((filtered["Risk Level"] == "Safe").sum())
moderate_count = int((filtered["Risk Level"] == "Moderate Risk").sum())
high_count = int((filtered["Risk Level"] == "High Risk").sum())

safe_pct = 0 if total_samples == 0 else round(100 * safe_count / total_samples)
active_alerts = moderate_count + high_count

avg_ph = filtered["pH Level"].mean()
avg_turbidity = filtered["Turbidity (NTU)"].mean()
avg_bacteria = filtered["Bacteria Count (CFU/mL)"].mean()
avg_contaminant = filtered["Contaminant Level (ppm)"].mean()

# -----------------------------------------------------------------------
# HERO
# -----------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-wrap">
        <div>
            <div class="hero-kicker">CLOSING NIGERIA'S WATER DATA GAP</div>
            <div class="hero-title">AquaWatch Naija: Hyperlocal Water Quality Monitor</div>
            <div class="hero-sub">
                Know your water safety before you drink. A community portal for checking
                local drinking water quality and safety alerts across Nigerian towns,
                backing <b>UN SDG 6: Clean Water and Sanitation</b>.
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    f"Showing **{total_samples}** of **{len(data)}** total test records "
    f"(Region: *{selected_region}*, Source: *{selected_source}*)"
)

# -----------------------------------------------------------------------
# KPI CARDS
# -----------------------------------------------------------------------
c1, c2, c3 = st.columns(3, gap="medium")

with c1:
    st.markdown(
        f"""
        <div class="glass-card kpi-card">
            <div class="kpi-label">Total Samples</div>
            <div class="kpi-value">{total_samples}</div>
            <div class="kpi-meta">Current filtered municipal records</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="glass-card kpi-card">
            <div class="kpi-label">Safe Sources</div>
            <div class="kpi-value">{safe_pct}%</div>
            <div class="kpi-meta">Meets pH, turbidity, bacteria & contaminant screening range</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class="glass-card kpi-card">
            <div class="kpi-label">Active Alerts</div>
            <div class="kpi-value">{active_alerts}</div>
            <div class="kpi-meta">{high_count} high risk • {moderate_count} moderate risk</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# -----------------------------------------------------------------------
# SAFETY ALERT BANNERS
# -----------------------------------------------------------------------
st.markdown('<div class="section-title">Safety Status</div>', unsafe_allow_html=True)

if total_samples == 0:
    st.info("No test records match the selected filters. Try a different Region or Water Source Type.")
else:
    # All 3 banners render inside ONE shared "alert-grid" CSS Grid
    # container (instead of 3 separate st.columns) for the same reason
    # as the action-grid in Tab 3: st.columns sizes each column to its
    # own content, and "Safe" has noticeably less copy than "Moderate
    # Risk" or "High Risk", so it would render as a visibly shorter box.
    st.markdown(
        f"""
        <div class="alert-grid">
            <div class="alert-safe">
                <div class="alert-icon">✓</div>
                <div>
                    <div class="alert-title">Safe: Meets Screening Range</div>
                    <div class="alert-copy">{safe_count} sample(s) currently pass all safety checks.</div>
                </div>
            </div>
            <div class="alert-caution">
                <div class="alert-icon">!</div>
                <div>
                    <div class="alert-title">Moderate Risk: Monitor Closely</div>
                    <div class="alert-copy">{moderate_count} sample(s) breach one threshold and should be monitored or retested.</div>
                </div>
            </div>
            <div class="alert-danger">
                <div class="alert-icon">⚠</div>
                <div>
                    <div class="alert-title">High Risk: Unsafe Without Treatment</div>
                    <div class="alert-copy">{high_count} sample(s) breach multiple thresholds and require urgent action.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# -----------------------------------------------------------------------
# TABS
# -----------------------------------------------------------------------
tab_map, tab_quality, tab_action = st.tabs(
    ["Water Safety Map", "Water Quality Breakdown", "Community Action Steps"]
)

# -----------------------------------------------------------------------
# TAB 1: MAP  (pydeck, discrete Green/Orange/Red risk coloring)
# -----------------------------------------------------------------------
with tab_map:
    st.markdown('<div class="section-title">Water Safety Map</div>', unsafe_allow_html=True)
    st.caption("Note: Points are placed at approximate regional locations for illustration.")

    if total_samples == 0:
        st.info("No samples match the current filters.")
    else:
        map_df = filtered.copy()
        map_df["color"] = map_df["Risk Level"].apply(risk_level_color)

        # Scale circle size and zoom to how narrow the current selection is.
        num_regions_shown = map_df["Region"].nunique()
        if selected_region != "All Regions":
            point_radius_m = 1200
            map_zoom = 8.3
        elif num_regions_shown <= 2:
            point_radius_m = 2500
            map_zoom = 7.0
        else:
            point_radius_m = 6000
            map_zoom = 5.2

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position="[lon, lat]",
            get_fill_color="color",
            get_radius=point_radius_m,
            radius_min_pixels=3,
            radius_max_pixels=35,
            pickable=True,
            opacity=0.8,
            stroked=True,
            get_line_color=[255, 255, 255],
            line_width_min_pixels=1,
        )

        view_state = pdk.ViewState(
            latitude=map_df["lat"].mean(),
            longitude=map_df["lon"].mean(),
            zoom=map_zoom,
        )

        tooltip = {
            "html": (
                "<b>Year:</b> {Year}<br/>"
                "<b>Region:</b> {Region}<br/>"
                "<b>Water Source:</b> {Water Source Type}<br/>"
                "<b>Risk Level:</b> {Risk Level}<br/>"
                "<b>Reason:</b> {Risk Reason}"
            ),
            "style": {"backgroundColor": "black", "color": "white"},
        }

        st.pydeck_chart(
            pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip=tooltip,
                map_provider="carto",
                map_style="road",  # road basemap for context; border layer above highlights Nigeria specifically
            )
        )

        st.caption("🟢 Safe   →   🟠 Moderate Risk   →   🔴 High Risk. Hover over a point for more details.")

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Safe", safe_count)
        with k2:
            st.metric("Moderate Risk", moderate_count)
        with k3:
            st.metric("High Risk", high_count)
        with k4:
            st.metric("Mapped Sources", len(map_df))

        st.markdown('<div class="section-title">Water Safety Status by Region</div>', unsafe_allow_html=True)

        map_table_cols = ["Year", "Region", "Water Source Type", "Risk Level", "pH Level", "Turbidity (NTU)"]
        map_table = filtered[map_table_cols].sort_values(
            by="Risk Level", key=lambda s: s.map({"High Risk": 0, "Moderate Risk": 1, "Safe": 2})
        )
        st.dataframe(
            map_table.style.apply(highlight_risk, axis=1),
            width="stretch",
            hide_index=True,
            height=340,
            # Same approach as the Municipal Water Testing Results table
            # below: every width is an explicit pixel value sized from
            # this data's real header/value lengths, not the vague
            # "small"/"medium"/"large" presets. Water Source Type in
            # particular can hold values up to 30 characters (e.g.
            # "Awulema Borehole (Ohimini LGA)"), which "medium" was not
            # reliably wide enough for.
            column_config={
                "Year": st.column_config.NumberColumn(width=80, format="%d"),
                "Region": st.column_config.TextColumn(width=125),
                "Water Source Type": st.column_config.TextColumn(width=240),
                "Risk Level": st.column_config.TextColumn(width=135),
                "pH Level": st.column_config.NumberColumn(width=100, format="%.2f"),
                "Turbidity (NTU)": st.column_config.NumberColumn(width=145, format="%.2f"),
            },
        )

# -----------------------------------------------------------------------
# TAB 2: WATER QUALITY BREAKDOWN
# -----------------------------------------------------------------------
with tab_quality:
    st.markdown('<div class="section-title">Water Quality Breakdown</div>', unsafe_allow_html=True)

    q1, q2, q3, q4 = st.columns(4, gap="medium")

    with q1:
        st.markdown(
            f"""
            <div class="glass-card metric-mini">
                <div class="metric-mini-label">Average pH</div>
                <div class="metric-mini-value">{"N/A" if pd.isna(avg_ph) else f"{avg_ph:.2f}"}</div>
                <div class="metric-mini-note">Target {PH_MIN}–{PH_MAX}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with q2:
        turbidity_display = "N/A" if pd.isna(avg_turbidity) else f"{avg_turbidity:.2f}"
        st.markdown(
            f"""
            <div class="glass-card metric-mini">
                <div class="metric-mini-label">Average Turbidity</div>
                <div class="metric-mini-value">{turbidity_display} NTU</div>
                <div class="metric-mini-note">Threshold ≤ {TURBIDITY_MAX} NTU</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with q3:
        bacteria_display = "N/A" if pd.isna(avg_bacteria) else f"{avg_bacteria:.0f}"
        st.markdown(
            f"""
            <div class="glass-card metric-mini">
                <div class="metric-mini-label">Average Bacteria</div>
                <div class="metric-mini-value">{bacteria_display}</div>
                <div class="metric-mini-note">CFU/mL, threshold ≤ {int(BACTERIA_MAX)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with q4:
        contaminant_display = "N/A" if pd.isna(avg_contaminant) else f"{avg_contaminant:.2f}"
        st.markdown(
            f"""
            <div class="glass-card metric-mini">
                <div class="metric-mini-label">Average Contaminant Level</div>
                <div class="metric-mini-value">{contaminant_display} ppm</div>
                <div class="metric-mini-note">Threshold ≤ {CONTAMINANT_MAX} ppm</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    st.markdown('<div class="section-title">Municipal Water Testing Results</div>', unsafe_allow_html=True)

    st.info(
        "ℹ️ **Two different signals here.**\n\n"
        "- **Risk Level:** Does *this water sample* pass its safety checks? "
        "(pH, turbidity, bacteria, contaminants)\n"
        "- **Disease Indicator / Risk:** Is *this region* seeing higher rates of "
        "Cholera, Typhoid, or Diarrheal disease? (For the 9 Abuja/Benue South sites "
        "with no regional disease data, this instead shows the original contamination "
        "note recorded in the field for that sample.)\n\n"
        "These can disagree: a sample can show **Safe** while its region still shows "
        "a **High** disease indicator, because regional illness rates can come from "
        "other causes (storage, distribution, sanitation, a past outbreak), not just "
        "this one sample. **That's expected, not an error.**"
    )

    quality_cols = [
        "Year",
        "Region",
        "Water Source Type",
        "pH Level",
        "Turbidity (NTU)",
        "Bacteria Count (CFU/mL)",
        "Contaminant Level (ppm)",
        "Dissolved Oxygen (mg/L)",
        "Water Treatment Method",
        "Risk Level",
        "Risk Reason",
        "Disease Indicator / Risk",
    ]
    quality_table = filtered[quality_cols].sort_values(
        by="Risk Level", key=lambda s: s.map({"High Risk": 0, "Moderate Risk": 1, "Safe": 2})
    )

    # --- Show missing readings as "Data not provided" instead of "None" -
    # Bacteria Count and Contaminant Level are genuinely blank for some
    # rows (e.g. both Abuja readings). Streamlit's NumberColumn renders a
    # missing numeric value as the literal text "None", which reads like
    # a bug. This formats those two columns to text *only in this display
    # copy* of the table. quality_table is a local copy used solely for
    # rendering, so the real numeric columns in `filtered`/`df` (used for
    # the Average Bacteria Count / Average Contaminant Level metric cards
    # above and for Risk Level classification) are completely untouched.
    for numeric_col, decimals in [
        ("Bacteria Count (CFU/mL)", 0),
        ("Contaminant Level (ppm)", 2),
    ]:
        quality_table[numeric_col] = quality_table[numeric_col].apply(
            lambda v, d=decimals: "Data not provided" if pd.isna(v) else f"{v:.{d}f}"
        )

    # --- Shorten the 9 verbatim Abuja/Benue South field notes for display
    # These originally run up to 113 characters (e.g. "High Turbidity &
    # Microbial Hazard (Turbidity: 52.04 NTU far exceeds safe clarity
    # limits; Coliforms up to 237 MPN)") because they embed raw instrument
    # readings that duplicate what the pH/Turbidity/Bacteria columns
    # already show elsewhere in this same row. Keeping just the phrase
    # before the first "(" preserves the actual field-recorded severity
    # description (e.g. "High Turbidity & Microbial Hazard") without the
    # redundant numbers, cutting the column's max width by more than half.
    #
    # EXCEPTION: one of the 9 notes explicitly names diseases inside the
    # parenthetical ("Severe Pathogen Alert (Cholera / Typhoid / Dysentery
    # risk; Extremely high coliforms >1600 MPN)"). Blindly cutting at "("
    # would silently delete the only disease name in a column called
    # "Disease Indicator / Risk", so any disease keyword found in the
    # dropped portion is re-appended in short form instead of discarded.
    # Display-only: quality_table is a local copy, so the untouched
    # verbatim note is still what's stored in filtered/df.
    _DISEASE_KEYWORDS = ["Cholera", "Typhoid", "Dysentery", "Diarrheal", "Diarrhea"]

    def _shorten_field_note(v):
        if not isinstance(v, str):
            return v
        head = v.split(" (")[0].strip()
        head_lower = head.lower()
        mentioned = [
            kw for kw in _DISEASE_KEYWORDS
            if kw.lower() in v.lower() and kw.lower() not in head_lower
        ]
        if mentioned:
            return f"{head} ({'/'.join(dict.fromkeys(mentioned))} risk)"
        return head

    quality_table["Disease Indicator / Risk"] = quality_table["Disease Indicator / Risk"].apply(
        _shorten_field_note
    )

    st.dataframe(
        quality_table.style.apply(highlight_risk, axis=1),
        width="stretch",
        hide_index=True,
        height=520,
        # Every width below is an explicit pixel value sized from this
        # table's *actual* data (both the header text and the longest
        # real cell value in each column), not the "small"/"medium"/
        # "large" presets. Those presets were the root problem: several
        # headers here are much longer than they look:
        # "Bacteria Count (CFU/mL)", "Contaminant Level (ppm)", and
        # "Dissolved Oxygen (mg/L)" are all 23-24 characters, so
        # "small" was clipping the header text itself even though the
        # values underneath are short. "Risk Reason" (now max 65 chars,
        # after removing a duplicated-text bug in the field-reported
        # label) and "Disease Indicator / Risk" (now max 54 chars in this
        # display copy, after trimming the 9 verbatim field notes down to
        # their core phrase) both fit comfortably at the widths below.
        column_config={
            "Year": st.column_config.NumberColumn(width=80),
            "Region": st.column_config.TextColumn(width=125),
            "Water Source Type": st.column_config.TextColumn(width=240),
            "pH Level": st.column_config.NumberColumn(width=100, format="%.2f"),
            "Turbidity (NTU)": st.column_config.NumberColumn(width=145, format="%.2f"),
            # TextColumn (not NumberColumn) because quality_table now
            # holds these as pre-formatted text; see the "Data not
            # provided" formatting step above.
            "Bacteria Count (CFU/mL)": st.column_config.TextColumn(width=210),
            "Contaminant Level (ppm)": st.column_config.TextColumn(width=210),
            "Dissolved Oxygen (mg/L)": st.column_config.NumberColumn(width=200, format="%.2f"),
            "Water Treatment Method": st.column_config.TextColumn(width=200),
            "Risk Level": st.column_config.TextColumn(width=135),
            "Risk Reason": st.column_config.TextColumn(width=460),
            # 360 comfortably fits this column's new longest entry (54
            # chars, "Severe Pathogen Alert (Cholera/Typhoid/Dysentery
            # risk)") now that the 9 verbatim field notes are trimmed to
            # their core phrase (with any disease name preserved) in the
            # display step above.
            "Disease Indicator / Risk": st.column_config.TextColumn(width=360),
        },
    )
    st.caption("🟢 Safe   →   🟠 Moderate Risk   →   🔴 High Risk, matching the colors in the table above.")
    st.caption(
        "For the 9 Abuja/Benue South rows, this shows the original field note recorded for that "
        "sample. For every other row, it names the disease (Cholera, Typhoid, or Diarrheal) with the "
        "highest incidence relative to this dataset."
    )

# -----------------------------------------------------------------------
# TAB 3: COMMUNITY ACTION STEPS
# -----------------------------------------------------------------------
with tab_action:
    st.markdown('<div class="section-title">Community Action Steps</div>', unsafe_allow_html=True)

    # All 4 cards render inside ONE shared "action-grid" CSS Grid container
    # (instead of 4 separate st.columns) specifically so they come out as
    # equal-size squares. st.columns can't do this on its own: each column
    # sizes itself to its own content, so card 4 (much more text than 1-3)
    # would render taller than the rest and break the grid look. CSS Grid's
    # row items stretch to match the tallest cell by default, so all 4
    # cards always match card 4's height, however long its text is.
    st.markdown(
        textwrap.dedent("""
        <div class="action-grid">
            <div class="glass-card action-card">
                <div class="action-step">1</div>
                <div class="action-title">Check the local result</div>
                <div class="action-copy">
                    Confirm the <b>Year</b>, <b>Region</b>, <b>Water Source Type</b>, and latest <b>Risk Level</b> before taking action.
                    Refer to the <i>Water Safety Status by Region</i> table.
                </div>
            </div>
            <div class="glass-card action-card">
                <div class="action-step">2</div>
                <div class="action-title">Check the Disease Indicator / Risk</div>
                <div class="action-copy">
                    A water sample that's <b>Safe</b> doesn't rule out a regional disease signal. Check the
                    <b>Disease Indicator / Risk</b> column in the <i>Municipal Water Testing Results</i> table.
                    If it names any concern, such as elevated illness incidence or a
                    pathogen alert, use safe storage and handling (covered containers, clean
                    hands and utensils). Stay alert to symptoms locally. Only "No elevated
                    disease indicators recorded" means no extra precaution is needed here.
                </div>
            </div>
            <div class="glass-card action-card">
                <div class="action-step">3</div>
                <div class="action-title">Treat or avoid unsafe water</div>
                <div class="action-copy">
                    For <b>Moderate</b> or <b>High Risk</b> readings, use an approved treatment method or an alternative safe source.
                    Refer to the <i>Municipal Water Testing Results</i> table.
                </div>
            </div>
            <div class="glass-card action-card">
                <div class="action-step">4</div>
                <div class="action-title">Report and request retesting</div>
                <div class="action-copy">
                    Escalate repeated unsafe readings to the appropriate local water authority and request verification.
                </div>
            </div>
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )

    st.write("")

    if high_count > 0:
        st.error(f"Urgent: {high_count} High Risk reading(s) are visible under the current filters.")
    elif moderate_count > 0:
        st.warning(f"{moderate_count} Moderate Risk reading(s) are visible. Treatment or retesting is recommended.")
    else:
        st.success("No Moderate or High Risk readings are visible under the current filters.")

# -----------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------
st.markdown("---")
st.caption(
    "Built for Grow with Google | Mentor Me Collective BUILD Project — "
    "UN SDG 6: Clean Water and Sanitation."
)
