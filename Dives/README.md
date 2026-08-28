# Dives

Local copies of the JSX/React sources saved to MotherDuck as
[Dives](https://motherduck.com/) — interactive data apps rendered against
live MotherDuck data.

| File | MotherDuck Dive | Dive ID | Live URL |
|---|---|---|---|
| `aapl_eod_snapshot.tsx` | AAPL EOD Snapshot | `a7e0efa2-9aa3-4d37-801d-f54f68c1399b` | https://app.motherduck.com/dives/aapl-eod-snapshot-a7e0efa2-9aa3-4d37-801d-f54f68c1399b |

Each `.tsx` has a sibling `<name>.metadata.json` (dive ID, title,
description, owner, status, current version) that
`scripts/deploy/deploy_dives.py` uses to track what's live. A Dive's
required databases/shares live only in its `REQUIRED_DATABASES` export in
the `.tsx` itself, not in metadata.json.

Editing a file here does **not** update MotherDuck by itself. Push a
change with `make deploy-dives` from the repo root (see the root
[README.md](../README.md#deploying) for setup) — it updates only the
Dives whose content actually changed, re-applies `status`, and refuses to
touch a Dive it doesn't own. Run `make download-dives` to pull the live
version back down first if you suspect drift.
