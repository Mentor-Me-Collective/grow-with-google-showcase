ELECTRICITY_RATE = 0.16  # $ per kWh - US average, used where no region is specified
CARBON_FACTOR = 0.4  # kg CO2 per kWh, used where no region is specified


def calc_kwh(watts, hours_per_day):
    return watts * hours_per_day * 30 / 1000


def calc_cost(kwh, rate=ELECTRICITY_RATE):
    return kwh * rate


def calc_carbon(kwh, factor=CARBON_FACTOR):
    return kwh * factor


def process_device(device):
    """Mutates and returns the given appliance dict with Monthly_kWh,
    Monthly_Cost, and Monthly_Carbon added."""
    kwh = calc_kwh(device["Avg_Watts"], device["Default_Hours_Per_Day"])
    device["Monthly_kWh"] = round(kwh, 2)
    device["Monthly_Cost"] = round(calc_cost(kwh), 2)
    device["Monthly_Carbon"] = round(calc_carbon(kwh), 2)
    return device


def calculate_home_totals(devices):
    total_kwh = total_cost = total_carbon = 0
    for device in devices:
        processed = process_device(device)
        total_kwh += processed["Monthly_kWh"]
        total_cost += processed["Monthly_Cost"]
        total_carbon += processed["Monthly_Carbon"]

    return {
        "Total_Monthly_kWh": round(total_kwh, 2),
        "Total_Monthly_Cost": round(total_cost, 2),
        "Total_Monthly_Carbon": round(total_carbon, 2),
    }


# --- Simulator engine, mirrored from frontend/src/lib/calculations.ts ---
# The frontend runs this same math client-side for live slider feedback;
# this copy is what backs /api/simulate so a non-JS caller gets identical
# numbers. Presentation-only helpers (currency/kWh string formatting) were
# left out - that's a display concern for whichever layer renders the response.


def clamp_hours(hours, min_hours, max_hours, default_hours):
    """Clamps hours/day input so edge values (0, 24, negatives, invalid) never crash or go negative."""
    try:
        hours = float(hours)
    except (TypeError, ValueError):
        return default_hours
    if hours != hours:  # NaN
        return default_hours
    return min(max_hours, max(min_hours, hours))


def build_breakdown(hours_by_appliance, appliances, rate=ELECTRICITY_RATE):
    """
    Takes {appliance_id: hours_per_day} and a list of appliance dicts
    (id, watts, default_hours, min_hours, max_hours), and returns
    per-appliance hours/kWh/cost for the month.
    """
    breakdown = []
    for appliance in appliances:
        hours = clamp_hours(
            hours_by_appliance.get(appliance["id"]),
            appliance["min_hours"],
            appliance["max_hours"],
            appliance["default_hours"],
        )
        kwh = calc_kwh(appliance["watts"], hours)
        breakdown.append({
            "appliance": appliance,
            "hours": hours,
            "kwh": kwh,
            "cost": calc_cost(kwh, rate),
        })
    return breakdown


def sum_kwh(breakdown):
    return sum(item["kwh"] for item in breakdown)


def top_energy_hogs(breakdown, count=3):
    return sorted(breakdown, key=lambda item: item["kwh"], reverse=True)[:count]


def energy_score(user_kwh, baseline_kwh):
    """
    Score of 1-100 relative to a regional baseline. Matching the baseline
    lands at 100; every 1% above baseline usage costs one point, floored at 1
    so it never crashes into zero or negative territory.
    """
    if baseline_kwh <= 0:
        return 100 if user_kwh <= 0 else 1
    ratio = user_kwh / baseline_kwh
    raw = 100 - (ratio - 1) * 100
    return min(100, max(1, round(raw)))


def build_delta(current, base):
    """Compares current to base (e.g. usage vs default) and returns
    {diff, is_good, direction} for a stat tile's delta badge."""
    diff = current - base
    if abs(diff) < 0.01:
        return {"diff": 0, "is_good": True, "direction": "down"}
    direction = "up" if diff > 0 else "down"
    return {"diff": diff, "is_good": diff <= 0, "direction": direction}
