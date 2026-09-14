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
| PostgreSQL | `localhost:7502` |
| Meilisearch | <http://localhost:7503> |
| Documentation (`just docs`) | <http://localhost:7504> |

Host-facing ports use the consecutive `7500` through `7504` range. The four Compose services occupy `7500` through `7503`; the optional documentation server uses `7504`. Containers retain their conventional internal ports, so service defaults and image health checks remain unchanged. Browser traffic should normally enter through the frontend, which mirrors production's `/api/*` boundary.
