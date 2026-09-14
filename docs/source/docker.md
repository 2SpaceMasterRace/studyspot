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

PostGIS and Meilisearch use versioned upstream images from their registries. Compose builds or downloads all four as needed.

Dockerfile layers are ordered so dependency manifests are copied and installed before frequently changed source code. This lets Docker reuse the expensive dependency layer after ordinary code edits.

## Compose topology

```text
Browser
   |
frontend:5173
   |
backend:8000
   |-- postgres:5432
   \-- meilisearch:7700
```

Compose creates private DNS using service names. Inside the backend container, `postgres` resolves to the database container. `localhost` would refer to the backend container itself.

## Port mappings

```yaml
ports:
  - "127.0.0.1:7501:8000"
```

The first port belongs to the host; the second belongs to the container. StudySpot uses consecutive host ports `7500` through `7503`, while containers retain the conventional ports expected by their images and development tools. Binding to `127.0.0.1` prevents local development services from being exposed on every network interface.

## Disposable containers and persistent data

Application containers should be replaceable. PostgreSQL and Meilisearch write to named volumes so a normal shutdown preserves their data:

```shell
docker compose down
```

Deleting volumes intentionally resets state:

```shell
docker compose down --volumes
```

## Health and startup order

Compose starts PostgreSQL and Meilisearch first. Their health checks verify that they are accepting requests before the backend starts. The frontend waits for the backend health endpoint. A running process is not considered ready until its health check succeeds.

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

Compose is appropriate for local development, integration tests, and a single-machine demo. It does not by itself provide multi-machine scheduling, managed TLS, database backups, or cross-region failover.
