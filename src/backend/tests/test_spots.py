"""API tests for the study-spot routes."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from studyspot_api.spots.models import StudySpot

CONTRACT_FIELDS = {
    "id",
    "name",
    "category",
    "address",
    "neighborhood",
    "borough",
    "latitude",
    "longitude",
    "university",
}


def names(payload: dict[str, Any]) -> list[str]:
    return [item["name"] for item in payload["items"]]


def get_spots(client: TestClient, **params: Any) -> dict[str, Any]:
    response = client.get("/spots", params=params)
    assert response.status_code == 200, response.text
    return response.json()


class TestListSpots:
    def test_returns_every_spot_in_the_database(
        self, client: TestClient, fixture_spots: list[StudySpot]
    ) -> None:
        payload = get_spots(client)
        assert payload["pagination"]["total"] == len(fixture_spots)
        assert len(payload["items"]) == len(fixture_spots)

    def test_orders_by_name_then_identifier(self, client: TestClient) -> None:
        payload = get_spots(client)
        assert names(payload) == sorted(names(payload))

    def test_every_item_matches_the_shared_contract(self, client: TestClient) -> None:
        payload = get_spots(client)
        for item in payload["items"]:
            assert set(item) == CONTRACT_FIELDS

    def test_reports_the_defaults_it_applied(self, client: TestClient) -> None:
        payload = get_spots(client)
        assert payload["pagination"]["limit"] == 20
        assert payload["pagination"]["offset"] == 0

    def test_serves_values_straight_from_the_database(self, client: TestClient) -> None:
        payload = get_spots(client, name="bobst")
        assert payload["items"] == [
            {
                "id": "facdb:bobst",
                "name": "Bobst Library",
                "category": "academic_library",
                "address": "70 Washington Square S, New York, NY 10012",
                "neighborhood": "Greenwich Village",
                "borough": "Manhattan",
                "latitude": 40.7295,
                "longitude": -73.9973,
                "university": "New York University",
            }
        ]

    def test_keeps_a_missing_neighborhood_null(self, client: TestClient) -> None:
        payload = get_spots(client, name="zanzibar")
        assert payload["items"][0]["neighborhood"] is None


class TestPagination:
    def test_walks_every_spot_exactly_once(
        self, client: TestClient, fixture_spots: list[StudySpot]
    ) -> None:
        seen: list[str] = []
        offset = 0
        while True:
            payload = get_spots(client, limit=5, offset=offset)
            seen.extend(item["id"] for item in payload["items"])
            if not payload["pagination"]["has_more"]:
                break
            offset += payload["pagination"]["limit"]

        assert len(seen) == len(set(seen)) == len(fixture_spots)

    def test_pages_do_not_overlap(self, client: TestClient) -> None:
        first = get_spots(client, limit=4, offset=0)
        second = get_spots(client, limit=4, offset=4)
        assert set(names(first)).isdisjoint(names(second))

    def test_counts_this_page_and_the_whole_result_set(
        self, client: TestClient, fixture_spots: list[StudySpot]
    ) -> None:
        payload = get_spots(client, limit=3)
        assert payload["pagination"]["count"] == 3
        assert payload["pagination"]["total"] == len(fixture_spots)

    def test_has_more_is_false_on_the_final_page(
        self, client: TestClient, fixture_spots: list[StudySpot]
    ) -> None:
        payload = get_spots(client, limit=5, offset=len(fixture_spots) - 5)
        assert payload["pagination"]["has_more"] is False

    def test_an_offset_past_the_end_is_an_empty_page(
        self, client: TestClient, fixture_spots: list[StudySpot]
    ) -> None:
        payload = get_spots(client, offset=500)
        assert payload["items"] == []
        assert payload["pagination"]["count"] == 0
        assert payload["pagination"]["total"] == len(fixture_spots)
        assert payload["pagination"]["has_more"] is False

    def test_total_ignores_the_page_window(self, client: TestClient) -> None:
        first = get_spots(client, limit=1)
        second = get_spots(client, limit=10, offset=2)
        assert first["pagination"]["total"] == second["pagination"]["total"]


class TestNameFilter:
    def test_matches_a_substring(self, client: TestClient) -> None:
        assert names(get_spots(client, name="Library")) == [
            "Bobst Library",
            "Bronx Library Center",
            "Butler Library",
            "CSI Library",
            "Fordham Walsh Library",
            "Pratt Institute Library",
            "Queens Central Library",
        ]

    @pytest.mark.parametrize("query", ["bobst", "BOBST", "BoBsT"])
    def test_ignores_casing(self, client: TestClient, query: str) -> None:
        assert names(get_spots(client, name=query)) == ["Bobst Library"]

    @pytest.mark.parametrize("query", ["café", "CAFÉ", "Café grumpy"])
    def test_ignores_casing_beyond_ascii(self, client: TestClient, query: str) -> None:
        assert names(get_spots(client, name=query)) == ["Café Grumpy"]

    def test_treats_a_percent_sign_as_text(self, client: TestClient) -> None:
        # Without escaping, "%" would be a wildcard and match every spot.
        assert names(get_spots(client, name="100%")) == ["100% Coffee"]

    def test_treats_an_underscore_as_text(self, client: TestClient) -> None:
        # Without escaping, "_" would match any single character.
        assert names(get_spots(client, name="sweet_leaf")) == ["Sweet_Leaf"]

    def test_trims_surrounding_whitespace(self, client: TestClient) -> None:
        assert names(get_spots(client, name="  bobst  ")) == ["Bobst Library"]

    def test_no_match_is_an_empty_page(self, client: TestClient) -> None:
        payload = get_spots(client, name="not a real place")
        assert payload["items"] == []
        assert payload["pagination"]["total"] == 0
        assert payload["pagination"]["has_more"] is False


class TestNeighborhoodFilter:
    @pytest.mark.parametrize("query", ["Greenwich Village", "greenwich village"])
    def test_matches_exactly_and_ignores_casing(self, client: TestClient, query: str) -> None:
        assert names(get_spots(client, neighborhood=query)) == [
            "Bobst Library",
            "New York University",
        ]

    def test_does_not_match_a_partial_neighborhood(self, client: TestClient) -> None:
        assert get_spots(client, neighborhood="Greenwich")["pagination"]["total"] == 0

    def test_excludes_spots_without_a_neighborhood(self, client: TestClient) -> None:
        assert "Zanzibar" not in names(get_spots(client, neighborhood="Greenpoint"))


class TestBoroughFilter:
    @pytest.mark.parametrize("query", ["Brooklyn", "brooklyn", "BROOKLYN"])
    def test_ignores_casing(self, client: TestClient, query: str) -> None:
        payload = get_spots(client, borough=query)
        assert payload["pagination"]["total"] == 2
        assert {item["borough"] for item in payload["items"]} == {"Brooklyn"}

    def test_handles_a_two_word_borough(self, client: TestClient) -> None:
        assert names(get_spots(client, borough="staten island")) == ["CSI Library"]

    @pytest.mark.parametrize(
        ("borough", "expected"),
        [("Manhattan", 5), ("Brooklyn", 2), ("Queens", 2), ("Bronx", 2), ("Staten Island", 1)],
    )
    def test_every_borough_returns_its_own_spots(
        self, client: TestClient, borough: str, expected: int
    ) -> None:
        payload = get_spots(client, borough=borough)
        assert payload["pagination"]["total"] == expected
        assert {item["borough"] for item in payload["items"]} == {borough}


class TestUniversityFilter:
    @pytest.mark.parametrize("query", ["Fordham University", "fordham university"])
    def test_matches_exactly_and_ignores_casing(self, client: TestClient, query: str) -> None:
        assert names(get_spots(client, university=query)) == [
            "Bronx Library Center",
            "Fordham Walsh Library",
        ]

    def test_includes_the_campus_itself(self, client: TestClient) -> None:
        assert names(get_spots(client, university="New York University")) == [
            "Bobst Library",
            "New York University",
        ]

    def test_excludes_spots_with_no_nearby_campus(self, client: TestClient) -> None:
        payload = get_spots(client, university="Columbia University")
        assert names(payload) == ["Butler Library"]
        assert all(item["university"] is not None for item in payload["items"])


class TestCombinedFilters:
    def test_filters_intersect(self, client: TestClient) -> None:
        assert names(get_spots(client, borough="Manhattan", name="library")) == [
            "Bobst Library",
            "Butler Library",
        ]

    def test_all_four_filters_together(self, client: TestClient) -> None:
        payload = get_spots(
            client,
            name="bobst",
            neighborhood="Greenwich Village",
            borough="Manhattan",
            university="New York University",
        )
        assert names(payload) == ["Bobst Library"]

    def test_contradictory_filters_return_nothing(self, client: TestClient) -> None:
        payload = get_spots(client, borough="Queens", neighborhood="Greenwich Village")
        assert payload["items"] == []
        assert payload["pagination"]["total"] == 0


class TestValidation:
    @pytest.mark.parametrize(
        ("params", "field"),
        [
            ({"limit": 0}, "query.limit"),
            ({"limit": 101}, "query.limit"),
            ({"limit": "many"}, "query.limit"),
            ({"offset": -1}, "query.offset"),
            ({"offset": "later"}, "query.offset"),
            ({"borough": "Bergen"}, "query.borough"),
            ({"name": "   "}, "query.name"),
            ({"name": "x" * 121}, "query.name"),
            ({"neighborhood": ""}, "query.neighborhood"),
            ({"university": ""}, "query.university"),
        ],
    )
    def test_rejects_bad_input(
        self, client: TestClient, params: dict[str, Any], field: str
    ) -> None:
        response = client.get("/spots", params=params)
        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "validation_error"
        assert [detail["field"] for detail in body["error"]["details"]] == [field]

    def test_rejects_an_unknown_query_parameter(self, client: TestClient) -> None:
        response = client.get("/spots", params={"borogh": "Queens"})
        assert response.status_code == 422
        detail = response.json()["error"]["details"][0]
        assert detail["field"] == "query.borogh"
        assert detail["type"] == "extra_forbidden"

    def test_names_the_allowed_boroughs(self, client: TestClient) -> None:
        response = client.get("/spots", params={"borough": "Bergen"})
        message = response.json()["error"]["details"][0]["message"]
        for borough in ("Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"):
            assert borough in message

    def test_reports_every_invalid_parameter_at_once(self, client: TestClient) -> None:
        response = client.get("/spots", params={"limit": 0, "offset": -5})
        fields = {detail["field"] for detail in response.json()["error"]["details"]}
        assert fields == {"query.limit", "query.offset"}

    @pytest.mark.parametrize("limit", [1, 100])
    def test_accepts_the_boundary_page_sizes(self, client: TestClient, limit: int) -> None:
        assert get_spots(client, limit=limit)["pagination"]["limit"] == limit


class TestGetSpot:
    def test_returns_one_spot(self, client: TestClient) -> None:
        response = client.get("/spots/facdb:butler")
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Butler Library"
        assert set(body) == CONTRACT_FIELDS

    def test_reports_an_unknown_identifier(self, client: TestClient) -> None:
        response = client.get("/spots/facdb:missing")
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "not_found"
        assert "facdb:missing" in body["error"]["message"]
        assert body["error"]["details"] == []


class TestErrorEnvelope:
    def test_every_error_uses_the_same_shape(self, client: TestClient) -> None:
        for response in (
            client.get("/spots", params={"limit": 0}),
            client.get("/spots/facdb:missing"),
            client.post("/spots"),
        ):
            body = response.json()
            assert set(body) == {"error"}
            assert set(body["error"]) == {"code", "message", "details"}
            assert isinstance(body["error"]["code"], str)
            assert isinstance(body["error"]["details"], list)

    def test_an_unsupported_method_is_reported_too(self, client: TestClient) -> None:
        response = client.post("/spots")
        assert response.status_code == 405
        assert response.json()["error"]["code"] == "method_not_allowed"


class TestOpenApi:
    def test_documents_the_route_and_its_filters(self, client: TestClient) -> None:
        schema = client.get("/openapi.json").json()
        parameters = schema["paths"]["/spots"]["get"]["parameters"]
        assert {parameter["name"] for parameter in parameters} == {
            "name",
            "neighborhood",
            "borough",
            "university",
            "limit",
            "offset",
        }


class TestComposedApplication:
    """The real composition, without a dependency override."""

    def test_an_unloaded_database_is_reported_as_503(self, tmp_path: Any, monkeypatch: Any) -> None:
        from studyspot_api.main import create_app

        monkeypatch.setenv("TURSO_DATABASE_URL", f"file:{tmp_path / 'empty.db'}")
        with TestClient(create_app()) as client:
            response = client.get("/spots")

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "database_unavailable"
