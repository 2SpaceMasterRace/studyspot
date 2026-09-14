# Architecture

StudySpot is a modular monolith with two deployable applications and reproducible public data.

```text
Browser -> SvelteKit -> FastAPI -> normalized NYC Open Data snapshot
                                      -> in-memory search index
```

The frontend owns presentation and browser interaction. FastAPI owns the HTTP boundary. The planned normalized snapshot will contain cafés and other public third places and provide reproducible input for list, detail, geographic, and search behavior. Its four-file boundary exists under `data/`, but ingestion is not implemented. Docker Compose also provides PostgreSQL/PostGIS and Meilisearch for integration work and waits for every local service to become healthy.

The frontend proxies `/api/*` to FastAPI during local development. Vercel uses the same public path boundary to route the two application services under one deployment domain.

## Why four services locally?

Each service has one lifecycle:

- SvelteKit can rebuild without restarting PostgreSQL.
- FastAPI can scale independently from the frontend.
- PostgreSQL data survives normal local container replacement.
- Any dedicated search index will be rebuildable from the normalized snapshot once search is implemented.

Packing all four processes into one container would couple their failures, scaling, logs, upgrades, and shutdown behavior. The current Vercel scaffold avoids that problem by deploying only the frontend and API. Whether a future release also packages the rebuildable public dataset depends on the data and search implementation that has not landed yet.

## Current capability

The API currently exposes only `/health/live`. Product routes, data ingestion, storage loading, and search remain owned by their corresponding implementation milestones.
