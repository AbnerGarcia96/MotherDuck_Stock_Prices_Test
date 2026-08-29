"""MotherDuck Flight: ingest marketstack AAPL EOD data into the Bronze layer.

Uses dlt (data load tool) for the extract/paginate/load plumbing instead of
a hand-rolled duckdb insert loop. dlt still writes plain `append` — no dlt
incremental cursor — so DATE_FROM/DATE_TO stay caller-controlled the same
way they always have, and re-running with the same range re-appends rather
than upserting. Dedup happens downstream in dbt's silver_aapl_eod, which
keeps the latest bronze row per (symbol, trade_date) via
`qualify row_number() ... order by loaded_at desc` — see
dbt/models/silver_aapl_eod.sql. See the root README for why bronze (a live
API call) is a Flight rather than a dbt model.

Single-file mirror of pipeline/run_marketstack_bronze.py from the
MotherDuck_Test repo (Flights can't import a local Python package, so the
extract/transform/load helpers are inlined here).

Config:
    API_URL     - full marketstack /v2/eod endpoint (non-secret)
    SYMBOL      - ticker symbol, defaults to AAPL
    DATE_FROM   - defaults to 2026-01-01
    DATE_TO     - defaults to today

Secret (type=flights, name=marketstack_api):
    API_ACCESS_KEY - apilayer marketstack access key
    Add this secret in the MotherDuck UI, then attach it to this Flight via
    update_flight(flight_secret_names=["marketstack_api"]).
"""
from __future__ import annotations

import json
import os
import time
from datetime import date, datetime, timezone

import dlt
import requests

DB = "marketstack_test"
DEFAULT_DATE_FROM = "2026-01-01"

# Explicit column types so dlt's schema inference matches the table this
# Flight has always written, instead of guessing types from the first batch.
BRONZE_COLUMNS = {
    "symbol": {"data_type": "text"},
    "trade_date": {"data_type": "date"},
    "raw": {"data_type": "text"},
    "request_date_from": {"data_type": "date"},
    "request_date_to": {"data_type": "date"},
    "request_offset": {"data_type": "bigint"},
    "loaded_at": {"data_type": "timestamp"},
}


def fetch_eod_page(
    symbol: str, date_from: str, date_to: str, offset: int = 0, limit: int = 100
) -> dict:
    api_url = os.environ["API_URL"]
    api_key = os.environ.get("marketstack_api_API_ACCESS_KEY") or os.environ["API_ACCESS_KEY"]

    params = {
        "access_key": api_key,
        "symbols": symbol,
        "date_from": date_from,
        "date_to": date_to,
        "limit": limit,
        "offset": offset,
    }
    response = requests.get(api_url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    if "error" in payload:
        raise RuntimeError(f"marketstack API error: {payload['error']}")

    return payload


def transform_eod_record(record: dict, offset: int, date_from: str, date_to: str) -> dict:
    return {
        "symbol": record.get("symbol"),
        "trade_date": record.get("date", "")[:10] or None,
        "raw": json.dumps(record),
        "request_date_from": date_from,
        "request_date_to": date_to,
        "request_offset": offset,
        "loaded_at": datetime.now(timezone.utc),
    }


@dlt.resource(name="aapl_eod_raw", write_disposition="append", columns=BRONZE_COLUMNS)
def aapl_eod_raw(symbol: str, date_from: str, date_to: str, limit: int = 100, delay_s: float = 1.0):
    """Page through marketstack EOD and yield rows shaped like bronze.aapl_eod_raw."""
    offset = 0
    while True:
        payload = fetch_eod_page(symbol, date_from, date_to, offset=offset, limit=limit)
        records = payload.get("data", [])
        if records:
            yield [transform_eod_record(r, offset, date_from, date_to) for r in records]

        pagination = payload.get("pagination", {})
        total = pagination.get("total", 0)
        offset += limit
        if offset >= total:
            break
        time.sleep(delay_s)


def main() -> None:
    symbol = os.environ.get("SYMBOL", "AAPL")
    date_from = os.environ.get("DATE_FROM", DEFAULT_DATE_FROM)
    date_to = os.environ.get("DATE_TO") or date.today().isoformat()

    # A Flight's own `md:` connection is already authenticated as the
    # Flight's identity (same as duckdb.connect("md:") in the Flight this
    # replaces) — dlt's motherduck destination resolves credentials the
    # same way, so no token is needed here.
    pipeline = dlt.pipeline(
        pipeline_name="marketstack_bronze",
        destination=dlt.destinations.motherduck(credentials=f"md:{DB}"),
        dataset_name="bronze",
    )

    load_info = pipeline.run(aapl_eod_raw(symbol, date_from, date_to))

    if load_info.has_failed_jobs:
        raise RuntimeError(f"dlt load failed: {load_info}")

    print(load_info)
    print(
        f"Done. Ingested via dlt for {symbol} ({date_from} to {date_to}) "
        "into bronze.aapl_eod_raw."
    )


if __name__ == "__main__":
    main()
