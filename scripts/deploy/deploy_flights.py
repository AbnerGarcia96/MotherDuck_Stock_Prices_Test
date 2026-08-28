"""Deploy every Flight under Flights/ to MotherDuck.

For each `Flights/<name>/` (main.py + optional requirements.txt), tracked by
a sibling `Flights/<name>/metadata.json`:

  - empty/missing `flight_id` -> create it (MD_CREATE_FLIGHT) and record the
    new id;
  - existing `flight_id` -> fetch the remote Flight and its current
    version's full source (MD_GET_FLIGHT_VERSION - MD_GET_FLIGHT alone only
    returns metadata), refuse to touch it if its owner doesn't match the
    current MotherDuck account, update only the fields that actually
    changed (a no-op otherwise), then rewrite metadata.json from the
    confirmed remote state.

Usage:
    uv run python scripts/deploy/deploy_flights.py
    # or: make deploy-flights
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _common import (  # noqa: E402
    REPO_ROOT,
    call_one,
    connect,
    current_user,
    info,
    ok,
    read_json,
    warn,
    write_json,
)

FLIGHTS_DIR = REPO_ROOT / "Flights"
FLIGHT_CASTS = {
    "config": "MAP(VARCHAR, VARCHAR)",
    "flight_secret_names": "VARCHAR[]",
}


def deploy_one(con, flight_dir: Path, user: str, dry_run: bool = False) -> bool:
    name = flight_dir.name
    main_py = flight_dir / "main.py"
    if not main_py.exists():
        return True  # not a Flight folder - nothing to deploy

    source_code = main_py.read_text(encoding="utf-8")
    requirements_path = flight_dir / "requirements.txt"
    requirements_txt = (
        requirements_path.read_text(encoding="utf-8") if requirements_path.exists() else None
    )

    meta_path = flight_dir / "metadata.json"
    metadata = read_json(meta_path)

    flight_id = metadata.get("flight_id") or None
    flight_name = metadata.get("name") or name
    schedule_cron = metadata.get("schedule_cron")
    config = metadata.get("config") or {}
    access_token_name = metadata.get("access_token_name")
    flight_secret_names = metadata.get("flight_secret_names") or []
    max_runtime_sec = metadata.get("max_runtime_sec")
    prefix = "[dry-run] " if dry_run else ""

    if flight_id:
        remote = call_one(con, "MD_GET_FLIGHT", flight_id=flight_id)
        if remote is None:
            warn(f"{name}: flight_id {flight_id} is set locally but doesn't exist on MotherDuck.")
            return False
        if remote["owner_name"] != user:
            warn(
                f"{name}: owned by '{remote['owner_name']}', not the current "
                f"account ('{user}'). Refusing to touch it."
            )
            return False

        version = call_one(
            con, "MD_GET_FLIGHT_VERSION", flight_id=flight_id, version_number=remote["current_version"]
        )

        changes: dict = {}
        if version["source_code"] != source_code:
            changes["source_code"] = source_code
        if (version.get("requirements_txt") or None) != requirements_txt:
            changes["requirements_txt"] = requirements_txt
        if (version.get("config") or {}) != config:
            changes["config"] = config
        if (version.get("access_token_name") or None) != access_token_name:
            changes["access_token_name"] = access_token_name
        if sorted(version.get("flight_secret_names") or []) != sorted(flight_secret_names):
            changes["flight_secret_names"] = flight_secret_names
        if (version.get("max_runtime_sec") or None) != max_runtime_sec:
            changes["max_runtime_sec"] = max_runtime_sec
        if (remote.get("schedule_cron") or None) != (schedule_cron or None):
            changes["schedule_cron"] = schedule_cron or ""
        if remote["flight_name"] != flight_name:
            changes["name"] = flight_name

        if dry_run:
            if changes:
                ok(f"{prefix}{name}: would update ({', '.join(sorted(changes))}).")
            else:
                info(f"{prefix}{name}: unchanged.")
            return True

        if changes:
            call_one(con, "MD_UPDATE_FLIGHT", casts=FLIGHT_CASTS, flight_id=flight_id, **changes)
            ok(f"{name}: updated ({', '.join(sorted(changes))}).")
        else:
            info(f"{name}: unchanged.")

        final = call_one(con, "MD_GET_FLIGHT", flight_id=flight_id)
    else:
        if dry_run:
            ok(f"{prefix}{name}: would create a new Flight named '{flight_name}'.")
            return True

        created = call_one(
            con,
            "MD_CREATE_FLIGHT",
            casts=FLIGHT_CASTS,
            name=flight_name,
            source_code=source_code,
            requirements_txt=requirements_txt,
            schedule_cron=schedule_cron,
            config=config or None,
            access_token_name=access_token_name,
            flight_secret_names=flight_secret_names or None,
            max_runtime_sec=max_runtime_sec,
        )
        flight_id = str(created["flight_id"])
        final = created
        ok(f"{name}: created as flight_id {flight_id}.")

    write_json(
        meta_path,
        {
            "flight_id": str(final["flight_id"]),
            "name": final["flight_name"],
            "schedule_cron": final.get("schedule_cron"),
            "config": config,
            "access_token_name": access_token_name,
            "flight_secret_names": flight_secret_names,
            "max_runtime_sec": max_runtime_sec,
            "owner_name": final["owner_name"],
            "current_version": final["current_version"],
            "status": final.get("status"),
        },
    )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="Report what would change without touching MotherDuck."
    )
    args = parser.parse_args()

    con = connect()
    user = current_user(con)
    print(f"Deploying Flights as MotherDuck user '{user}'{' (dry run)' if args.dry_run else ''}...")

    flight_dirs = sorted(p for p in FLIGHTS_DIR.iterdir() if p.is_dir())
    if not flight_dirs:
        print("No Flight folders found under Flights/.")
        return

    results = [deploy_one(con, d, user, dry_run=args.dry_run) for d in flight_dirs]
    if not all(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
