"""Run both pipelines: flights then dives.

Usage:
    uv run python -m pipeline.run_all
"""
from __future__ import annotations

from pipeline import run_dives, run_flights


def main() -> None:
    print("--- Flights ---")
    run_flights.main()
    print("--- Dives ---")
    run_dives.main()


if __name__ == "__main__":
    main()
