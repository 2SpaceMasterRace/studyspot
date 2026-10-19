# Architecture

StudySpot is a modular monolith with two deployable applications and reproducible public data.

```text
Browser -> SvelteKit -> Django REST Framework -> Postgres

NYC Open Data -> normalized snapshot -> Postgres
                                      \-> search index
```

The frontend owns presentation and browser interaction. Django owns the HTTP boundary, the shared study-spot model, and the dataset loader. The normalized snapshot under `data/` contains cafés and other public third places and provides reproducible input for list, detail, geographic, and search behavior. Docker Compose provides the frontend, backend, database, and Meilisearch containers and waits for every service to become healthy.

The frontend proxies `/api/*` to Django during local development. Both deployments use the same public path boundary, and both strip the `/api` prefix at the edge, so nothing in Django knows about it.

## One model, three consumers

The study-spot definition exists once, as a Django model in `src/backend/spots/models.py`. The HTTP routes, the dataset loader, and any future search projection all read it, so they cannot drift apart: a column the loader writes is a column the API can serve, and a field outside the shared contract makes the loader fail rather than quietly disappear.

What the model deliberately does not own is the HTTP layer's own concerns. Paging and query validation live in serializers, because the page size is a property of the route rather than of a study spot.

## Why four containers locally?

Each service has one lifecycle:

- SvelteKit can rebuild without restarting Django.
- Django can scale independently from the frontend.
- Postgres keeps its data across application rebuilds, and its own startup is slow enough that sharing it with the application would make every restart slow.
- Meilisearch can restart or rebuild without restarting either application.
- Any dedicated search index will be rebuildable from the normalized snapshot once search is implemented.

Packing the processes into one container would couple their failures, logs, upgrades, and shutdown behavior.

Postgres being a local container is itself a decision. The previous implementation ran an embedded SQLite-compatible database locally and a hosted one in deployment, which meant local behaviour and deployed behaviour were only ever as similar as one adapter managed to make them. One database engine everywhere costs a container and removes a class of difference that is otherwise discovered in deployment. See [Postgres database](database.md).

## Two deployment targets

| Target | Frontend | API | Database |
|---|---|---|---|
| Vercel | Vercel service | Vercel Python service | None by default |
| AWS | S3 behind CloudFront | Lambda behind CloudFront | RDS Postgres, private |

One revision, two deployments, no shared state. The application is the same either way: it holds nothing between requests and opens a database connection per request, which is what a serverless function needs and what a development server does not mind. The frontend picks its SvelteKit adapter from `DEPLOY_TARGET`, producing a Vercel build or a set of prerendered files for S3.

See [Deployment](deployment.md) for both, including why the Vercel deployment has no database.

## Current capability

The API exposes `GET /health/live`, `GET /spots`, and `GET /spots/{id}`. The shared model, the migrations, the loader, and both deployment targets are implemented. Data ingestion is a placeholder, and search and readiness reporting remain owned by their corresponding implementation milestones.
