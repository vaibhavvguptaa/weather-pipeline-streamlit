"""
Shared pytest fixtures for the weather pipeline test suite.
"""

import os
import sys

import pandas as pd
import pytest

# Ensure project root is on sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_raw_data():
    """Mock API response dict mimicking Open-Meteo JSON."""
    times = [f"2026-04-{12 + d:02d}T{h:02d}:00" for d in range(7) for h in range(24)]
    n = len(times)  # 168
    return {
        "hourly": {
            "time": times,
            "temperature_2m": [25.0] * n,
            "relative_humidity_2m": [50.0] * n,
            "precipitation_probability": [10.0] * n,
            "windspeed_10m": [20.0] * n,
            "weathercode": [1] * n,
        },
        "hourly_units": {
            "time": "iso8601",
            "temperature_2m": "°C",
            "relative_humidity_2m": "%",
            "precipitation_probability": "%",
            "windspeed_10m": "km/h",
            "weathercode": "wmo code",
        },
    }


@pytest.fixture
def sample_df():
    """A valid 168-row DataFrame that passes all validation checks."""
    times = pd.date_range("2026-04-12", periods=168, freq="h")
    return pd.DataFrame(
        {
            "time": times,
            "temperature_2m": [25.0] * 168,
            "relative_humidity_2m": [50.0] * 168,
            "precipitation_probability": [10.0] * 168,
            "windspeed_10m": [20.0] * 168,
            "weathercode": [1] * 168,
            "city": ["Delhi"] * 168,
            "date": [t.date() for t in times],
            "hour": [t.hour for t in times],
        }
    )


@pytest.fixture
def invalid_config_kwargs():
    """Various invalid config overrides for testing validation."""
    return {
        "invalid_latitude": {
            "latitude": 999.0,
            "longitude": 77.2090,
            "city_name": "Test",
            "output_dir": "data",
            "db_name": "test.db",
            "max_retries": 3,
            "retry_backoff": 2,
        },
        "invalid_longitude": {
            "latitude": 28.6139,
            "longitude": 999.0,
            "city_name": "Test",
            "output_dir": "data",
            "db_name": "test.db",
            "max_retries": 3,
            "retry_backoff": 2,
        },
        "empty_city": {
            "latitude": 28.6139,
            "longitude": 77.2090,
            "city_name": "",
            "output_dir": "data",
            "db_name": "test.db",
            "max_retries": 3,
            "retry_backoff": 2,
        },
        "zero_retries": {
            "latitude": 28.6139,
            "longitude": 77.2090,
            "city_name": "Test",
            "output_dir": "data",
            "db_name": "test.db",
            "max_retries": 0,
            "retry_backoff": 2,
        },
        "negative_backoff": {
            "latitude": 28.6139,
            "longitude": 77.2090,
            "city_name": "Test",
            "output_dir": "data",
            "db_name": "test.db",
            "max_retries": 3,
            "retry_backoff": 0,
        },
    }
