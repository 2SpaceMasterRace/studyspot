"""Tests for the NYC Open Data study-spot importer.

These tests exercise the pure mapping and validation logic without touching the
network. Fetching from the Socrata SODA API is covered by running ``ingest.py``
directly; here we pin the schema contract and the normalization behavior.
"""

from __future__ import annotations

import json
from pathlib import Path

import ingest
from ingest import (
    NYU_BUILDINGS,
    SCHEMA_FIELDS,
    build_dataset,
    build_query_url,
    normalize_libraries,
    normalize_library,
    nyu_spots,
)

# A representative FacDB public-library row (trimmed to the fields we read).
SAMPLE_LIBRARY = {
    "uid": "abc123",
    "facname": "FORT WASHINGTON LIBRARY",
    "address": "535 WEST 179 STREET",
    "boro": "MANHATTAN",
    "latitude": "40.848",
    "longitude": "-73.937",
    "facgroup": "LIBRARIES",
    "facsubgrp": "PUBLIC LIBRARIES",
}


def test_normalize_library_maps_to_schema() -> None:
    spot = normalize_library(SAMPLE_LIBRARY)
    assert spot is not None
    assert set(spot) == set(SCHEMA_FIELDS)
    assert spot["id"] == "facdb-abc123"
    assert spot["name"] == "Fort Washington Library"
    assert spot["category"] == "library"
    assert spot["address"] == "535 West 179 Street"
    assert spot["borough"] == "Manhattan"
    assert spot["neighborhood"] is None
    assert spot["latitude"] == 40.848
    assert spot["longitude"] == -73.937
    assert isinstance(spot["latitude"], float)


def test_normalize_library_drops_rows_without_coordinates() -> None:
    for missing in ("latitude", "longitude"):
        row = dict(SAMPLE_LIBRARY, **{missing: None})
        assert normalize_library(row) is None


def test_normalize_library_drops_rows_without_identity() -> None:
    assert normalize_library(dict(SAMPLE_LIBRARY, uid=None)) is None
    assert normalize_library(dict(SAMPLE_LIBRARY, facname="")) is None


def test_normalize_libraries_skips_invalid_rows() -> None:
    rows = [SAMPLE_LIBRARY, dict(SAMPLE_LIBRARY, uid=None, facname="")]
    spots = normalize_libraries(rows)
    assert len(spots) == 1


def test_nyu_hand_list_matches_schema_and_has_unique_ids() -> None:
    spots = nyu_spots()
    assert 8 <= len(spots) <= 12
    ids = [spot["id"] for spot in spots]
    assert len(ids) == len(set(ids))
    for spot in spots:
        assert set(spot) == set(SCHEMA_FIELDS)
        assert spot["id"]
        assert spot["name"]
        assert isinstance(spot["latitude"], float)
        assert isinstance(spot["longitude"], float)
        assert spot["borough"] in {"Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"}


def test_nyu_hand_list_is_not_mutated_between_calls() -> None:
    nyu_spots()[0]["name"] = "mutated"
    assert nyu_spots()[0]["name"] != "mutated"
    assert NYU_BUILDINGS[0]["name"] != "mutated"


def test_build_dataset_combines_and_sorts() -> None:
    spots = build_dataset([SAMPLE_LIBRARY])
    assert len(spots) == 1 + len(NYU_BUILDINGS)
    ids = [spot["id"] for spot in spots]
    assert len(ids) == len(set(ids)), "ids must be unique across sources"
    keys = [(spot["borough"] or "", spot["name"]) for spot in spots]
    assert keys == sorted(keys), "dataset must be sorted for a stable snapshot"


def test_build_dataset_deduplicates_by_id() -> None:
    duplicated = [SAMPLE_LIBRARY, dict(SAMPLE_LIBRARY)]
    spots = build_dataset(duplicated)
    ids = [spot["id"] for spot in spots]
    assert len(ids) == len(set(ids))


def test_build_query_url_targets_public_libraries() -> None:
    url = build_query_url()
    assert ingest.SODA_RESOURCE_URL in url
    assert "PUBLIC+LIBRARIES" in url or "PUBLIC%20LIBRARIES" in url


def test_committed_spots_json_is_valid_and_matches_schema() -> None:
    path = Path(__file__).resolve().parent / "spots.json"
    spots = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(spots, list)
    if not spots:
        return  # snapshot not yet generated
    ids = [spot["id"] for spot in spots]
    assert len(ids) == len(set(ids))
    for spot in spots:
        assert set(spot) == set(SCHEMA_FIELDS)
        assert -90 <= spot["latitude"] <= 90
        assert -180 <= spot["longitude"] <= 0
