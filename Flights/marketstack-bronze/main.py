"""MotherDuck Flight: ingest marketstack AAPL EOD data into the Bronze layer.

Self-contained single-file job (a Flight can't import a local Python
package, so the extract/transform/load steps are all inlined here).

This is a local copy of the source currently saved to MotherDuck as the
"marketstack-bronze" Flight (flight_id 3100db19-37d5-4d42-852e-f07888f4129c).
Edit here, then push changes with:
    update_flight(id="3100db19-37d5-4d42-852e-f07888f4129c", source_code=...)

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
from datetime import date

import duckdb
import pandas as pd
import requests

DB = "marketstack_test"
DEFAULT_DATE_FROM = "2026-01-01"

SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE TABLE IF NOT EXISTS bronze.aapl_eod_raw (
    symbol VARCHAR,
    trade_date DATE,
    raw VARCHAR,
    request_date_from DATE,
    request_date_to DATE,
    request_offset INTEGER,
    loaded_at TIMESTAMP DEFAULT now()
);
"""


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


def fetch_eod_range(symbol: str, date_from: str, date_to: str, limit: int = 100, delay_s: float = 1.0):
    offset = 0
    while True:
        payload = fetch_eod_page(symbol, date_from, date_to, offset=offset, limit=limit)
        records = payload.get("data", [])
        yield records, offset

        pagination = payload.get("pagination", {})
        total = pagination.get("total", 0)
        offset += limit
        if offset >= total:
            break
        time.sleep(delay_s)


def transform_eod_page(raw_records: list[dict], offset: int, date_from: str, date_to: str) -> pd.DataFrame:
    rows = [
        {
            "symbol": record.get("symbol"),
            "trade_date": record.get("date", "")[:10] or None,
            "raw": json.dumps(record),
            "request_date_from": date_from,
            "request_date_to": date_to,
            "request_offset": offset,
        }
        for record in raw_records
    ]
    return pd.DataFrame(rows)


def append_raw(con: duckdb.DuckDBPyConnection, df: pd.DataFrame, table: str) -> None:
    if df.empty:
        return
    con.register("_incoming", df)
    try:
        columns = ", ".join(df.columns)
        con.execute(f"INSERT INTO {table} ({columns}) SELECT {columns} FROM _incoming")
    finally:
        con.unregister("_incoming")


def main() -> None:
    symbol = os.environ.get("SYMBOL", "AAPL")
    date_from = os.environ.get("DATE_FROM", DEFAULT_DATE_FROM)
    date_to = os.environ.get("DATE_TO") or date.today().isoformat()

    con = duckdb.connect("md:")
    con.execute(f'CREATE DATABASE IF NOT EXISTS "{DB}"')
    con.execute(f'USE "{DB}"')
    con.execute(SCHEMA_SQL)

    total_rows = 0
    for raw, offset in fetch_eod_range(symbol, date_from, date_to):
        df = transform_eod_page(raw, offset, date_from, date_to)
        if df.empty:
            continue
        append_raw(con, df, "bronze.aapl_eod_raw")
        total_rows += len(df)
        print(f"Ingested page at offset {offset}: {len(df)} record(s)")

    if total_rows == 0:
        print("No records returned - nothing ingested.")
        return

    print(
        f"Done. Ingested {total_rows} record(s) for {symbol} "
        f"({date_from} to {date_to}) into bronze.aapl_eod_raw."
    )


if __name__ == "__main__":
    main()
