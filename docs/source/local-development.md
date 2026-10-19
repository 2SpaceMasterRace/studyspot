# Local development

## Docker and Compose model

A Dockerfile builds one reusable image. A container is a running instance of that image. Docker Compose defines how the frontend, backend, database, and search containers start, communicate, persist local state, and report health.

```text
Dockerfile -> image -> container

Browser -> frontend:5173 -> backend:8000 -> postgres:5432
                                      \----> meilisearch:7700
```

Compose gives every service a private DNS name. The backend connects to `postgres:5432` and `meilisearch:7700`; `localhost` inside the backend container refers only to that backend container. On the host, Compose publishes frontend `7500`, backend `7501`, Meilisearch `7502`, and Postgres on `127.0.0.1:5432`.

Postgres is published because the backend is often run outside Compose. `just dev-backend`, `just migrate`, and `just test` all reach the same database the containers use, so there is one local database rather than one per way of starting the application.

## Fast edit loop

Run:

```shell
just dev
```

Compose Watch synchronizes frontend and backend source into their running containers. Vite applies frontend hot module replacement, while Django's development server reloads after Python changes. Dependency lockfile or Dockerfile changes rebuild only the affected image.

The equivalent Docker-only command is:

```shell
docker compose up --build --watch
```

The backend container applies migrations before starting the server, so `docker compose up` on a fresh volume serves a working API rather than `503`s until someone remembers. It does not load data; see below.

## Working on the backend outside Compose

The backend needs only the database running:

```shell
just start-db
just migrate
just load-data
just dev-backend
```

`just start-db` starts the `postgres` service alone and waits for its health check. `just migrate` brings the schema up to date, `just load-data` copies `data/spots.json` into it, and `just dev-backend` serves the API on `127.0.0.1:7501`. The default connection string in `src/backend/studyspot/settings.py` already points at that published port, so nothing has to be exported for this to work; `.env.example` lists the variables worth overriding.

## Data lifecycle

The Postgres data directory and the Meilisearch index use named volumes. Normal shutdown preserves them:

```shell
just shutdown
```

To deliberately remove containers and local data:

```shell
just clean
```

The clean operation cannot be undone unless the data was backed up. It is safe here because every record can be rebuilt with `just migrate` and `just load-data`.

## Useful diagnostics

```shell
just check
docker compose ps
docker compose logs --follow backend
docker compose exec backend sh
docker compose exec postgres psql --username=studyspot studyspot
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
- the same normalized `data/spots.json` snapshot
- the same Postgres schema, applied by the same Django migrations
- the same HTTP routes and response contracts
- the same data mapping and search-ranking behavior
- the same liveness and readiness semantics

The database is the part that used to differ and no longer does: local development, CI, and the AWS deployment all run Postgres with one schema and one driver, so a query that works locally is not relying on behaviour the deployed database does not have. What still differs is how the application is served — a development server locally, a Lambda function on AWS, a Vercel function on Vercel — which is why the API holds no state between requests and opens a connection per request. See [Postgres database](database.md) for that reasoning and [Deployment](deployment.md) for the two targets.

Meilisearch remains a local integration target; no deployed search service exists yet.

The backend receives these Compose defaults:

```text
DATABASE_URL=postgresql://studyspot:studyspot@postgres:5432/studyspot
DJANGO_DEBUG=true
MEILISEARCH_URL=http://meilisearch:7700
```

Copy `.env.example` to `.env` to override them; `just` loads that file if it exists, so a copied `.env` takes effect without exporting anything, and its absence is not an error. The `just` targets also default `DJANGO_DEBUG` to `true`, because `settings.py` refuses to start without a `DJANGO_SECRET_KEY` when debug is off — right for a deployment, useless for `just test`. Nothing deploys through `just`.

`DJANGO_DEBUG=true` also mounts the Django admin and DRF's browsable API; both are off in deployments, where nothing guards the admin but a password nobody has set.
