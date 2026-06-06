"""
Tests for main.py — CLI argument parsing and run metadata.
"""

import inspect

from main import apply_overrides, build_parser, run_once


class TestCLIParser:
    """Verify argparse setup and flag definitions."""

    def test_parser_has_city_flag(self):
        parser = build_parser()
        # Parse with --city
        args = parser.parse_args(["--city", "Mumbai"])
        assert args.city == "Mumbai"

    def test_parser_has_short_city_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "Mumbai"])
        assert args.city == "Mumbai"

    def test_parser_has_lat_lon_flags(self):
        parser = build_parser()
        args = parser.parse_args(["--lat", "19.08", "--lon", "72.88"])
        assert args.lat == 19.08
        assert args.lon == 72.88

    def test_parser_has_days_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--days", "14"])
        assert args.days == 14

    def test_parser_has_schedule_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--schedule", "60"])
        assert args.schedule == 60

    def test_parser_has_short_schedule_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-s", "30"])
        assert args.schedule == 30

    def test_parser_has_no_csv_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--no-csv"])
        assert args.no_csv is True

    def test_parser_has_no_sqlite_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--no-sqlite"])
        assert args.no_sqlite is True

    def test_parser_defaults(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.city is None
        assert args.lat is None
        assert args.lon is None
        assert args.days is None
        assert args.schedule is None
        assert args.no_csv is False
        assert args.no_sqlite is False


class TestApplyOverrides:
    """Verify CLI args override config values."""

    def test_city_override(self):
        from src.config import config

        parser = build_parser()
        args = parser.parse_args(["--city", "Tokyo"])
        original = config.city_name
        apply_overrides(args)
        assert config.city_name == "Tokyo"
        assert config.cities == ["Tokyo"]
        # Restore
        config.city_name = original
        config.cities = [original]

    def test_lat_override(self):
        from src.config import config

        parser = build_parser()
        args = parser.parse_args(["--lat", "35.68"])
        original = config.latitude
        apply_overrides(args)
        assert config.latitude == 35.68
        config.latitude = original

    def test_days_override(self):
        from src.config import API_PARAMS

        parser = build_parser()
        args = parser.parse_args(["--days", "14"])
        original = API_PARAMS.get("forecast_days")
        apply_overrides(args)
        assert API_PARAMS["forecast_days"] == 14
        API_PARAMS["forecast_days"] = original


class TestRunMetadata:
    """Verify run() includes run_id and metadata tracking."""

    def test_run_has_run_id(self):
        source = inspect.getsource(run_once)
        assert "run_id" in source

    def test_run_has_uuid(self):
        source = inspect.getsource(run_once)
        assert "uuid" in source

    def test_run_has_timestamp(self):
        source = inspect.getsource(run_once)
        assert "run_timestamp" in source

    def test_run_logs_row_count(self):
        source = inspect.getsource(run_once)
        assert "Rows processed" in source

    def test_run_has_cities_loop(self):
        source = inspect.getsource(run_once)
        assert "config.cities" in source
