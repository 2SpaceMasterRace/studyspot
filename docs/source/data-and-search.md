# Data and search

StudySpot has one small data boundary:

```text
NYC Open Data -> data/ingest.py -> data/spots.json -> Turso -> API
                                       ^                \-> search index
OSM opening_hours -> data/enrich_hours.py -----------+
```

The first dataset will showcase cafés and other public third places where students might meet or study. These are candidate locations, not guarantees of Wi-Fi, outlets, seating, quietness, or availability.

The data directory contains the source boundary and its optional hours enrichment:

- `README.md` documents the boundary.
- `ingest.py` is the placeholder for download, normalization, and validation.
- `spots.json` is the canonical generated dataset and currently contains an empty array.
- `test_ingest.py` is the placeholder for importer tests.
- `enrich_hours.py` matches source spots to OpenStreetMap hours without changing
  their identity or location; `test_enrich_hours.py` checks that matching rule.

Every spot will contain `id`, `name`, `category`, `address`, `neighborhood`, `borough`, `latitude`, and `longitude`. Source-specific fields must be normalized before reaching the API. `opening_hours` is optional and contains an OpenStreetMap expression plus an IANA timezone. A missing or ambiguous hours match stays unknown. The NYC Open Data importer remains a placeholder, so the canonical snapshot is still empty.

The separate `data/enrich_hours.py` step accepts saved Overpass JSON and only
adds hours when the normalized name matches exactly and the OSM place is within
50 meters. Multiple nearby candidates are left unresolved. OpenStreetMap hours
are used under the Open Database License; attribution and source links must be
retained when an enriched snapshot is distributed.

Load a populated snapshot with `just load-data`, then run `just reindex` (or
`just refresh-data` for both steps). The loader refuses an empty snapshot by
default, and the added `spot_hours` table does not alter the existing eight
spot columns.

The importer and real dataset remain separate work. `just reindex` reads the
full `spots` table from Turso, configures the `spots` index, clears it, and
repopulates it. It is safe to run repeatedly and reports the indexed count.
Search uses ordered attributes `name`, `neighborhood`, `category`, `address`,
and `borough`, with indexing-time prefix search and Meilisearch defaults for
typo tolerance. Reindexing also projects coordinates into Meilisearch's `_geo`
field. Radius and the IDs currently open are combined as search filters before
the 20-result limit; the API evaluates hours when each request arrives.
