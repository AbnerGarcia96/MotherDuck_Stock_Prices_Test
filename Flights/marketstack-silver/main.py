"""MotherDuck Flight: dedupe/type Bronze's raw AAPL EOD records into Silver.

Reads the latest row per (symbol, trade_date) out of bronze.aapl_eod_raw,
parses each one's raw JSON into typed columns, and upserts into
silver.aapl_eod.

This is a local copy of the source currently saved to MotherDuck as the
"marketstack-silver" Flight (flight_id 258dcf8a-344a-4247-8550-12f410e4a74f).
Edit here, then push changes with:
    update_flight(id="258dcf8a-344a-4247-8550-12f410e4a74f", source_code=...)
"""
from __future__ import annotations

import json

import duckdb
import pandas as pd

DB = "marketstack_test"

SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS silver;
CREATE TABLE IF NOT EXISTS silver.aapl_eod (
    symbol VARCHAR,
    trade_date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    adj_open DOUBLE,
    adj_high DOUBLE,
    adj_low DOUBLE,
    adj_close DOUBLE,
    adj_volume DOUBLE,
    split_factor DOUBLE,
    dividend DOUBLE,
    exchange VARCHAR,
    exchange_code VARCHAR,
    price_currency VARCHAR,
    silvered_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (symbol, trade_date)
);
"""


def fetch_latest_raw(con: duckdb.DuckDBPyConnection, table: str, key_columns: list[str]) -> pd.DataFrame:
    keys = ", ".join(key_columns)
    return con.sql(
        f"""
        SELECT * FROM {table}
        QUALIFY ROW_NUMBER() OVER (PARTITION BY {keys} ORDER BY loaded_at DESC) = 1
        """
    ).df()


def transform_bronze_to_silver(bronze_rows: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, bronze_row in bronze_rows.iterrows():
        record = json.loads(bronze_row["raw"])
        rows.append(
            {
                "symbol": bronze_row["symbol"],
                "trade_date": bronze_row["trade_date"],
                "open": record.get("open"),
                "high": record.get("high"),
                "low": record.get("low"),
                "close": record.get("close"),
                "volume": record.get("volume"),
                "adj_open": record.get("adj_open"),
                "adj_high": record.get("adj_high"),
                "adj_low": record.get("adj_low"),
                "adj_close": record.get("adj_close"),
                "adj_volume": record.get("adj_volume"),
                "split_factor": record.get("split_factor"),
                "dividend": record.get("dividend"),
                "exchange": record.get("exchange"),
                "exchange_code": record.get("exchange_code"),
                "price_currency": record.get("price_currency"),
            }
        )
    return pd.DataFrame(rows)


def load_dataframe(con: duckdb.DuckDBPyConnection, df: pd.DataFrame, table: str, key_columns: list[str]) -> None:
    if df.empty:
        return
    con.register("_incoming", df)
    try:
        columns = ", ".join(df.columns)
        conflict_cols = ", ".join(key_columns)
        update_cols = [c for c in df.columns if c not in key_columns]
        if update_cols:
            updates = ", ".join(f"{c} = excluded.{c}" for c in update_cols)
            con.execute(
                f"""
                INSERT INTO {table} ({columns})
                SELECT {columns} FROM _incoming
                ON CONFLICT ({conflict_cols}) DO UPDATE SET {updates}
                """
            )
        else:
            con.execute(
                f"""
                INSERT INTO {table} ({columns})
                SELECT {columns} FROM _incoming
                ON CONFLICT ({conflict_cols}) DO NOTHING
                """
            )
    finally:
        con.unregister("_incoming")


def main() -> None:
    con = duckdb.connect("md:")
    con.execute(f'CREATE DATABASE IF NOT EXISTS "{DB}"')
    con.execute(f'USE "{DB}"')
    con.execute(SCHEMA_SQL)

    bronze_rows = fetch_latest_raw(con, "bronze.aapl_eod_raw", ["symbol", "trade_date"])
    if bronze_rows.empty:
        print("No rows in bronze.aapl_eod_raw - nothing to silver.")
        return

    df = transform_bronze_to_silver(bronze_rows)
    load_dataframe(con, df, "silver.aapl_eod", key_columns=["symbol", "trade_date"])
    print(f"Upserted {len(df)} row(s) into silver.aapl_eod.")


if __name__ == "__main__":
    main()
