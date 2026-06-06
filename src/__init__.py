"""
Weather Data Pipeline

A production-style ETL pipeline that fetches weather forecast data,
cleans and validates it, and loads it into CSV and SQLite.
"""

from src.config import config, API_URL, API_PARAMS
from src.logger import get_logger
from src.extract import fetch_weather
from src.transform import transform
from src.load import save_csv, save_sqlite
from src.validators import validate
from src.utils import ensure_output_dir, ensure_log_dir

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