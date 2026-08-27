"""Entry point: extract dives from the configured API, load into MotherDuck.

Usage:
    uv run python -m pipeline.run_dives
"""
from __future__ import annotations

from dotenv import load_dotenv

from pipeline.db import ensure_schema, get_connection
from pipeline.extract.dives import fetch_dives
from pipeline.load.loader import load_dataframe
from pipeline.transform.dives import transform_dives


def main() -> None:
    load_dotenv()

    raw = fetch_dives()
    df = transform_dives(raw)
    if df.empty:
        print("No dives returned - nothing to load.")
        return

    con = get_connection()
    ensure_schema(con)
    load_dataframe(con, df, "dives", key_columns=["dive_id"])
    print(f"Loaded {len(df)} dive row(s) into MotherDuck.")


if __name__ == "__main__":
    main()
