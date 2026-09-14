from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock

import pytest

from studyspot_api.spots.model import StudySpotSummary
from studyspot_api.spots.repository import SCHEMA, StudySpotRepository, _row_to_summary


def test_schema_and_rows_use_numeric_coordinates(tmp_path: Path) -> None:
    database = tmp_path / "spots.db"
    with StudySpotRepository(f"file:{database}") as repository:
        connection = cast(Any, repository._connection)
        connection.execute(SCHEMA)
        connection.execute(
            "INSERT INTO spots VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("nyc-1", "Starbucks", "cafe", "1 Main St", "Astoria", "Queens", 40.7, -73.9),
        )
        connection.commit()
        result = repository.all()

    assert result == [
        StudySpotSummary(
            id="nyc-1",
            name="Starbucks",
            category="cafe",
            address="1 Main St",
            neighborhood="Astoria",
            borough="Queens",
            latitude=40.7,
            longitude=-73.9,
        )
    ]


def test_row_conversion_accepts_sqlite_mapping() -> None:
    row = {
        "id": "1",
        "name": "Cafe",
        "category": "cafe",
        "address": "A",
        "neighborhood": "N",
        "borough": "B",
        "latitude": 1,
        "longitude": 2,
    }
    assert _row_to_summary(row).latitude == 1


def test_repository_closes_connection(tmp_path: Path) -> None:
    repository = StudySpotRepository(f"file:{tmp_path / 'spots.db'}")
    repository.close()
    repository.close()
    assert repository._connection is None


def test_hosted_adapter_and_cleanup(monkeypatch):
    import libsql

    connection = Mock()
    connect = Mock(return_value=connection)
    monkeypatch.setattr(libsql, "connect", connect)
    with StudySpotRepository("libsql://example.turso.io", "token"):
        pass
    connect.assert_called_once_with(database="libsql://example.turso.io", auth_token="token")
    connection.close.assert_called_once()


def test_schema_failure_closes_connection(monkeypatch):
    connection = Mock()
    connection.execute.side_effect = RuntimeError("schema failure")
    monkeypatch.setattr("studyspot_api.spots.repository.connect_database", lambda *args: connection)
    with pytest.raises(RuntimeError, match="schema failure"):
        StudySpotRepository("file:unused")
    connection.close.assert_called_once()
