"""Exercise the installed reindex command and API against real Meilisearch."""

import os
import subprocess
import sys

import httpx
import pytest
from fastapi.testclient import TestClient

from studyspot_api.main import create_app
from studyspot_api.spots.repository import StudySpotRepository, connect_database

pytestmark = pytest.mark.integration


def test_reindex_and_search(tmp_path, monkeypatch):
    url = os.environ["MEILISEARCH_URL"]
    token = os.environ.get("MEILISEARCH_API_KEY", "")
    database = f"file:{tmp_path / 'source.db'}"
    monkeypatch.setenv("TURSO_DATABASE_URL", database)
    monkeypatch.setenv("MEILISEARCH_INDEX", "integration-spots")
    with StudySpotRepository(database):
        pass

    def execute(sql, parameters=()):
        connection = connect_database(database)
        try:
            connection.execute(sql, parameters)
            connection.commit()
        finally:
            connection.close()

    for row in [
        (
            "starbucks-1",
            "Starbucks Reserve",
            "cafe",
            "123 Broadway",
            "Union Square",
            "Manhattan",
            40.7,
            -73.99,
        ),
        (
            "coffee-1",
            "Coffee Project",
            "library",
            "456 Bedford Avenue",
            "Williamsburg",
            "Brooklyn",
            40.7,
            -73.96,
        ),
    ]:
        execute("INSERT INTO spots VALUES (?, ?, ?, ?, ?, ?, ?, ?)", row)

    def reindex(count):
        result = subprocess.run(
            [sys.executable, "-m", "studyspot_api.reindex"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=90,
        )
        assert result.returncode == 0, result.stderr
        assert f"Indexed {count} study spots" in result.stdout

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    with httpx.Client(base_url=url, headers=headers, timeout=5) as search:

        def documents():
            response = search.get("/indexes/integration-spots/documents")
            response.raise_for_status()
            return sorted(response.json()["results"], key=lambda item: item["id"])

        reindex(2)
        first = documents()
        assert len(first) == 2
        reindex(2)
        assert documents() == first
        with TestClient(create_app()) as api:
            for query, expected in [
                ("starbu", "starbucks-1"),
                ("cofee", "coffee-1"),
                ("library", "coffee-1"),
                ("Williamsburg", "coffee-1"),
                ("Broadway", "starbucks-1"),
            ]:
                response = api.get("/spots/search", params={"q": query})
                assert response.status_code == 200
                assert response.json()[0]["id"] == expected
                assert set(response.json()[0]) == {
                    "id",
                    "name",
                    "category",
                    "address",
                    "neighborhood",
                    "borough",
                    "latitude",
                    "longitude",
                }
            assert api.get("/spots/search?q=zzzzzzzzzz").json() == []

        execute("DELETE FROM spots WHERE id = 'coffee-1'")
        execute("UPDATE spots SET name = 'Updated Cafe'")
        reindex(1)
        assert [(d["id"], d["name"]) for d in documents()] == [("starbucks-1", "Updated Cafe")]
        execute("DELETE FROM spots")
        reindex(0)
        assert documents() == []

        # More than one page of relevant text hits must be filtered in
        # Meilisearch before the API's 20-result limit is applied.
        for number in range(25):
            execute(
                "INSERT INTO spots VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (f"far-{number:02}", "Coffee", "cafe", "A", "N", "Manhattan", 40.70, -74.05),
            )
        for identifier in ("open-near", "closed-near"):
            execute(
                "INSERT INTO spots VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (identifier, "Coffee Study", "cafe", "A", "N", "Manhattan", 40.73, -73.99),
            )
        execute(
            "INSERT INTO spot_hours VALUES (?, ?, ?)", ("open-near", "24/7", "America/New_York")
        )
        execute(
            "INSERT INTO spot_hours VALUES (?, ?, ?)",
            ("closed-near", "24/7 off", "America/New_York"),
        )
        reindex(27)
        with TestClient(create_app()) as api:
            unfiltered = api.get("/spots/search", params={"q": "coffee"}).json()
            assert len(unfiltered) == 20
            assert "open-near" not in {spot["id"] for spot in unfiltered}
            response = api.post(
                "/spots/search",
                json={
                    "q": "coffee",
                    "latitude": 40.73,
                    "longitude": -73.99,
                    "radius_miles": 0.2,
                    "open_now": True,
                },
            )
            assert response.status_code == 200, response.text
            assert [spot["id"] for spot in response.json()] == ["open-near"]
            assert response.json()[0]["distance_miles"] == 0
