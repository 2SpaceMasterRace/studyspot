"""NYC Open Data study-spot importer.

Pipeline::

    NYC Open Data (Socrata SODA) -> ingest.py -> spots.json

This importer pulls the public library branches of New York City from the NYC
Facilities Database (FacDB) via the Socrata Open Data API, normalizes each
record into the shared study-spot schema, appends a small hand-maintained list
of NYU buildings for university coverage, and writes the canonical
``data/spots.json`` snapshot consumed by the backend Turso loader.

Run it from the repository root::

    python3 data/ingest.py

The script depends only on the Python standard library so that it can run
without provisioning the backend or frontend toolchains.

StudySpot treats every record as a candidate gathering and study location. The
importer never invents amenities: it must not claim that a location has Wi-Fi,
outlets, seating, or a quiet environment unless NYC Open Data actually supplies
that information. FacDB does not, so those fields are simply absent here.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections.abc import Iterable
from pathlib import Path
from typing import Any

# --- Source configuration ---------------------------------------------------

# NYC Facilities Database (FacDB), Socrata dataset "ji82-xba5". The dataset that
# is titled "Library" on the open-data portal (p4pf-fyc4) is a map visualization
# and exposes no tabular columns over SODA, so FacDB is the queryable source of
# record for library branch locations.
SODA_RESOURCE_URL = "https://data.cityofnewyork.us/resource/ji82-xba5.json"

# The five-borough public branch network. Within the LIBRARIES facility group,
# "PUBLIC LIBRARIES" isolates the ~227 NYPL, Brooklyn, and Queens branches from
# the academic and special (non-public) libraries in the same group.
LIBRARY_WHERE = "facgroup='LIBRARIES' AND facsubgrp='PUBLIC LIBRARIES'"

# SODA returns at most 1000 rows by default; request comfortably above the
# branch count so a single page covers the whole network.
SODA_PAGE_LIMIT = 2000

SPOTS_PATH = Path(__file__).resolve().parent / "spots.json"

# Fields the study-spot schema promises for every record.
SCHEMA_FIELDS = (
    "id",
    "name",
    "category",
    "address",
    "neighborhood",
    "borough",
    "latitude",
    "longitude",
)

# FacDB stores boroughs in upper case; present them in the conventional form.
_BOROUGH_TITLES = {
    "MANHATTAN": "Manhattan",
    "BRONX": "Bronx",
    "BROOKLYN": "Brooklyn",
    "QUEENS": "Queens",
    "STATEN ISLAND": "Staten Island",
}


# --- Hand-maintained NYU coverage -------------------------------------------

# A short, curated list of NYU buildings gives the dataset university coverage
# alongside the public library branches. The records live in the versioned data
# file below (not hardcoded here) so they can be edited without touching code;
# coordinates and addresses are recorded by hand from public building
# information. Keep the list small and factual.
NYU_BUILDINGS_PATH = Path(__file__).resolve().parent / "nyu_buildings.json"


# --- Fetching ---------------------------------------------------------------


def build_query_url(
    resource_url: str = SODA_RESOURCE_URL,
    where: str = LIBRARY_WHERE,
    limit: int = SODA_PAGE_LIMIT,
) -> str:
    """Return the SODA request URL for the public library branches."""
    query = urllib.parse.urlencode(
        {
            "$where": where,
            "$limit": limit,
            "$order": "uid",
        }
    )
    return f"{resource_url}?{query}"


def fetch_library_records(url: str | None = None, timeout: float = 60.0) -> list[dict[str, Any]]:
    """Fetch raw FacDB library rows from the Socrata SODA API."""
    request_url = url or build_query_url()
    request = urllib.request.Request(request_url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


# --- Normalization ----------------------------------------------------------


def _clean_text(value: Any) -> str | None:
    """Collapse whitespace and title-case a FacDB text value, or return None."""
    if value is None:
        return None
    text = " ".join(str(value).split())
    if not text:
        return None
    # FacDB stores names and streets in upper case; title-case reads better while
    # keeping the source content intact.
    return text.title()


def _parse_coordinate(value: Any) -> float | None:
    """Parse a latitude/longitude string into a float, or return None."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_library(record: dict[str, Any]) -> dict[str, Any] | None:
    """Map one FacDB library row into the shared study-spot schema.

    Returns ``None`` when the row lacks the identity or coordinates required to
    place it on the map. FacDB does not publish a human-readable neighborhood
    name for these branches, so ``neighborhood`` is left ``None`` rather than
    guessed.
    """
    uid = record.get("uid")
    name = _clean_text(record.get("facname"))
    latitude = _parse_coordinate(record.get("latitude"))
    longitude = _parse_coordinate(record.get("longitude"))

    if not uid or not name or latitude is None or longitude is None:
        return None

    borough_raw = (record.get("boro") or "").strip().upper()
    borough = _BOROUGH_TITLES.get(borough_raw, _clean_text(record.get("boro")))

    address = _clean_text(record.get("address"))

    return {
        "id": f"facdb-{uid}",
        "name": name,
        "category": "library",
        "address": address,
        "neighborhood": None,
        "borough": borough,
        "latitude": latitude,
        "longitude": longitude,
    }


def normalize_libraries(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize FacDB rows, dropping any that cannot be placed."""
    spots = []
    for record in records:
        spot = normalize_library(record)
        if spot is not None:
            spots.append(spot)
    return spots


def nyu_spots(path: Path = NYU_BUILDINGS_PATH) -> list[dict[str, Any]]:
    """Read the hand-maintained NYU building records from the data file."""
    buildings = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(buildings, list):
        raise ValueError(f"{path} must contain a JSON array of NYU buildings")
    return [dict(building) for building in buildings]


def build_dataset(library_records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Combine normalized library branches with the NYU hand-list.

    Records are de-duplicated by ``id`` (NYU entries win on collision) and sorted
    for a stable, review-friendly snapshot.
    """
    combined: dict[str, dict[str, Any]] = {}
    for spot in normalize_libraries(library_records):
        combined[spot["id"]] = spot
    for spot in nyu_spots():
        combined[spot["id"]] = spot
    return sorted(combined.values(), key=lambda spot: (spot["borough"] or "", spot["name"]))


def write_spots(spots: list[dict[str, Any]], path: Path = SPOTS_PATH) -> None:
    """Write the dataset to ``spots.json`` as pretty-printed, stable JSON."""
    path.write_text(json.dumps(spots, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    """Fetch, normalize, and persist the canonical study-spot dataset."""
    records = fetch_library_records()
    spots = build_dataset(records)
    write_spots(spots)
    libraries = sum(1 for spot in spots if spot["category"] == "library")
    universities = len(spots) - libraries
    print(
        f"Wrote {len(spots)} spots to {SPOTS_PATH} "
        f"({libraries} library branches, {universities} NYU buildings)."
    )


if __name__ == "__main__":
    main()
