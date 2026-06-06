# Weather ETL & Analytics Pipeline

[![CI Build](https://github.com/vaibhavvguptaa/weather-pipeline-streamlit/actions/workflows/ci.yml/badge.svg)](https://github.com/vaibhavvguptaa/weather-pipeline-streamlit/actions)
[![Scheduled ETL](https://github.com/vaibhavvguptaa/weather-pipeline-streamlit/actions/workflows/scheduled_etl.yml/badge.svg)](https://github.com/vaibhavvguptaa/weather-pipeline-streamlit/actions)
[![Live Dashboard](https://img.shields.io/badge/Live-Streamlit%20App-FF4B4B?style=for-the-badge&logo=streamlit)](https://vaibhavvguptaa-weather-pipeline-streamlit-dashboard-gdjcfy.streamlit.app/)

A production-grade ETL pipeline that fetches 7-day hourly weather forecasts from the [Open-Meteo API](https://open-meteo.com), validates data quality, and loads it into CSV + SQLite — with an interactive Streamlit dashboard for visualization.

```
EXTRACT              TRANSFORM             LOAD                 DASHBOARD
Open-Meteo API  -->  Pandas clean    -->   CSV (dated)    -->   Streamlit app
+ tenacity retry     Type casting          SQLite upsert        Plotly charts
+ response check     6 validation checks   Idempotent           KPI metrics
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11+ |
| HTTP / Retry | `requests` + `tenacity` (exponential backoff) |
| Data processing | `pandas` |
| Storage | CSV + SQLite (idempotent upsert) |
| Dashboard | `streamlit` + `plotly` |
| Config | `python-dotenv` + dataclass validation |
| Logging | Python `logging` (console + rotating file) |
| Testing | `pytest` (59 tests) + `pytest-cov` |
| CI/CD | GitHub Actions (automated tests + ruff linting) |
| CLI | `argparse` (built-in) |

---

## Project Structure

```
weather-pipeline/
├── main.py               # CLI entry point + pipeline orchestrator
├── dashboard.py           # Streamlit visualization dashboard
├── src/
│   ├── config.py          # .env config + validation + multi-city
│   ├── extract.py         # API fetch with retry + response validation
│   ├── transform.py       # Parse, clean, type-cast
│   ├── validators.py      # 6 data quality checks
│   ├── load.py            # CSV + SQLite idempotent writer
│   ├── logger.py          # Rotating file + console logging
│   └── utils.py           # Shared helpers
├── tests/                 # 59 pytest tests
├── data/                  # Output files (gitignored)
├── logs/                  # Log files (gitignored)
├── pyproject.toml         # Packaging + tool config
├── .github/workflows/     # CI/CD pipeline
└── .env.example           # Config template
```

---

## Quickstart

```bash
# 1. Clone and install
git clone https://github.com/vaibhavvvguptaa/weather-pipeline.git
cd weather-pipeline
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure (optional — defaults to Delhi)
cp .env.example .env

# 3. Run the pipeline
python main.py
```

---

## CLI Usage

```bash
# Default run (uses .env settings)
python main.py

# Override city and coordinates
python main.py --city Mumbai --lat 19.08 --lon 72.88

# 14-day forecast instead of 7
python main.py --days 14

# Skip specific outputs
python main.py --no-csv
python main.py --no-sqlite

# Run on a schedule (every 60 minutes)
python main.py --schedule 60
```

---

## Multi-City Support

Set multiple cities in `.env` (comma-separated):

```env
CITIES=Delhi,Mumbai,Bangalore
```

The pipeline loops through all cities in a single run, producing separate CSVs and deduplicating by `(time, city)` in SQLite.

---

## Dashboard

Visualize your collected data with an interactive dashboard:

```bash
streamlit run dashboard.py
```

Features:
- City selector dropdown
- KPI cards (temperature, humidity, wind speed, data points)
- Hourly temperature trend line chart
- Daily average humidity bar chart
- Wind speed scatter plot
- Weather condition distribution pie chart (WMO codes)
- Precipitation probability area chart
- Raw data table with expand/collapse

---

## Automated Deployment & Live Updates

This project is configured for serverless automation:
* **Scheduled ETL Pipeline:** A GitHub Actions workflow (`.github/workflows/scheduled_etl.yml`) runs automatically every 12 hours.
* **Auto-Ingestion:** The workflow extracts weather forecast data for 5 major cities (`Delhi`, `Mumbai`, `Bangalore`, `Kolkata`, `Chennai`), runs transformations, validates data quality, and updates `data/weather.db`.
* **Database Sync:** The workflow automatically commits and pushes the updated `weather.db` back to the GitHub repository.
* **Real-time Streamlit Sync:** The hosted Streamlit Community Cloud app detects the update and pulls the fresh database automatically, showing live forecasts to visitors.

---

## Data Quality Checks

| Check | Rule | Behavior |
|---|---|---|
| Null values | > 20% per column | Error (pipeline stops) |
| Null values | <= 20% per column | Warning (logged) |
| Temperature | -50 to 60 °C | Error |
| Humidity | 0 to 100% | Error |
| Precipitation | 0 to 100% | Error |
| Wind speed | 0 to 300 km/h | Error |
| Weather code | 0 to 99 (WMO) | Error |
| Duplicates | No duplicate (time, city) | Error |
| Time gaps | < 1h 15m between rows | Warning |
| Row count | >= 90% of expected rows | Error |

---

## Key Engineering Decisions

**Idempotency** — SQLite uses a composite primary key `(time, city)` with `INSERT OR REPLACE` via a temporary table. Safe to re-run without duplicates.

**Retry with exponential backoff** — `tenacity` retries on `ConnectionError`, `Timeout`, HTTP 429, and 5xx errors with wait times 2s -> 4s -> 8s.

**Structured logging** — Dual output to console (INFO+) and rotating file (DEBUG+). 5MB rotation with 5 backups. Run ID tracking via UUID.

**Configuration validation** — Dataclass-based config with `__post_init__` validation for lat/lon ranges, city name, and retry parameters. Invalid config fails fast with clear error messages.

---

## Testing

```bash
# Run all 59 tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## Author

**Vaibhav Gupta** — Technical Support Analyst at Highspring India LLP

[LinkedIn](https://linkedin.com/in/vaibhavvvgupta) | [GitHub](https://github.com/vaibhavvvguptaa)
