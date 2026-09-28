"""Turso-backed study-spot repository."""

from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .hours import SpotOpeningHours
from .model import StudySpotRecord, StudySpotSummary

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

HOURS_SCHEMA = """
CREATE TABLE IF NOT EXISTS spot_hours (
    spot_id TEXT PRIMARY KEY REFERENCES spots(id),
    expression TEXT NOT NULL,
    timezone TEXT NOT NULL
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
            self._connection.execute(HOURS_SCHEMA)
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
        rows = self._connection.execute(
            """SELECT id, name, category, address, neighborhood, borough,
                      latitude, longitude
               FROM spots ORDER BY id"""
        ).fetchall()
        return [_row_to_summary(row) for row in rows]

    def hours(self) -> dict[str, tuple[SpotOpeningHours, float, float]]:
        """Return known opening hours with the coordinates needed for evaluation."""
        if self._connection is None:
            raise RuntimeError("repository is closed")
        rows = self._connection.execute(
            """SELECT s.id, h.expression, h.timezone, s.latitude, s.longitude
               FROM spot_hours h JOIN spots s ON s.id = h.spot_id"""
        ).fetchall()
        known_hours = {}
        for row in rows:
            try:
                hours = SpotOpeningHours(expression=row[1], timezone=row[2])
            except ValidationError:
                continue
            known_hours[row[0]] = (hours, float(row[3]), float(row[4]))
        return known_hours

    def replace(self, records: list[StudySpotRecord]) -> int:
        """Replace the source snapshot and its hours in one transaction."""
        if self._connection is None:
            raise RuntimeError("repository is closed")
        connection = self._connection
        try:
            connection.execute("DELETE FROM spot_hours")
            connection.execute("DELETE FROM spots")
            for record in records:
                connection.execute(
                    """INSERT INTO spots
                       (id, name, category, address, neighborhood, borough, latitude, longitude)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record.id,
                        record.name,
                        record.category,
                        record.address,
                        record.neighborhood,
                        record.borough,
                        record.latitude,
                        record.longitude,
                    ),
                )
                if record.opening_hours is not None:
                    connection.execute(
                        "INSERT INTO spot_hours (spot_id, expression, timezone) VALUES (?, ?, ?)",
                        (
                            record.id,
                            record.opening_hours.expression,
                            record.opening_hours.timezone,
                        ),
                    )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        return len(records)
