from pathlib import Path
import re
import unicodedata

import polars as pl


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REVIEW_DIR = PROJECT_ROOT / "data" / "review"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REVIEW_DIR.mkdir(parents=True, exist_ok=True)

MISSING_VALUES = {
    "",
    "na",
    "n/a",
    "none",
    "null",
    "unknown",
    "not available",
}


def clean_text_expression(column: str) -> pl.Expr:
    """Clean general text while preserving original capitalization."""
    return (
        pl.col(column)
        .cast(pl.String)
        .str.strip_chars()
        .str.replace_all(r"\s+", " ")
        .map_elements(
            lambda value: None
            if value is None or value.casefold() in MISSING_VALUES
            else unicodedata.normalize("NFKC", value),
            return_dtype=pl.String,
        )
    )


def normalize_name_expression(column: str) -> pl.Expr:
    """
    Produce a matching key for scientific names.

    This does not remove subspecies, varieties, or authors automatically.
    """
    return (
        clean_text_expression(column)
        .str.to_lowercase()
        .str.replace_all(r"\s+", " ")
        .alias("scientific_name_key")
    )


def normalize_code_expression(column: str) -> pl.Expr:
    return (
        clean_text_expression(column)
        .str.to_uppercase()
        .alias("usda_code")
    )