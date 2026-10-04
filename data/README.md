# Study-spot data

This directory is the small boundary between NYC Open Data and StudySpot:

```text
NYC Open Data (Socrata SODA) -> ingest.py -> spots.json
```

- `ingest.py` downloads NYC public library branches from the NYC Facilities
  Database (FacDB) and licensed sidewalk cafes from Dining Out NYC over the
  Socrata SODA API, resolves each record's neighborhood against the 2020
  Neighborhood Tabulation Areas, normalizes everything into the shared schema,
  appends a small hand-maintained list of NYU buildings, and writes
  `spots.json`.
- `spots.json` is the canonical generated dataset consumed by the application.
- `test_ingest.py` is the placeholder for mapping and validation tests.
- `enrich_hours.py` optionally matches saved OpenStreetMap Overpass records to
  existing spots by name and distance; `test_enrich_hours.py` covers the matching rules.

Every spot contains `id`, `name`, `category`, `address`, `neighborhood`,
`borough`, `latitude`, `longitude`, and `university`.

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

## Regenerating the dataset

Run from the repository root (standard library only, no extra dependencies):

```shell
python3 data/ingest.py
```

This refreshes `spots.json` with the current five-borough public library
network (~227 NYPL, Brooklyn, and Queens branches), the issued sidewalk cafe
licences (~1,555), and the NYU hand-list.

## Source notes

- The open-data dataset titled "Library" (`p4pf-fyc4`) is a map visualization
  and exposes no tabular columns over SODA, so FacDB (`ji82-xba5`, filtered to
  `facgroup='LIBRARIES' AND facsubgrp='PUBLIC LIBRARIES'`) is the queryable
  source of record for branch locations.
- Dining Out NYC (`fpeh-f7ci`, filtered to `license_status='Issued' AND
  license_type='Sidewalk'`) is the successor to the retired DCA sidewalk-cafe
  licence dataset. Roadway licences cover in-street dining structures, which are
  not study spots, so they are excluded.
- Neither source publishes a human-readable neighborhood name, but both carry a
  2020 NTA code, so `9nt8-h7nd` resolves one for 1,790 of 1,792 records without
  a geometry join. Anything it cannot resolve stays `null` rather than guessed.
- Names and streets arrive in upper case with heavy abbreviation. Expansion is
  best effort and deliberately conservative: ambiguous tokens such as `ST`,
  which may be either Street or Saint, are left alone.
- A record outside the five boroughs is dropped. The shared contract accepts
  only the five, so it could not be loaded anyway.

Turso migrations, local database files, and search indexes do not belong here.
The backend store (`studyspot_api.spots.store`) copies this snapshot into the
Turso serving database; from the repository root, run `just load-spots` after
regenerating `spots.json`.

StudySpot treats these records as candidate gathering and study locations. It
must not claim that a location has Wi-Fi, outlets, seating, or a quiet
environment unless NYC Open Data actually supplies that information.
