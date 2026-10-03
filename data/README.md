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
- `nyu_buildings.json` is the hand-maintained list of NYU buildings, kept as
  data (not hardcoded in `ingest.py`) so it can be edited without touching code.
- `test_ingest.py` covers the mapping and validation logic.

Every spot contains `id`, `name`, `category`, `address`, `neighborhood`,
`borough`, `latitude`, `longitude`, and `university`.

`university` is set only for records taken from the hand-maintained campus
list. It is never inferred: being near a campus is not an affiliation, and an
earlier draft that assigned the nearest campus within 500 m produced results
such as a cafe labelled with a hospital's nursing school.

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
