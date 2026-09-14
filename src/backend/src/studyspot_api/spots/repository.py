"""Turso-backed study-spot repository."""

from collections.abc import Iterator
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

from .model import StudySpotSummary

SCHEMA = """
CREATE TABLE IF NOT EXISTS spots (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    address TEXT NOT NULL,
    neighborhood TEXT NOT NULL,
    borough TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
)
"""


def connect_database(url: str, auth_token: str = "") -> Any:
    """Open either an embedded Turso file or a hosted libSQL connection."""
    if url.startswith("file:"):
        import turso

        path = url.removeprefix("file:")
        return turso.connect(str(Path(path)))

    import libsql

    return getattr(libsql, "connect")(database=url, auth_token=auth_token)  # noqa: B009


def _row_to_summary(row: Any) -> StudySpotSummary:
    """Convert a sqlite-style row, tuple, or mapping to the shared model."""
    if hasattr(row, "keys"):
        values = {key: row[key] for key in row}
    else:
        values = dict(zip(StudySpotSummary.model_fields, row, strict=True))
    return StudySpotSummary(**values)


class StudySpotRepository(AbstractContextManager["StudySpotRepository"]):
    """Small repository with deterministic connection cleanup."""

    def __init__(self, url: str, auth_token: str = "") -> None:
        self._connection = connect_database(url, auth_token)
        try:
            self._connection.execute(SCHEMA)
            self._connection.commit()
        except Exception:
            self.close()
            raise

    def __enter__(self) -> "StudySpotRepository":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        """Commit and close the underlying connection exactly once."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def all(self) -> list[StudySpotSummary]:
        """Return every source row in stable primary-key order."""
        if self._connection is None:
            raise RuntimeError("repository is closed")
        rows: Iterator[Any] = self._connection.execute(
            """SELECT id, name, category, address, neighborhood, borough,
                      latitude, longitude
               FROM spots ORDER BY id"""
        )
        return [_row_to_summary(row) for row in rows]
