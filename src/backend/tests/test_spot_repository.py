"""Contract tests for the shared study-spot repository.

The API, the search projection, and the dataset loader all go through this one
interface, so the tests below exercise it the way each of those three does.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from studyspot_api.spots.database import Database, DatabaseUnavailable, local_database_path
from studyspot_api.spots.models import SpotFilters, StudySpot
from studyspot_api.spots.repository import (
    TursoSpotRepository,
    build_where,
    escape_like,
)

# Record shapes drawn from what the real snapshots contain, including the awkward
# ones: a record with no address, one with no neighborhood, one that predates the
# university field, and two different category vocabularies.
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
        "id": "facdb:allerton",
        "name": "Allerton Library",
        "category": "library",
        "address": "2740 Barnes Avenue",
        "neighborhood": None,
        "borough": "Bronx",
        "latitude": 40.8668,
        "longitude": -73.8632,
    },
    {
        "id": "facdb:bobst-hall",
        "name": "NYU Bobst Hall",
        "category": "university_building",
        "address": None,
        "neighborhood": None,
        "borough": "Manhattan",
        "latitude": 40.7291,
        "longitude": -73.9965,
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


@pytest.fixture
def spots() -> list[StudySpot]:
    return [StudySpot.model_validate(record) for record in RECORDS]


@pytest.fixture
def repository(tmp_path: Path, spots: list[StudySpot]) -> TursoSpotRepository:
    repository = TursoSpotRepository(Database(f"file:{tmp_path / 'studyspot.db'}"))
    repository.replace_all(spots)
    return repository


class TestSharedContract:
    """The model must accept every shape the committed snapshots contain."""

    def test_accepts_a_record_without_an_address(self) -> None:
        assert StudySpot.model_validate(RECORDS[2]).address is None

    def test_accepts_a_record_without_a_neighborhood(self) -> None:
        assert StudySpot.model_validate(RECORDS[1]).neighborhood is None

    def test_accepts_a_record_predating_the_university_field(self) -> None:
        assert "university" not in RECORDS[1]
        assert StudySpot.model_validate(RECORDS[1]).university is None

    @pytest.mark.parametrize(
        "category", ["library", "academic_library", "university_building", "cafe"]
    )
    def test_accepts_every_importer_vocabulary(self, category: str) -> None:
        record = {**RECORDS[0], "category": category}
        assert StudySpot.model_validate(record).category == category

    @pytest.mark.parametrize("borough", ["brooklyn", "BROOKLYN", " Staten  Island "])
    def test_borough_ignores_casing_and_spacing(self, borough: str) -> None:
        spot = StudySpot.model_validate({**RECORDS[0], "borough": borough})
        assert spot.borough.value in {"Brooklyn", "Staten Island"}

    def test_rejects_a_borough_outside_the_five(self) -> None:
        with pytest.raises(ValueError):
            StudySpot.model_validate({**RECORDS[0], "borough": "Yonkers"})


class TestLoaderConsumer:
    """How data/ingest.py's loader uses the repository."""

    def test_creates_the_schema_and_writes_every_record(
        self, tmp_path: Path, spots: list[StudySpot]
    ) -> None:
        repository = TursoSpotRepository(Database(f"file:{tmp_path / 'new.db'}"))
        assert repository.replace_all(spots) == len(spots)

    def test_is_repeatable(self, repository: TursoSpotRepository, spots: list[StudySpot]) -> None:
        assert repository.replace_all(spots) == len(spots)
        assert repository.replace_all(spots) == len(spots)

    def test_drops_records_removed_upstream(
        self, repository: TursoSpotRepository, spots: list[StudySpot]
    ) -> None:
        # The table is a rebuildable projection, so an upsert would wrongly keep
        # rows the importer no longer produces.
        repository.replace_all(spots[:2])
        _, total = repository.list_spots(SpotFilters(), limit=100, offset=0)
        assert total == 2
        assert repository.get_spot("dining:grumpy") is None

    def test_an_empty_snapshot_empties_the_table(self, repository: TursoSpotRepository) -> None:
        assert repository.replace_all([]) == 0


class TestApiConsumer:
    """How the HTTP routes use the repository."""

    def test_lists_in_a_deterministic_order(self, repository: TursoSpotRepository) -> None:
        found, _ = repository.list_spots(SpotFilters(), limit=100, offset=0)
        assert [spot.name for spot in found] == sorted(spot.name for spot in found)

    def test_reports_the_total_beyond_the_page(self, repository: TursoSpotRepository) -> None:
        found, total = repository.list_spots(SpotFilters(), limit=2, offset=0)
        assert len(found) == 2
        assert total == len(RECORDS)

    def test_offset_moves_the_window(self, repository: TursoSpotRepository) -> None:
        first, _ = repository.list_spots(SpotFilters(), limit=1, offset=0)
        second, _ = repository.list_spots(SpotFilters(), limit=1, offset=1)
        assert first[0].id != second[0].id

    def test_filters_by_name_substring(self, repository: TursoSpotRepository) -> None:
        found, _ = repository.list_spots(SpotFilters(name="library"), limit=100, offset=0)
        assert {spot.id for spot in found} == {"facdb:bobst", "facdb:allerton"}

    @pytest.mark.parametrize("query", ["café grumpy", "CAFÉ GRUMPY"])
    def test_name_folds_case_beyond_ascii(
        self, repository: TursoSpotRepository, query: str
    ) -> None:
        found, _ = repository.list_spots(SpotFilters(name=query), limit=100, offset=0)
        assert [spot.id for spot in found] == ["dining:grumpy"]

    @pytest.mark.parametrize(("query", "expected"), [("100%", 1), ("_", 0)])
    def test_wildcards_in_a_name_filter_are_literal(
        self, repository: TursoSpotRepository, query: str, expected: int
    ) -> None:
        _, total = repository.list_spots(SpotFilters(name=query), limit=100, offset=0)
        assert total == expected

    def test_filters_by_neighborhood(self, repository: TursoSpotRepository) -> None:
        found, _ = repository.list_spots(
            SpotFilters(neighborhood="greenpoint"), limit=100, offset=0
        )
        assert [spot.id for spot in found] == ["dining:hundred"]

    def test_filters_by_borough(self, repository: TursoSpotRepository) -> None:
        _, total = repository.list_spots(SpotFilters(borough="bronx"), limit=100, offset=0)
        assert total == 1

    def test_filters_by_university(self, repository: TursoSpotRepository) -> None:
        found, _ = repository.list_spots(
            SpotFilters(university="new york university"), limit=100, offset=0
        )
        assert [spot.id for spot in found] == ["facdb:bobst"]

    def test_filters_combine(self, repository: TursoSpotRepository) -> None:
        _, total = repository.list_spots(
            SpotFilters(borough="Manhattan", name="library"), limit=100, offset=0
        )
        assert total == 1

    def test_fetches_one_spot(self, repository: TursoSpotRepository) -> None:
        spot = repository.get_spot("facdb:bobst")
        assert spot is not None and spot.name == "Bobst Library"

    def test_an_unknown_identifier_is_none(self, repository: TursoSpotRepository) -> None:
        assert repository.get_spot("facdb:missing") is None


class TestSearchProjectionConsumer:
    """How the reindex command uses the repository."""

    def test_yields_every_spot_in_primary_key_order(self, repository: TursoSpotRepository) -> None:
        found = list(repository.iter_all())
        assert [spot.id for spot in found] == sorted(record["id"] for record in RECORDS)

    def test_yields_documents_the_index_can_use(self, repository: TursoSpotRepository) -> None:
        document = next(iter(repository.iter_all())).model_dump()
        assert set(document) == {
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

    def test_an_empty_table_yields_nothing(self, repository: TursoSpotRepository) -> None:
        repository.replace_all([])
        assert list(repository.iter_all()) == []


class TestConnection:
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("file:.local/studyspot.db", ".local/studyspot.db"),
            ("file:/app/.local/studyspot.db", "/app/.local/studyspot.db"),
            ("file:///app/.local/studyspot.db", "/app/.local/studyspot.db"),
        ],
    )
    def test_reads_a_local_url_as_a_path(self, url: str, expected: str) -> None:
        assert local_database_path(url) == Path(expected)

    def test_a_file_url_uses_the_local_driver(self) -> None:
        import turso

        assert Database("file:.local/studyspot.db").driver is turso

    def test_a_hosted_url_uses_the_remote_driver(self) -> None:
        import libsql

        assert Database("libsql://studyspot-staging.turso.io", "token").driver is libsql

    def test_a_hosted_url_without_a_token_is_refused(self) -> None:
        with pytest.raises(DatabaseUnavailable, match="TURSO_AUTH_TOKEN"):
            Database("libsql://studyspot-staging.turso.io").connect()

    def test_a_missing_table_is_reported_as_unavailable(self, tmp_path: Path) -> None:
        repository = TursoSpotRepository(Database(f"file:{tmp_path / 'empty.db'}"))
        with pytest.raises(DatabaseUnavailable):
            repository.list_spots(SpotFilters(), limit=10, offset=0)


class TestQueryBuilding:
    def test_no_filters_produce_no_clause(self) -> None:
        assert build_where(SpotFilters()) == ("", [])

    def test_values_are_bound_not_interpolated(self) -> None:
        where, parameters = build_where(SpotFilters(neighborhood="'; DROP TABLE spots; --"))
        assert where == "WHERE neighborhood_folded = ?"
        assert parameters == ["'; drop table spots; --"]

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("plain", "plain"), ("100%", "100\\%"), ("a_b", "a\\_b"), ("c\\d", "c\\\\d")],
    )
    def test_escapes_wildcards(self, value: str, expected: str) -> None:
        assert escape_like(value) == expected
