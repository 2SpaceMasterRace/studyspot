# Architecture

StudySpot is a modular monolith with two deployable applications and reproducible public data.

```text
Browser -> SvelteKit -> FastAPI -> normalized NYC/NYU snapshot
                                      -> in-memory search index
```

The frontend owns presentation and browser interaction. FastAPI owns the HTTP boundary. The normalized snapshot is the reproducible input for list, detail, geographic, and search behavior. Docker Compose also provides PostgreSQL/PostGIS and Meilisearch for integration work and waits for every local service to become healthy.

The frontend proxies `/api/*` to FastAPI during local development. Vercel uses the same public path boundary to route the two application services under one deployment domain.

## Why four services locally?

Each service has one lifecycle:

- SvelteKit can rebuild without restarting PostgreSQL.
- FastAPI can scale independently from the frontend.
- PostgreSQL data survives normal local container replacement.
- Meilisearch can be rebuilt from the normalized snapshot.

Packing all four processes into one container would couple their failures, scaling, logs, upgrades, and shutdown behavior. The first Vercel release avoids that problem by deploying only the frontend and API and packaging the rebuildable public dataset with them.

## Current capability

The API currently exposes only `/health/live`. Product routes, dependency readiness, migrations, seeding, and indexing remain owned by their corresponding implementation milestones.
