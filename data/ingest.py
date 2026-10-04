"""NYC Open Data study-spot importer.

Pipeline::

    NYC Open Data (Socrata SODA) -> ingest.py -> spots.json

This importer pulls the public library branches of New York City from the NYC
Facilities Database (FacDB) and the licensed sidewalk cafes from Dining Out NYC
via the Socrata Open Data API, resolves each record's neighborhood against the
2020 Neighborhood Tabulation Areas, normalizes everything into the shared
study-spot schema, appends a small hand-maintained list of NYU buildings for
university coverage, and writes the canonical ``data/spots.json`` snapshot
consumed by the backend Turso loader.

Run it from the repository root::

    python3 data/ingest.py

The script depends only on the Python standard library so that it can run
without provisioning the backend or frontend toolchains.

StudySpot treats every record as a candidate gathering and study location. The
importer never invents amenities: it must not claim that a location has Wi-Fi,
outlets, seating, or a quiet environment unless NYC Open Data actually supplies
that information. Neither source does, so those fields are simply absent here.

``university`` is likewise never inferred. It is set only for records taken from
the hand-maintained campus list, so proximity to a campus is never reported as
if it were an affiliation.
"""

from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from collections.abc import Iterable, Mapping
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

# Dining Out NYC Locations (DOT), Socrata dataset "fpeh-f7ci". This is the
# successor to the retired DCA sidewalk-cafe licence dataset and the queryable
# source of record for cafes with outdoor seating.
DINING_RESOURCE_URL = "https://data.cityofnewyork.us/resource/fpeh-f7ci.json"

# Only licences that are both issued and sidewalk-based. Roadway licences cover
# in-street dining structures, which are not study spots.
CAFE_WHERE = "license_status='Issued' AND license_type='Sidewalk'"

CAFE_PAGE_LIMIT = 5000

# 2020 Neighborhood Tabulation Areas (DCP), Socrata dataset "9nt8-h7nd". Both
# source datasets carry an ``nta2020`` code, so one lookup gives every record a
# human-readable neighborhood without a geometry join.
NTA_RESOURCE_URL = "https://data.cityofnewyork.us/resource/9nt8-h7nd.json"

NTA_PAGE_LIMIT = 500

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
    "university",
)

# FacDB stores boroughs in upper case; present them in the conventional form.
_BOROUGH_TITLES = {
    "MANHATTAN": "Manhattan",
    "BRONX": "Bronx",
    "BROOKLYN": "Brooklyn",
    "QUEENS": "Queens",
    "STATEN ISLAND": "Staten Island",
}

# NYC Open Data stores names and streets in upper case with heavy abbreviation.
# Expanding them is best effort and deliberately conservative: ambiguous tokens
# such as "ST", which may be either Street or Saint, are left alone.
_ABBREVIATIONS = {
    "ACAD": "Academy",
    "AMER": "American",
    "BKLYN": "Brooklyn",
    "BR": "Branch",
    "BRCH": "Branch",
    "COL": "College",
    "COLL": "College",
    "COMM": "Community",
    "CTR": "Center",
    "EDUC": "Education",
    "INST": "Institute",
    "LIB": "Library",
    "MEM": "Memorial",
    "SCH": "School",
    "UNIV": "University",
}

# Acronyms that must survive title casing unchanged.
_KEEP_UPPER = {"BPL", "CUNY", "NY", "NYC", "NYPL", "NYU", "QPL", "SUNY"}

# Separators inside a single token, including the typographic apostrophe and en
# dash that appear in a handful of real business names.
_TOKEN_SEPARATORS = "-/&.,'’–"


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
    where: str | None = LIBRARY_WHERE,
    limit: int = SODA_PAGE_LIMIT,
    order: str = "uid",
    select: str | None = None,
) -> str:
    """Return a SODA request URL, ordered so a repeated run is reproducible."""
    query: dict[str, Any] = {"$limit": limit, "$order": order}
    if where:
        query["$where"] = where
    if select:
        query["$select"] = select
    return f"{resource_url}?{urllib.parse.urlencode(query)}"


def fetch_records(url: str, timeout: float = 60.0) -> list[dict[str, Any]]:
    """Fetch raw rows from the Socrata SODA API."""
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def fetch_library_records(url: str | None = None, timeout: float = 60.0) -> list[dict[str, Any]]:
    """Fetch raw FacDB library rows from the Socrata SODA API."""
    return fetch_records(url or build_query_url(), timeout)


def fetch_cafe_records(url: str | None = None, timeout: float = 60.0) -> list[dict[str, Any]]:
    """Fetch raw Dining Out NYC sidewalk-cafe rows from the Socrata SODA API."""
    request_url = url or build_query_url(
        DINING_RESOURCE_URL, CAFE_WHERE, CAFE_PAGE_LIMIT, order=":id"
    )
    return fetch_records(request_url, timeout)


def fetch_neighborhood_names(url: str | None = None, timeout: float = 60.0) -> dict[str, str]:
    """Return the ``nta2020`` code to neighborhood name lookup."""
    request_url = url or build_query_url(
        NTA_RESOURCE_URL,
        where=None,
        limit=NTA_PAGE_LIMIT,
        order="nta2020",
        select="nta2020,ntaname",
    )
    return {
        str(row["nta2020"]).strip(): str(row["ntaname"]).strip()
        for row in fetch_records(request_url, timeout)
        if row.get("nta2020") and row.get("ntaname")
    }


# --- Normalization ----------------------------------------------------------


def _titlecase(text: str) -> str:
    """Title-case an upper-case source value and expand known abbreviations."""
    words: list[str] = []
    for raw in text.split():
        rendered: list[str] = []
        previous = ""
        for part in _split_token(raw):
            if not part.isalnum():
                rendered.append(part)
                previous = part
                continue
            upper = part.upper()
            if upper in _ABBREVIATIONS:
                rendered.append(_ABBREVIATIONS[upper])
            elif upper in _KEEP_UPPER:
                rendered.append(upper)
            elif previous in ("'", "’") and len(part) <= 2:
                # A contraction or possessive ("JOE'S"), not a new word.
                rendered.append(part.lower())
            else:
                rendered.append(part.capitalize())
            previous = part
        words.append("".join(rendered))
    return " ".join(words)


def _split_token(token: str) -> list[str]:
    """Split a token into alphanumeric runs and the separators between them."""
    parts: list[str] = []
    current = ""
    for character in token:
        if character in _TOKEN_SEPARATORS:
            if current:
                parts.append(current)
                current = ""
            parts.append(character)
        else:
            current += character
    if current:
        parts.append(current)
    return parts


def _clean_text(value: Any) -> str | None:
    """Collapse whitespace and title-case a source text value, or return None."""
    if value is None:
        return None
    text = " ".join(str(value).split())
    if not text:
        return None
    # Both sources store names and streets in upper case; title-casing reads
    # better while keeping the source content intact.
    return _titlecase(text)


def _format_address(street: Any, city: Any, postcode: Any) -> str | None:
    """Join the address parts a source supplies into one display address."""
    line = _clean_text(street)
    if not line:
        return None
    parts = [line]
    town = _clean_text(city)
    if town:
        parts.append(town)
    zipcode = str(postcode).strip()[:5] if postcode else ""
    parts.append(f"NY {zipcode}" if zipcode else "NY")
    return ", ".join(parts)


def _borough(value: Any) -> str | None:
    """Return one of the five borough names, or ``None`` for anything else.

    The shared contract accepts only the five, so a record outside them cannot be
    loaded and is better dropped here than at load time.
    """
    if value is None:
        return None
    return _BOROUGH_TITLES.get(" ".join(str(value).split()).upper())


def _parse_coordinate(value: Any) -> float | None:
    """Parse a latitude/longitude string into a float, or return None."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _neighborhood_for(
    record: dict[str, Any], neighborhoods: Mapping[str, str] | None
) -> str | None:
    """Resolve a record's ``nta2020`` code into a neighborhood name."""
    if not neighborhoods:
        return None
    return neighborhoods.get(str(record.get("nta2020") or "").strip()) or None


def normalize_library(
    record: dict[str, Any], neighborhoods: Mapping[str, str] | None = None
) -> dict[str, Any] | None:
    """Map one FacDB library row into the shared study-spot schema.

    Returns ``None`` when the row lacks the identity or coordinates required to
    place it on the map. FacDB publishes no neighborhood name directly, but it
    does carry a 2020 NTA code, so ``neighborhoods`` resolves one; without that
    lookup the field is left ``None`` rather than guessed.
    """
    uid = record.get("uid")
    name = _clean_text(record.get("facname"))
    latitude = _parse_coordinate(record.get("latitude"))
    longitude = _parse_coordinate(record.get("longitude"))

    if not uid or not name or latitude is None or longitude is None:
        return None

    borough = _borough(record.get("boro"))
    if borough is None:
        return None

    return {
        "id": f"facdb-{uid}",
        "name": name,
        "category": "library",
        "address": _format_address(
            record.get("address"), record.get("city"), record.get("zipcode")
        ),
        "neighborhood": _neighborhood_for(record, neighborhoods),
        "borough": borough,
        "latitude": latitude,
        "longitude": longitude,
        "university": None,
    }


def normalize_libraries(
    records: Iterable[dict[str, Any]], neighborhoods: Mapping[str, str] | None = None
) -> list[dict[str, Any]]:
    """Normalize FacDB rows, dropping any that cannot be placed."""
    spots = []
    for record in records:
        spot = normalize_library(record, neighborhoods)
        if spot is not None:
            spots.append(spot)
    return spots


def normalize_cafe(
    record: dict[str, Any], neighborhoods: Mapping[str, str] | None = None
) -> dict[str, Any] | None:
    """Map one Dining Out NYC row into the shared study-spot schema.

    Dining Out publishes no stable row identifier, so the identifier is derived
    from the business name and address, which together identify one storefront
    and stay the same between runs.
    """
    name = _clean_text(record.get("assumed_name_s")) or _clean_text(
        record.get("business_legal_name")
    )
    latitude = _parse_coordinate(record.get("latitude"))
    longitude = _parse_coordinate(record.get("longitude"))
    address = _format_address(record.get("street"), record.get("city"), record.get("postcode"))

    if not name or address is None or latitude is None or longitude is None:
        return None

    borough = _borough(record.get("borough"))
    if borough is None:
        return None

    digest = hashlib.sha1(f"{name}|{address}".encode()).hexdigest()[:16]
    return {
        "id": f"dining-{digest}",
        "name": name,
        "category": "cafe",
        "address": address,
        "neighborhood": _neighborhood_for(record, neighborhoods),
        "borough": borough,
        "latitude": latitude,
        "longitude": longitude,
        "university": None,
    }


def normalize_cafes(
    records: Iterable[dict[str, Any]], neighborhoods: Mapping[str, str] | None = None
) -> list[dict[str, Any]]:
    """Normalize Dining Out NYC rows, dropping any that cannot be placed."""
    spots = []
    for record in records:
        spot = normalize_cafe(record, neighborhoods)
        if spot is not None:
            spots.append(spot)
    return spots


def nyu_spots(path: Path = NYU_BUILDINGS_PATH) -> list[dict[str, Any]]:
    """Read the hand-maintained NYU building records from the data file."""
    buildings = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(buildings, list):
        raise ValueError(f"{path} must contain a JSON array of NYU buildings")
    return [dict(building) for building in buildings]


def build_dataset(
    library_records: Iterable[dict[str, Any]],
    cafe_records: Iterable[dict[str, Any]] = (),
    neighborhoods: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Combine normalized branches and cafes with the NYU hand-list.

    Records are de-duplicated by ``id`` (NYU entries win on collision) and sorted
    for a stable, review-friendly snapshot.
    """
    combined: dict[str, dict[str, Any]] = {}
    for spot in normalize_libraries(library_records, neighborhoods):
        combined[spot["id"]] = spot
    for spot in normalize_cafes(cafe_records, neighborhoods):
        combined[spot["id"]] = spot
    for spot in nyu_spots():
        combined[spot["id"]] = spot
    return sorted(combined.values(), key=lambda spot: (spot["borough"] or "", spot["name"]))


def write_spots(spots: list[dict[str, Any]], path: Path = SPOTS_PATH) -> None:
    """Write the dataset to ``spots.json`` as pretty-printed, stable JSON."""
    path.write_text(json.dumps(spots, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    """Fetch, normalize, and persist the canonical study-spot dataset."""
    neighborhoods = fetch_neighborhood_names()
    spots = build_dataset(fetch_library_records(), fetch_cafe_records(), neighborhoods)
    write_spots(spots)
    counts: dict[str, int] = {}
    for spot in spots:
        counts[spot["category"]] = counts.get(spot["category"], 0) + 1
    placed = sum(1 for spot in spots if spot["neighborhood"])
    summary = ", ".join(f"{count} {category}" for category, count in sorted(counts.items()))
    print(f"Wrote {len(spots)} spots to {SPOTS_PATH} ({summary}).")
    print(f"Neighborhood resolved for {placed} of {len(spots)}.")


if __name__ == "__main__":
    main()
