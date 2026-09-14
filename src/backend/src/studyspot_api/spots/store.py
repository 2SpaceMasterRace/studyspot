"""Study-spot data store: the libSQL connection and the snapshot loader.

This single module owns StudySpot's access to the serving database:

- ``connect`` opens one libSQL interface for both a local embedded ``file:``
  database (local development and Docker Compose) and a Turso Cloud database
  (Vercel Preview and Production), driven by ``TURSO_DATABASE_URL`` and
  ``TURSO_AUTH_TOKEN`` (see ``docs/source/database.md``). Never expose either
  value to browser code; the API owns all database access.
- The loader projects ``data/spots.json`` -- the reproducible source of truth
  produced by ``data/ingest.py`` -- into the ``spots`` table the API queries.
  The table is a rebuildable projection, so loading is idempotent: it
  (re)creates the schema and upserts every record by ``id``.

Run the loader against the configured database from the repository root::

    just load-spots

or equivalently::

    PYTHONPATH=src/backend/src uv run --project src/backend \\
        python -m studyspot_api.spots.store

Point it at a specific snapshot or database with flags::

    ... python -m studyspot_api.spots.store --spots data/spots.json
    ... python -m studyspot_api.spots.store --database-url file:.local/studyspot.db
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import libsql

# --- Connection -------------------------------------------------------------

TURSO_DATABASE_URL_ENV = "TURSO_DATABASE_URL"
TURSO_AUTH_TOKEN_ENV = "TURSO_AUTH_TOKEN"


def _resolve_local_path(database_url: str) -> str | None:
    """Return a filesystem path for a local ``file:`` URL, else ``None``.

    A local libSQL database is addressed as ``file:<path>``. Everything else
    (``libsql://``, ``https://``, ``wss://``) is a remote Turso Cloud endpoint.
    """
    if database_url.startswith("file:"):
        return database_url[len("file:") :]
    return None


def connect(
    database_url: str | None = None,
    auth_token: str | None = None,
) -> libsql.Connection:  # ty: ignore[unresolved-attribute]  # libsql ships no type stubs
    """Connect to the configured libSQL database.

    ``database_url`` and ``auth_token`` default to the ``TURSO_DATABASE_URL`` and
    ``TURSO_AUTH_TOKEN`` environment variables. A ``file:`` URL opens a local
    embedded database and ignores the token; any other URL connects to Turso
    Cloud and requires the token.
    """
    database_url = (
        database_url if database_url is not None else os.environ.get(TURSO_DATABASE_URL_ENV)
    )
    if not database_url:
        raise RuntimeError(
            f"{TURSO_DATABASE_URL_ENV} is not set; expected a file: path or a Turso Cloud URL"
        )

    auth_token = auth_token if auth_token is not None else os.environ.get(TURSO_AUTH_TOKEN_ENV, "")

    local_path = _resolve_local_path(database_url)
    if local_path is not None:
        return libsql.connect(local_path)  # ty: ignore[unresolved-attribute]

    if not auth_token:
        raise RuntimeError(
            f"{TURSO_AUTH_TOKEN_ENV} is required for the remote database {database_url!r}"
        )
    return libsql.connect(database_url, auth_token=auth_token)  # ty: ignore[unresolved-attribute]


# --- Loader -----------------------------------------------------------------

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

# Repo-root default: this file is src/backend/src/studyspot_api/spots/store.py.
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
    conn = connect(database_url=database_url, auth_token=auth_token)
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
        help=f"libSQL URL (default: ${TURSO_DATABASE_URL_ENV}).",
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
