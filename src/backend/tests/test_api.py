from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi.testclient import TestClient

from studyspot_api.main import create_app
from studyspot_api.search.client import MeilisearchError
from studyspot_api.search.routes import get_hours_statuses, get_search_client
from studyspot_api.spots.hours import SpotOpeningHours
from studyspot_api.spots.model import StudySpotRecord, StudySpotSummary
from studyspot_api.spots.repository import StudySpotRepository


class FakeSearchClient:
    def __init__(self, results=None, error=False):
        self.results = results or []
        self.error = error
        self.query = None
        self.limit = None
        self.filters = None

    async def search(self, query, limit, filters=None):
        self.query, self.limit = query, limit
        self.filters = filters
        if self.error:
            raise MeilisearchError("down")
        return self.results


def client_for(fake, statuses=None):
    app = create_app()
    app.dependency_overrides[get_search_client] = lambda: fake
    app.dependency_overrides[get_hours_statuses] = lambda: statuses or {}
    return TestClient(app)


def test_search_trims_query_and_preserves_order_and_public_shape():
    fake = FakeSearchClient(
        [
            StudySpotSummary(
                id="2",
                name="Coffee",
                category="cafe",
                address="B",
                neighborhood="N",
                borough="B",
                latitude=1,
                longitude=2,
            ),
            StudySpotSummary(
                id="1",
                name="Starbucks",
                category="cafe",
                address="A",
                neighborhood="N",
                borough="B",
                latitude=3,
                longitude=4,
            ),
        ]
    )
    response = client_for(fake).get("/spots/search?q=%20cofee%20")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == ["2", "1"]
    assert fake.query == "cofee" and fake.limit == 20


@pytest.mark.parametrize("query", ["", "   "])
def test_blank_search_is_rejected(query):
    assert (
        client_for(FakeSearchClient()).get("/spots/search", params={"q": query}).status_code == 422
    )


def test_search_failure_is_503():
    assert client_for(FakeSearchClient(error=True)).get("/spots/search?q=coffee").status_code == 503


def test_filtered_search_combines_text_radius_and_open_now():
    spot = StudySpotSummary(
        id="near",
        name="Coffee",
        category="cafe",
        address="A",
        neighborhood="N",
        borough="Manhattan",
        latitude=40.73,
        longitude=-73.99,
    )
    fake = FakeSearchClient([spot])
    response = client_for(fake, {"near": "open"}).post(
        "/spots/search",
        json={
            "q": " coffee ",
            "latitude": 40.73,
            "longitude": -73.99,
            "radius_miles": 1,
            "open_now": True,
        },
    )
    assert response.status_code == 200, response.text
    assert fake.query == "coffee" and fake.limit == 20
    assert fake.filters == ["_geoRadius(40.73, -73.99, 1609)", 'id IN ["near"]']
    assert response.json()[0]["distance_miles"] == 0
    assert response.json()[0]["hours_status"] == "open"


def test_open_now_excludes_unknown_hours_before_search():
    fake = FakeSearchClient()
    response = client_for(fake).post("/spots/search", json={"open_now": True})
    assert response.status_code == 200
    assert response.json() == []
    assert fake.query is None


@pytest.mark.parametrize(
    "payload",
    [
        {"latitude": 40.73},
        {"longitude": -73.99},
        {"radius_miles": 1},
        {"latitude": 91, "longitude": 0},
        {"latitude": 40.73, "longitude": -73.99, "radius_miles": 0},
    ],
)
def test_filtered_search_rejects_invalid_location(payload):
    assert client_for(FakeSearchClient()).post("/spots/search", json=payload).status_code == 422


@pytest.mark.parametrize("driver", ["turso", "libsql"])
@pytest.mark.parametrize("open_now", [False, True])
def test_filtered_search_with_real_database(tmp_path, monkeypatch, driver, open_now):
    # A plain path exercises the installed libsql driver without a remote service.
    path = str(tmp_path / "spots.db")
    url = f"file:{path}" if driver == "turso" else path
    monkeypatch.setenv("TURSO_DATABASE_URL", url)
    record = StudySpotRecord(
        id="near",
        name="Cafe",
        category="cafe",
        address="A",
        neighborhood="N",
        borough="Manhattan",
        latitude=40.73,
        longitude=-73.99,
        opening_hours=SpotOpeningHours(expression="24/7"),
    )
    with StudySpotRepository(url) as repository:
        repository.replace([record])
        summaries = repository.all()
    fake = FakeSearchClient(summaries)
    app = create_app()
    app.dependency_overrides[get_search_client] = lambda: fake
    with TestClient(app) as client:
        response = client.post("/spots/search", json={"open_now": open_now})
    assert response.status_code == 200, response.text
    assert response.json()[0]["hours_status"] == "open"
    assert fake.filters == (['id IN ["near"]'] if open_now else [])


def test_slow_hours_read_does_not_block_other_requests(tmp_path, monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", f"file:{tmp_path / 'spots.db'}")
    started, release = Event(), Event()
    original_hours = StudySpotRepository.hours

    def slow_hours(repository):
        started.set()
        assert release.wait(5), "Timed out waiting to release the database read"
        return original_hours(repository)

    monkeypatch.setattr(StudySpotRepository, "hours", slow_hours)
    app = create_app()
    app.dependency_overrides[get_search_client] = lambda: FakeSearchClient()
    # The context keeps both requests on the same application event loop.
    with TestClient(app) as client, ThreadPoolExecutor(max_workers=2) as executor:
        search = executor.submit(client.post, "/spots/search", json={})
        try:
            assert started.wait(2)
            health = executor.submit(client.get, "/health/live")
            assert health.result(timeout=2).status_code == 200
        finally:
            release.set()
        assert search.result(timeout=2).status_code == 200
