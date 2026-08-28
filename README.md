# Marketstack → MotherDuck

AAPL end-of-day price data, extracted from [marketstack](https://marketstack.com/)
(via apilayer) and processed entirely on [MotherDuck](https://motherduck.com/)
compute — no local pipeline to run or maintain.

## Layout

```
dbt/        # dbt project: the silver + gold transforms, tests, and models
Flights/    # source for the bronze extraction + dbt-build MotherDuck Flights
Dives/      # source for the MotherDuck Dive that visualizes the gold layer
```

### Flights + dbt

Two on-demand MotherDuck [Flights](https://motherduck.com/) do the ELT
work, each a single-file Python job running on MotherDuck compute:

| Flight | Does |
|---|---|
| `marketstack-bronze` | Fetches raw EOD pages from marketstack, appends into `bronze.aapl_eod_raw` |
| `marketstack-dbt` | Runs `dbt build` (the [`dbt/`](dbt) project) to produce `silver.aapl_eod` and `gold.aapl_daily_returns` from Bronze |

Silver and gold are pure SQL transforms, so they're modeled in
[`dbt/`](dbt) — named models, `ref()`/`source()` lineage, and schema
tests — rather than hand-rolled as inline SQL strings. Bronze stays a
Flight since it makes a live marketstack API call, which isn't something
dbt can express as a model. To change a transform, edit `dbt/`, not
`Flights/marketstack-dbt/main.py` directly — see [Flights/README.md](Flights/README.md)
for how that Flight's source is generated from `dbt/`.

All write to the `marketstack_test` MotherDuck database. See
[Flights/README.md](Flights/README.md) for Flight IDs and how to push local
edits back to MotherDuck.

### Dives

`Dives/aapl_eod_snapshot.tsx` is the source for the **AAPL EOD Snapshot**
[Dive](https://motherduck.com/) — an interactive dashboard (KPIs, price
chart, volume chart, observations) reading live from
`gold.aapl_daily_returns`. See [Dives/README.md](Dives/README.md) for the
live URL and how to push local edits back to MotherDuck.

## Running

Trigger a Flight run (in order — `marketstack-dbt` depends on
`marketstack-bronze`'s output) via the MotherDuck UI or the `run_flight`
MCP tool/API. There's no local `uv run` step anymore; everything executes
on MotherDuck compute — `marketstack-dbt` runs `dbt build` on MotherDuck
compute the same way, not from CI or a laptop.

## Deploying

Deployment is manual, not CI/CD — there's no pipeline in this repo. Each
Flight/Dive folder carries a `metadata.json` (id, owner, current version,
plus its own config) alongside its content, and `scripts/deploy/` has one
script per direction:

| Command | Does |
|---|---|
| `make deploy-flights` | Push `Flights/*/main.py` to MotherDuck (create if `flight_id` is empty, otherwise update only what changed) |
| `make deploy-dives` | Push `Dives/*.tsx` to MotherDuck (same create-or-update logic) |
| `make download-flights` | Pull each tracked Flight's current version back into its folder |
| `make download-dives` | Pull each tracked Dive's current content back into its folder |

Setup: `cp .env.example .env` and fill in `MOTHERDUCK_TOKEN` (a personal
token to try things out; a `prod_service_account` token for a real
deploy). Both deploy scripts refuse to touch anything not owned by that
token's account, and are no-ops when nothing actually changed. Add
`--dry-run` to either (`uv run python scripts/deploy/deploy_flights.py --dry-run`)
to see what would happen without touching MotherDuck.

## Devcontainer

This project also has a `.devcontainer/` setup (Python, `uv`, and the
DuckDB CLI) for ad hoc local `duckdb` queries against MotherDuck, and for
iterating on [`dbt/`](dbt) — run `dbt build` locally against
`md:marketstack_test` (needs a `motherduck_token` env var) before
regenerating and pushing the `marketstack-dbt` Flight. Open the folder in
VS Code and "Reopen in Container", then run `uv sync` (done automatically
via `postCreateCommand`) to install dependencies into `.venv`.
