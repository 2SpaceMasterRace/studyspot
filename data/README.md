# Study-spot data

This directory is the small boundary between NYC Open Data and StudySpot:

```text
NYC Open Data (Socrata SODA) -> ingest.py -> spots.json
```

- `ingest.py` downloads NYC public library branches from the NYC Facilities
  Database (FacDB) over the Socrata SODA API, normalizes them into the shared
  schema, appends a small hand-maintained list of NYU buildings, and writes
  `spots.json`.
- `spots.json` is the canonical generated dataset consumed by the application.
- `test_ingest.py` covers the mapping and validation logic.

Every spot contains `id`, `name`, `category`, `address`, `neighborhood`,
`borough`, `latitude`, and `longitude`.

## Regenerating the dataset

Run from the repository root (standard library only, no extra dependencies):

```shell
python3 data/ingest.py
```

This refreshes `spots.json` with the current five-borough public library
network (~227 NYPL, Brooklyn, and Queens branches) plus the NYU hand-list.

## Source notes

- The open-data dataset titled "Library" (`p4pf-fyc4`) is a map visualization
  and exposes no tabular columns over SODA, so FacDB (`ji82-xba5`, filtered to
  `facgroup='LIBRARIES' AND facsubgrp='PUBLIC LIBRARIES'`) is the queryable
  source of record for branch locations.
- FacDB does not publish a human-readable neighborhood name for these branches,
  so `neighborhood` is `null` for library records rather than guessed. The NYU
  hand-list records neighborhoods it knows by hand.

Turso migrations, local database files, and search indexes do not belong here.
The backend loader (`studyspot_api.spots.loader`) copies this snapshot into the
Turso serving database; from the repository root, run `just load-spots` after
regenerating `spots.json`.

StudySpot treats these records as candidate gathering and study locations. It
must not claim that a location has Wi-Fi, outlets, seating, or a quiet
environment unless NYC Open Data actually supplies that information.
