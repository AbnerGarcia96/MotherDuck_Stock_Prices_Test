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
| `marketstack-dbt/` | `marketstack-dbt` | `f1a1b924-b71c-466b-bbb7-8372b7799532` |

These files are for reference/version control — editing them here does
**not** update MotherDuck. Push a change with `update_flight` (or
`edit_flight_source` for a small patch), then re-sync this copy.

Both currently run on-demand only (no `schedule_cron`).

### `marketstack-dbt/`

Replaces the old `marketstack-silver` and `marketstack-gold` Flights. It
runs `dbt build` (via dbt-core's Python API) against the dbt project
checked into [`dbt/`](../dbt) at the repo root, which is the source of
truth for the silver/gold models, schema tests, and config.

`marketstack-dbt/main.py` is **generated**, not hand-written — it embeds a
copy of every file under `dbt/` as string constants, because a Flight
can't import a local package or read other repo files at runtime. To
change a model or test:

1. Edit files under [`dbt/`](../dbt).
2. Regenerate `main.py`: `python Flights/marketstack-dbt/generate.py`
3. Push with `update_flight`, then re-sync this copy as usual.

Never hand-edit the `PROJECT_FILES` block in `marketstack-dbt/main.py` —
it will be overwritten the next time `generate.py` runs.
