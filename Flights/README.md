# Flights

Local copies of the single-file Python sources saved to MotherDuck as
[Flights](https://motherduck.com/) — scheduled/on-demand jobs that run on
MotherDuck compute rather than locally. Each is self-contained in one file
since a Flight can't import a local Python package.

Each Flight gets its own folder, named after the Flight, holding its
entrypoint (`main.py`) and pinned dependencies (`requirements.txt`).

| Folder | MotherDuck Flight | Flight ID |
|---|---|---|
| `marketstack-bronze/` | `marketstack-bronze` | `3100db19-37d5-4d42-852e-f07888f4129c` |
| `marketstack-silver/` | `marketstack-silver` | `258dcf8a-344a-4247-8550-12f410e4a74f` |
| `marketstack-gold/` | `marketstack-gold` | `2f9a6ed2-42a0-45d9-8955-202d3712c7e3` |

These files are for reference/version control — editing them here does
**not** update MotherDuck. Push a change with `update_flight` (or
`edit_flight_source` for a small patch), then re-sync this copy.

All three currently run on-demand only (no `schedule_cron`).
