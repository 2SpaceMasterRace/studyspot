"""Copy the normalized dataset into the Turso serving database.

``data/spots.json`` is the source of truth; the ``spots`` table is a rebuildable
projection of it:

.. code-block:: shell

    just load-data

Every record is validated against the shared contract before it reaches the
repository, so the serving table can only ever hold records the API can serve.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from ..config import Settings
from .database import Database
from .models import StudySpot
from .repository import TursoSpotRepository

#: ``src/backend/src/studyspot_api/spots/loader.py`` -> repository root.
REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_DATASET = REPOSITORY_ROOT / "data" / "spots.json"


def read_dataset(path: Path) -> list[StudySpot]:
    """Read and validate the normalized dataset."""
    records = json.loads(path.read_text("utf-8"))
    if not isinstance(records, list):
        raise ValueError(f"{path} must contain a JSON array of study spots.")
    return [StudySpot.model_validate(record) for record in records]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load data/spots.json into Turso.")
    parser.add_argument(
        "--dataset", type=Path, default=DEFAULT_DATASET, help="Normalized dataset to load."
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Override TURSO_DATABASE_URL. The auth token is only ever read from the "
        "environment, never from the command line.",
    )
    arguments = parser.parse_args(argv)

    settings = Settings.from_environment()
    database = Database(
        arguments.database_url or settings.turso_database_url, settings.turso_auth_token
    )
    written = TursoSpotRepository(database).replace_all(read_dataset(arguments.dataset))
    print(f"loaded {written} spots from {arguments.dataset} into {database.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
