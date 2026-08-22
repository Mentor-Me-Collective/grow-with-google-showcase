from flask import Flask, jsonify, request
from flask_cors import CORS

import data
from calculations import (
    build_breakdown,
    calc_carbon,
    calculate_home_totals,
    energy_score,
    build_delta,
    sum_kwh,
    top_energy_hogs,
)

app = Flask(__name__)
CORS(app)

DEFAULT_REGION_ID = "us-national"
DEFAULT_BASELINE_ID = "1-bed-apartment"


def resolve_profile_hours(appliances, profile):
    """A profile only specifies hours for the appliances typical of that home
    size; anything it doesn't mention falls back to that appliance's own EIA
    default rather than zeroing out (a laptop doesn't stop existing just
    because a profile forgot to list it)."""
    return {
        appliance["id"]: profile["hours_by_appliance"].get(appliance["id"], appliance["default_hours"])
        for appliance in appliances
    }


@app.route("/")
def index():
    return jsonify(message="Tenant Power Tracker API - see /api/health")


@app.route("/api/health")
def health():
    return jsonify(status="ok")


@app.route("/api/appliances")
def appliances():
    """Peace's detailed EIA dataset - 11 individual appliances with watts/hours/category."""
    return jsonify(data.load_eia_appliances())


@app.route("/api/appliances/totals")
def appliance_totals():
    """Whole-home monthly kWh/cost/carbon from the detailed EIA dataset at default hours."""
    devices = [
        {
            "Appliance": d["Appliance"],
            "Avg_Watts": d["Avg_Watts"],
            "Default_Hours_Per_Day": d["Default_Hours_Per_Day"],
        }
        for d in data.load_eia_appliances()
    ]
    return jsonify(calculate_home_totals(devices))


@app.route("/api/tenant-profiles")
def tenant_profiles():
    return jsonify(data.load_tenant_profiles())


@app.route("/api/simulator/appliances")
def simulator_appliances():
    """Peace's 11 EIA appliances, shaped for the simulator UI (id/watts/hours/category/tip)."""
    return jsonify(data.load_simulator_appliances())


@app.route("/api/simulator/baseline-profiles")
def simulator_baseline_profiles():
    """Peace's 3 tenant profiles, reshaped to hours keyed by simulator appliance id."""
    return jsonify(data.load_tenant_baseline_profiles())


@app.route("/api/regions")
def regions():
    return jsonify(data.load_regions())


@app.route("/api/simulate", methods=["POST"])
def simulate():
    """
    Runs the simulator's math server-side, region-aware.

    Body: {
      "hours_by_appliance": {"refrigerator": 24, "air-conditioner": 8, ...},
      "region_id": "us-california",     # optional, defaults to us-national
      "baseline_id": "2-bed-apartment"  # optional, defaults to 1-bed-apartment
    }

    The score baseline isn't a flat number - it's what the selected tenant
    profile's own hours would cost, computed the same way the user's
    scenario is, so it reflects the same appliances and the same region.
    """
    body = request.get_json(silent=True) or {}
    hours_by_appliance = body.get("hours_by_appliance", {})
    region_id = body.get("region_id", DEFAULT_REGION_ID)
    baseline_id = body.get("baseline_id", DEFAULT_BASELINE_ID)

    region = data.get_region(region_id)
    if region is None:
        return jsonify(error=f"Unknown region_id '{region_id}'"), 400

    baseline = data.get_baseline_profile(baseline_id)
    if baseline is None:
        return jsonify(error=f"Unknown baseline_id '{baseline_id}'"), 400

    appliances = data.load_simulator_appliances()

    breakdown = build_breakdown(hours_by_appliance, appliances, rate=region["rate_per_kwh"])
    total_kwh = sum_kwh(breakdown)
    total_cost = total_kwh * region["rate_per_kwh"]
    total_carbon_lbs = calc_carbon(total_kwh, factor=region["carbon_lbs_per_kwh"])

    baseline_hours = resolve_profile_hours(appliances, baseline)
    baseline_breakdown = build_breakdown(baseline_hours, appliances, rate=region["rate_per_kwh"])
    baseline_kwh = sum_kwh(baseline_breakdown)

    return jsonify(
        region=region,
        baseline=baseline,
        breakdown=breakdown,
        total_kwh=round(total_kwh, 2),
        total_cost=round(total_cost, 2),
        total_carbon_lbs=round(total_carbon_lbs, 2),
        top_hogs=top_energy_hogs(breakdown, 3),
        baseline_kwh=round(baseline_kwh, 2),
        score=energy_score(total_kwh, baseline_kwh),
        delta_kwh=build_delta(total_kwh, baseline_kwh),
    )


if __name__ == "__main__":
    app.run(debug=True, port=5050)
