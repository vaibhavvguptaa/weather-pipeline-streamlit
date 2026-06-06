"""
Weather Data Pipeline — CLI entry point.

Usage:
    python main.py                           # single run with .env defaults
    python main.py --city Mumbai --lat 19.08 --lon 72.88
    python main.py --days 14                 # 14-day forecast
    python main.py --no-sqlite               # CSV only
    python main.py --schedule 60             # run every 60 minutes
"""
import argparse
import sys
import time
import uuid
from datetime import datetime

from src.logger import get_logger
from src.config import config, API_PARAMS
from src.extract import fetch_weather
from src.transform import transform
from src.load import save_csv, save_sqlite

logger = get_logger("main", log_dir=config.log_dir)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="weather-pipeline",
        description="ETL pipeline for Open-Meteo weather forecast data.",
    )
    parser.add_argument(
        "-c", "--city",
        type=str,
        default=None,
        help="Override city name (default: from .env CITIES or CITY_NAME)",
    )
    parser.add_argument(
        "--lat",
        type=float,
        default=None,
        help="Override latitude (default: from .env LATITUDE)",
    )
    parser.add_argument(
        "--lon",
        type=float,
        default=None,
        help="Override longitude (default: from .env LONGITUDE)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Override forecast_days (default: 7)",
    )
    parser.add_argument(
        "-s", "--schedule",
        type=int,
        default=None,
        metavar="MINUTES",
        help="Run in scheduled mode every MINUTES interval",
    )
    parser.add_argument(
        "--no-csv",
        action="store_true",
        help="Skip saving CSV output",
    )
    parser.add_argument(
        "--no-sqlite",
        action="store_true",
        help="Skip saving to SQLite database",
    )
    return parser


def apply_overrides(args: argparse.Namespace) -> None:
    """Apply CLI overrides to the global config and API_PARAMS."""
    if args.city is not None:
        config.city_name = args.city
        config.cities = [args.city]
    if args.lat is not None:
        config.latitude = args.lat
    if args.lon is not None:
        config.longitude = args.lon
    if args.days is not None:
        API_PARAMS["forecast_days"] = args.days


def run_once(args: argparse.Namespace | None = None) -> None:
    """Execute one full ETL pass, looping over all configured cities."""
    run_id = str(uuid.uuid4())[:8]
    run_timestamp = datetime.now().isoformat()

    logger.info("=" * 60)
    logger.info(f"weather-pipeline  START [run_id: {run_id}]")
    logger.info(f"Timestamp: {run_timestamp}")
    logger.info("=" * 60)

    no_csv = args.no_csv if args else False
    no_sqlite = args.no_sqlite if args else False

    try:
        cities = config.cities
        logger.info(f"Cities to process: {', '.join(cities)}")

        for city in cities:
            logger.info("-" * 40)
            logger.info(f"Processing city: {city}")

            # Temporarily override city_name for this iteration
            original_city = config.city_name
            config.city_name = city

            try:
                # ── Extract ───────────────────────────────────────────────
                logger.info("[1/3] EXTRACT — fetching from Open-Meteo API")
                raw = fetch_weather()

                # ── Transform ─────────────────────────────────────────────
                logger.info("[2/3] TRANSFORM — cleaning and validating")
                df = transform(raw, city_name=city)

                # ── Load ──────────────────────────────────────────────────
                logger.info("[3/3] LOAD — writing outputs")

                csv_path = None
                db_path = None
                if not no_csv:
                    csv_path = save_csv(df)
                if not no_sqlite:
                    db_path = save_sqlite(df)

                logger.info(f"  City '{city}' completed successfully")
                if csv_path:
                    logger.info(f"  CSV  → {csv_path}")
                if db_path:
                    logger.info(f"  DB   → {db_path}")
                logger.info(f"  Rows processed: {len(df)}")

            finally:
                # Restore original city_name
                config.city_name = original_city

        logger.info("=" * 60)
        logger.info(f"Pipeline completed successfully [run_id: {run_id}]")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Pipeline FAILED [run_id: {run_id}]: {e}")
        logger.error("=" * 60)
        sys.exit(1)


def run_scheduled(interval_minutes: int, args: argparse.Namespace) -> None:
    """Run the pipeline on a recurring schedule using the schedule library."""
    try:
        import schedule as sched_lib
    except ImportError:
        logger.error(
            "The 'schedule' package is required for scheduled mode. "
            "Install it with: pip install schedule"
        )
        sys.exit(1)

    logger.info(f"Starting scheduled mode — running every {interval_minutes} minute(s)")
    logger.info("Press Ctrl+C to stop")

    # Run immediately on start
    run_once(args)

    # Schedule recurring runs
    sched_lib.every(interval_minutes).minutes.do(run_once, args=args)

    try:
        while True:
            sched_lib.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user (Ctrl+C)")


def run():
    """Main entry point — parses CLI args and dispatches."""
    parser = build_parser()
    args = parser.parse_args()

    apply_overrides(args)

    if args.schedule is not None:
        run_scheduled(args.schedule, args)
    else:
        run_once(args)


if __name__ == "__main__":
    run()
