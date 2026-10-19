# Getting started

Docker Compose is the default path because it requires the fewest host tools. Nix is optional and provides the pinned development toolchain used by the repository.

## Docker-only setup

Install Git and a recent Docker distribution with Docker Compose 2.23 or newer, then run:

```shell
git clone git@github.com:2SpaceMasterRace/studyspot.git
cd studyspot
docker compose up --build --watch
```

Open <http://localhost:7500>. Requests under `/api/*` are proxied to the Django API. The backend applies its migrations on startup, so the first run leaves you with a working but empty database; see [Local database configuration](#local-database-configuration) to fill it.

## Nix setup

With Nix and Docker installed:

```shell
nix develop
just setup
just check
just dev
```

Nix supplies command-line tools but does not start a Docker daemon. Docker Desktop, Podman with Docker compatibility, or a native Docker daemon must already be running.

If `direnv` is installed and hooked into your shell, the committed `.envrc` can enter the same flake automatically:

```shell
direnv allow
```

Approval is intentionally local to each clone. Leaving the repository directory restores the previous shell environment.

## Manual native setup

Install Bun, Python 3.12, uv, just, pre-commit, Git, and Docker. Then run:

```shell
just setup
just check
just dev
```

Use `just --list` as the authoritative list of supported commands.

## Local addresses

| Service | Address |
|---|---|
| Frontend | <http://localhost:7500> |
| API liveness | <http://localhost:7501/health/live> |
| Meilisearch | <http://localhost:7502> |
| Documentation (`just docs`) | <http://localhost:7503> |
| Postgres | `127.0.0.1:5432` |

Application and search ports use the consecutive `7500` through `7503` range: the frontend, backend, and Meilisearch containers occupy `7500` through `7502`, and the optional documentation server uses `7503`. Postgres keeps its conventional `5432`, because every Postgres client and connection string assumes it. Browser traffic should normally enter through the frontend, which mirrors the deployed `/api/*` boundary.

## Local database configuration

The database is a Postgres container, and the application reaches it through one variable:

```text
DATABASE_URL=postgresql://studyspot:studyspot@localhost:5432/studyspot
```

Inside Compose the host is the service name, `postgres`; outside it, the same database is published on `127.0.0.1:5432`. Settings already default to that published port, so native development needs no configuration at all. `.env.example` lists the variables worth overriding, and `just` picks up a `.env` copied from it without any exporting. No hosted database, account, or token is involved in local development.

Populate the database before using the study-spot routes:

```shell
just load-data
curl --fail 'http://localhost:7501/spots?limit=5'
```

`just load-data` replaces the table's contents with `data/spots.json` in one transaction and is safe to re-run. Before any data can be loaded the schema has to exist: Compose migrates on startup, and outside Compose that is `just migrate`.

To work on the backend without running the whole system:

```shell
just start-db
just migrate
just load-data
just dev-backend
```

See [Local development](local-development.md) for the rest of that loop and [Postgres database](database.md) for what the schema guarantees.
