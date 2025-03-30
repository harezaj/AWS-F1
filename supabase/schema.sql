CREATE TABLE IF NOT EXISTS sessions (
    session_key INTEGER PRIMARY KEY,
    session_name TEXT,
    date_start TIMESTAMPTZ,
    date_end TIMESTAMPTZ,
    session_type TEXT,
    meeting_key INTEGER,
    location TEXT,
    country_name TEXT,
    circuit_short_name TEXT,
    year INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS drivers (
    id BIGSERIAL PRIMARY KEY,
    session_key INTEGER REFERENCES sessions(session_key),
    driver_number INTEGER,
    name_acronym TEXT,
    full_name TEXT,
    team_name TEXT,
    team_colour TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(session_key, driver_number)
);

CREATE TABLE IF NOT EXISTS weather (
    id BIGSERIAL PRIMARY KEY,
    session_key INTEGER REFERENCES sessions(session_key),
    date TIMESTAMPTZ,
    air_temperature NUMERIC,
    humidity NUMERIC,
    track_temperature NUMERIC,
    wind_speed NUMERIC,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pit_stops (
    id BIGSERIAL PRIMARY KEY,
    session_key INTEGER REFERENCES sessions(session_key),
    driver_number INTEGER,
    pit_duration NUMERIC,
    lap_number INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS stints (
    id BIGSERIAL PRIMARY KEY,
    session_key INTEGER REFERENCES sessions(session_key),
    driver_number INTEGER,
    stint_number INTEGER,
    compound TEXT,
    lap_start INTEGER,
    lap_end INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_sessions_year ON sessions(year);
CREATE INDEX idx_drivers_session ON drivers(session_key);
CREATE INDEX idx_weather_session ON weather(session_key);
CREATE INDEX idx_pitstops_session ON pit_stops(session_key);
CREATE INDEX idx_stints_session ON stints(session_key); 