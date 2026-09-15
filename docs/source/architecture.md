# Architecture

StudySpot is a modular monolith with two deployable applications and reproducible public data.

```text
Browser -> SvelteKit -> FastAPI -> Turso

NYC Open Data -> normalized snapshot -> Turso
                                      \-> search index
```

The frontend owns presentation and browser interaction. FastAPI owns the HTTP boundary and the Turso adapter. The normalized snapshot under `data/` contains cafés and other public third places and provides reproducible input for list, detail, geographic, and search behavior. Docker Compose provides the frontend, backend, and Meilisearch containers and waits for every service to become healthy.

The frontend proxies `/api/*` to FastAPI during local development. Vercel uses the same public path boundary to route the two application services under one deployment domain.

## Why three containers locally?

Each service has one lifecycle:

- SvelteKit can rebuild without restarting FastAPI.
- FastAPI can scale independently from the frontend.
- Meilisearch can restart or rebuild without restarting either application.
- Any dedicated search index will be rebuildable from the normalized snapshot once search is implemented.

Turso does not add a fourth local service. The local adapter opens an embedded database file stored on the backend's `turso-data` volume. Production FastAPI functions are stateless and connect to Turso Cloud with `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`. Both modes stay behind the same repository interface and run the same SQLite-compatible schema and query tests.

Packing the three running processes into one container would couple their failures, logs, upgrades, and shutdown behavior. Vercel deploys only the frontend and API; Turso Cloud is managed separately, and a dedicated production search service is not required by the current scaffold.

## Current capability

The API exposes `/health/live`, `GET /spots`, and `GET /spots/{id}`. Data ingestion, the Turso adapter, and the loader are implemented. Search and readiness reporting remain owned by their corresponding implementation milestones.
