"""
Benchmark-based Energy Efficiency Score.

This module converts a household's consumption relative to its
benchmark into a simple MVP efficiency score.

The score is a rule-based indicator. It is not a scientific
measurement of physical energy efficiency.
"""


def calculate_efficiency_score(pct_vs_benchmark):
    """
    Calculate a benchmark-based energy efficiency score.

    Lower consumption relative to the benchmark receives a
    higher score.

    Args:
        pct_vs_benchmark: Household consumption expressed as
            a percentage of the benchmark.

    Returns:
        int or None: Efficiency score from 25 to 100.

        Returns None when a benchmark percentage is unavailable.
    """

    if pct_vs_benchmark is None:
        return None

    if pct_vs_benchmark <= 50:
        return 100

    if pct_vs_benchmark <= 75:
        return 85

    if pct_vs_benchmark <= 100:
        return 70

    if pct_vs_benchmark <= 125:
        return 55

    if pct_vs_benchmark <= 150:
        return 40

    return 25


def get_efficiency_label(score):
    """
    Convert an efficiency score into a user-friendly label.

    Args:
        score: Efficiency score.

    Returns:
        str or None: Description of the score.
    """

    if score is None:
        return None

    if score >= 85:
        return "Efficient"

    if score >= 70:
        return "Within benchmark"

    if score >= 55:
        return "Above benchmark"

    if score >= 40:
        return "High consumption"

    return "Very high consumption"