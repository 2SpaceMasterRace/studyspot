"""Hours enrichment must never replace or guess NYC Open Data records."""

import pytest

from data.enrich_hours import enrich


def spot(identifier: str, longitude: float) -> dict:
    return {
        "id": identifier,
        "name": "Village Café",
        "latitude": 40.73,
        "longitude": longitude,
    }


def osm(identifier: int, longitude: float, hours: str | None) -> dict:
    return {
        "type": "node",
        "id": identifier,
        "lat": 40.73,
        "lon": longitude,
        "tags": {"name": "Village Cafe", "opening_hours": hours},
    }


def test_enrichment_adds_only_unambiguous_nearby_hours():
    source = [spot("near", -73.99), spot("far", -73.98)]
    records, count = enrich(source, [osm(1, -73.9901, "Mo-Fr 09:00-17:00")])
    assert count == 1
    assert [record["id"] for record in records] == ["near", "far"]
    assert records[0]["opening_hours"]["expression"] == "Mo-Fr 09:00-17:00"
    assert (
        records[0]["opening_hours_source_url"] == "https://www.openstreetmap.org/node/1"
    )
    assert "opening_hours" not in records[1]
    assert source[0] == spot("near", -73.99)


def test_ambiguous_or_invalid_hours_are_left_unknown():
    source = [spot("one", -73.99)]
    records, count = enrich(
        source,
        [
            osm(1, -73.9901, "24/7"),
            osm(2, -73.9902, "Mo-Fr 09:00-17:00"),
            osm(3, -73.9901, "invalid schedule"),
        ],
    )
    assert count == 0
    assert records == source


@pytest.mark.parametrize("hours", [None, "invalid schedule", ""])
def test_candidate_without_valid_hours_still_makes_match_ambiguous(hours):
    source = [spot("one", -73.99)]
    other = osm(2, -73.9902, hours)
    if hours is None:
        del other["tags"]["opening_hours"]
    records, count = enrich(source, [osm(1, -73.9901, "24/7"), other])
    assert count == 0
    assert records == source


@pytest.mark.parametrize("hours", [None, "invalid schedule", ""])
def test_unique_candidate_without_valid_hours_stays_unknown(hours):
    source = [spot("one", -73.99)]
    records, count = enrich(source, [osm(1, -73.9901, hours)])
    assert count == 0
    assert records == source
