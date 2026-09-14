import httpx
import pytest

from studyspot_api.search.client import INDEX_SETTINGS, MeilisearchClient, MeilisearchError
from studyspot_api.spots.model import StudySpotSummary


def spot(identifier="stable-id"):
    return StudySpotSummary(
        id=identifier,
        name="Cafe",
        category="cafe",
        address="A",
        neighborhood="N",
        borough="B",
        latitude=1,
        longitude=2,
    )


@pytest.mark.anyio
async def test_configure_and_full_replacement():
    calls = []
    responses = {
        ("POST", "/indexes"): {"taskUid": 1},
        ("PATCH", "/indexes/spots/settings"): {"taskUid": 2},
        ("DELETE", "/indexes/spots/documents"): {"taskUid": 3},
        ("POST", "/indexes/spots/documents"): {"taskUid": 4},
    }

    async def handler(request):
        calls.append((request.method, request.url.path, request.content))
        if request.method == "GET" and request.url.path == "/indexes/spots":
            return httpx.Response(404, json={"code": "index_not_found"})
        if request.url.path.startswith("/tasks/"):
            return httpx.Response(200, json={"status": "succeeded"})
        return httpx.Response(202, json=responses[(request.method, request.url.path)])

    client = MeilisearchClient("http://test", transport=httpx.MockTransport(handler))
    await client.configure()
    assert await client.replace_documents([spot()]) == 1
    assert b'"searchableAttributes":["name","neighborhood","category","address","borough"]' in next(
        content for method, path, content in calls if method == "PATCH"
    )
    document_call = next(
        content
        for method, path, content in calls
        if method == "POST" and path == "/indexes/spots/documents"
    )
    assert b'"id":"stable-id"' in document_call


@pytest.mark.anyio
async def test_failed_task_is_reported():
    async def handler(request):
        return httpx.Response(200, json={"status": "failed"})

    client = MeilisearchClient("http://test", transport=httpx.MockTransport(handler))
    with pytest.raises(MeilisearchError):
        await client.wait_for_task(9)


def test_settings_contract():
    assert INDEX_SETTINGS["prefixSearch"] == "indexingTime"
    assert INDEX_SETTINGS["typoTolerance"]["minWordSizeForTypos"] == {"oneTypo": 5, "twoTypos": 9}


@pytest.mark.anyio
async def test_task_timeout():
    client = MeilisearchClient(
        "http://test",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"status": "processing"})
        ),
    )
    with pytest.raises(MeilisearchError, match="timed out"):
        await client.wait_for_task(1, timeout=0.01)


@pytest.mark.anyio
async def test_authentication_failure():
    def handler(request):
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(401, json={"message": "invalid key"})

    client = MeilisearchClient(
        "http://test", api_key="test-key", transport=httpx.MockTransport(handler)
    )
    with pytest.raises(MeilisearchError):
        await client.search("coffee")
