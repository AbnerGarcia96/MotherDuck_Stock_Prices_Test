"""MotherDuck connection helpers."""
from __future__ import annotations

import os
from pathlib import Path

import duckdb

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(database: str | None = None) -> duckdb.DuckDBPyConnection:
    """Open a connection to a MotherDuck database.

    Relies on the MOTHERDUCK_TOKEN environment variable, which DuckDB's
    `md:` connection string picks up automatically. Raises a clear error
    up front instead of letting the connection fail with an opaque one.
    """
    if not os.environ.get("MOTHERDUCK_TOKEN"):
        raise RuntimeError(
            "MOTHERDUCK_TOKEN is not set. Copy .env.example to .env, fill "
            "in your token, and make sure it's loaded (run_*.py scripts do "
            "this via python-dotenv) before calling get_connection()."
        )
    db_name = database or os.environ.get("MOTHERDUCK_DATABASE", "dives_and_flights")
    return duckdb.connect(f"md:{db_name}")


def ensure_schema(con: duckdb.DuckDBPyConnection) -> None:
    """Create the flights/dives tables if they don't already exist."""
    con.execute(SCHEMA_PATH.read_text())
