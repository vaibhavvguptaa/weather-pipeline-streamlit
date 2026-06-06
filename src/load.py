"""
Data loading module for weather pipeline.
Handles saving data to CSV and SQLite databases.
"""
import sqlite3
import pandas as pd
from pathlib import Path
from src.config import config
from src.logger import get_logger
from src.utils import ensure_output_dir

logger = get_logger(__name__)


def save_csv(df: pd.DataFrame) -> Path:
    """Save DataFrame to a date-stamped CSV file."""
    out_dir = ensure_output_dir()
    run_date = df["date"].min()   # earliest date in the batch
    filename = out_dir / f"weather_{config.city_name.lower()}_{run_date}.csv"

    df.to_csv(filename, index=False)
    logger.info(f"CSV saved → {filename}  ({len(df)} rows)")
    return filename


def save_sqlite(df: pd.DataFrame) -> Path:
    """
    Upsert DataFrame into SQLite.
    Uses INSERT OR REPLACE so re-running the pipeline is idempotent.
    """
    out_dir = ensure_output_dir()
    db_path = out_dir / config.db_name

    with sqlite3.connect(db_path) as conn:
        # Create table with a composite primary key so re-runs don't duplicate
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weather_forecast (
                time                     TEXT,
                city                     TEXT,
                temperature_2m           REAL,
                relative_humidity_2m     REAL,
                precipitation_probability REAL,
                windspeed_10m            REAL,
                weathercode              INTEGER,
                date                     TEXT,
                hour                     INTEGER,
                PRIMARY KEY (time, city)
            )
        """)

        # Convert date/time columns to string for SQLite compatibility
        df_load = df.copy()
        df_load["time"] = df_load["time"].astype(str)
        df_load["date"] = df_load["date"].astype(str)

        # Use a temporary table for proper upsert logic
        # Step 1: Insert into temp table
        df_load.to_sql(
            "weather_temp",
            conn,
            if_exists="replace",
            index=False,
        )

        # Step 2: Insert or replace from temp table to main table
        conn.execute("""
            INSERT OR REPLACE INTO weather_forecast 
            SELECT * FROM weather_temp
        """)

        # Step 3: Drop temp table
        conn.execute("DROP TABLE IF EXISTS weather_temp")
        conn.commit()

        count = conn.execute(
            "SELECT COUNT(*) FROM weather_forecast"
        ).fetchone()[0]

    logger.info(f"SQLite saved → {db_path}  (total rows in DB: {count})")
    return db_path