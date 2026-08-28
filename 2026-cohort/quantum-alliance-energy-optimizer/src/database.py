"""
Database access layer for the Household Energy Efficiency Optimizer.

This module handles communication with the SQLite database.

It does not contain energy calculation formulas.
Those calculations are handled by energy_calculations.py.
"""

import sqlite3
from pathlib import Path


# The database is stored in the same directory as this file.
DB_PATH = Path(__file__).resolve().parent / "energy_optimizer.db"


def get_connection():
    """
    Create and return a connection to the SQLite database.

    Foreign key enforcement is enabled for this connection.

    Returns:
        sqlite3.Connection: Active database connection.
    """

    connection = sqlite3.connect(DB_PATH)

    # Allows database rows to be accessed by column name.
    connection.row_factory = sqlite3.Row

    # SQLite requires this to be enabled for foreign key constraints.
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection


def create_household(
    housing_type,
    square_footage=None,
    apartment_size_category=None,
    electricity_rate_per_kwh=None,
    carbon_emission_factor=None
):
    """
    Create a new household.

    The database schema requires either square footage or
    an apartment size category.

    Args:
        housing_type: Household housing type.
        square_footage: Optional exact home size.
        apartment_size_category: Optional size category.
        electricity_rate_per_kwh: Optional electricity price per kWh.
        carbon_emission_factor: Optional kg CO2e per kWh.

    Returns:
        int: ID of the newly created household.
    """

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO households (
                housing_type,
                square_footage,
                apartment_size_category,
                electricity_rate_per_kwh,
                carbon_emission_factor
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                housing_type,
                square_footage,
                apartment_size_category,
                electricity_rate_per_kwh,
                carbon_emission_factor
            )
        )

        return cursor.lastrowid


def get_household(household_id):
    """
    Retrieve one household by its ID.

    Args:
        household_id: ID of the household.

    Returns:
        sqlite3.Row or None: Household record if found.
    """

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                household_id,
                housing_type,
                square_footage,
                apartment_size_category,
                electricity_rate_per_kwh,
                carbon_emission_factor,
                created_at
            FROM households
            WHERE household_id = ?
            """,
            (household_id,)
        ).fetchone()


def get_appliances():
    """
    Retrieve all appliance reference records.

    Returns:
        list: Appliance records from the appliances table.
    """

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                appliance_id,
                appliance_name,
                default_wattage,
                energy_star_rated
            FROM appliances
            ORDER BY appliance_name
            """
        ).fetchall()


def add_household_appliance(
    household_id,
    appliance_id,
    appliance_quantity=1,
    wattage_override=None,
    daily_usage_hours=0
):
    """
    Add an appliance to a household.

    Args:
        household_id: ID of the household.
        appliance_id: ID of the appliance reference record.
        appliance_quantity: Number of appliances owned.
        wattage_override: Optional household-specific wattage.
        daily_usage_hours: Average hours used per day.

    Returns:
        None
    """

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO household_appliances (
                household_id,
                appliance_id,
                appliance_quantity,
                wattage_override,
                daily_usage_hours
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                household_id,
                appliance_id,
                appliance_quantity,
                wattage_override,
                daily_usage_hours
            )
        )


def get_household_appliances(household_id):
    """
    Retrieve all appliances belonging to a household.

    The query combines household-specific usage information
    with the appliance reference data.

    If a household has supplied a wattage override, that value
    is returned as the effective wattage. Otherwise, the
    appliance's default wattage is returned.

    Args:
        household_id: ID of the household.

    Returns:
        list: Household appliance records.
    """

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                ha.household_id,
                ha.appliance_id,
                a.appliance_name,
                a.default_wattage,
                ha.wattage_override,
                CASE
                    WHEN ha.wattage_override IS NOT NULL
                    THEN ha.wattage_override
                    ELSE a.default_wattage
                END AS effective_wattage,
                ha.appliance_quantity,
                ha.daily_usage_hours,
                a.energy_star_rated
            FROM household_appliances AS ha
            JOIN appliances AS a
                ON ha.appliance_id = a.appliance_id
            WHERE ha.household_id = ?
            ORDER BY a.appliance_name
            """,
            (household_id,)
        ).fetchall()


def get_benchmark(housing_type, region=None):
    """
    Retrieve the benchmark for a housing type and region.

    The current MVP reference data uses NULL for region.

    Args:
        housing_type: Household housing type.
        region: Optional benchmark region.

    Returns:
        sqlite3.Row or None: Matching benchmark record.
    """

    with get_connection() as connection:
        if region is None:
            return connection.execute(
                """
                SELECT
                    benchmark_id,
                    housing_type,
                    region,
                    benchmark_kwh_monthly
                FROM benchmarks
                WHERE housing_type = ?
                  AND region IS NULL
                LIMIT 1
                """,
                (housing_type,)
            ).fetchone()

        return connection.execute(
            """
            SELECT
                benchmark_id,
                housing_type,
                region,
                benchmark_kwh_monthly
            FROM benchmarks
            WHERE housing_type = ?
              AND region = ?
            LIMIT 1
            """,
            (housing_type, region)
        ).fetchone()


def save_usage_estimate(
    household_id,
    estimated_kwh_monthly,
    estimated_cost_monthly,
    pct_vs_benchmark=None
):
    """
    Save a calculated household estimate for historical tracking.

    Args:
        household_id: ID of the household.
        estimated_kwh_monthly: Estimated monthly electricity consumption.
        estimated_cost_monthly: Estimated monthly electricity cost.
        pct_vs_benchmark: Household consumption as a percentage
            of the benchmark.

    Returns:
        int: ID of the newly created estimate.
    """

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO usage_estimates (
                household_id,
                estimated_kwh_monthly,
                estimated_cost_monthly,
                pct_vs_benchmark
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                household_id,
                estimated_kwh_monthly,
                estimated_cost_monthly,
                pct_vs_benchmark
            )
        )

        return cursor.lastrowid


def get_usage_history(household_id):
    """
    Retrieve historical estimates for a household.

    Args:
        household_id: ID of the household.

    Returns:
        list: Historical usage estimates ordered newest first.
    """

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                estimate_id,
                household_id,
                estimated_kwh_monthly,
                estimated_cost_monthly,
                pct_vs_benchmark,
                generated_at
            FROM usage_estimates
            WHERE household_id = ?
            ORDER BY generated_at DESC
            """,
            (household_id,)
        ).fetchall()