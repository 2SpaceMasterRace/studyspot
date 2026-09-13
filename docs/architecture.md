# Architecture

StudySpot is a modular monolith with two deployable applications and two managed data services.

```text
Browser -> Svelte -> FastAPI -> PostgreSQL/PostGIS
                            -> Meilisearch
```

The frontend owns presentation and browser interaction. FastAPI owns the HTTP boundary. PostgreSQL is the system of record. Meilisearch is a rebuildable search index. Docker Compose defines the local topology and waits for each required service to become healthy.

The frontend proxies `/api/*` to FastAPI during local development. The API currently exposes only `/health/live`; product routes, dependency readiness, migrations, seeding, and indexing remain owned by their corresponding tickets.
