# Data and search

StudySpot has one small data boundary:

```text
NYC Open Data -> data/ingest.py -> data/spots.json -> Turso -> API
                                                   \-> search index
```

The first dataset will showcase cafés and other public third places where students might meet or study. These are candidate locations, not guarantees of Wi-Fi, outlets, seating, quietness, or availability.

The directory intentionally contains only four files:

- `README.md` documents the boundary.
- `ingest.py` is the placeholder for download, normalization, and validation.
- `spots.json` is the canonical generated dataset and currently contains an empty array.
- `test_ingest.py` is the placeholder for importer tests.

Every spot will contain `id`, `name`, `category`, `address`, `neighborhood`, `borough`, `latitude`, and `longitude`. Source-specific fields must be normalized before reaching the API.

The importer and real dataset remain separate work. `just reindex` reads the
full `spots` table from Turso, configures the `spots` index, clears it, and
repopulates it. It is safe to run repeatedly and reports the indexed count.
Search uses ordered attributes `name`, `neighborhood`, `category`, `address`,
and `borough`, with indexing-time prefix search and Meilisearch defaults for
typo tolerance.
