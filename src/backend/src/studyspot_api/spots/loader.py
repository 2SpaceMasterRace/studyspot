"""Load the normalized study-spot snapshot into the Turso serving table.

``data/spots.json`` is the reproducible source of truth produced by
``data/ingest.py``. This loader projects it into the ``spots`` table that the
API queries. The table is a rebuildable projection, so loading is idempotent:
it (re)creates the schema and upserts every record by ``id``.

Run it against the configured database (see ``studyspot_api.db``). From the
repository root::

    just load-spots

or equivalently::

    PYTHONPATH=src/backend/src uv run --project src/backend \
        python -m studyspot_api.spots.loader

Point it at a specific snapshot or database with flags::

    ... python -m studyspot_api.spots.loader --spots data/spots.json
    ... python -m studyspot_api.spots.loader --database-url file:.local/studyspot.db
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import libsql

from studyspot_api import db

# Columns mirror the shared study-spot schema. Coordinates are required so every
# row can be placed on the map; address and neighborhood may be absent when the
# source does not supply them.
CREATE_SPOTS_TABLE = """
CREATE TABLE IF NOT EXISTS spots (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    address TEXT,
    neighborhood TEXT,
    borough TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
)
"""

UPSERT_SPOT = """
INSERT INTO spots (id, name, category, address, neighborhood, borough, latitude, longitude)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    name = excluded.name,
    category = excluded.category,
    address = excluded.address,
    neighborhood = excluded.neighborhood,
    borough = excluded.borough,
    latitude = excluded.latitude,
    longitude = excluded.longitude
"""

_COLUMNS = ("id", "name", "category", "address", "neighborhood", "borough", "latitude", "longitude")

# Repo-root default: this file is src/backend/src/studyspot_api/spots/loader.py.
_DEFAULT_SPOTS_PATH = Path(__file__).resolve().parents[5] / "data" / "spots.json"

SPOTS_PATH_ENV = "STUDYSPOT_SPOTS_PATH"


def read_spots(path: Path) -> list[dict[str, Any]]:
    """Read and lightly validate the study-spot snapshot from ``path``."""
    spots = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(spots, list):
        raise ValueError(f"{path} must contain a JSON array of spots")
    return spots


def _row(spot: dict[str, Any]) -> tuple[Any, ...]:
    """Return a spot as a positional row, validating required fields."""
    for required in ("id", "name", "category", "latitude", "longitude"):
        if spot.get(required) in (None, ""):
            raise ValueError(f"spot {spot.get('id')!r} is missing required field {required!r}")
    return tuple(spot.get(column) for column in _COLUMNS)


def load_spots(conn: libsql.Connection, spots: Iterable[dict[str, Any]]) -> int:  # ty: ignore[unresolved-attribute]
    """Create the ``spots`` table if needed and upsert every record.

    Returns the number of rows written.
    """
    rows: Sequence[tuple[Any, ...]] = [_row(spot) for spot in spots]
    cursor = conn.cursor()
    cursor.execute(CREATE_SPOTS_TABLE)
    if rows:
        cursor.executemany(UPSERT_SPOT, rows)
    conn.commit()
    return len(rows)


def default_spots_path() -> Path:
    """Return the snapshot path from the environment or the repo default."""
    override = os.environ.get(SPOTS_PATH_ENV)
    return Path(override) if override else _DEFAULT_SPOTS_PATH


def load_from_file(
    spots_path: Path | None = None,
    database_url: str | None = None,
    auth_token: str | None = None,
) -> int:
    """Load a snapshot file into the configured database. Returns rows written."""
    path = spots_path or default_spots_path()
    spots = read_spots(path)
    conn = db.connect(database_url=database_url, auth_token=auth_token)
    return load_spots(conn, spots)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load spots.json into the Turso spots table.")
    parser.add_argument(
        "--spots",
        type=Path,
        default=None,
        help=f"Path to spots.json (default: ${SPOTS_PATH_ENV} or {_DEFAULT_SPOTS_PATH}).",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help=f"libSQL URL (default: ${db.TURSO_DATABASE_URL_ENV}).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point: load the snapshot and report the row count."""
    args = _parse_args(argv)
    path = args.spots or default_spots_path()
    written = load_from_file(spots_path=path, database_url=args.database_url)
    print(f"Loaded {written} spots from {path} into the spots table.")


if __name__ == "__main__":
    main()
