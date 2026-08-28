"""Deploy every Dive under Dives/ to MotherDuck.

For each `Dives/<name>.tsx`, tracked by a sibling `Dives/<name>.metadata.json`:

  - empty/missing `dive_id` -> create it (MD_CREATE_DIVE) and record the new
    id;
  - existing `dive_id` -> fetch the remote Dive, refuse to touch it if its
    owner doesn't match the current MotherDuck account, update its content
    only if the content or REQUIRED_DATABASES actually changed (a no-op
    otherwise), re-apply `status`, then rewrite metadata.json from the
    confirmed remote state.

`REQUIRED_DATABASES` is read out of the .tsx itself (see _tsx.py) rather
than duplicated in metadata.json, since the Dive runtime already requires
it to live in the source - keeping it in one place only.

Usage:
    uv run python scripts/deploy/deploy_dives.py
    # or: make deploy-dives
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
from _tsx import extract_required_databases  # noqa: E402

DIVES_DIR = REPO_ROOT / "Dives"
REQUIRED_RESOURCES_CAST = "STRUCT(url VARCHAR, alias VARCHAR)[]"


def metadata_path_for(tsx_path: Path) -> Path:
    return tsx_path.with_suffix("").with_suffix(".metadata.json")


def humanize(stem: str) -> str:
    return stem.replace("_", " ").replace("-", " ").title()


def deploy_one(con, tsx_path: Path, user: str, dry_run: bool = False) -> bool:
    name = tsx_path.stem
    content = tsx_path.read_text(encoding="utf-8")
    meta_path = metadata_path_for(tsx_path)
    metadata = read_json(meta_path)

    try:
        required_resources = extract_required_databases(content)
    except ValueError as exc:
        warn(f"{name}: {exc} - skipping.")
        return False

    dive_id = metadata.get("dive_id") or None
    title = metadata.get("title") or humanize(name)
    description = metadata.get("description", "")
    status = metadata.get("status", "draft")
    prefix = "[dry-run] " if dry_run else ""

    if dive_id:
        remote = call_one(con, "MD_GET_DIVE", id=dive_id)
        if remote is None:
            warn(f"{name}: dive_id {dive_id} is set locally but doesn't exist on MotherDuck.")
            return False
        if remote["owner_name"] != user:
            warn(
                f"{name}: owned by '{remote['owner_name']}', not the current "
                f"account ('{user}'). Refusing to touch it."
            )
            return False

        current_version = remote["current_version"]
        remote_resources = [
            {"url": r["url"], "alias": r["alias"]}
            for r in (remote.get("version_required_resources") or [])
        ]
        content_changed = remote["content"] != content or remote_resources != required_resources
        metadata_changed = remote["title"] != title or remote["description"] != description

        if content_changed:
            if dry_run:
                ok(f"{prefix}{name}: would update content (v{current_version} -> new version).")
            else:
                updated = call_one(
                    con,
                    "MD_UPDATE_DIVE_CONTENT",
                    casts={"required_resources": REQUIRED_RESOURCES_CAST},
                    id=dive_id,
                    content=content,
                    description=description,
                    required_resources=required_resources,
                )
                current_version = updated["version"]
                ok(f"{name}: content updated (now version {current_version}).")
        else:
            info(f"{prefix}{name}: content unchanged.")

        if metadata_changed:
            if dry_run:
                ok(f"{prefix}{name}: would update title/description.")
            else:
                call_one(con, "MD_UPDATE_DIVE_METADATA", id=dive_id, title=title, description=description)
                ok(f"{name}: title/description updated.")

        if dry_run:
            return True

        final = call_one(con, "MD_UPDATE_DIVE_STATUS", id=dive_id, status=status, version=current_version)
    else:
        if dry_run:
            ok(f"{prefix}{name}: would create a new Dive titled '{title}'.")
            return True

        created = call_one(
            con,
            "MD_CREATE_DIVE",
            casts={"required_resources": REQUIRED_RESOURCES_CAST},
            title=title,
            content=content,
            description=description,
            required_resources=required_resources,
        )
        dive_id = str(created["id"])
        final = call_one(
            con, "MD_UPDATE_DIVE_STATUS", id=dive_id, status=status, version=created["current_version"]
        )
        ok(f"{name}: created as dive_id {dive_id}.")

    write_json(
        meta_path,
        {
            "dive_id": str(final["id"]),
            "title": final["title"],
            "description": final["description"],
            "status": final["status"],
            "owner_name": final["owner_name"],
            "current_version": final["current_version"],
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
    print(f"Deploying Dives as MotherDuck user '{user}'{' (dry run)' if args.dry_run else ''}...")

    tsx_files = sorted(DIVES_DIR.glob("*.tsx"))
    if not tsx_files:
        print("No .tsx files found under Dives/.")
        return

    results = [deploy_one(con, path, user, dry_run=args.dry_run) for path in tsx_files]
    if not all(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
