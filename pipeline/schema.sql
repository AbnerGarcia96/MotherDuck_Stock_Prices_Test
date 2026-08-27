-- Schema for the marketstack MotherDuck database.
-- Applied via pipeline.db.ensure_schema() before every load.

-- Bronze layer: raw, append-only landing tables. One row per record as
-- returned by the source API, with ingestion metadata. Never upserted or
-- deduped - see pipeline/load/bronze.py - so later Silver/Gold layers can
-- be re-derived without re-hitting a rate-limited API.
CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.aapl_eod_raw (
    symbol VARCHAR,
    trade_date DATE,
    raw VARCHAR,              -- full JSON record as returned by marketstack, as text
    request_date_from DATE,
    request_date_to DATE,
    request_offset INTEGER,
    loaded_at TIMESTAMP DEFAULT now()
);

-- Silver layer: cleaned, typed, deduped. One row per (symbol, trade_date),
-- upserted from the latest matching Bronze row - see
-- pipeline/run_marketstack_silver.py.
CREATE SCHEMA IF NOT EXISTS silver;

CREATE TABLE IF NOT EXISTS silver.aapl_eod (
    symbol VARCHAR,
    trade_date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    adj_open DOUBLE,
    adj_high DOUBLE,
    adj_low DOUBLE,
    adj_close DOUBLE,
    adj_volume DOUBLE,
    split_factor DOUBLE,
    dividend DOUBLE,
    exchange VARCHAR,
    exchange_code VARCHAR,
    price_currency VARCHAR,
    silvered_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (symbol, trade_date)
);

-- Gold layer: business-level marts, fully recomputed from Silver on each
-- run - see pipeline/gold/aapl_daily_returns.sql.
CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE IF NOT EXISTS gold.aapl_daily_returns (
    symbol VARCHAR,
    trade_date DATE,
    close DOUBLE,
    prior_close DOUBLE,
    daily_return_pct DOUBLE,
    volume DOUBLE,
    PRIMARY KEY (symbol, trade_date)
);
