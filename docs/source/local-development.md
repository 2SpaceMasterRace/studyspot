# Local development

## Docker and Compose model

A Dockerfile builds one reusable image. A container is a running instance of that image. Docker Compose defines how the frontend, backend, and search containers start, communicate, persist local state, and report health.

```text
Dockerfile -> image -> container

Browser -> frontend:5173 -> backend:8000 -> /app/.local/studyspot.db
                                      \----> meilisearch:7700
```

Compose gives every service a private DNS name. The backend connects to `meilisearch:7700`; `localhost` inside the backend container refers only to that backend container. Turso is an embedded file on the backend's named volume, not a network service. On the host, Compose publishes frontend `7500`, backend `7501`, and Meilisearch `7502`.

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

The local Turso file and Meilisearch index use named volumes. Normal shutdown preserves them:

```shell
just shutdown
```

To deliberately remove containers and local data:

```shell
just clean
```

The clean operation cannot be undone unless the data was backed up.

## Useful diagnostics

```shell
just check
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
- the same normalized `data/spots.json` snapshot once the importer populates it
- the same Turso repository interface, schema, and query contract
- the same HTTP routes and response contracts
- the same data mapping and search-ranking behavior
- the same liveness and readiness semantics

The infrastructure differs only where the runtime requires it: local FastAPI will open an embedded Turso file, while stateless Vercel functions will connect to Turso Cloud over the network. The planned adapter hides that transport difference and must pass the same tests in both modes. Meilisearch remains a local integration target; no permanent production search service is required by the current scaffold.

The backend receives these Compose defaults:

```text
TURSO_DATABASE_URL=file:/app/.local/studyspot.db
TURSO_AUTH_TOKEN=
MEILISEARCH_URL=http://meilisearch:7700
MEILISEARCH_API_KEY=
MEILISEARCH_INDEX=spots
```

To exercise the hosted adapter deliberately, set a Turso Cloud URL and token
in an ignored `.env` file before starting Compose. Do not use the production
token locally. Run `just reindex` after loading rows into `spots`; it uses a
disposable backend container and waits for Meilisearch tasks. Hosted
Meilisearch can be configured with `MEILISEARCH_URL` and the optional API key.
