"""
Logging configuration for the weather pipeline.
Provides structured logging with console and file handlers.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def get_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    """
    Get a logger with console and rotating file handlers.
    
    Args:
        name: Logger name (typically __name__)
        log_dir: Directory for log files
        
    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler — INFO and above
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    # File handler with rotation — DEBUG and above (captures everything)
    # Rotates at 5MB, keeps 5 backup files (25MB max)
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path / "pipeline.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)

    return logger