"""Pull remote Dives back into Dives/, for review/version control.

Only refreshes Dives already tracked locally (a `dive_id` present in
`Dives/<name>.metadata.json`) - it does not go looking for other Dives your
account owns that have no local file yet, since this flat layout has no
natural filename to invent for one.

Usage:
    uv run python scripts/deploy/download_dives.py
    # or: make download-dives
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _common import REPO_ROOT, call_one, connect, info, ok, read_json, warn, write_json  # noqa: E402
from deploy_dives import metadata_path_for  # noqa: E402

DIVES_DIR = REPO_ROOT / "Dives"


def download_one(con, tsx_path: Path) -> bool:
    name = tsx_path.stem
    meta_path = metadata_path_for(tsx_path)
    metadata = read_json(meta_path)
    dive_id = metadata.get("dive_id") or None

    if not dive_id:
        info(f"{name}: no dive_id in metadata.json yet - nothing to download.")
        return True

    remote = call_one(con, "MD_GET_DIVE", id=dive_id)
    if remote is None:
        warn(f"{name}: dive_id {dive_id} not found on MotherDuck.")
        return False

    local_content = tsx_path.read_text(encoding="utf-8")
    if remote["content"] != local_content:
        tsx_path.write_text(remote["content"], encoding="utf-8")
        ok(f"{name}: content refreshed from version {remote['current_version']}.")
    else:
        info(f"{name}: content already matches remote.")

    write_json(
        meta_path,
        {
            "dive_id": str(remote["id"]),
            "title": remote["title"],
            "description": remote["description"],
            "status": remote["status"],
            "owner_name": remote["owner_name"],
            "current_version": remote["current_version"],
        },
    )
    return True


def main() -> None:
    con = connect()
    print("Downloading Dives...")

    tsx_files = sorted(DIVES_DIR.glob("*.tsx"))
    if not tsx_files:
        print("No .tsx files found under Dives/.")
        return

    results = [download_one(con, path) for path in tsx_files]
    if not all(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
