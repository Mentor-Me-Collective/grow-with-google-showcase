import csv
import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Practical energy-saving tips per appliance. Not part of Peace's dataset (her
# CSV columns are final) - original copy, shown alongside her data in the UI.
TIPS_BY_APPLIANCE = {
    "Refrigerator": "Keep the coils clear and set it to 37-40 degrees Fahrenheit, colder wastes energy without a food-safety benefit.",
    "Air Conditioner": "Shift your thermostat 2 degrees toward the outdoor temperature to trim cooling load.",
    "Washing Machine": "Wash full loads on cold, hot water accounts for most of a washer's energy draw.",
    "Television": "Turn on eco/auto-brightness mode and switch it off instead of leaving it on as background noise.",
    "Laptop": "Enable sleep after a few idle minutes instead of leaving it awake and charging all day.",
    "Gaming Console": "Turn off 'instant-on' standby, it keeps drawing power even when you're not playing.",
    "Microwave": "Already one of the more efficient ways to heat food, not much to save here.",
    "Dishwasher": "Skip the heated dry cycle and let dishes air-dry instead.",
    "LED Lights": "Already efficient, pair with motion sensors or timers in rooms you tend to leave lit.",
    "Clothes Dryer": "Use the moisture-sensing auto cycle instead of a fixed timer, and clean the lint trap every load.",
    "Router": "Not worth turning off, but check you're not also running a second always-on extender you don't need.",
}

DEFAULT_TIP = "Consider cutting its hours or unplugging it when idle, every hour off is a direct saving."


def slugify(label):
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def load_eia_appliances():
    """Peace's detailed EIA dataset: Appliance, Avg_Watts, Default_Hours_Per_Day, Category."""
    with open(DATA_DIR / "eia_appliances.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["Avg_Watts"] = float(row["Avg_Watts"])
        row["Default_Hours_Per_Day"] = float(row["Default_Hours_Per_Day"])
    return rows


def load_tenant_profiles():
    """Peace's 3 tenant baselines (1-Bed / 2-Bed / 3-Bed), hours per appliance."""
    with open(DATA_DIR / "tenant_profiles.json") as f:
        return json.load(f)


def load_simulator_appliances():
    """
    Peace's EIA appliance dataset, reshaped for the simulator UI: stable slug
    id, camelCase-friendly field names, a 0-24hr slider range, and a tip.
    """
    appliances = []
    for row in load_eia_appliances():
        appliances.append(
            {
                "id": slugify(row["Appliance"]),
                "label": row["Appliance"],
                "watts": row["Avg_Watts"],
                "default_hours": row["Default_Hours_Per_Day"],
                "min_hours": 0,
                "max_hours": 24,
                "category": row["Category"],
                "tip": TIPS_BY_APPLIANCE.get(row["Appliance"], DEFAULT_TIP),
            }
        )
    return appliances


def load_tenant_baseline_profiles():
    """
    Peace's 3 tenant profiles, reshaped for the simulator: an id/label plus
    hours keyed by the same appliance ids load_simulator_appliances() uses,
    so a profile's hours can be applied directly to the appliance list.
    """
    profiles = []
    for label, hours_by_appliance_label in load_tenant_profiles().items():
        profiles.append(
            {
                "id": slugify(label),
                "label": label,
                "hours_by_appliance": {
                    slugify(appliance_label): hours
                    for appliance_label, hours in hours_by_appliance_label.items()
                },
            }
        )
    return profiles


def load_regions():
    """Rate/carbon table across 15 regions, used to make the simulator global rather than US-only."""
    with open(DATA_DIR / "regions.json") as f:
        return json.load(f)


def get_region(region_id):
    return next((r for r in load_regions() if r["id"] == region_id), None)


def get_baseline_profile(baseline_id):
    return next((p for p in load_tenant_baseline_profiles() if p["id"] == baseline_id), None)
