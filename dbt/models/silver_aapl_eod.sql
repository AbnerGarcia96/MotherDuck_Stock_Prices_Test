-- Dedupe/type Bronze's raw AAPL EOD records into Silver.
--
-- Takes the latest bronze row per (symbol, trade_date) (mirrors the
-- marketstack-silver Flight it replaces) and parses each one's `raw` JSON
-- blob into typed columns using DuckDB's native JSON operators instead of
-- a per-row Python json.loads loop.
--
-- Materialized as incremental + delete+insert (config in dbt_project.yml,
-- keyed on symbol/trade_date) so re-running replaces existing rows for
-- the same key, same effect as the Flight's ON CONFLICT DO UPDATE.
-- ('merge' isn't valid here: dbt-duckdb only supports it for
-- iceberg/delta destinations, not plain DuckDB tables.)

with latest_raw as (

    select *
    from {{ source('bronze', 'aapl_eod_raw') }}
    qualify row_number() over (
        partition by symbol, trade_date order by loaded_at desc
    ) = 1

)

select
    symbol,
    trade_date,
    cast(raw::json ->> '$.open' as double) as open,
    cast(raw::json ->> '$.high' as double) as high,
    cast(raw::json ->> '$.low' as double) as low,
    cast(raw::json ->> '$.close' as double) as close,
    cast(raw::json ->> '$.volume' as double) as volume,
    cast(raw::json ->> '$.adj_open' as double) as adj_open,
    cast(raw::json ->> '$.adj_high' as double) as adj_high,
    cast(raw::json ->> '$.adj_low' as double) as adj_low,
    cast(raw::json ->> '$.adj_close' as double) as adj_close,
    cast(raw::json ->> '$.adj_volume' as double) as adj_volume,
    cast(raw::json ->> '$.split_factor' as double) as split_factor,
    cast(raw::json ->> '$.dividend' as double) as dividend,
    raw::json ->> '$.exchange' as exchange,
    raw::json ->> '$.exchange_code' as exchange_code,
    raw::json ->> '$.price_currency' as price_currency,
    now() as silvered_at
from latest_raw
