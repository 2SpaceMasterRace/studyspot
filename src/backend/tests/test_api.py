import pytest
from fastapi.testclient import TestClient

from studyspot_api.main import create_app
from studyspot_api.search.client import MeilisearchError
from studyspot_api.search.routes import get_search_client
from studyspot_api.spots.model import StudySpotSummary


class FakeSearchClient:
    def __init__(self, results=None, error=False):
        self.results = results or []
        self.error = error
        self.query = None
        self.limit = None

    async def search(self, query, limit):
        self.query, self.limit = query, limit
        if self.error:
            raise MeilisearchError("down")
        return self.results


def client_for(fake):
    app = create_app()
    app.dependency_overrides[get_search_client] = lambda: fake
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
