# Dives & Flights → MotherDuck Pipeline

A small extract/transform/load pipeline that pulls flight and dive data
from external APIs and loads it into a [MotherDuck](https://motherduck.com/)
database using [DuckDB](https://duckdb.org/). Managed with
[uv](https://docs.astral.sh/uv/).

## Layout

```
pipeline/
  db.py             # MotherDuck connection + schema setup
  schema.sql        # flights / dives table definitions
  extract/
    flights.py      # AviationStack (free tier) client
    dives.py        # generic REST API placeholder - point at your source
  transform/
    flights.py      # raw API JSON -> flights DataFrame
    dives.py        # raw API JSON -> dives DataFrame
  load/
    loader.py        # generic upsert: DataFrame -> MotherDuck table
  run_flights.py    # extract -> transform -> load, flights
  run_dives.py      # extract -> transform -> load, dives
  run_all.py        # runs both
```

## Setup

1. Copy `.env.example` to `.env` and fill in:
   - `MOTHERDUCK_TOKEN` - from MotherDuck (Settings → Access Tokens).
   - `MOTHERDUCK_DATABASE` - defaults to `dives_and_flights`.
   - `AVIATIONSTACK_API_KEY` - a free key from
     [aviationstack.com/signup/free](https://aviationstack.com/signup/free).
     Free tier notes: HTTP only (not HTTPS), limited monthly quota,
     real-time/recent flights only (see `pipeline/extract/flights.py`).
   - `DIVE_API_BASE_URL` / `DIVE_API_KEY` - point these at your actual
     dive-log source. The dive extractor/transformer are placeholders;
     adjust `pipeline/extract/dives.py` and `pipeline/transform/dives.py`
     to match your API's real request/response shape.

2. Install dependencies:
   ```
   uv sync
   ```

## Running

```
uv run python -m pipeline.run_flights
uv run python -m pipeline.run_flights --dep-iata JFK --flight-date 2026-08-20
uv run python -m pipeline.run_dives
uv run python -m pipeline.run_all
```

Tables are created automatically on first run (see `pipeline/schema.sql`).
Re-running a script upserts by `flight_id`/`dive_id`, so it's safe to run
repeatedly (e.g. on a schedule) without creating duplicate rows.

## Devcontainer

This project also has a `.devcontainer/` setup (Python, `uv`, and the
DuckDB CLI). Open the folder in VS Code and "Reopen in Container", then
run `uv sync` (done automatically via `postCreateCommand`) to install
dependencies into `.venv`.
