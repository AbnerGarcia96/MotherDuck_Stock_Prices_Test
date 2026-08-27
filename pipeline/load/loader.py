"""Generic upsert loader: pandas DataFrame -> MotherDuck table."""
from __future__ import annotations

import duckdb
import pandas as pd


def load_dataframe(
    con: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    table: str,
    key_columns: list[str],
) -> None:
    """Upsert `df` into `table`, keyed on `key_columns`.

    Requires `table` to have a PRIMARY KEY/UNIQUE constraint on
    `key_columns` (see schema.sql) so ON CONFLICT can resolve repeat
    loads by overwriting non-key columns with the new values.
    """
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
