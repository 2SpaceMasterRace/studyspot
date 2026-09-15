"""Shared fixtures: a temporary Turso database loaded with known study spots."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from studyspot_api.main import create_app
from studyspot_api.spots.database import Database
from studyspot_api.spots.models import StudySpot
from studyspot_api.spots.repository import TursoSpotRepository
from studyspot_api.spots.router import get_repository

#: A small dataset chosen to exercise every filter, including the awkward values real
#: NYC Open Data contains: accented names, SQL wildcard characters, and a spot whose
#: neighborhood the source never supplied.
FIXTURE_SPOTS: list[dict[str, Any]] = [
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
        "id": "facdb:nyu",
        "name": "New York University",
        "category": "university",
        "address": "70 Washington Square S, New York, NY 10012",
        "neighborhood": "Greenwich Village",
        "borough": "Manhattan",
        "latitude": 40.7291,
        "longitude": -73.9965,
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
        "id": "dining:zanzibar",
        "name": "Zanzibar",
        "category": "cafe",
        "address": "645 9 Avenue, New York, NY 10036",
        "neighborhood": None,
        "borough": "Manhattan",
        "latitude": 40.7592,
        "longitude": -73.9908,
        "university": None,
    },
    {
        "id": "facdb:pratt",
        "name": "Pratt Institute Library",
        "category": "academic_library",
        "address": "200 Willoughby Avenue, Brooklyn, NY 11205",
        "neighborhood": "Clinton Hill",
        "borough": "Brooklyn",
        "latitude": 40.6913,
        "longitude": -73.9639,
        "university": "Pratt Institute",
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
    {
        "id": "dining:sweetleaf",
        "name": "Sweet_Leaf",
        "category": "cafe",
        "address": "10-93 Jackson Avenue, Long Island City, NY 11101",
        "neighborhood": "Long Island City-Hunters Point",
        "borough": "Queens",
        "latitude": 40.7437,
        "longitude": -73.9486,
        "university": None,
    },
    {
        "id": "facdb:queens",
        "name": "Queens Central Library",
        "category": "library",
        "address": "89-11 Merrick Boulevard, Jamaica, NY 11432",
        "neighborhood": "Jamaica",
        "borough": "Queens",
        "latitude": 40.7043,
        "longitude": -73.7938,
        "university": None,
    },
    {
        "id": "facdb:fordham",
        "name": "Fordham Walsh Library",
        "category": "academic_library",
        "address": "441 East Fordham Road, Bronx, NY 10458",
        "neighborhood": "Belmont",
        "borough": "Bronx",
        "latitude": 40.8617,
        "longitude": -73.8854,
        "university": "Fordham University",
    },
    {
        "id": "facdb:csi",
        "name": "CSI Library",
        "category": "library",
        "address": "2800 Victory Boulevard, Staten Island, NY 10314",
        "neighborhood": "Willowbrook",
        "borough": "Staten Island",
        "latitude": 40.6019,
        "longitude": -74.1502,
        "university": "CUNY College of Staten Island",
    },
    {
        "id": "facdb:bronx",
        "name": "Bronx Library Center",
        "category": "library",
        "address": "310 East Kingsbridge Road, Bronx, NY 10458",
        "neighborhood": "Fordham Heights",
        "borough": "Bronx",
        "latitude": 40.8667,
        "longitude": -73.895,
        "university": "Fordham University",
    },
]


@pytest.fixture(scope="session")
def fixture_spots() -> list[StudySpot]:
    """The fixture dataset, validated against the shared contract."""
    return [StudySpot.model_validate(record) for record in FIXTURE_SPOTS]


@pytest.fixture(scope="session")
def database(tmp_path_factory: pytest.TempPathFactory, fixture_spots: list[StudySpot]) -> Database:
    """A temporary local Turso database holding the fixture dataset."""
    path: Path = tmp_path_factory.mktemp("turso") / "studyspot.db"
    database = Database(f"file:{path}")
    TursoSpotRepository(database).replace_all(fixture_spots)
    return database


@pytest.fixture
def repository(database: Database) -> TursoSpotRepository:
    return TursoSpotRepository(database)


@pytest.fixture
def client(repository: TursoSpotRepository) -> Iterator[TestClient]:
    """A client for an application composed against the temporary database."""
    application = create_app()
    application.dependency_overrides[get_repository] = lambda: repository
    with TestClient(application) as test_client:
        yield test_client
