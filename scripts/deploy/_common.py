"""Shared helpers for the deploy_*/download_* scripts.

Not a public module - only imported by the sibling scripts in this
directory, which add this folder to sys.path before importing it.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_env() -> None:
    """Load MOTHERDUCK_TOKEN (and friends) from repo-root .env, if present."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(REPO_ROOT / ".env")


def connect() -> duckdb.DuckDBPyConnection:
    """Open a MotherDuck connection using MOTHERDUCK_TOKEN from the env/.env.

    Use a prod_service_account token (see .env.example) for real deploys;
    a personal token works fine for trying the scripts out.
    """
    load_env()
    token = os.environ.get("MOTHERDUCK_TOKEN")
    if not token:
        raise SystemExit(
            "MOTHERDUCK_TOKEN is not set. Copy .env.example to .env and "
            "fill in a token, or export MOTHERDUCK_TOKEN in your shell."
        )
    return duckdb.connect(f"md:?motherduck_token={token}")


def current_user(con: duckdb.DuckDBPyConnection) -> str:
    """The MotherDuck username the current token authenticates as."""
    return con.sql("SELECT md_user()").fetchone()[0]


def as_uuid(value: str) -> uuid.UUID:
    return uuid.UUID(str(value))


def call(
    con: duckdb.DuckDBPyConnection,
    function: str,
    casts: dict[str, str] | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Run `SELECT * FROM <function>(key := $key, ...)`.

    kwargs whose value is None are omitted entirely (MotherDuck treats a
    missing named argument as "leave unchanged" on MD_UPDATE_*, which is
    different from passing an explicit NULL). `casts` names an explicit SQL
    type to CAST a given kwarg to - needed for MAP/LIST-typed parameters,
    since DuckDB can't always infer those from a bound Python value alone.
    """
    casts = casts or {}
    provided = {k: v for k, v in kwargs.items() if v is not None}
    clauses = [
        f"{k} := CAST(${k} AS {casts[k]})" if k in casts else f"{k} := ${k}"
        for k in provided
    ]
    sql = f"SELECT * FROM {function}({', '.join(clauses)})"
    result = con.execute(sql, provided)
    columns = [d[0] for d in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


def call_one(
    con: duckdb.DuckDBPyConnection,
    function: str,
    casts: dict[str, str] | None = None,
    **kwargs: Any,
) -> dict[str, Any] | None:
    rows = call(con, function, casts=casts, **kwargs)
    return rows[0] if rows else None


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def info(msg: str) -> None:
    print(f"  - {msg}")


def ok(msg: str) -> None:
    print(f"  * {msg}")


def warn(msg: str) -> None:
    print(f"  ! {msg}")
