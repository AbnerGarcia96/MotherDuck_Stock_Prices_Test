"""Flatten marketstack EOD records into rows matching pipeline/schema.sql's
`bronze.aapl_eod_raw` and `silver.aapl_eod` tables.
"""
from __future__ import annotations

import json

import pandas as pd


def transform_eod_page(
    raw_records: list[dict], offset: int, date_from: str, date_to: str
) -> pd.DataFrame:
    rows = [
        {
            "symbol": record.get("symbol"),
            "trade_date": record.get("date", "")[:10] or None,
            "raw": json.dumps(record),
            "request_date_from": date_from,
            "request_date_to": date_to,
            "request_offset": offset,
        }
        for record in raw_records
    ]
    return pd.DataFrame(rows)


def transform_bronze_to_silver(bronze_rows: pd.DataFrame) -> pd.DataFrame:
    """Parse each Bronze row's `raw` JSON text into silver.aapl_eod's typed
    columns - one already-deduped row per (symbol, trade_date) in, one
    typed row out.
    """
    rows = []
    for _, bronze_row in bronze_rows.iterrows():
        record = json.loads(bronze_row["raw"])
        rows.append(
            {
                "symbol": bronze_row["symbol"],
                "trade_date": bronze_row["trade_date"],
                "open": record.get("open"),
                "high": record.get("high"),
                "low": record.get("low"),
                "close": record.get("close"),
                "volume": record.get("volume"),
                "adj_open": record.get("adj_open"),
                "adj_high": record.get("adj_high"),
                "adj_low": record.get("adj_low"),
                "adj_close": record.get("adj_close"),
                "adj_volume": record.get("adj_volume"),
                "split_factor": record.get("split_factor"),
                "dividend": record.get("dividend"),
                "exchange": record.get("exchange"),
                "exchange_code": record.get("exchange_code"),
                "price_currency": record.get("price_currency"),
            }
        )
    return pd.DataFrame(rows)
