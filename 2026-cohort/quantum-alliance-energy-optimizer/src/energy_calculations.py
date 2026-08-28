"""
Core energy calculations for the Household Energy Efficiency Optimizer.

This module contains calculation logic only.
It does not connect to SQLite or Streamlit.

All energy calculations are estimates based on appliance wattage,
quantity, and daily usage hours.

MVP assumptions:
- 30 days are used for a monthly estimate.
- Carbon emission factor is expressed as kg CO2e per kWh.
"""


DAYS_PER_MONTH = 30


def calculate_daily_kwh(
    wattage: float,
    quantity: int,
    daily_usage_hours: float
) -> float:
    """
    Calculate an appliance's estimated daily electricity consumption.

    Formula:
        daily kWh = (wattage × quantity × usage hours) / 1000

    Args:
        wattage: Appliance power rating in watts.
        quantity: Number of appliances owned.
        daily_usage_hours: Average hours used per day.

    Returns:
        Estimated daily electricity consumption in kWh.
    """

    return (wattage * quantity * daily_usage_hours) / 1000


def calculate_monthly_kwh(
    daily_kwh: float,
    days_per_month: int = DAYS_PER_MONTH
) -> float:
    """
    Calculate estimated monthly electricity consumption.

    Args:
        daily_kwh: Estimated daily electricity consumption in kWh.
        days_per_month: Number of days used for the monthly estimate.

    Returns:
        Estimated monthly electricity consumption in kWh.
    """

    return daily_kwh * days_per_month


def calculate_monthly_cost(
    monthly_kwh: float,
    electricity_rate_per_kwh: float
) -> float:
    """
    Calculate estimated monthly electricity cost.

    Args:
        monthly_kwh: Estimated monthly electricity consumption.
        electricity_rate_per_kwh: Electricity price per kWh.

    Returns:
        Estimated monthly electricity cost.
    """

    return monthly_kwh * electricity_rate_per_kwh


def calculate_carbon_footprint(
    monthly_kwh: float,
    carbon_emission_factor: float
) -> float:
    """
    Calculate estimated monthly carbon footprint.

    The carbon emission factor is assumed to be expressed as
    kg CO2e per kWh.

    Args:
        monthly_kwh: Estimated monthly electricity consumption.
        carbon_emission_factor: kg CO2e emitted per kWh.

    Returns:
        Estimated monthly carbon footprint in kg CO2e.
    """

    return monthly_kwh * carbon_emission_factor


def calculate_benchmark_percentage(
    monthly_kwh: float,
    benchmark_kwh_monthly: float
) -> float | None:
    """
    Calculate household consumption as a percentage of its benchmark.

    Formula:
        percentage = (household kWh / benchmark kWh) × 100

    Returns:
        Percentage of benchmark consumption.

        Returns None if the benchmark is zero because division
        by zero is not meaningful.
    """

    if benchmark_kwh_monthly == 0:
        return None

    return (monthly_kwh / benchmark_kwh_monthly) * 100


def calculate_appliance_monthly_kwh(
    wattage: float,
    quantity: int,
    daily_usage_hours: float,
    days_per_month: int = DAYS_PER_MONTH
) -> float:
    """
    Calculate an appliance's estimated monthly electricity consumption.

    This combines the daily and monthly calculations into one
    convenience function.
    """

    daily_kwh = calculate_daily_kwh(
        wattage,
        quantity,
        daily_usage_hours
    )

    return calculate_monthly_kwh(
        daily_kwh,
        days_per_month
    )