"""Generic append-only loader for Bronze tables: DataFrame -> MotherDuck.

Distinct from pipeline/load/loader.py, which upserts into Silver-style
tables keyed on a primary key. Bronze never upserts or dedupes - each call
just appends the rows it's given, so a table can accumulate duplicate rows
across re-runs. That's intentional: Bronze is the raw, replayable landing
zone, and dedup is a Silver-layer concern.
"""
from __future__ import annotations

import duckdb
import pandas as pd


def append_raw(con: duckdb.DuckDBPyConnection, df: pd.DataFrame, table: str) -> None:
    """Append every row of `df` into `table`, columns matched by name."""
    if df.empty:
        return

    con.register("_incoming", df)
    try:
        columns = ", ".join(df.columns)
        con.execute(f"INSERT INTO {table} ({columns}) SELECT {columns} FROM _incoming")
    finally:
        con.unregister("_incoming")


def fetch_latest_raw(
    con: duckdb.DuckDBPyConnection, table: str, key_columns: list[str]
) -> pd.DataFrame:
    """Read one row per `key_columns` from a Bronze table - the most
    recently loaded one - collapsing the duplicates that accumulate there
    across re-runs. This is Silver's "extract" step: reading from Bronze
    instead of an external API.
    """
    keys = ", ".join(key_columns)
    return con.sql(
        f"""
        SELECT * FROM {table}
        QUALIFY ROW_NUMBER() OVER (PARTITION BY {keys} ORDER BY loaded_at DESC) = 1
        """
    ).df()
