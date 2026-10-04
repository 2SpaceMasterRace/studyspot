# Study-spot data

This directory is the small boundary between NYC Open Data and StudySpot:

```text
NYC Open Data -> ingest.py -> spots.json
```

- `ingest.py` is the placeholder for downloading and normalizing NYC Open Data.
- `spots.json` is the canonical generated dataset consumed by the application.
- `test_ingest.py` is the placeholder for mapping and validation tests.
- `enrich_hours.py` optionally matches saved OpenStreetMap Overpass records to
  existing spots by name and distance; `test_enrich_hours.py` covers the matching rules.

The first dataset will showcase cafés and other public third places where students might meet
or study. A spot will contain `id`, `name`, `category`, `address`, `neighborhood`, `borough`,
`latitude`, and `longitude`.

The NYC Open Data importer and real records are not implemented yet. `spots.json` is
therefore an empty JSON array. Run that importer before hours enrichment. To enrich a
populated snapshot, save an Overpass JSON response containing `name`, `opening_hours`,
and coordinates, then run:

```shell
uv run --project src/backend python data/enrich_hours.py --input overpass.json
```

The enrichment step fills only a missing `opening_hours` field when exactly one OSM
place has the same normalized name within 50 meters. It records the OSM source URL,
leaves ambiguous or invalid hours unknown, and keeps all existing NYC Open Data spot
fields. Enriched snapshots include OpenStreetMap data, which is available under the
[Open Database License](https://www.openstreetmap.org/copyright); keep the attribution
and source links when sharing the snapshot. Turso files and search indexes do not
belong here; `just load-data` copies a populated snapshot into Turso.

StudySpot treats these records as candidate gathering and study locations. It must not claim
that a location has Wi-Fi, outlets, seating, or a quiet environment unless NYC Open Data
actually supplies that information.
