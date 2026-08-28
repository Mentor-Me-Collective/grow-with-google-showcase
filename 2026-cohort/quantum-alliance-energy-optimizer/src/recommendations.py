"""
Rule-based energy efficiency recommendations.

This module generates simple, explainable recommendations
using the household analysis results.

The recommendation engine does not use machine learning.
"""


def generate_recommendations(analysis_result):
    """
    Generate recommendations for a household.

    Args:
        analysis_result: Dictionary returned by
            analyze_household().

    Returns:
        list: A list of recommendation dictionaries.
    """

    recommendations = []

    monthly_kwh = analysis_result["monthly_kwh"]
    benchmark_kwh = analysis_result["benchmark_kwh_monthly"]
    appliances = analysis_result["appliances"]

    # ------------------------------------------------------------
    # Rule 1: Household consumption above benchmark
    # ------------------------------------------------------------

    if (
        benchmark_kwh is not None
        and monthly_kwh > benchmark_kwh
    ):
        recommendations.append({
            "type": "household",
            "priority": "high",
            "title": "Household consumption is above the benchmark",
            "message": (
                "Your estimated monthly electricity consumption is "
                "above the reference level for your housing type. "
                "Review your highest-consuming appliances and "
                "reduce unnecessary usage where possible."
            ),
        })

    # ------------------------------------------------------------
    # Rule 2: Identify high-impact appliances
    #
    # An appliance is considered high-impact if it accounts for
    # at least 20% of total household monthly consumption.
    # ------------------------------------------------------------

    if monthly_kwh > 0:

        for appliance in appliances:

            appliance_share = (
                appliance["monthly_kwh"] / monthly_kwh
            ) * 100

            if appliance_share >= 20:

                recommendations.append({
                    "type": "appliance",
                    "priority": "high",
                    "title": (
                        f"{appliance['appliance_name']} "
                        "is a major energy consumer"
                    ),
                    "message": (
                        f"{appliance['appliance_name']} accounts for "
                        f"{appliance_share:.1f}% of your estimated "
                        "monthly electricity consumption. "
                        "Consider reducing its usage where practical."
                    ),
                    "appliance_name": appliance["appliance_name"],
                    "monthly_kwh": appliance["monthly_kwh"],
                    "share_percent": appliance_share,
                })

    # ------------------------------------------------------------
    # Rule 3: Long daily usage
    #
    # Appliances used for more than 8 hours per day are flagged.
    # ------------------------------------------------------------

    for appliance in appliances:

        if appliance["daily_usage_hours"] > 8:

            recommendations.append({
                "type": "usage",
                "priority": "medium",
                "title": (
                    f"Review usage of {appliance['appliance_name']}"
                ),
                "message": (
                    f"{appliance['appliance_name']} is used for "
                    f"{appliance['daily_usage_hours']} hours per day. "
                    "Reducing unnecessary operating time could lower "
                    "your electricity consumption."
                ),
                "appliance_name": appliance["appliance_name"],
                "daily_usage_hours": appliance["daily_usage_hours"],
            })

    # ------------------------------------------------------------
    # Rule 4: If no issues were detected
    # ------------------------------------------------------------

    if not recommendations:

        recommendations.append({
            "type": "general",
            "priority": "low",
            "title": "No major issues detected",
            "message": (
                "Your estimated household consumption is within the "
                "reference benchmark and no major appliance usage "
                "patterns were flagged."
            ),
        })

    return recommendations