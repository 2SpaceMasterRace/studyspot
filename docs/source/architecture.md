# Architecture

StudySpot is a modular monolith with two deployable applications and two managed data services.

```text
Browser -> SvelteKit -> FastAPI -> PostgreSQL/PostGIS
                               -> Meilisearch
```

The frontend owns presentation and browser interaction. FastAPI owns the HTTP boundary. PostgreSQL is the system of record. Meilisearch is a rebuildable search index. Docker Compose defines the local topology and waits for each required service to become healthy.

The frontend proxies `/api/*` to FastAPI during local development. Vercel uses the same public path boundary to route the two application services under one deployment domain.

## Why four services locally?

Each service has one lifecycle:

- SvelteKit can rebuild without restarting PostgreSQL.
- FastAPI can scale independently from the frontend.
- PostgreSQL data survives application replacement.
- Meilisearch can be rebuilt from the source of truth.

Packing all four processes into one container would couple their failures, scaling, logs, upgrades, and shutdown behavior. It would also make persistent data unsafe on a stateless application platform.

## Current capability

The API currently exposes only `/health/live`. Product routes, dependency readiness, migrations, seeding, and indexing remain owned by their corresponding implementation milestones.
