-- Turso serving schema for study spots.
--
-- One table serves the HTTP API, the search projection, and the loader. Only
-- `SpotRepository` writes it, so no consumer needs to know about the `_folded`
-- columns below.
--
-- Those columns hold Python `str.casefold()` output. SQLite's own `lower()` and
-- `LIKE` fold only the ASCII range, so comparing against them is what makes
-- filters case-insensitive for every character NYC Open Data contains.

CREATE TABLE IF NOT EXISTS spots (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    category            TEXT NOT NULL,
    address             TEXT,
    neighborhood        TEXT,
    borough             TEXT NOT NULL,
    latitude            REAL NOT NULL,
    longitude           REAL NOT NULL,
    university          TEXT,
    name_folded         TEXT NOT NULL,
    neighborhood_folded TEXT,
    borough_folded      TEXT NOT NULL,
    university_folded   TEXT,

    CHECK (borough IN ('Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island')),
    CHECK (latitude BETWEEN -90 AND 90),
    CHECK (longitude BETWEEN -180 AND 180)
);

-- Matches the deterministic list ordering, so paging never repeats or drops a row.
CREATE INDEX IF NOT EXISTS spots_order_idx ON spots (name, id);

CREATE INDEX IF NOT EXISTS spots_neighborhood_idx ON spots (neighborhood_folded);
CREATE INDEX IF NOT EXISTS spots_borough_idx ON spots (borough_folded);
CREATE INDEX IF NOT EXISTS spots_university_idx ON spots (university_folded);
