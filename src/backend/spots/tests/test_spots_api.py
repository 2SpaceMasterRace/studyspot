"""Contract tests for the study-spot routes.

The published contract in ``docs/source/api.md`` is what the frontend, the
importer, and any future search index agree on, so these tests assert the shape
of the response and not just its contents. They are the check that the move from
FastAPI to Django did not quietly change the API.
"""

from __future__ import annotations

from typing import Any

import pytest
from django.urls import reverse

from spots.models import StudySpot

#: A small dataset chosen to exercise every filter, including the awkward values
#: real NYC Open Data contains: accented names, SQL wildcard characters, and a
#: spot whose neighborhood the source never supplied.
RECORDS: list[dict[str, Any]] = [
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
    },
    {
        "id": "facdb:butler",
        "name": "Butler Library",
        "category": "academic_library",
        "address": "535 West 114 Street, New York, NY 10027",
        "neighborhood": "Morningside Heights",
        "borough": "Manhattan",
        "latitude": 40.8063,
        "longitude": -73.9634,
        "university": "Columbia University",
    },
    {
        "id": "facdb:allerton",
        "name": "Allerton Library",
        "category": "library",
        "address": "2740 Barnes Avenue",
        "neighborhood": None,
        "borough": "Bronx",
        "latitude": 40.8668,
        "longitude": -73.8632,
        "university": None,
    },
    {
        "id": "dining:grumpy",
        "name": "Café Grumpy",
        "category": "cafe",
        "address": "224 West 20 Street, New York, NY 10011",
        "neighborhood": "Chelsea-Hudson Yards",
        "borough": "Manhattan",
        "latitude": 40.7442,
        "longitude": -74.0,
        "university": None,
    },
    {
        "id": "dining:hundred",
        "name": "100% Coffee",
        "category": "cafe",
        "address": "1 Manhattan Avenue, Brooklyn, NY 11222",
        "neighborhood": "Greenpoint",
        "borough": "Brooklyn",
        "latitude": 40.7304,
        "longitude": -73.9543,
        "university": None,
    },
]

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


@pytest.fixture
def spots(db: None) -> list[StudySpot]:
    """The fixture dataset, written through the model."""
    return StudySpot.objects.bulk_create(StudySpot(**record) for record in RECORDS)


class TestLiveness:
    def test_reports_ok(self, client: Any) -> None:
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_does_not_touch_the_database(self, client: Any) -> None:
        # No `db` fixture, so any query would fail. Liveness answers whether the
        # process is alive, which a database cannot make false.
        assert client.get("/health/live").status_code == 200


class TestListEnvelope:
    def test_returns_the_published_envelope(self, client: Any, spots: list[StudySpot]) -> None:
        body = client.get("/spots").json()
        assert set(body) == {"items", "pagination"}
        assert set(body["pagination"]) == {"limit", "offset", "count", "total", "has_more"}

    def test_items_carry_exactly_the_contract_fields(
        self, client: Any, spots: list[StudySpot]
    ) -> None:
        body = client.get("/spots").json()
        assert set(body["items"][0]) == CONTRACT_FIELDS

    def test_defaults_to_twenty_per_page(self, client: Any, spots: list[StudySpot]) -> None:
        pagination = client.get("/spots").json()["pagination"]
        assert pagination["limit"] == 20
        assert pagination["offset"] == 0
        assert pagination["total"] == len(RECORDS)
        assert pagination["has_more"] is False

    def test_reports_the_total_beyond_the_page(self, client: Any, spots: list[StudySpot]) -> None:
        pagination = client.get("/spots?limit=2").json()["pagination"]
        assert pagination["count"] == 2
        assert pagination["total"] == len(RECORDS)
        assert pagination["has_more"] is True

    def test_offset_moves_the_window(self, client: Any, spots: list[StudySpot]) -> None:
        first = client.get("/spots?limit=2").json()["items"]
        second = client.get("/spots?limit=2&offset=2").json()["items"]
        assert {spot["id"] for spot in first}.isdisjoint({spot["id"] for spot in second})

    def test_the_order_is_stable_across_requests(self, client: Any, spots: list[StudySpot]) -> None:
        # Deliberately not compared against Python's sorted(): that is codepoint
        # order, while Postgres orders by the database collation, and the two
        # disagree about punctuation and digits. What the contract promises is
        # that the order does not move, not what the order is.
        first = [spot["id"] for spot in client.get("/spots?limit=100").json()["items"]]
        second = [spot["id"] for spot in client.get("/spots?limit=100").json()["items"]]
        assert first == second

    def test_paging_covers_every_row_exactly_once(
        self, client: Any, spots: list[StudySpot]
    ) -> None:
        # The property that matters, and the reason the ordering carries the
        # primary key as a tiebreaker: no row is repeated across pages and none
        # is skipped.
        seen: list[str] = []
        for offset in range(0, len(RECORDS) + 2, 2):
            page = client.get(f"/spots?limit=2&offset={offset}").json()["items"]
            seen.extend(spot["id"] for spot in page)

        assert sorted(seen) == sorted(record["id"] for record in RECORDS)
        assert len(seen) == len(set(seen))


class TestFilters:
    def test_filters_by_name_substring(self, client: Any, spots: list[StudySpot]) -> None:
        body = client.get("/spots?name=library").json()
        assert body["pagination"]["total"] == 3

    def test_name_filter_is_case_insensitive(self, client: Any, spots: list[StudySpot]) -> None:
        assert client.get("/spots?name=LIBRARY").json()["pagination"]["total"] == 3

    def test_name_filter_matches_accented_characters(
        self, client: Any, spots: list[StudySpot]
    ) -> None:
        body = client.get("/spots?name=café").json()
        assert [spot["id"] for spot in body["items"]] == ["dining:grumpy"]

    @pytest.mark.parametrize("query", ["%", "_", "100%"])
    def test_like_wildcards_are_matched_literally(
        self, client: Any, spots: list[StudySpot], query: str
    ) -> None:
        # Django escapes LIKE metacharacters in an icontains value, so "%" is a
        # search for a percent sign rather than for everything.
        body = client.get(f"/spots?name={query}").json()
        expected = [record["id"] for record in RECORDS if query in record["name"]]
        assert sorted(spot["id"] for spot in body["items"]) == sorted(expected)

    def test_filters_by_neighborhood(self, client: Any, spots: list[StudySpot]) -> None:
        body = client.get("/spots?neighborhood=greenpoint").json()
        assert [spot["id"] for spot in body["items"]] == ["dining:hundred"]

    def test_filters_by_borough(self, client: Any, spots: list[StudySpot]) -> None:
        assert client.get("/spots?borough=Bronx").json()["pagination"]["total"] == 1

    @pytest.mark.parametrize("borough", ["brooklyn", "BROOKLYN", "  Brooklyn  "])
    def test_borough_ignores_casing_and_spacing(
        self, client: Any, spots: list[StudySpot], borough: str
    ) -> None:
        body = client.get("/spots", {"borough": borough}).json()
        assert [spot["id"] for spot in body["items"]] == ["dining:hundred"]

    def test_filters_by_university(self, client: Any, spots: list[StudySpot]) -> None:
        body = client.get("/spots?university=new york university").json()
        assert [spot["id"] for spot in body["items"]] == ["facdb:bobst"]

    def test_a_university_filter_excludes_records_without_one(
        self, client: Any, spots: list[StudySpot]
    ) -> None:
        total = client.get("/spots?university=New York University").json()["pagination"]["total"]
        assert total == 1

    def test_filters_combine(self, client: Any, spots: list[StudySpot]) -> None:
        body = client.get("/spots?borough=Manhattan&name=library").json()
        assert body["pagination"]["total"] == 2


class TestValidation:
    @pytest.mark.parametrize(
        "query",
        ["limit=0", "limit=101", "limit=abc", "offset=-1", "name=", "borough=Yonkers"],
    )
    def test_a_bad_parameter_is_422(self, client: Any, spots: list[StudySpot], query: str) -> None:
        response = client.get(f"/spots?{query}")
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"

    def test_an_unknown_parameter_is_rejected(self, client: Any, spots: list[StudySpot]) -> None:
        # A misspelled filter that was ignored would return a plausible page of
        # the wrong results.
        response = client.get("/spots?neighbourhood=Greenpoint")
        assert response.status_code == 422
        details = response.json()["error"]["details"]
        assert [detail["field"] for detail in details] == ["query.neighbourhood"]

    def test_errors_use_the_shared_envelope(self, client: Any, spots: list[StudySpot]) -> None:
        body = client.get("/spots?limit=0").json()
        assert set(body) == {"error"}
        assert set(body["error"]) == {"code", "message", "details"}


class TestDetail:
    def test_fetches_one_spot(self, client: Any, spots: list[StudySpot]) -> None:
        body = client.get("/spots/facdb:bobst").json()
        assert body["name"] == "Bobst Library"
        assert set(body) == CONTRACT_FIELDS

    def test_an_identifier_keeps_its_dataset_prefix(
        self, client: Any, spots: list[StudySpot]
    ) -> None:
        # The colon in "facdb:bobst" has to survive URL routing.
        assert client.get("/spots/dining:grumpy").json()["id"] == "dining:grumpy"

    def test_an_unknown_identifier_is_404(self, client: Any, spots: list[StudySpot]) -> None:
        response = client.get("/spots/facdb:nothing")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"


class TestRouting:
    def test_the_routes_reverse_without_a_trailing_slash(self) -> None:
        # The published contract is /spots, and APPEND_SLASH is off, so a
        # trailing slash added here would become a 404 rather than a redirect.
        assert reverse("spot-list") == "/spots"
        assert reverse("spot-detail", kwargs={"spot_id": "facdb:bobst"}) == "/spots/facdb:bobst"
