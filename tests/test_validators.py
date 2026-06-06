"""
Tests for src/validators.py — data quality validation checks.
"""

import pandas as pd
import pytest

from src.validators import (
    check_nulls,
    check_ranges,
    validate,
)


class TestValidDataFrame:
    """A valid DataFrame should pass all checks."""

    def test_validate_passes(self, sample_df):
        result = validate(sample_df)
        assert len(result) == 168


class TestWindspeedValidation:
    def test_rejects_windspeed_above_300(self):
        times = pd.date_range("2026-04-12", periods=168, freq="h")
        df = pd.DataFrame(
            {
                "time": times,
                "temperature_2m": [25.0] * 168,
                "relative_humidity_2m": [50.0] * 168,
                "precipitation_probability": [10.0] * 168,
                "windspeed_10m": [350.0] * 168,  # invalid
                "weathercode": [1] * 168,
                "city": ["Delhi"] * 168,
                "date": [t.date() for t in times],
                "hour": [t.hour for t in times],
            }
        )
        with pytest.raises(ValueError, match="windspeed"):
            validate(df)


class TestWeathercodeValidation:
    def test_rejects_weathercode_above_99(self):
        times = pd.date_range("2026-04-12", periods=168, freq="h")
        df = pd.DataFrame(
            {
                "time": times,
                "temperature_2m": [25.0] * 168,
                "relative_humidity_2m": [50.0] * 168,
                "precipitation_probability": [10.0] * 168,
                "windspeed_10m": [20.0] * 168,
                "weathercode": [150] * 168,  # invalid
                "city": ["Delhi"] * 168,
                "date": [t.date() for t in times],
                "hour": [t.hour for t in times],
            }
        )
        with pytest.raises(ValueError, match="weathercode"):
            validate(df)


class TestDuplicateDetection:
    def test_detects_duplicate_timestamps(self):
        times = pd.date_range("2026-04-12", periods=168, freq="h").tolist()
        times.append(times[5])  # add a duplicate
        n = len(times)
        df = pd.DataFrame(
            {
                "time": times,
                "temperature_2m": [25.0] * n,
                "relative_humidity_2m": [50.0] * n,
                "precipitation_probability": [10.0] * n,
                "windspeed_10m": [20.0] * n,
                "weathercode": [1] * n,
                "city": ["Delhi"] * n,
                "date": [pd.Timestamp(t).date() for t in times],
                "hour": [pd.Timestamp(t).hour for t in times],
            }
        )
        with pytest.raises(ValueError, match="duplicate"):
            validate(df)


class TestTemporalContinuity:
    def test_warns_on_time_gaps(self, caplog):
        """Time gaps >1h15m should log a warning but not raise."""
        import logging

        with caplog.at_level(logging.WARNING):
            times = list(pd.date_range("2026-04-12 00:00", periods=84, freq="h"))
            start_after_gap = pd.Timestamp("2026-04-12 00:00") + pd.Timedelta(hours=87)
            times.extend(pd.date_range(start_after_gap, periods=84, freq="h"))
            n = len(times)
            df = pd.DataFrame(
                {
                    "time": times,
                    "temperature_2m": [25.0] * n,
                    "relative_humidity_2m": [50.0] * n,
                    "precipitation_probability": [10.0] * n,
                    "windspeed_10m": [20.0] * n,
                    "weathercode": [1] * n,
                    "city": ["Delhi"] * n,
                    "date": [t.date() for t in times],
                    "hour": [t.hour for t in times],
                }
            )
            result = validate(df)
            assert len(result) == n


class TestRowCount:
    def test_rejects_too_few_rows(self):
        times = pd.date_range("2026-04-12", periods=100, freq="h")
        df = pd.DataFrame(
            {
                "time": times,
                "temperature_2m": [25.0] * 100,
                "relative_humidity_2m": [50.0] * 100,
                "precipitation_probability": [10.0] * 100,
                "windspeed_10m": [20.0] * 100,
                "weathercode": [1] * 100,
                "city": ["Delhi"] * 100,
                "date": [t.date() for t in times],
                "hour": [t.hour for t in times],
            }
        )
        with pytest.raises(ValueError, match="Row count"):
            validate(df)


class TestNullChecks:
    def test_warns_on_low_nulls(self, sample_df):
        """Nulls below threshold should produce warnings, not errors."""
        # Introduce a few nulls (below 20% threshold)
        df = sample_df.copy()
        df.loc[:5, "temperature_2m"] = None
        errors, warnings, null_counts = check_nulls(df)
        assert len(errors) == 0
        assert len(warnings) > 0

    def test_errors_on_high_nulls(self):
        """Nulls above 20% threshold should produce errors."""
        times = pd.date_range("2026-04-12", periods=168, freq="h")
        df = pd.DataFrame(
            {
                "time": times,
                "temperature_2m": [None] * 168,  # 100% nulls
                "relative_humidity_2m": [50.0] * 168,
                "precipitation_probability": [10.0] * 168,
                "windspeed_10m": [20.0] * 168,
                "weathercode": [1] * 168,
                "city": ["Delhi"] * 168,
                "date": [t.date() for t in times],
                "hour": [t.hour for t in times],
            }
        )
        errors, warnings, null_counts = check_nulls(df)
        assert len(errors) > 0


class TestRangeChecks:
    def test_rejects_temperature_out_of_range(self):
        times = pd.date_range("2026-04-12", periods=168, freq="h")
        df = pd.DataFrame(
            {
                "time": times,
                "temperature_2m": [100.0] * 168,  # above 60
                "relative_humidity_2m": [50.0] * 168,
                "precipitation_probability": [10.0] * 168,
                "windspeed_10m": [20.0] * 168,
                "weathercode": [1] * 168,
            }
        )
        errors = check_ranges(df)
        assert any("temperature" in e for e in errors)
