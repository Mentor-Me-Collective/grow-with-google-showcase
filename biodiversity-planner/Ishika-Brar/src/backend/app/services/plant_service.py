from pathlib import Path
import pandas as pd


DATASET_PATH = (
    Path(__file__).resolve().parents[5]
    / "Alexis-Paitoo"
    / "datasets"
    / "plants.csv"
)


REQUIRED_COLUMNS = {
    "species_id",
    "common_name",
    "scientific_name",
    "native_range",
    "bloom_start",
    "bloom_end",
    "sun_needs",
    "soil_type",
    "moisture",
    "pollinators_supported",
    "hardiness_zones",
    "source",
    "source_url",
    "notes",
}


def load_plants():
    plants = pd.read_csv(DATASET_PATH)

    missing_columns = REQUIRED_COLUMNS - set(plants.columns)
    
    # Error checking to ensure that the dataset contains all required columns
    if missing_columns:
        raise ValueError(
            f"Dataset is missing columns: {missing_columns}"
        )

    return plants