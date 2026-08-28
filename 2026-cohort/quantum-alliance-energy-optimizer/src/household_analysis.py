from src.database import (
    get_household,
    get_household_appliances,
    get_benchmark,
)
from src.energy_calculations import (
    calculate_daily_kwh,
    calculate_monthly_kwh,
    calculate_monthly_cost,
    calculate_carbon_footprint,
    calculate_benchmark_percentage,
)
from src.energy_efficiency import (
    calculate_efficiency_score,
    get_efficiency_label,
)

# ------------------------------------------------------------
# Fallback defaults, used when a household hasn't provided its
# own electricity_rate_per_kwh / carbon_emission_factor. Both
# fields are optional in the schema, so these prevent a crash
# for tenants who skip them. Approximate U.S. averages — swap
# in more precise figures if the team has better ones.
# ------------------------------------------------------------
DEFAULT_ELECTRICITY_RATE_PER_KWH = 0.17  # USD/kWh
DEFAULT_CARBON_EMISSION_FACTOR = 0.4     # kg CO2e/kWh


def analyze_household(household_id):
    household = get_household(household_id)
    if not household:
        return None
    benchmark = get_benchmark(household["housing_type"])
    if not benchmark:
        benchmark_kwh_monthly = None
    else:
        benchmark_kwh_monthly = benchmark["benchmark_kwh_monthly"]

    appliances = get_household_appliances(household_id)
    total_daily_kwh = 0.0
    appliance_analysis = []
    for app_row in appliances:
        app = dict(app_row)
        daily_kwh = calculate_daily_kwh(
            app["effective_wattage"],
            app["appliance_quantity"],
            app["daily_usage_hours"],
        )
        monthly_kwh = calculate_monthly_kwh(daily_kwh)
        total_daily_kwh += daily_kwh
        appliance_analysis.append({
            "appliance_id": app["appliance_id"],
            "appliance_name": app["appliance_name"],
            "wattage": app["effective_wattage"],
            "quantity": app["appliance_quantity"],
            "daily_usage_hours": app["daily_usage_hours"],
            "daily_kwh": round(daily_kwh, 2),
            "monthly_kwh": round(monthly_kwh, 2),
            "energy_star_rated": app["energy_star_rated"],
        })

    total_monthly_kwh = calculate_monthly_kwh(total_daily_kwh)

    # Fall back to defaults if the household didn't set these
    # (both are optional in the schema).
    electricity_rate = (
        household["electricity_rate_per_kwh"]
        if household["electricity_rate_per_kwh"] is not None
        else DEFAULT_ELECTRICITY_RATE_PER_KWH
    )
    carbon_factor = (
        household["carbon_emission_factor"]
        if household["carbon_emission_factor"] is not None
        else DEFAULT_CARBON_EMISSION_FACTOR
    )

    monthly_cost = calculate_monthly_cost(total_monthly_kwh, electricity_rate)
    monthly_carbon = calculate_carbon_footprint(total_monthly_kwh, carbon_factor)

    pct_vs_benchmark = calculate_benchmark_percentage(
        total_monthly_kwh,
        benchmark_kwh_monthly,
    )
    efficiency_score = calculate_efficiency_score(pct_vs_benchmark)
    efficiency_label = get_efficiency_label(efficiency_score)

    return {
        "household_id": household["household_id"],
        "housing_type": household["housing_type"],
        "apartment_size_category": household["apartment_size_category"],
        "electricity_rate_per_kwh": electricity_rate,
        "carbon_emission_factor": carbon_factor,
        "benchmark_kwh_monthly": benchmark_kwh_monthly,
        "daily_kwh": round(total_daily_kwh, 2),
        "monthly_kwh": round(total_monthly_kwh, 2),
        "monthly_cost": round(monthly_cost, 2),
        "monthly_carbon_kg": round(monthly_carbon, 2),
        "pct_vs_benchmark": (
            round(pct_vs_benchmark, 2)
            if pct_vs_benchmark is not None
            else None
        ),
        "efficiency_score": efficiency_score,
        "efficiency_label": efficiency_label,
        "appliances": appliance_analysis,
    }
