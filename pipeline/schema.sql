-- Schema for the dives_and_flights MotherDuck database.
-- Applied via pipeline.db.ensure_schema() before every load.

CREATE TABLE IF NOT EXISTS flights (
    flight_id VARCHAR PRIMARY KEY,   -- synthetic key, see transform/flights.py
    flight_date DATE,
    flight_status VARCHAR,
    airline_name VARCHAR,
    airline_iata VARCHAR,
    flight_number VARCHAR,
    flight_iata VARCHAR,
    dep_airport VARCHAR,
    dep_iata VARCHAR,
    dep_scheduled TIMESTAMP,
    dep_actual TIMESTAMP,
    arr_airport VARCHAR,
    arr_iata VARCHAR,
    arr_scheduled TIMESTAMP,
    arr_actual TIMESTAMP,
    aircraft_registration VARCHAR,
    ingested_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dives (
    dive_id VARCHAR PRIMARY KEY,     -- from the source API, see transform/dives.py
    dive_date DATE,
    dive_site VARCHAR,
    location VARCHAR,
    max_depth_m DOUBLE,
    duration_min DOUBLE,
    water_temp_c DOUBLE,
    visibility_m DOUBLE,
    buddy VARCHAR,
    notes VARCHAR,
    ingested_at TIMESTAMP DEFAULT now()
);
