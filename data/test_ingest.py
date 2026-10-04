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
    SCHEMA_FIELDS,
    build_dataset,
    build_query_url,
    normalize_cafe,
    normalize_cafes,
    normalize_libraries,
    normalize_library,
    nyu_spots,
)

# A representative FacDB public-library row (trimmed to the fields we read).
SAMPLE_LIBRARY = {
    "uid": "abc123",
    "facname": "FORT WASHINGTON LIBRARY",
    "address": "535 WEST 179 STREET",
    "city": "NEW YORK",
    "zipcode": "10033",
    "boro": "MANHATTAN",
    "latitude": "40.848",
    "longitude": "-73.937",
    "facgroup": "LIBRARIES",
    "facsubgrp": "PUBLIC LIBRARIES",
    "nta2020": "MN0301",
}

# A representative Dining Out NYC sidewalk-cafe row (trimmed to what we read).
SAMPLE_CAFE = {
    "business_legal_name": "THIERRY INC",
    "assumed_name_s": "LE CHARLOT",
    "street": "19 EAST   69 STREET",
    "city": "NEW YORK",
    "postcode": "10021",
    "borough": "Manhattan",
    "latitude": "40.769770",
    "longitude": "-73.966662",
    "nta2020": "MN0802",
    "license_status": "Issued",
    "license_type": "Sidewalk",
}

NEIGHBORHOODS = {"MN0301": "Washington Heights (South)", "MN0802": "Upper East Side-Lenox Hill"}


def test_normalize_library_maps_to_schema() -> None:
    spot = normalize_library(SAMPLE_LIBRARY)
    assert spot is not None
    assert set(spot) == set(SCHEMA_FIELDS)
    assert spot["id"] == "facdb-abc123"
    assert spot["name"] == "Fort Washington Library"
    assert spot["category"] == "library"
    assert spot["address"] == "535 West 179 Street, New York, NY 10033"
    assert spot["borough"] == "Manhattan"
    assert spot["neighborhood"] is None
    assert spot["university"] is None
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


def test_nyu_hand_list_is_read_fresh_each_call() -> None:
    nyu_spots()[0]["name"] = "mutated"
    assert nyu_spots()[0]["name"] != "mutated"


def test_build_dataset_combines_and_sorts() -> None:
    spots = build_dataset([SAMPLE_LIBRARY])
    assert len(spots) == 1 + len(nyu_spots())
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


# --- Neighborhood resolution -------------------------------------------------


def test_normalize_library_resolves_the_neighborhood_when_given_the_lookup() -> None:
    spot = normalize_library(SAMPLE_LIBRARY, NEIGHBORHOODS)
    assert spot is not None
    assert spot["neighborhood"] == "Washington Heights (South)"


def test_normalize_library_leaves_an_unmapped_code_empty() -> None:
    spot = normalize_library(dict(SAMPLE_LIBRARY, nta2020="ZZ9999"), NEIGHBORHOODS)
    assert spot is not None
    assert spot["neighborhood"] is None


# --- Sidewalk cafes ----------------------------------------------------------


def test_normalize_cafe_maps_to_schema() -> None:
    spot = normalize_cafe(SAMPLE_CAFE, NEIGHBORHOODS)
    assert spot is not None
    assert set(spot) == set(SCHEMA_FIELDS)
    assert spot["name"] == "Le Charlot"
    assert spot["category"] == "cafe"
    assert spot["address"] == "19 East 69 Street, New York, NY 10021"
    assert spot["neighborhood"] == "Upper East Side-Lenox Hill"
    assert spot["borough"] == "Manhattan"
    assert spot["university"] is None


def test_normalize_cafe_falls_back_to_the_legal_name() -> None:
    spot = normalize_cafe(dict(SAMPLE_CAFE, assumed_name_s=""))
    assert spot is not None
    assert spot["name"] == "Thierry Inc"


def test_normalize_cafe_identifier_is_stable_between_runs() -> None:
    first = normalize_cafe(SAMPLE_CAFE)
    second = normalize_cafe(dict(SAMPLE_CAFE, latitude="40.769771"))
    assert first is not None and second is not None
    assert first["id"] == second["id"]
    assert first["id"].startswith("dining-")


def test_normalize_cafe_identifier_differs_between_storefronts() -> None:
    first = normalize_cafe(SAMPLE_CAFE)
    second = normalize_cafe(dict(SAMPLE_CAFE, street="21 EAST 69 STREET"))
    assert first is not None and second is not None
    assert first["id"] != second["id"]


def test_normalize_cafe_drops_unusable_rows() -> None:
    for overrides in (
        {"latitude": None},
        {"longitude": None},
        {"assumed_name_s": "", "business_legal_name": ""},
        {"street": "  "},
        {"borough": "YONKERS"},
    ):
        assert normalize_cafe(dict(SAMPLE_CAFE, **overrides)) is None


def test_normalize_cafes_skips_invalid_rows() -> None:
    rows = [SAMPLE_CAFE, dict(SAMPLE_CAFE, latitude=None)]
    assert len(normalize_cafes(rows)) == 1


# --- Address and name normalization ------------------------------------------


def test_address_collapses_whitespace_and_appends_the_state() -> None:
    assert (
        ingest._format_address("19 EAST   69 STREET", "NEW YORK", "10021")
        == "19 East 69 Street, New York, NY 10021"
    )


def test_address_omits_a_missing_postcode() -> None:
    assert ingest._format_address("1 MAIN STREET", "BRONX", None) == "1 Main Street, Bronx, NY"


def test_address_requires_a_street() -> None:
    assert ingest._format_address("   ", "NEW YORK", "10021") is None


def test_titlecase_expands_abbreviations_and_keeps_acronyms() -> None:
    assert ingest._clean_text("MID-MANHATTAN LIB BR") == "Mid-Manhattan Library Branch"
    assert ingest._clean_text("CUNY HUNTER COLL") == "CUNY Hunter College"


def test_titlecase_handles_possessives() -> None:
    assert ingest._clean_text("O'NEILL'S") == "O'Neill's"
    assert ingest._clean_text("DAWN’S TIL DUSK") == "Dawn’s Til Dusk"


# --- Combined dataset --------------------------------------------------------


def test_build_dataset_includes_cafes() -> None:
    spots = build_dataset([SAMPLE_LIBRARY], [SAMPLE_CAFE], NEIGHBORHOODS)
    categories = {spot["category"] for spot in spots}
    assert {"library", "cafe"} <= categories
    assert len(spots) == 2 + len(nyu_spots())


def test_nyu_hand_list_states_its_university() -> None:
    for spot in nyu_spots():
        assert spot["university"] == "New York University"


def test_only_curated_records_carry_a_university() -> None:
    spots = build_dataset([SAMPLE_LIBRARY], [SAMPLE_CAFE], NEIGHBORHOODS)
    affiliated = {spot["id"] for spot in spots if spot["university"]}
    assert affiliated == {spot["id"] for spot in nyu_spots()}


def test_build_query_url_targets_issued_sidewalk_cafes() -> None:
    url = build_query_url(ingest.DINING_RESOURCE_URL, ingest.CAFE_WHERE, order=":id")
    assert ingest.DINING_RESOURCE_URL in url
    assert "Issued" in url
    assert "Sidewalk" in url


def test_normalize_library_drops_a_borough_outside_the_five() -> None:
    # The shared contract accepts only the five boroughs, so anything else
    # cannot be loaded and must not reach spots.json.
    assert normalize_library(dict(SAMPLE_LIBRARY, boro="YONKERS")) is None
