"""Entry point: recompute the AAPL daily-returns Gold mart from Silver.

Usage:
    uv run python -m pipeline.run_marketstack_gold

Unlike Bronze/Silver, Gold has no new source data of its own - it's a pure
SQL recompute of gold.aapl_daily_returns from silver.aapl_eod (see
pipeline/gold/aapl_daily_returns.sql), so there's no extract/transform/load
split here, just a schema-ensure and one CREATE OR REPLACE TABLE.
"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from pipeline.db import ensure_schema, get_connection

GOLD_SQL_PATH = Path(__file__).parent / "gold" / "aapl_daily_returns.sql"


def main() -> None:
    load_dotenv()

    con = get_connection()
    ensure_schema(con)

    con.execute(GOLD_SQL_PATH.read_text())
    row_count = con.sql("SELECT count(*) FROM gold.aapl_daily_returns").fetchone()[0]
    print(f"Rebuilt gold.aapl_daily_returns: {row_count} row(s).")


if __name__ == "__main__":
    main()
