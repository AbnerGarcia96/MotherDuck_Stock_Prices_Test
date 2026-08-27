"""Entry point: extract flights from AviationStack, load into MotherDuck.

Usage:
    uv run python -m pipeline.run_flights
    uv run python -m pipeline.run_flights --dep-iata JFK --flight-date 2026-08-20
"""
from __future__ import annotations

import argparse

from dotenv import load_dotenv

from pipeline.db import ensure_schema, get_connection
from pipeline.extract.flights import fetch_flights
from pipeline.load.loader import load_dataframe
from pipeline.transform.flights import transform_flights


def parse_args() -> dict:
    parser = argparse.ArgumentParser(description="Load flights into MotherDuck.")
    parser.add_argument("--dep-iata", help="Filter by departure airport IATA code")
    parser.add_argument("--arr-iata", help="Filter by arrival airport IATA code")
    parser.add_argument("--airline-iata", help="Filter by airline IATA code")
    parser.add_argument("--flight-iata", help="Filter by flight IATA code, e.g. AA123")
    parser.add_argument("--flight-date", help="Filter by date, YYYY-MM-DD")
    args = parser.parse_args()

    param_map = {
        "dep_iata": args.dep_iata,
        "arr_iata": args.arr_iata,
        "airline_iata": args.airline_iata,
        "flight_iata": args.flight_iata,
        "flight_date": args.flight_date,
    }
    return {k: v for k, v in param_map.items() if v}


def main() -> None:
    load_dotenv()
    params = parse_args()

    raw = fetch_flights(params or None)
    df = transform_flights(raw)
    if df.empty:
        print("No flights returned - nothing to load.")
        return

    con = get_connection()
    ensure_schema(con)
    load_dataframe(con, df, "flights", key_columns=["flight_id"])
    print(f"Loaded {len(df)} flight row(s) into MotherDuck.")


if __name__ == "__main__":
    main()
