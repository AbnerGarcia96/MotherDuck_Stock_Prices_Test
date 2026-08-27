"""Fetch dive log data from a generic REST API.

This is a placeholder client: dive-log sources vary a lot (a dive
computer's cloud service, Subsurface, a personal logging API, ...), so
this just makes an authenticated GET against DIVE_API_BASE_URL and
tries a couple of common response envelope shapes.

Point DIVE_API_BASE_URL/DIVE_API_KEY at your real source in .env, then
adjust the response-unwrapping below (and the field mapping in
transform/dives.py) to match its actual shape.
"""
from __future__ import annotations

import os

import requests


def fetch_dives(params: dict | None = None) -> list[dict]:
    """Return raw dive records (list of dicts) from the configured API."""
    base_url = os.environ.get("DIVE_API_BASE_URL")
    if not base_url:
        raise RuntimeError(
            "DIVE_API_BASE_URL is not set. Point it at your dive-log API "
            "in .env - see pipeline/extract/dives.py for how the response "
            "is parsed."
        )

    headers = {}
    api_key = os.environ.get("DIVE_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    response = requests.get(base_url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        # TODO: adjust to your API's actual envelope key.
        return payload.get("data") or payload.get("dives") or []
    raise RuntimeError(f"Unexpected dive API response shape: {type(payload)!r}")
