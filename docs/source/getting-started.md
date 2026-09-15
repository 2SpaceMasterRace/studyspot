# Getting started

Docker Compose is the default path because it requires the fewest host tools. Nix is optional and provides the pinned development toolchain used by the repository.

## Docker-only setup

Install Git and a recent Docker distribution with Docker Compose 2.23 or newer, then run:

```shell
git clone git@github.com:2SpaceMasterRace/studyspot.git
cd studyspot
docker compose up --build --watch
```

Open <http://localhost:7500>. Requests under `/api/*` are proxied to FastAPI.

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

Host-facing ports use the consecutive `7500` through `7503` range. The three Compose services occupy `7500` through `7502`; the optional documentation server uses `7503`. Turso uses an embedded file locally and therefore needs no port. Browser traffic should normally enter through the frontend, which mirrors production's `/api/*` boundary.

## Local database configuration

Compose supplies `TURSO_DATABASE_URL=file:/app/.local/studyspot.db` and mounts the file on a named volume. Native development uses the value in `.env.example`:

```text
TURSO_DATABASE_URL=file:.local/studyspot.db
TURSO_AUTH_TOKEN=
```

No Turso account, CLI, or token is required for local development.

Populate the local database before using the study-spot routes:

```shell
just load-data
curl --fail 'http://localhost:7501/spots?limit=5'
```

The loader copies `data/spots.json` into the embedded database file and is safe to re-run.
