"""
Data validation utilities for the weather pipeline.
Contains all validation checks for data quality assurance.
"""
import pandas as pd
from src.logger import get_logger

logger = get_logger(__name__)

REQUIRED_COLUMNS = [
    "time",
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation_probability",
    "windspeed_10m",
    "weathercode",
]

# Validation ranges
VALIDATION_RANGES = {
    "temperature_2m": (-50, 60),
    "relative_humidity_2m": (0, 100),
    "precipitation_probability": (0, 100),
    "windspeed_10m": (0, 300),
    "weathercode": (0, 99),
}

NULL_THRESHOLD_PERCENT = 20
EXPECTED_ROWS = 7 * 24  # 7 days × 24 hours
ROW_COUNT_THRESHOLD = 0.9


def check_nulls(df: pd.DataFrame) -> tuple[list, list]:
    """
    Check for null values in required columns.
    
    Returns:
        tuple: (errors, warnings) lists
    """
    errors = []
    warnings = []
    
    null_counts = df[REQUIRED_COLUMNS].isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            pct = round(count / len(df) * 100, 1)
            if pct > NULL_THRESHOLD_PERCENT:
                errors.append(
                    f"Column '{col}' has {pct}% nulls (threshold: {NULL_THRESHOLD_PERCENT}%)"
                )
            else:
                warnings.append(f"Column '{col}' has {count} nulls ({pct}%)")
    
    return errors, warnings, null_counts


def check_ranges(df: pd.DataFrame) -> list:
    """
    Check if numeric columns are within valid ranges.
    
    Returns:
        list: Validation errors found
    """
    errors = []
    
    for col, (min_val, max_val) in VALIDATION_RANGES.items():
        if col in df.columns:
            if not df[col].between(min_val, max_val).all():
                if col == "weathercode":
                    invalid_codes = df[col][~df[col].between(min_val, max_val)].unique()
                    errors.append(
                        f"{col} has invalid WMO codes: {invalid_codes}"
                    )
                else:
                    errors.append(f"{col} out of range [{min_val}, {max_val}]")
    
    return errors


def check_duplicates(df: pd.DataFrame) -> list:
    """
    Check for duplicate (time, city) combinations.
    
    Returns:
        list: Validation errors found
    """
    errors = []
    
    duplicate_times = df[df.duplicated(subset=["time", "city"], keep=False)]
    if len(duplicate_times) > 0:
        errors.append(
            f"Found {len(duplicate_times)} duplicate (time, city) combinations"
        )
    
    return errors


def check_temporal_continuity(df: pd.DataFrame) -> list:
    """
    Check for gaps in time series data.
    
    Returns:
        list: Validation warnings found
    """
    warnings = []
    
    df_sorted = df.sort_values("time")
    time_diffs = df_sorted["time"].diff()
    
    # Expected 1-hour intervals; allow 15-minute tolerance
    expected_interval = pd.Timedelta(hours=1)
    tolerance = pd.Timedelta(minutes=15)
    
    if len(time_diffs) > 1:
        valid_diffs = time_diffs.dropna()
        gaps = valid_diffs[valid_diffs > (expected_interval + tolerance)]
        if len(gaps) > 0:
            warnings.append(
                f"Found {len(gaps)} time gaps larger than 1h 15m. "
                f"Max gap: {gaps.max()}"
            )
    
    return warnings


def check_row_count(df: pd.DataFrame) -> list:
    """
    Check if DataFrame has expected number of rows.
    
    Returns:
        list: Validation errors found
    """
    errors = []
    
    if len(df) < EXPECTED_ROWS * ROW_COUNT_THRESHOLD:
        errors.append(
            f"Row count {len(df)} is below {ROW_COUNT_THRESHOLD * 100:.0f}% "
            f"of expected {EXPECTED_ROWS}"
        )
    
    return errors


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run all data quality checks. Raises on critical failures,
    logs warnings on non-critical issues.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Validated DataFrame
        
    Raises:
        ValueError: If critical validation checks fail
    """
    all_errors = []
    all_warnings = []
    
    # Run all checks
    null_errors, null_warnings, null_counts = check_nulls(df)
    all_errors.extend(null_errors)
    all_warnings.extend(null_warnings)
    
    all_errors.extend(check_ranges(df))
    all_errors.extend(check_duplicates(df))
    all_warnings.extend(check_temporal_continuity(df))
    all_errors.extend(check_row_count(df))
    
    # Log warnings
    for w in all_warnings:
        logger.warning(f"[VALIDATION] {w}")
    
    # Handle errors
    if all_errors:
        for e in all_errors:
            logger.error(f"[VALIDATION FAILED] {e}")
        error_details = "; ".join(all_errors)
        raise ValueError(
            f"Data validation failed with {len(all_errors)} error(s): "
            f"{error_details}"
        )
    
    logger.info(
        f"Validation passed — {len(df)} rows, "
        f"{null_counts.sum()} total nulls"
    )
    return df
