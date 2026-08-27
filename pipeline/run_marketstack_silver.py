"""Entry point: dedupe/type Bronze's raw AAPL EOD records into Silver.

Usage:
    uv run python -m pipeline.run_marketstack_silver

Reads the latest row per (symbol, trade_date) out of bronze.aapl_eod_raw
(collapsing the duplicates that accumulate there across re-runs - see
pipeline/load/bronze.py:fetch_latest_raw()), parses each one's raw JSON
into typed columns, and upserts into silver.aapl_eod.
"""
from __future__ import annotations

from dotenv import load_dotenv

from pipeline.db import ensure_schema, get_connection
from pipeline.load.bronze import fetch_latest_raw
from pipeline.load.loader import load_dataframe
from pipeline.transform.marketstack import transform_bronze_to_silver


def main() -> None:
    load_dotenv()

    con = get_connection()
    ensure_schema(con)

    bronze_rows = fetch_latest_raw(con, "bronze.aapl_eod_raw", ["symbol", "trade_date"])
    if bronze_rows.empty:
        print("No rows in bronze.aapl_eod_raw - nothing to silver.")
        return

    df = transform_bronze_to_silver(bronze_rows)
    load_dataframe(con, df, "silver.aapl_eod", key_columns=["symbol", "trade_date"])
    print(f"Upserted {len(df)} row(s) into silver.aapl_eod.")


if __name__ == "__main__":
    main()
