# Study-spot data

This directory is the small boundary between NYC Open Data and StudySpot:

```text
NYC Open Data -> ingest.py -> spots.json
```

- `ingest.py` is the placeholder for downloading and normalizing NYC Open Data.
- `spots.json` is the canonical generated dataset consumed by the application.
- `test_ingest.py` is the placeholder for mapping and validation tests.

The first dataset will showcase cafés and other public third places where students might meet
or study. A spot will contain `id`, `name`, `category`, `address`, `neighborhood`, `borough`,
`latitude`, and `longitude`.

The importer, tests, and real records are not implemented yet. `spots.json` is therefore an
empty JSON array. Database migrations, database files, and search indexes do not belong here;
the serving layer will load the normalized dataset into its chosen storage.

StudySpot treats these records as candidate gathering and study locations. It must not claim
that a location has Wi-Fi, outlets, seating, or a quiet environment unless NYC Open Data
actually supplies that information.
