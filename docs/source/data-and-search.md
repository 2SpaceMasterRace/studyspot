# Data and search

StudySpot has one small data boundary:

```text
NYC Open Data -> data/ingest.py -> data/spots.json -> Postgres -> API
                                                   \-> search index
```

The first dataset will showcase cafés and other public third places where students might meet or study. These are candidate locations, not guarantees of Wi-Fi, outlets, seating, quietness, or availability.

The directory intentionally contains only four files:

- `README.md` documents the boundary.
- `ingest.py` is the placeholder for download, normalization, and validation.
- `spots.json` is the canonical generated dataset and currently contains an empty array.
- `test_ingest.py` is the placeholder for importer tests.

Every spot will contain `id`, `name`, `category`, `address`, `neighborhood`, `borough`, `latitude`, and `longitude`, plus `university` for the records the importer takes from a curated campus list. Source-specific fields must be normalized before reaching the API, and the loader rejects a snapshot carrying any field outside that contract rather than dropping it silently.

The importer and the real dataset are not implemented; the loader, the schema, and its migrations are. Database code belongs to the backend's `spots` app rather than to this source-data directory: the model, the migrations, and the `load_spots` command live there, and nothing in `data/` talks to a database. The serving table and any separate search index remain rebuildable projections of `spots.json` until the product accepts non-reproducible writes — see [Postgres database](database.md).
