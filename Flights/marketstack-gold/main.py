"""MotherDuck Flight: recompute the AAPL daily-returns Gold mart from Silver.

Gold has no source data of its own - it's a pure SQL recompute of
gold.aapl_daily_returns from silver.aapl_eod.

This is a local copy of the source currently saved to MotherDuck as the
"marketstack-gold" Flight (flight_id 2f9a6ed2-42a0-45d9-8955-202d3712c7e3).
Edit here, then push changes with:
    update_flight(id="2f9a6ed2-42a0-45d9-8955-202d3712c7e3", source_code=...)
"""
from __future__ import annotations

import duckdb

DB = "marketstack_test"

SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS gold;"

GOLD_SQL = """
CREATE OR REPLACE TABLE gold.aapl_daily_returns AS
SELECT
    symbol,
    trade_date,
    close,
    LAG(close) OVER (PARTITION BY symbol ORDER BY trade_date) AS prior_close,
    (close - LAG(close) OVER (PARTITION BY symbol ORDER BY trade_date))
        / LAG(close) OVER (PARTITION BY symbol ORDER BY trade_date) * 100 AS daily_return_pct,
    volume
FROM silver.aapl_eod
ORDER BY symbol, trade_date;
"""


def main() -> None:
    con = duckdb.connect("md:")
    con.execute(f'CREATE DATABASE IF NOT EXISTS "{DB}"')
    con.execute(f'USE "{DB}"')
    con.execute(SCHEMA_SQL)
    con.execute(GOLD_SQL)

    row_count = con.sql("SELECT count(*) FROM gold.aapl_daily_returns").fetchone()[0]
    print(f"Rebuilt gold.aapl_daily_returns: {row_count} row(s).")


if __name__ == "__main__":
    main()
