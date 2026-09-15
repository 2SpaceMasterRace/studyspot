"""The one study-spot repository.

Every consumer goes through this interface rather than writing its own SQL:

- the HTTP API lists and fetches spots;
- the search projection streams every spot with :meth:`SpotRepository.iter_all`; and
- the dataset loader replaces the table with :meth:`SpotRepository.replace_all`.

Keeping the schema and the SQL in one place is what stops three consumers from each
creating a differently shaped ``spots`` table.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any, Protocol

from .database import Database, DatabaseUnavailable
from .models import SpotFilters, StudySpot

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

COLUMNS = (
    "id",
    "name",
    "category",
    "address",
    "neighborhood",
    "borough",
    "latitude",
    "longitude",
    "university",
)

SELECT_COLUMNS = ", ".join(COLUMNS)

WRITE_COLUMNS = (
    *COLUMNS,
    "name_folded",
    "neighborhood_folded",
    "borough_folded",
    "university_folded",
)

INSERT = (
    f"INSERT INTO spots ({', '.join(WRITE_COLUMNS)}) VALUES ({', '.join('?' * len(WRITE_COLUMNS))})"
)

#: Deterministic and total, so a row can never be repeated or skipped across pages.
LIST_ORDER = "ORDER BY name, id"

#: The projection consumers walk the table in primary-key order.
SCAN_ORDER = "ORDER BY id"

LIKE_ESCAPE = "\\"


class SpotRepository(Protocol):
    """What every StudySpot consumer needs from the study-spot store."""

    def replace_all(self, spots: Sequence[StudySpot]) -> int:
        """Replace the table's contents. Returns the number of rows written."""
        ...

    def list_spots(
        self, filters: SpotFilters, *, limit: int, offset: int
    ) -> tuple[list[StudySpot], int]:
        """Return one page of matching spots and the total number of matches."""
        ...

    def get_spot(self, spot_id: str) -> StudySpot | None:
        """Return one spot, or ``None`` when no spot has that identifier."""
        ...

    def iter_all(self) -> Iterator[StudySpot]:
        """Yield every spot in primary-key order, for rebuilding a projection."""
        ...


def folded(value: str | None) -> str | None:
    """Case-fold a value for the case-insensitive filter columns."""
    return value.casefold() if value is not None else None


def escape_like(value: str) -> str:
    """Escape the wildcards SQL ``LIKE`` would otherwise interpret."""
    for character in (LIKE_ESCAPE, "%", "_"):
        value = value.replace(character, LIKE_ESCAPE + character)
    return value


def build_where(filters: SpotFilters) -> tuple[str, list[Any]]:
    """Render the filters as a WHERE clause and its bound parameters."""
    clauses: list[str] = []
    parameters: list[Any] = []

    if filters.name:
        clauses.append(f"name_folded LIKE ? ESCAPE '{LIKE_ESCAPE}'")
        parameters.append(f"%{escape_like(filters.name.casefold())}%")
    if filters.neighborhood:
        clauses.append("neighborhood_folded = ?")
        parameters.append(filters.neighborhood.casefold())
    if filters.borough:
        clauses.append("borough_folded = ?")
        parameters.append(filters.borough.casefold())
    if filters.university:
        clauses.append("university_folded = ?")
        parameters.append(filters.university.casefold())

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, parameters


def to_row(spot: StudySpot) -> tuple[Any, ...]:
    """Render a spot as the row the serving table stores."""
    return (
        spot.id,
        spot.name,
        spot.category,
        spot.address,
        spot.neighborhood,
        spot.borough.value,
        spot.latitude,
        spot.longitude,
        spot.university,
        spot.name.casefold(),
        folded(spot.neighborhood),
        spot.borough.value.casefold(),
        folded(spot.university),
    )


def to_spot(row: Any) -> StudySpot:
    """Rebuild a spot from a selected row."""
    return StudySpot.model_validate(dict(zip(COLUMNS, row, strict=True)))


class TursoSpotRepository:
    """Reads and writes study spots in Turso, local file or Turso Cloud alike."""

    def __init__(self, database: Database) -> None:
        self._database = database

    # -- write path ------------------------------------------------------------

    def replace_all(self, spots: Sequence[StudySpot]) -> int:
        """Create the schema if needed, then replace every row in one transaction.

        The table is a rebuildable projection of ``data/spots.json``, so a record
        dropped upstream must disappear here too. That is why this replaces rather
        than upserts.
        """
        with self._connect() as connection:
            cursor = connection.cursor()
            self._apply_schema(cursor)
            cursor.execute("DELETE FROM spots")
            if spots:
                cursor.executemany(INSERT, [to_row(spot) for spot in spots])
            connection.commit()
            return int(cursor.execute("SELECT count(*) FROM spots").fetchone()[0])

    # -- read paths ------------------------------------------------------------

    def list_spots(
        self, filters: SpotFilters, *, limit: int, offset: int
    ) -> tuple[list[StudySpot], int]:
        where, parameters = build_where(filters)
        with self._connect() as connection:
            cursor = connection.cursor()
            total = cursor.execute(
                f"SELECT count(*) FROM spots {where}".strip(), tuple(parameters)
            ).fetchone()[0]
            rows = cursor.execute(
                f"SELECT {SELECT_COLUMNS} FROM spots {where} {LIST_ORDER} LIMIT ? OFFSET ?".strip(),
                (*parameters, limit, offset),
            ).fetchall()
        return [to_spot(row) for row in rows], int(total)

    def get_spot(self, spot_id: str) -> StudySpot | None:
        with self._connect() as connection:
            row = (
                connection.cursor()
                .execute(f"SELECT {SELECT_COLUMNS} FROM spots WHERE id = ?", (spot_id,))
                .fetchone()
            )
        return to_spot(row) if row else None

    def iter_all(self) -> Iterator[StudySpot]:
        """Yield every spot, for rebuilding a search projection."""
        with self._connect() as connection:
            rows = (
                connection.cursor()
                .execute(f"SELECT {SELECT_COLUMNS} FROM spots {SCAN_ORDER}")
                .fetchall()
            )
        yield from (to_spot(row) for row in rows)

    # -- plumbing --------------------------------------------------------------

    @staticmethod
    def _apply_schema(cursor: Any) -> None:
        for statement in SCHEMA_PATH.read_text("utf-8").split(";"):
            if statement.strip():
                cursor.execute(statement)

    @contextmanager
    def _connect(self) -> Iterator[Any]:
        """Open a connection per operation and always close it.

        The connection is a local, never an attribute: neither driver hands out
        connections that are safe to share between the threads FastAPI runs
        synchronous endpoints on, and one repository instance serves every request.
        """
        try:
            connection = self._database.connect()
        except self._database.errors as error:
            raise DatabaseUnavailable(str(error)) from error

        try:
            yield connection
        except self._database.errors as error:
            raise DatabaseUnavailable(str(error)) from error
        finally:
            # Closing must never mask the error the caller is already handling.
            with suppress(Exception):
                connection.close()
