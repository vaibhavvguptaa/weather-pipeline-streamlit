"""
Weather Data Pipeline

A production-style ETL pipeline that fetches weather forecast data,
cleans and validates it, and loads it into CSV and SQLite.
"""

from src.config import API_PARAMS, API_URL, config
from src.extract import fetch_weather
from src.load import save_csv, save_sqlite
from src.logger import get_logger
from src.transform import transform
from src.utils import ensure_log_dir, ensure_output_dir
from src.validators import validate

__all__ = [
    "config",
    "API_URL",
    "API_PARAMS",
    "get_logger",
    "fetch_weather",
    "transform",
    "save_csv",
    "save_sqlite",
    "validate",
    "ensure_output_dir",
    "ensure_log_dir",
]
