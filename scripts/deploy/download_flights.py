"""Pull remote Flights back into Flights/, for review/version control.

Only refreshes Flights already tracked locally (a `flight_id` present in
`Flights/<name>/metadata.json`) - it does not go looking for other Flights
your account owns that have no local folder yet.

Usage:
    uv run python scripts/deploy/download_flights.py
    # or: make download-flights
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _common import REPO_ROOT, call_one, connect, info, ok, read_json, warn, write_json  # noqa: E402

FLIGHTS_DIR = REPO_ROOT / "Flights"


def download_one(con, flight_dir: Path) -> bool:
    name = flight_dir.name
    meta_path = flight_dir / "metadata.json"
    metadata = read_json(meta_path)
    flight_id = metadata.get("flight_id") or None

    if not flight_id:
        info(f"{name}: no flight_id in metadata.json yet - nothing to download.")
        return True

    remote = call_one(con, "MD_GET_FLIGHT", flight_id=flight_id)
    if remote is None:
        warn(f"{name}: flight_id {flight_id} not found on MotherDuck.")
        return False

    version = call_one(
        con, "MD_GET_FLIGHT_VERSION", flight_id=flight_id, version_number=remote["current_version"]
    )

    main_py = flight_dir / "main.py"
    if not main_py.exists() or main_py.read_text(encoding="utf-8") != version["source_code"]:
        main_py.write_text(version["source_code"], encoding="utf-8")
        ok(f"{name}: main.py refreshed from version {remote['current_version']}.")
    else:
        info(f"{name}: main.py already matches remote.")

    requirements_path = flight_dir / "requirements.txt"
    remote_requirements = version.get("requirements_txt") or ""
    if remote_requirements:
        if not requirements_path.exists() or requirements_path.read_text(encoding="utf-8") != remote_requirements:
            requirements_path.write_text(remote_requirements, encoding="utf-8")
            ok(f"{name}: requirements.txt refreshed.")

    write_json(
        meta_path,
        {
            "flight_id": str(remote["flight_id"]),
            "name": remote["flight_name"],
            "schedule_cron": remote.get("schedule_cron"),
            "config": version.get("config") or {},
            "access_token_name": version.get("access_token_name"),
            "flight_secret_names": version.get("flight_secret_names") or [],
            "max_runtime_sec": version.get("max_runtime_sec"),
            "owner_name": remote["owner_name"],
            "current_version": remote["current_version"],
            "status": remote.get("status"),
        },
    )
    return True


def main() -> None:
    con = connect()
    print("Downloading Flights...")

    flight_dirs = sorted(p for p in FLIGHTS_DIR.iterdir() if p.is_dir())
    if not flight_dirs:
        print("No Flight folders found under Flights/.")
        return

    results = [download_one(con, d) for d in flight_dirs]
    if not all(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
