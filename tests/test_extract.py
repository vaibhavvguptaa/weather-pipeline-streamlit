"""
Tests for src/extract.py — API response validation and HTTP retry logic.
"""
import inspect
import pytest
from unittest.mock import Mock
from requests.exceptions import HTTPError

from src.extract import fetch_weather, is_retryable_http_error


class TestExtractValidation:
    """Verify that extract module has proper response validation logic."""

    def test_checks_hourly_key(self):
        source = inspect.getsource(fetch_weather)
        assert '"hourly" not in data' in source

    def test_checks_field_presence(self):
        source = inspect.getsource(fetch_weather)
        assert "missing expected fields" in source

    def test_checks_empty_data(self):
        source = inspect.getsource(fetch_weather)
        assert "empty hourly data" in source


class TestHTTPRetryLogic:
    """Verify is_retryable_http_error correctly classifies errors."""

    @pytest.mark.parametrize("status_code", [429, 500, 502, 503, 504])
    def test_retryable_errors(self, status_code):
        error = HTTPError(response=Mock(status_code=status_code))
        assert is_retryable_http_error(error) is True

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404, 409])
    def test_non_retryable_errors(self, status_code):
        error = HTTPError(response=Mock(status_code=status_code))
        assert is_retryable_http_error(error) is False

    def test_non_http_error(self):
        """Non-HTTPError exceptions should not be retryable."""
        assert is_retryable_http_error(ValueError("oops")) is False

    def test_http_error_without_response(self):
        """HTTPError with no response object should not be retryable."""
        error = HTTPError()
        assert is_retryable_http_error(error) is False


class TestEnvExample:
    """Verify .env.example has correct values."""

    def test_latitude_is_correct(self):
        with open(".env.example", "r") as f:
            content = f.read()
        assert "LATITUDE=28.6139" in content

    def test_no_old_incorrect_latitude(self):
        with open(".env.example", "r") as f:
            content = f.read()
        assert "LATITUDE=68139" not in content

    def test_cities_variable_present(self):
        with open(".env.example", "r") as f:
            content = f.read()
        assert "CITIES=" in content
