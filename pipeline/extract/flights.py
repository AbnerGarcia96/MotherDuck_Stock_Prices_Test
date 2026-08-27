"""Fetch flight data from AviationStack's free-tier API.

Docs: https://aviationstack.com/documentation

Notes on the free plan:
- HTTP only (no HTTPS) - the base URL below is intentionally http://.
- Limited to 100 requests/month, and only real-time + recent flights
  (no deep historical lookups).
- Pass query params (e.g. dep_iata, arr_iata, flight_date, airline_iata,
  flight_iata) to narrow results and conserve your quota - an
  unfiltered call returns a broad, effectively-random slice of global
  flights.
"""
from __future__ import annotations

import os

import requests

BASE_URL = "http://api.aviationstack.com/v1/flights"


def fetch_flights(params: dict | None = None) -> list[dict]:
    """Return raw flight records (list of dicts) from AviationStack."""
    api_key = os.environ.get("AVIATIONSTACK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "AVIATIONSTACK_API_KEY is not set. Get a free key at "
            "https://aviationstack.com/signup/free and add it to .env."
        )

    query = {"access_key": api_key}
    if params:
        query.update(params)

    response = requests.get(BASE_URL, params=query, timeout=30)
    response.raise_for_status()
    payload = response.json()

    if "error" in payload:
        error = payload["error"]
        raise RuntimeError(f"AviationStack API error: {error}")

    return payload.get("data", [])
