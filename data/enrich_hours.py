"""Add OpenStreetMap opening hours to existing NYC Open Data spot records.

This script never creates or removes spots. It only fills missing opening_hours
when an OSM place has the same normalized name and is within 50 metres.
Ambiguous and invalid matches remain unknown.
"""

import argparse
import json
import math
import re
import unicodedata
from pathlib import Path

from pydantic import ValidationError
from studyspot_api.spots.hours import SpotOpeningHours

MAX_MATCH_METERS = 50


def _name_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).casefold()
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return " ".join(re.findall(r"\w+", normalized))


def _distance_meters(first: tuple[float, float], second: tuple[float, float]) -> float:
    lat_1, lon_1 = map(math.radians, first)
    lat_2, lon_2 = map(math.radians, second)
    difference = lat_2 - lat_1
    longitude_difference = lon_2 - lon_1
    haversine = (
        math.sin(difference / 2) ** 2
        + math.cos(lat_1) * math.cos(lat_2) * math.sin(longitude_difference / 2) ** 2
    )
    return 6_371_000 * 2 * math.asin(min(1, math.sqrt(haversine)))


def enrich(spots: list[dict], osm_elements: list[dict]) -> tuple[list[dict], int]:
    """Return the original records with only unambiguous hours matches added."""
    candidates: dict[str, list[tuple[tuple[float, float], str | None, str]]] = {}
    for element in osm_elements:
        tags = element.get("tags", {})
        name, expression = tags.get("name"), tags.get("opening_hours")
        if not name:
            continue
        point = element.get("center", element)
        latitude, longitude = point.get("lat"), point.get("lon")
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            continue
        source = f"https://www.openstreetmap.org/{element['type']}/{element['id']}"
        candidates.setdefault(_name_key(name), []).append(
            ((latitude, longitude), expression, source)
        )

    enriched = []
    added = 0
    for spot in spots:
        updated = spot.copy()
        if not updated.get("opening_hours"):
            nearby = [
                (expression, source)
                for point, expression, source in candidates.get(
                    _name_key(updated["name"]), []
                )
                if _distance_meters(
                    (float(updated["latitude"]), float(updated["longitude"])), point
                )
                <= MAX_MATCH_METERS
            ]
            if len(nearby) == 1 and nearby[0][0] is not None:
                try:
                    validated = SpotOpeningHours(expression=nearby[0][0])
                except ValidationError:
                    pass
                else:
                    updated["opening_hours"] = validated.model_dump()
                    updated["opening_hours_source_url"] = nearby[0][1]
                    added += 1
        enriched.append(updated)
    return enriched, added


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", required=True, type=Path, help="Saved OSM Overpass JSON"
    )
    parser.add_argument(
        "--spots", type=Path, default=Path(__file__).with_name("spots.json")
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()

    spots = json.loads(arguments.spots.read_text(encoding="utf-8"))
    if not spots:
        raise ValueError(
            "No NYC Open Data spots to enrich; run the original importer first"
        )
    osm = json.loads(arguments.input.read_text(encoding="utf-8"))
    records, added = enrich(spots, osm.get("elements", []))
    output = arguments.output or arguments.spots
    output.write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Added OpenStreetMap hours to {added} of {len(records)} existing spots")


if __name__ == "__main__":
    main()
