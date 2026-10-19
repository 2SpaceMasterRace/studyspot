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

Postgres and Meilisearch use versioned upstream images from their registries. Compose builds the two application images and downloads the other two as needed.

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

Compose private DNS lets the backend reach `postgres:5432` and `meilisearch:7700`; `localhost` inside a container refers only to that container. Postgres is the one service also published on the host, at `127.0.0.1:5432`, so that a backend run outside Compose uses the same database as the one inside it.

## Port mappings

```yaml
ports:
  - "127.0.0.1:7501:8000"
```

The first port belongs to the host; the second belongs to the container. StudySpot's application and search containers use consecutive host ports `7500` through `7502`, while containers retain the conventional ports expected by their images and development tools. The optional documentation server uses `7503`. Postgres keeps its conventional `5432` on the host as well, because every Postgres client and connection string assumes it. Binding to `127.0.0.1` prevents local development services from being exposed on every network interface.

## Disposable containers and persistent data

Application containers should be replaceable. The Postgres data directory and the Meilisearch index live on named volumes so a normal shutdown preserves them:

```shell
docker compose down
```

Deleting volumes intentionally resets state:

```shell
docker compose down --volumes
```

## Health and startup order

Compose starts Postgres and Meilisearch first and verifies that both are accepting requests before the backend starts. `pg_isready` is given the database name explicitly, because without it the check passes against the user's default database while initialization is still running. The frontend waits for the backend health endpoint. A running process is not considered ready until its health check succeeds.

The backend then applies migrations before it starts serving, so a fresh volume gets a schema without anyone remembering to ask for one. It does not load data: an empty database is a valid state, and `GET /spots` answers with an empty page rather than an error. Fill it with:

```shell
just load-data
```

## Development loop

```shell
docker compose up --build --watch
```

Compose Watch synchronizes source edits into the application containers. Vite updates the browser, Django's development server reloads Python, and dependency or Dockerfile changes rebuild only the affected image.

## Essential commands

```shell
docker compose ps
docker compose logs --follow
docker compose logs --follow backend
docker compose exec backend sh
docker compose exec postgres psql --username=studyspot studyspot
docker compose restart backend
docker compose down
```

Compose is appropriate for local development, integration tests, and a single-machine demo. It does not provide managed TLS, remote database backups, or cross-region failover. Deployed database operations belong to RDS, which the AWS target provisions with Terraform; see [Deployment](deployment.md).
