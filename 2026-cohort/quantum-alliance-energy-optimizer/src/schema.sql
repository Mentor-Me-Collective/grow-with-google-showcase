
-- ============================================================
-- Household Energy Efficiency Optimizer — SQL Schema
-- Team Quantum Alliance
--
-- Design notes:
--   - Normalized to 3NF: appliance specs and housing-type
--     benchmarks live in their own reference tables so they are
--     never repeated per household.
--   - household_appliances is the junction table linking a
--     household to what it owns, with per-household overrides
--     (quantity, usage hours, optional wattage override).
--   - usage_estimates stores calculated output with a timestamp,
--     so a household can have multiple estimates over time.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- 1. households
--    One row per user/household. square_footage is optional 
--    apartment_size_category is the fallback for users who
--    don't know exact square footage.
-- ------------------------------------------------------------
CREATE TABLE households (
    household_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    housing_type             TEXT    NOT NULL
                              CHECK (housing_type IN ('Apartment', 'Condo', 'Studio', 'Multi-family', 'Other')),
    square_footage            INTEGER NULL
                              CHECK (square_footage IS NULL OR square_footage > 0),
    apartment_size_category   TEXT    NULL
                              CHECK (apartment_size_category IS NULL
                                     OR apartment_size_category IN ('Studio', '1BR', '2BR', '3BR+')),
    electricity_rate_per_kwh  DECIMAL(6,4) NULL
                              CHECK (electricity_rate_per_kwh IS NULL OR electricity_rate_per_kwh >= 0),
    carbon_emission_factor    DECIMAL(6,4) NULL
                              CHECK (carbon_emission_factor IS NULL OR carbon_emission_factor >= 0),
    created_at                DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- must have at least one way to size the home
    CHECK (square_footage IS NOT NULL OR apartment_size_category IS NOT NULL)
);

-- ------------------------------------------------------------
-- 2. appliances (reference table — populated once from
--    ENERGY STAR, not repeated per household)
-- ------------------------------------------------------------
CREATE TABLE appliances (
    appliance_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    appliance_name      TEXT NOT NULL UNIQUE,
    default_wattage     DECIMAL(8,2) NOT NULL
                        CHECK (default_wattage >= 0),
    energy_star_rated   BOOLEAN NOT NULL DEFAULT 0
);

-- ------------------------------------------------------------
-- 3. household_appliances (junction table — what each
--    household owns and how they use it)
-- ------------------------------------------------------------
CREATE TABLE household_appliances (
    household_id          INTEGER NOT NULL,
    appliance_id           INTEGER NOT NULL,
    appliance_quantity      INTEGER NOT NULL DEFAULT 1
                            CHECK (appliance_quantity > 0),
    wattage_override         DECIMAL(8,2) NULL
                            CHECK (wattage_override IS NULL OR wattage_override >= 0),
    daily_usage_hours        DECIMAL(4,2) NOT NULL
                            CHECK (daily_usage_hours >= 0 AND daily_usage_hours <= 24),

    PRIMARY KEY (household_id, appliance_id),
    FOREIGN KEY (household_id) REFERENCES households (household_id) ON DELETE CASCADE,
    FOREIGN KEY (appliance_id) REFERENCES appliances (appliance_id) ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- 4. benchmarks (reference table — from EIA RECS, one row
--    per housing type/region average)
-- ------------------------------------------------------------
CREATE TABLE benchmarks (
    benchmark_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    housing_type            TEXT NOT NULL,
    region                  TEXT NULL,
    benchmark_kwh_monthly    DECIMAL(8,2) NOT NULL
                            CHECK (benchmark_kwh_monthly >= 0),

    UNIQUE (housing_type, region)
);

-- ------------------------------------------------------------
-- 5. usage_estimates (calculated output; one row per estimate
--    run, so historical tracking works via generated_at)
-- ------------------------------------------------------------
CREATE TABLE usage_estimates (
    estimate_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id              INTEGER NOT NULL,
    estimated_kwh_monthly       DECIMAL(8,2) NOT NULL
                               CHECK (estimated_kwh_monthly >= 0),
    estimated_cost_monthly      DECIMAL(8,2) NOT NULL
                               CHECK (estimated_cost_monthly >= 0),
    pct_vs_benchmark             DECIMAL(6,2) NULL,
    generated_at                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (household_id) REFERENCES households (household_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Helpful indexes for the lookups the app will do most often
-- ------------------------------------------------------------
CREATE INDEX idx_household_appliances_household ON household_appliances (household_id);
CREATE INDEX idx_usage_estimates_household       ON usage_estimates (household_id);
CREATE INDEX idx_benchmarks_housing_type         ON benchmarks (housing_type);

