# Local development

## Docker and Compose model

A Dockerfile builds one reusable image. A container is a running instance of that image. Docker Compose defines how the frontend, backend, database, and search containers start, communicate, persist data, and report health.

```text
Dockerfile -> image -> container

Browser -> frontend:5173 -> backend:8000 -> postgres:5432
                                      \----> meilisearch:7700
```

Compose gives every service a private DNS name. The backend therefore connects to `postgres:5432` and `meilisearch:7700`; `localhost` inside the backend container refers only to that backend container.

## Fast edit loop

Run:

```shell
just dev
```

Compose Watch synchronizes frontend and backend source into their running containers. Vite applies frontend hot module replacement, while Uvicorn reloads after Python changes. Dependency lockfile or Dockerfile changes rebuild only the affected image.

The equivalent Docker-only command is:

```shell
docker compose up --build --watch
```

## Data lifecycle

PostgreSQL and Meilisearch use named volumes. Normal shutdown preserves their data:

```shell
just down
```

To deliberately remove containers and local data:

```shell
just clean
```

The clean operation cannot be undone unless the data was backed up.

## Useful diagnostics

```shell
just doctor
docker compose ps
docker compose logs --follow backend
docker compose exec backend sh
docker compose restart backend
```

## Nix command surface

The flake pins the repository toolchain. Enter it interactively with `nix develop`, run one command with `nix develop -c COMMAND`, or use the packaged StudySpot command:

```shell
nix run . -- check
nix run . -- dev
nix run . -- deploy-preview
```

The package delegates to the repository's `justfile`, so Nix and non-Nix developers use the same supported commands. Nix does not store or manage deployment secrets.

## Local and production parity

The goal is behavioral parity rather than identical infrastructure:

- the same application source and dependency locks
- the same normalized public-data snapshot
- the same HTTP routes and response contracts
- the same data mapping and search-ranking behavior
- the same liveness and readiness semantics

PostgreSQL/PostGIS and Meilisearch remain in Compose as integration targets for future durable features. The first release does not deploy them because all current source data and search state can be reproduced from the versioned snapshot.
