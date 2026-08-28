import sqlite3

DB_NAME = "energy_optimizer.db"


def load_reference_data(db_name=DB_NAME):
    """
    Load appliance and household energy benchmark reference data
    into the SQLite database.

    The values are representative MVP reference values.
    They are intended for estimation and benchmarking, not
    as exact measurements for individual appliances or homes.
    """

    # ------------------------------------------------------------
    # Appliance reference data
    #
    # These are representative default wattages used when the
    # user does not know the actual wattage of an appliance.
    #
    # Users can override the wattage in household_appliances
    # when they know the actual appliance rating.
    # ------------------------------------------------------------

    appliances = [
        # (appliance_name, default_wattage, energy_star_rated)

        ("Refrigerator", 150, 1),
        ("Window Air Conditioner", 900, 1),
        ("Washing Machine", 500, 1),
        ("Clothes Dryer", 3000, 1),
        ("Dishwasher", 1200, 1),
        ("Microwave", 1000, 0),
        ("Space Heater", 1500, 0),
        ("Television (LED)", 100, 1),
        ("Laptop", 50, 0),
        ("LED Light Bulb", 10, 0),
    ]

    # ------------------------------------------------------------
    # Benchmark reference data
    #
    # These are simplified MVP benchmark values used to provide
    # directional comparisons between the household estimate and
    # a reference level.
    #
    # They are not official household-level EIA averages.
    # ------------------------------------------------------------

    benchmarks = [
        # (housing_type, region, benchmark_kwh_monthly)

        ("Studio", None, 250),
        ("Apartment", None, 350),
        ("Condo", None, 450),
        ("Multi-family", None, 400),
        ("Other", None, 600),
    ]

    # ------------------------------------------------------------
    # Connect to database
    # ------------------------------------------------------------

    with sqlite3.connect(db_name) as conn:

        # Enable foreign key enforcement
        conn.execute("PRAGMA foreign_keys = ON;")

        # --------------------------------------------------------
        # Insert appliance data
        #
        # appliance_name is UNIQUE in the schema, so INSERT OR
        # IGNORE prevents duplicate appliance records.
        # --------------------------------------------------------

        conn.executemany(
            """
            INSERT OR IGNORE INTO appliances
            (
                appliance_name,
                default_wattage,
                energy_star_rated
            )
            VALUES (?, ?, ?)
            """,
            appliances
        )

        # --------------------------------------------------------
        # Insert benchmark data
        #
        # We cannot rely on INSERT OR IGNORE here because SQLite
        # treats NULL values as distinct for UNIQUE constraints.
        #
        # The schema uses region = NULL for these benchmarks.
        # Therefore, we explicitly check whether the combination
        # already exists before inserting it.
        # --------------------------------------------------------

        for housing_type, region, benchmark_kwh in benchmarks:

            existing = conn.execute(
                """
                SELECT 1
                FROM benchmarks
                WHERE housing_type = ?
                  AND region IS ?
                LIMIT 1
                """,
                (housing_type, region)
            ).fetchone()

            if existing is None:
                conn.execute(
                    """
                    INSERT INTO benchmarks
                    (
                        housing_type,
                        region,
                        benchmark_kwh_monthly
                    )
                    VALUES (?, ?, ?)
                    """,
                    (housing_type, region, benchmark_kwh)
                )

    print("Reference data loaded successfully.")


if __name__ == "__main__":
    load_reference_data()