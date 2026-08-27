# Marketstack → MotherDuck

AAPL end-of-day price data, extracted from [marketstack](https://marketstack.com/)
(via apilayer) and processed entirely on [MotherDuck](https://motherduck.com/)
compute — no local pipeline to run or maintain.

## Layout

```
Flights/    # source for the bronze -> silver -> gold MotherDuck Flights
Dives/      # source for the MotherDuck Dive that visualizes the gold layer
```

### Flights

Three on-demand MotherDuck [Flights](https://motherduck.com/) do the ELT
work, each a single-file Python job running on MotherDuck compute:

| Flight | Does |
|---|---|
| `marketstack-bronze` | Fetches raw EOD pages from marketstack, appends into `bronze.aapl_eod_raw` |
| `marketstack-silver` | Dedupes/types the latest Bronze row per `(symbol, trade_date)` into `silver.aapl_eod` |
| `marketstack-gold` | Recomputes `gold.aapl_daily_returns` (day-over-day price change) from Silver |

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

Trigger a Flight run (in order — silver depends on bronze's output, gold on
silver's) via the MotherDuck UI or the `run_flight` MCP tool/API. There's no
local `uv run` step anymore; everything executes on MotherDuck compute.

## Devcontainer

This project also has a `.devcontainer/` setup (Python, `uv`, and the
DuckDB CLI) for ad hoc local `duckdb` queries against MotherDuck. Open the
folder in VS Code and "Reopen in Container", then run `uv sync` (done
automatically via `postCreateCommand`) to install dependencies into `.venv`.
