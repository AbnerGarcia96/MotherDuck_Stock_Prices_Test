"""Normalize raw dive records into rows matching pipeline/schema.sql's
`dives` table.

The field-name fallbacks below (e.g. `id`/`dive_id`) are guesses at
common shapes - adjust once you know your real API's response format.
"""
from __future__ import annotations

import pandas as pd


def transform_dives(raw_dives: list[dict]) -> pd.DataFrame:
    rows = []
    for d in raw_dives:
        dive_id = d.get("id") or d.get("dive_id")
        if dive_id is None:
            continue  # can't upsert without a stable key
        rows.append(
            {
                "dive_id": str(dive_id),
                "dive_date": d.get("date") or d.get("dive_date"),
                "dive_site": d.get("site") or d.get("dive_site"),
                "location": d.get("location"),
                "max_depth_m": d.get("max_depth") or d.get("max_depth_m"),
                "duration_min": d.get("duration") or d.get("duration_min"),
                "water_temp_c": d.get("water_temp") or d.get("water_temp_c"),
                "visibility_m": d.get("visibility") or d.get("visibility_m"),
                "buddy": d.get("buddy"),
                "notes": d.get("notes"),
            }
        )

    return pd.DataFrame(rows)
