# Getting started

Docker Compose is the default path because it requires the fewest host tools. Nix is optional and provides the pinned development toolchain used by the repository.

## Docker-only setup

Install Git and a recent Docker distribution with Docker Compose 2.22 or newer, then run:

```shell
git clone git@github.com:2SpaceMasterRace/studyspot.git
cd studyspot
docker compose up --build --watch
```

Open <http://localhost:5173>. Requests under `/api/*` are proxied to FastAPI.

## Nix setup

With Nix and Docker installed:

```shell
nix develop
just doctor
just setup
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
just doctor
just setup
just dev
```

Use `just --list` as the authoritative list of supported commands.

## Local addresses

| Service | Address |
|---|---|
| Frontend | <http://localhost:5173> |
| API liveness | <http://localhost:8000/health/live> |
| PostgreSQL | `localhost:5432` |
| Meilisearch | <http://localhost:7700> |

The conventional service ports are retained because existing database and search tools recognize them. Browser traffic should normally enter through the frontend, which mirrors production's `/api/*` boundary.
