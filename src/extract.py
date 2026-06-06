import requests
from requests.exceptions import HTTPError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    retry_if_exception,
)
import logging
from src.config import config, API_URL, API_PARAMS
from src.logger import get_logger

logger = get_logger(__name__)


def is_retryable_http_error(exception: Exception) -> bool:
    """Check if an HTTP error should trigger a retry."""
    if isinstance(exception, HTTPError):
        # Retry on server errors (5xx) and rate limits (429)
        if hasattr(exception, 'response') and exception.response is not None:
            status_code = exception.response.status_code
            return status_code in (429, 500, 502, 503, 504)
    return False


@retry(
    stop=stop_after_attempt(config.max_retries),
    wait=wait_exponential(multiplier=config.retry_backoff, min=2, max=30),
    retry=(
        retry_if_exception_type((requests.ConnectionError, requests.Timeout)) |
        retry_if_exception(is_retryable_http_error)
    ),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def fetch_weather() -> dict:
    """
    Fetch 7-day hourly forecast from Open-Meteo.
    Retries on connection errors, timeouts, and HTTP 5xx/429 errors with exponential backoff.
    """
    logger.info(f"Fetching weather data for {config.city_name} "
                f"({config.latitude}, {config.longitude})")

    # Build params with location from config
    params = {
        **API_PARAMS,
        "latitude": config.latitude,
        "longitude": config.longitude,
    }

    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    
    # Validate response structure
    if not isinstance(data, dict):
        raise ValueError(f"API returned invalid response type: {type(data).__name__}")
    
    if "hourly" not in data:
        raise ValueError("API response missing 'hourly' key — unexpected schema")
    
    hourly = data["hourly"]
    if not isinstance(hourly, dict):
        raise ValueError(f"'hourly' field has invalid type: {type(hourly).__name__}")
    
    if "time" not in hourly:
        raise ValueError("API response missing 'hourly.time' field")
    
    if len(hourly.get("time", [])) == 0:
        raise ValueError("API returned empty hourly data")
    
    # Verify all requested fields are present
    missing_fields = [field for field in API_PARAMS["hourly"] if field not in hourly]
    if missing_fields:
        raise ValueError(f"API response missing expected fields: {missing_fields}")
    
    logger.info(f"API response received — status {response.status_code}")
    logger.debug(f"Raw API units: {data.get('hourly_units', {})}")

    return data