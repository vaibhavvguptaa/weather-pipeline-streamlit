"""
Data transformation module for weather pipeline.
Handles parsing, cleaning, and validation of raw API data.
"""
import pandas as pd
from src.config import config
from src.logger import get_logger
from src.validators import validate

logger = get_logger(__name__)

SCHEMA = {
    "temperature_2m": "float64",
    "relative_humidity_2m": "float64",
    "precipitation_probability": "float64",
    "windspeed_10m": "float64",
    "weathercode": "int64",
}


def parse_raw(raw: dict) -> pd.DataFrame:
    """Convert raw API JSON into a flat DataFrame."""
    hourly = raw.get("hourly", {})

    if not hourly:
        raise ValueError("API response missing 'hourly' key — unexpected schema")

    df = pd.DataFrame(hourly)
    logger.info(f"Parsed raw data — {len(df)} rows, {len(df.columns)} columns")
    return df


def clean(df: pd.DataFrame, city_name: str | None = None) -> pd.DataFrame:
    """Clean and type-cast the raw DataFrame."""
    from src.validators import REQUIRED_COLUMNS

    # ── Schema check ──────────────────────────────────────────────
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing expected columns: {missing_cols}")

    df = df[REQUIRED_COLUMNS].copy()

    # ── Datetime parsing ──────────────────────────────────────────
    df["time"] = pd.to_datetime(df["time"])
    logger.debug("Parsed 'time' column to datetime")

    # ── Type casting ──────────────────────────────────────────────
    for col, dtype in SCHEMA.items():
        df[col] = df[col].astype(dtype)

    # ── Add derived columns ───────────────────────────────────────
    df["city"] = city_name or config.city_name
    df["date"] = df["time"].dt.date
    df["hour"] = df["time"].dt.hour

    logger.info(f"Clean complete — {len(df)} rows, {df['date'].nunique()} days")
    return df


def transform(raw: dict, city_name: str | None = None) -> pd.DataFrame:
    """Full transform pipeline: parse → clean → validate."""
    df = parse_raw(raw)
    df = clean(df, city_name=city_name)
    df = validate(df)
    return df