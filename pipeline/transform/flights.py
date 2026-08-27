"""Flatten AviationStack's nested flight records into rows matching
pipeline/schema.sql's `flights` table.
"""
from __future__ import annotations

import pandas as pd


def transform_flights(raw_flights: list[dict]) -> pd.DataFrame:
    rows = []
    for f in raw_flights:
        departure = f.get("departure") or {}
        arrival = f.get("arrival") or {}
        airline = f.get("airline") or {}
        flight = f.get("flight") or {}
        aircraft = f.get("aircraft") or {}

        flight_date = f.get("flight_date")
        flight_iata = flight.get("iata") or flight.get("icao") or "UNKNOWN"
        # AviationStack has no single stable flight id - build one from
        # flight number + date, which is unique enough for our purposes.
        flight_id = f"{flight_iata}_{flight_date}"

        rows.append(
            {
                "flight_id": flight_id,
                "flight_date": flight_date,
                "flight_status": f.get("flight_status"),
                "airline_name": airline.get("name"),
                "airline_iata": airline.get("iata"),
                "flight_number": flight.get("number"),
                "flight_iata": flight_iata,
                "dep_airport": departure.get("airport"),
                "dep_iata": departure.get("iata"),
                "dep_scheduled": departure.get("scheduled"),
                "dep_actual": departure.get("actual"),
                "arr_airport": arrival.get("airport"),
                "arr_iata": arrival.get("iata"),
                "arr_scheduled": arrival.get("scheduled"),
                "arr_actual": arrival.get("actual"),
                "aircraft_registration": aircraft.get("registration"),
            }
        )

    return pd.DataFrame(rows)
