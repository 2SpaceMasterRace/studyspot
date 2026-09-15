# Docker and Docker Compose

Docker packages an application and its dependencies into an image. A container is a running instance of that image. Docker Compose describes how multiple containers operate as one local system.

## Vocabulary

```text
Dockerfile -> image -> container
               |
               -> reusable, immutable template
```

Dockerfiles contain image build instructions. Images contain code, a runtime, and dependencies. Containers run an image as an isolated process. Volumes keep data outside a container's disposable filesystem, while networks let containers reach one another by service name.

## StudySpot images

StudySpot builds the frontend and backend from their local Dockerfiles:

```shell
docker build --tag studyspot-frontend src/frontend
docker build --tag studyspot-backend src/backend
```

Meilisearch uses a versioned upstream image from its registry. Compose builds the two application images and downloads the search image as needed.

Dockerfile layers are ordered so dependency manifests are copied and installed before frequently changed source code. This lets Docker reuse the expensive dependency layer after ordinary code edits.

## Compose topology

```text
Browser
   |
frontend:5173
   |
backend:8000
   |-- /app/.local/studyspot.db
   \-- meilisearch:7700
```

The database path is an embedded Turso file on the backend's named volume, so there is no database container, private DNS name, or host port. Compose private DNS lets the backend reach `meilisearch:7700`; `localhost` inside a container refers only to that container.

## Port mappings

```yaml
ports:
  - "127.0.0.1:7501:8000"
```

The first port belongs to the host; the second belongs to the container. StudySpot's containers use consecutive host ports `7500` through `7502`, while containers retain the conventional ports expected by their images and development tools. The optional documentation server uses `7503`. Binding to `127.0.0.1` prevents local development services from being exposed on every network interface.

## Disposable containers and persistent data

Application containers should be replaceable. The backend's local Turso file and Meilisearch index live on named volumes so a normal shutdown preserves them:

```shell
docker compose down
```

Deleting volumes intentionally resets state:

```shell
docker compose down --volumes
```

## Health and startup order

Compose starts Meilisearch first and verifies that it is accepting requests before the backend starts. The frontend waits for the backend health endpoint. The Turso adapter opens its local file in the backend process, so database readiness belongs in the planned API readiness check rather than Compose startup order. The Compose backend has no copy of `data/spots.json`, so its database is empty and the study-spot routes answer `503 database_unavailable` until a deployment step loads it. A running process is not considered ready until its health check succeeds.

## Development loop

```shell
docker compose up --build --watch
```

Compose Watch synchronizes source edits into the application containers. Vite updates the browser, Uvicorn reloads Python, and dependency or Dockerfile changes rebuild only the affected image.

## Essential commands

```shell
docker compose ps
docker compose logs --follow
docker compose logs --follow backend
docker compose exec backend sh
docker compose restart backend
docker compose down
```

Compose is appropriate for local development, integration tests, and a single-machine demo. It does not provide managed TLS, remote database backups, or cross-region failover; production database operations belong to Turso Cloud.
