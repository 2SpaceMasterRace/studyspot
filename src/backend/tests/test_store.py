"""Tests for the study-spot data store (connection + snapshot loader).

These run against a temporary local libSQL file, exercising the same schema and
loading contract that the remote adapter must satisfy.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from studyspot_api.spots import store

SAMPLE_SPOTS = [
    {
        "id": "facdb-1",
        "name": "Allerton Library",
        "category": "library",
        "address": "2740 Barnes Avenue",
        "neighborhood": None,
        "borough": "Bronx",
        "latitude": 40.8668,
        "longitude": -73.8632,
    },
    {
        "id": "nyu-bobst-library",
        "name": "Elmer Holmes Bobst Library",
        "category": "university_library",
        "address": "70 Washington Square South, New York, NY 10012",
        "neighborhood": "Greenwich Village",
        "borough": "Manhattan",
        "latitude": 40.7295,
        "longitude": -73.9974,
    },
]


@pytest.fixture
def local_db_url(tmp_path: Path) -> str:
    return f"file:{tmp_path / 'studyspot.db'}"


def test_connect_opens_local_file(local_db_url: str) -> None:
    conn = store.connect(database_url=local_db_url)
    assert conn.execute("SELECT 1").fetchone() == (1,)


def test_connect_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(store.TURSO_DATABASE_URL_ENV, raising=False)
    with pytest.raises(RuntimeError, match="TURSO_DATABASE_URL"):
        store.connect()


def test_connect_remote_requires_auth_token() -> None:
    with pytest.raises(RuntimeError, match="TURSO_AUTH_TOKEN"):
        store.connect(database_url="libsql://example.turso.io", auth_token="")


def test_load_spots_inserts_all_rows(local_db_url: str) -> None:
    conn = store.connect(database_url=local_db_url)
    written = store.load_spots(conn, SAMPLE_SPOTS)
    assert written == len(SAMPLE_SPOTS)
    count = conn.execute("SELECT count(*) FROM spots").fetchone()[0]
    assert count == len(SAMPLE_SPOTS)


def test_load_spots_is_idempotent(local_db_url: str) -> None:
    conn = store.connect(database_url=local_db_url)
    store.load_spots(conn, SAMPLE_SPOTS)
    store.load_spots(conn, SAMPLE_SPOTS)  # second load must not duplicate
    count = conn.execute("SELECT count(*) FROM spots").fetchone()[0]
    assert count == len(SAMPLE_SPOTS)


def test_load_spots_upserts_changed_fields(local_db_url: str) -> None:
    conn = store.connect(database_url=local_db_url)
    store.load_spots(conn, SAMPLE_SPOTS)
    changed = [dict(SAMPLE_SPOTS[0], name="Allerton Branch")]
    store.load_spots(conn, changed)
    name = conn.execute("SELECT name FROM spots WHERE id = ?", ("facdb-1",)).fetchone()[0]
    assert name == "Allerton Branch"


def test_load_spots_rejects_missing_required_field(local_db_url: str) -> None:
    conn = store.connect(database_url=local_db_url)
    with pytest.raises(ValueError, match="latitude"):
        store.load_spots(conn, [dict(SAMPLE_SPOTS[0], latitude=None)])


def test_load_from_file_reads_and_loads(tmp_path: Path, local_db_url: str) -> None:
    snapshot = tmp_path / "spots.json"
    snapshot.write_text(json.dumps(SAMPLE_SPOTS), encoding="utf-8")
    written = store.load_from_file(spots_path=snapshot, database_url=local_db_url)
    assert written == len(SAMPLE_SPOTS)


def test_read_spots_rejects_non_array(tmp_path: Path) -> None:
    bad = tmp_path / "spots.json"
    bad.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
    with pytest.raises(ValueError, match="JSON array"):
        store.read_spots(bad)
