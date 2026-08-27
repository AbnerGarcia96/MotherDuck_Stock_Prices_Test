"""Fetch end-of-day price data from marketstack (via apilayer).

Docs: https://marketstack.com/documentation

Notes:
- API_URL and API_ACCESS_KEY come from .env - API_URL already points at the
  full /v2/eod endpoint (e.g. https://api.apilayer.net/marketstack/v2/eod).
- The response is paginated via `limit`/`offset`, capped by the plan tier
  (100 per page on the free/basic apilayer tier regardless of what's
  requested) - fetch_eod_range() drives the loop off the response's own
  pagination.total rather than assuming a fixed page count.
"""
from __future__ import annotations

import os
import time
from collections.abc import Iterator

import requests


def fetch_eod_page(
    symbol: str,
    date_from: str,
    date_to: str,
    offset: int = 0,
    limit: int = 100,
) -> dict:
    """Return one raw page (`{"pagination": ..., "data": [...]}`) of EOD records."""
    api_url = os.environ.get("API_URL")
    api_key = os.environ.get("API_ACCESS_KEY")
    if not api_url:
        raise RuntimeError("API_URL is not set. Add it to .env at the repo root.")
    if not api_key:
        raise RuntimeError("API_ACCESS_KEY is not set. Add it to .env at the repo root.")

    params = {
        "access_key": api_key,
        "symbols": symbol,
        "date_from": date_from,
        "date_to": date_to,
        "limit": limit,
        "offset": offset,
    }
    response = requests.get(api_url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    if "error" in payload:
        raise RuntimeError(f"marketstack API error: {payload['error']}")

    return payload


def fetch_eod_range(
    symbol: str,
    date_from: str,
    date_to: str,
    limit: int = 100,
    delay_s: float = 1.0,
) -> Iterator[tuple[list[dict], int]]:
    """Yield `(records, offset)` for each page covering [date_from, date_to].

    Loops on `offset` until the response's `pagination.total` is exhausted,
    sleeping `delay_s` between requests to stay under the API's rate limit.
    """
    offset = 0
    while True:
        payload = fetch_eod_page(symbol, date_from, date_to, offset=offset, limit=limit)
        records = payload.get("data", [])
        yield records, offset

        pagination = payload.get("pagination", {})
        total = pagination.get("total", 0)
        offset += limit
        if offset >= total:
            break
        time.sleep(delay_s)
