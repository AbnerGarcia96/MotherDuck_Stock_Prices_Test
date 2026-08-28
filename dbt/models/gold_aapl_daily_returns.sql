-- Recompute the AAPL daily-returns Gold mart from Silver.
--
-- Pure SQL recompute (materialized as a table, config in dbt_project.yml)
-- from silver_aapl_eod — replaces the marketstack-gold Flight's GOLD_SQL.

select
    symbol,
    trade_date,
    close,
    lag(close) over (partition by symbol order by trade_date) as prior_close,
    (close - lag(close) over (partition by symbol order by trade_date))
        / lag(close) over (partition by symbol order by trade_date) * 100 as daily_return_pct,
    volume
from {{ ref('silver_aapl_eod') }}
order by symbol, trade_date
