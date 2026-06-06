"""
Configuration management for the weather pipeline.
Loads environment variables and provides validated configuration.
"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


# API Configuration
API_URL = "https://api.open-meteo.com/v1/forecast"
API_PARAMS = {
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation_probability",
        "windspeed_10m",
        "weathercode",
    ],
    "timezone": "Asia/Kolkata",
    "forecast_days": 7,
}


@dataclass
class Config:
    """Pipeline configuration loaded from environment variables."""

    latitude: float = field(default_factory=lambda: float(os.getenv("LATITUDE", 28.6139)))
    longitude: float = field(default_factory=lambda: float(os.getenv("LONGITUDE", 77.2090)))
    city_name: str = field(default_factory=lambda: os.getenv("CITY_NAME", "Delhi"))
    cities: list[str] = field(default_factory=list)
    output_dir: str = field(default_factory=lambda: os.getenv("OUTPUT_DIR", "data"))
    log_dir: str = field(default_factory=lambda: os.getenv("LOG_DIR", "logs"))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", "weather.db"))
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", 3)))
    retry_backoff: int = field(default_factory=lambda: int(os.getenv("RETRY_BACKOFF", 2)))

    def __post_init__(self):
        """Validate configuration values after initialization."""
        # Parse CITIES env var (comma-separated) — takes precedence over CITY_NAME
        raw_cities = os.getenv("CITIES", "").strip()
        if raw_cities:
            self.cities = [c.strip() for c in raw_cities.split(",") if c.strip()]
        else:
            self.cities = [self.city_name]

        # Validate latitude range (-90 to 90)
        if not -90 <= self.latitude <= 90:
            raise ValueError(
                f"Invalid latitude: {self.latitude}. Must be between -90 and 90 degrees."
            )

        # Validate longitude range (-180 to 180)
        if not -180 <= self.longitude <= 180:
            raise ValueError(
                f"Invalid longitude: {self.longitude}. Must be between -180 and 180 degrees."
            )

        # Validate city_name is not empty
        if not self.city_name or not self.city_name.strip():
            raise ValueError("CITY_NAME cannot be empty.")

        # Validate max_retries is positive
        if self.max_retries < 1:
            raise ValueError(f"Invalid MAX_RETRIES: {self.max_retries}. Must be at least 1.")

        # Validate retry_backoff is positive
        if self.retry_backoff < 1:
            raise ValueError(f"Invalid RETRY_BACKOFF: {self.retry_backoff}. Must be at least 1.")


config = Config()
