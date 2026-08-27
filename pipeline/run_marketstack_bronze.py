"""Entry point: ingest marketstack AAPL EOD data into the Bronze layer.

Usage:
    uv run python -m pipeline.run_marketstack_bronze
    uv run python -m pipeline.run_marketstack_bronze --symbol AAPL --date-from 2026-01-01 --date-to 2026-08-26

Pages are appended to bronze.aapl_eod_raw as they arrive rather than
accumulated in memory, so a failure partway through a backfill only loses
the in-flight page - see pipeline/extract/marketstack.py:fetch_eod_range().
"""
from __future__ import annotations

import argparse
from datetime import date

from dotenv import load_dotenv

from pipeline.db import ensure_schema, get_connection
from pipeline.extract.marketstack import fetch_eod_range
from pipeline.load.bronze import append_raw
from pipeline.transform.marketstack import transform_eod_page

DEFAULT_DATE_FROM = "2026-01-01"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest marketstack EOD data into bronze.aapl_eod_raw."
    )
    parser.add_argument("--symbol", default="AAPL", help="Ticker symbol (default: AAPL)")
    parser.add_argument(
        "--date-from",
        default=DEFAULT_DATE_FROM,
        help=f"Start date, YYYY-MM-DD (default: {DEFAULT_DATE_FROM})",
    )
    parser.add_argument(
        "--date-to",
        default=date.today().isoformat(),
        help="End date, YYYY-MM-DD (default: today)",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    con = get_connection()
    ensure_schema(con)

    total_rows = 0
    for raw, offset in fetch_eod_range(args.symbol, args.date_from, args.date_to):
        df = transform_eod_page(raw, offset, args.date_from, args.date_to)
        if df.empty:
            continue
        append_raw(con, df, "bronze.aapl_eod_raw")
        total_rows += len(df)
        print(f"Ingested page at offset {offset}: {len(df)} record(s)")

    if total_rows == 0:
        print("No records returned - nothing ingested.")
        return

    print(
        f"Done. Ingested {total_rows} record(s) for {args.symbol} "
        f"({args.date_from} to {args.date_to}) into bronze.aapl_eod_raw."
    )


if __name__ == "__main__":
    main()
