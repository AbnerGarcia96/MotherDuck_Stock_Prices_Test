# Marketstack → MotherDuck Pipeline

A small Bronze/Silver/Gold extract/transform/load pipeline that pulls AAPL
end-of-day price data from [marketstack](https://marketstack.com/) (via
apilayer) and loads it into a [MotherDuck](https://motherduck.com/) database
using [DuckDB](https://duckdb.org/). Managed with
[uv](https://docs.astral.sh/uv/).

## Layout

```
pipeline/
  db.py                       # MotherDuck connection + schema setup
  schema.sql                  # bronze / silver / gold table definitions
  extract/
    marketstack.py            # marketstack (via apilayer) EOD client
  transform/
    marketstack.py            # raw API JSON -> bronze/silver DataFrames
  load/
    bronze.py                 # append-only loader for the Bronze layer
    loader.py                 # generic upsert: DataFrame -> MotherDuck table
  gold/
    aapl_daily_returns.sql    # Gold mart: day-over-day AAPL price change
  run_marketstack_bronze.py   # extract -> load, raw EOD pages into Bronze
  run_marketstack_silver.py   # dedupe/type Bronze into Silver
  run_marketstack_gold.py     # recompute the Gold mart from Silver
  run_all.py                  # runs bronze -> silver -> gold in sequence
```

The same bronze/silver/gold logic also runs as three on-demand MotherDuck
Flights (`marketstack-bronze`, `marketstack-silver`, `marketstack-gold`), so
it can be scheduled or triggered from MotherDuck compute instead of running
locally.

## Setup

1. Copy `.env.example` to `.env` and fill in:
   - `MOTHERDUCK_TOKEN` - from MotherDuck (Settings → Access Tokens).
   - `MOTHERDUCK_DATABASE` - defaults to `marketstack_test`.
   - `API_URL` - the full marketstack `/v2/eod` endpoint, e.g.
     `https://api.apilayer.net/marketstack/v2/eod`.
   - `API_ACCESS_KEY` - your apilayer access key. Sign up at
     [marketstack.com](https://marketstack.com/) and get a key from your
     apilayer dashboard.

2. Install dependencies:
   ```
   uv sync
   ```

## Running

```
uv run python -m pipeline.run_marketstack_bronze
uv run python -m pipeline.run_marketstack_bronze --symbol AAPL --date-from 2026-01-01 --date-to 2026-08-26
uv run python -m pipeline.run_marketstack_silver
uv run python -m pipeline.run_marketstack_gold
uv run python -m pipeline.run_all
```

Or via `make`: `make run-marketstack-all` (or the individual
`run-marketstack-bronze` / `-silver` / `-gold` targets).

Tables are created automatically on first run (see `pipeline/schema.sql`).
Bronze is append-only and safe to re-run; Silver upserts by
`(symbol, trade_date)`; Gold is fully recomputed from Silver each run.

## Devcontainer

This project also has a `.devcontainer/` setup (Python, `uv`, and the
DuckDB CLI). Open the folder in VS Code and "Reopen in Container", then
run `uv sync` (done automatically via `postCreateCommand`) to install
dependencies into `.venv`.
