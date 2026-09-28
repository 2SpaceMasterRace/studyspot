"""Load a normalized spot snapshot into Turso before rebuilding search."""

import argparse
import os
from pathlib import Path

from pydantic import TypeAdapter

from .spots.model import StudySpotRecord
from .spots.repository import StudySpotRepository


def load_snapshot(path: Path, allow_empty: bool = False) -> int:
    records = TypeAdapter(list[StudySpotRecord]).validate_json(path.read_text(encoding="utf-8"))
    if not records and not allow_empty:
        raise ValueError("Refusing to replace spots with an empty snapshot")
    identifiers = [record.id for record in records]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Snapshot contains duplicate spot IDs")
    with StudySpotRepository(
        os.environ["TURSO_DATABASE_URL"], os.getenv("TURSO_AUTH_TOKEN", "")
    ) as repository:
        return repository.replace(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--allow-empty", action="store_true")
    arguments = parser.parse_args()
    print(f"Loaded {load_snapshot(arguments.path, arguments.allow_empty)} study spots")
