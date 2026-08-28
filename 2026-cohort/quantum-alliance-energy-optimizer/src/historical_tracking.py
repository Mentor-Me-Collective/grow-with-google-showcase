"""
Historical tracking for household energy estimates.

This module connects household analysis results to the
usage_estimates table so that households can track their
estimated energy consumption over time.
"""

from src.household_analysis import analyze_household
from src.database import (
    save_usage_estimate,
    get_usage_history,
)


def save_household_analysis(household_id):
    """
    Analyze a household and save the current results
    to the historical usage table.

    Args:
        household_id: ID of the household to analyze.

    Returns:
        int: ID of the newly saved estimate.
    """

    # Run the current household analysis.
    result = analyze_household(household_id)

    # Save the values supported by the usage_estimates schema.
    estimate_id = save_usage_estimate(
        household_id=household_id,
        estimated_kwh_monthly=result["monthly_kwh"],
        estimated_cost_monthly=result["monthly_cost"],
        pct_vs_benchmark=result["pct_vs_benchmark"],
    )

    return estimate_id


def get_household_history(household_id):
    """
    Retrieve historical energy estimates for a household.

    Args:
        household_id: ID of the household.

    Returns:
        list: Historical estimates ordered newest first.
    """

    return get_usage_history(household_id)