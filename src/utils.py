"""
Utility functions for the weather pipeline.
Contains shared helper functions used across modules.
"""
from pathlib import Path
from src.config import config


def ensure_output_dir() -> Path:
    """
    Ensure the output directory exists.
    
    Returns:
        Path object for the output directory
    """
    out = Path(config.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    return out


def ensure_log_dir() -> Path:
    """
    Ensure the log directory exists.
    
    Returns:
        Path object for the log directory
    """
    log = Path(config.log_dir)
    log.mkdir(parents=True, exist_ok=True)
    return log
