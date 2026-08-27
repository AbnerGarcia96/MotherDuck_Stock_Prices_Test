-- Gold mart: day-over-day AAPL price change. Fully recomputed from Silver
-- on every run - see pipeline/run_marketstack_gold.py.
CREATE OR REPLACE TABLE gold.aapl_daily_returns AS
SELECT
    symbol,
    trade_date,
    close,
    LAG(close) OVER (PARTITION BY symbol ORDER BY trade_date) AS prior_close,
    (close - LAG(close) OVER (PARTITION BY symbol ORDER BY trade_date))
        / LAG(close) OVER (PARTITION BY symbol ORDER BY trade_date) * 100 AS daily_return_pct,
    volume
FROM silver.aapl_eod
ORDER BY symbol, trade_date;
