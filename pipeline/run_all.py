"""Run the full marketstack pipeline: bronze, then silver, then gold.

Usage:
    uv run python -m pipeline.run_all
"""
from __future__ import annotations

from pipeline import run_marketstack_bronze, run_marketstack_gold, run_marketstack_silver


def main() -> None:
    print("--- Bronze ---")
    run_marketstack_bronze.main()
    print("--- Silver ---")
    run_marketstack_silver.main()
    print("--- Gold ---")
    run_marketstack_gold.main()


if __name__ == "__main__":
    main()
