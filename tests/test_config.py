"""
Tests for src/config.py — configuration validation and CITIES parsing.
"""

import pytest

from src.config import Config


class TestConfigValidation:
    """Verify that invalid configuration values are rejected."""

    def test_rejects_invalid_latitude(self, invalid_config_kwargs):
        with pytest.raises(ValueError, match="latitude"):
            Config(**invalid_config_kwargs["invalid_latitude"])

    def test_rejects_invalid_longitude(self, invalid_config_kwargs):
        with pytest.raises(ValueError, match="longitude"):
            Config(**invalid_config_kwargs["invalid_longitude"])

    def test_rejects_empty_city_name(self, invalid_config_kwargs):
        with pytest.raises(ValueError, match="CITY_NAME"):
            Config(**invalid_config_kwargs["empty_city"])

    def test_rejects_zero_retries(self, invalid_config_kwargs):
        with pytest.raises(ValueError, match="MAX_RETRIES"):
            Config(**invalid_config_kwargs["zero_retries"])

    def test_rejects_zero_backoff(self, invalid_config_kwargs):
        with pytest.raises(ValueError, match="RETRY_BACKOFF"):
            Config(**invalid_config_kwargs["negative_backoff"])

    def test_valid_config_loads(self):
        cfg = Config(
            latitude=28.6139,
            longitude=77.2090,
            city_name="Delhi",
            output_dir="data",
            db_name="test.db",
            max_retries=3,
            retry_backoff=2,
        )
        assert cfg.latitude == 28.6139
        assert cfg.longitude == 77.2090
        assert cfg.city_name == "Delhi"


class TestCitiesParsing:
    """Verify CITIES comma-separated parsing."""

    def test_cities_from_env(self, monkeypatch):
        monkeypatch.setenv("CITIES", "Delhi,Mumbai,Bangalore")
        cfg = Config(
            latitude=28.6139,
            longitude=77.2090,
            city_name="Delhi",
            output_dir="data",
            db_name="test.db",
            max_retries=3,
            retry_backoff=2,
        )
        assert cfg.cities == ["Delhi", "Mumbai", "Bangalore"]

    def test_cities_fallback_to_city_name(self, monkeypatch):
        monkeypatch.setenv("CITIES", "")
        cfg = Config(
            latitude=28.6139,
            longitude=77.2090,
            city_name="Delhi",
            output_dir="data",
            db_name="test.db",
            max_retries=3,
            retry_backoff=2,
        )
        assert cfg.cities == ["Delhi"]

    def test_cities_strips_whitespace(self, monkeypatch):
        monkeypatch.setenv("CITIES", " Delhi , Mumbai ")
        cfg = Config(
            latitude=28.6139,
            longitude=77.2090,
            city_name="Delhi",
            output_dir="data",
            db_name="test.db",
            max_retries=3,
            retry_backoff=2,
        )
        assert cfg.cities == ["Delhi", "Mumbai"]

    def test_cities_ignores_empty_entries(self, monkeypatch):
        monkeypatch.setenv("CITIES", "Delhi,,Mumbai,")
        cfg = Config(
            latitude=28.6139,
            longitude=77.2090,
            city_name="Delhi",
            output_dir="data",
            db_name="test.db",
            max_retries=3,
            retry_backoff=2,
        )
        assert cfg.cities == ["Delhi", "Mumbai"]
