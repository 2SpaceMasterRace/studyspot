# [StudySpot](https://studyspot-nyu.vercel.app/)
<<<<<<< HEAD

_I just want somewhere nearby to meet or study, but finding a good café or third place means searching scattered listings and guessing what is actually useful._

StudySpot is an open-source search demo for discovering cafés and other third places across New York City. The goal is to make finding a useful place feel immediate: search by a name, category, or neighborhood and get a small, consistent set of results derived from NYC Open Data.

> [!IMPORTANT]
> StudySpot is currently a scaffold. The frontend, FastAPI liveness endpoint, local Turso configuration, Meilisearch service, CI, Vercel deployment, and empty data boundary are in place. Study-spot routes, data ingestion, Turso loading, indexing, and search behavior are not implemented yet.

## How will it work?

=======
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

StudySpot is an open-source search demo for discovering cafés and other third places across New York City. The goal is to make finding a useful place feel immediate: search by a name, category, or neighborhood and get a small, consistent set of results derived from NYC Open Data.

> [!IMPORTANT]
> StudySpot is currently a scaffold. The frontend, FastAPI liveness endpoint, local Turso configuration, Meilisearch service, CI, Vercel deployment, and empty data boundary are in place. Study-spot routes, data ingestion, Turso loading, indexing, and search behavior are not implemented yet.

## How will it work?

>>>>>>> origin/staging
StudySpot is designed as a small modular monolith with two deployed applications and a versioned public-data snapshot:

```text
Browser -> SvelteKit -> FastAPI -> Turso

NYC Open Data -> ingest.py -> spots.json -> Turso
                                      \-> search index
```

The [Svelte 5](https://svelte.dev/) frontend owns the search experience. A [FastAPI](https://fastapi.tiangolo.com/) service provides the HTTP boundary. [Turso](https://turso.tech/) is the selected serving database. The normalized NYC Open Data snapshot remains the reproducible source used to load Turso and rebuild any search index.

Local development uses Docker Compose for the browser app, API, and Meilisearch. The backend receives a local `file:` URL and reserves a named volume for its embedded Turso database, so no separate database process or port is required. On [Vercel](https://vercel.com/), FastAPI will connect to Turso Cloud over the network with environment-scoped credentials. The database adapter is not implemented yet.

The shared study-spot summary contract is intentionally small:

```json
{
  "id": "string",
  "name": "string",
  "category": "cafe",
  "address": "string",
  "neighborhood": "string",
  "borough": "string",
  "latitude": 40.7128,
  "longitude": -74.006
}
```

The planned public routes are `GET /spots`, `GET /spots/{id}`, and `GET /spots/search?q=coffee`. Today, only `GET /health/live` is available.

<<<<<<< HEAD
### FAQ

**Why make this?** Cafés and public gathering places are spread across separate city datasets and listings. StudySpot explores what happens when candidate third places have one predictable shape and one fast search interface.

**Why Turso?** It keeps local development lightweight with an embedded database file while giving stateless Vercel functions a managed remote database. Its SQLite-compatible SQL also fits a small, reproducible public dataset without operating another database server.

**Why keep Meilisearch locally?** It provides a realistic integration target for dedicated typo-tolerant search. Its index is derived data, so the first release can build a smaller in-memory index from the packaged dataset instead of operating a permanent search server.

**Where will the data come from?** The first dataset will use NYC Open Data records for cafés and other public third places. The intentionally small [`data/`](data/) scaffold will contain one importer, its tests, and the generated `spots.json` dataset.

**Does every result have Wi-Fi, outlets, or quiet seating?** Not necessarily. StudySpot presents candidate places to meet or study and only claims amenities explicitly supported by the source data.

=======
>>>>>>> origin/staging
## Development

The simplest setup only requires Git and Docker Compose 2.23 or newer:

```shell
docker compose up --build --watch
```

Open <http://localhost:7500>. Source changes are synchronized into the frontend and backend containers; dependency changes rebuild only the affected image.

For a pinned toolchain, use [Nix](https://nixos.org/). You will still need a running Docker engine.

```shell
nix develop
just setup
just check
```

Developers with `direnv` can run `direnv allow` once to activate the flake automatically when entering the repository.

Without Nix, install Bun, Python 3.12, uv, just, pre-commit, Git, and Docker, then run `just setup` followed by `just check`. Use `just --list` to see every supported repository command.

### Running the complete system

Build and start all three container services with live source updates:

```shell
just dev
```

Or start them in the background and wait for their health checks:

```shell
just start
```

Once healthy, the services are available at:

| Service | Local address |
|---|---|
| Frontend | <http://localhost:7500> |
| API liveness | <http://localhost:7501/health/live> |
| Meilisearch | <http://localhost:7502> |
| Documentation (`just docs`) | <http://localhost:7503> |

Follow logs with `just logs`, stop services while preserving local data with `just shutdown`, or remove the local Turso and Meilisearch volumes with `just clean`.

### Running one application

Run the frontend development server:

```shell
just dev-frontend
```

Run the backend development server:

```shell
just dev-backend
```

The frontend proxies `/api/*` requests to FastAPI during local development.

### Loading data

The data boundary is scaffolded in [`data/`](data/): `ingest.py` will normalize NYC Open Data into `spots.json`, and `test_ingest.py` will verify the mapping. The importer is not implemented, so `spots.json` currently contains an empty array. Loading that snapshot into Turso and deriving any search index remain separate backend concerns.

### Checks

Verify the toolchain, Docker daemon, Compose configuration, formatting, linting, type checking, production frontend build, and warning-strict documentation build:

```shell
just check
```

Run `just nix-check` to validate the pinned development environment. Tests will be added beside the behavior they verify; the scaffold deliberately contains no placeholder test suite.

## Deployment

Vercel's Git integration owns normal deployments:

- feature pull requests receive isolated Preview deployments;
- pushes to `staging` update the shared staging deployment; and
- pushes to `main` update production.

The Vercel deployment status is a required pull-request check. GitHub Actions runs repository, container, documentation, and Nix checks, but does not perform a second deployment.

Create an out-of-band Vercel preview deployment with:

```shell
just deploy-preview
```

Deploy the current revision directly to production only for an explicit manual release or recovery:

```shell
just deploy-production
```

The project uses Vercel Services to deploy the SvelteKit frontend and FastAPI backend together. Feature pull requests target `staging`; release pull requests merge `staging` into `main`. Preview deployments will use the staging Turso database, while production uses a separate database and token. See the [deployment guide](docs/source/deployment.md) for the environment model and rollback behavior.

## Documentation

The documentation is written in MyST Markdown, built with Sphinx, and rendered with the Furo theme. Sources live in [`docs/source/`](docs/source/).

Run `just docs`, then open <http://localhost:7503>. The command builds the documentation before starting the local server.

<<<<<<< HEAD
Documentation from `main` is published to <https://2spacemasterrace.github.io/studyspot/>.
=======
Documentation is published alongside the staging app at <https://dev-studyspot-nyu.vercel.app/docs/>.
>>>>>>> origin/staging

Useful starting points include the [architecture](docs/source/architecture.md), [local development](docs/source/local-development.md), [deployment](docs/source/deployment.md), [testing](docs/source/testing.md), and [contribution guide](CONTRIBUTING.md).

## Technology

- **Frontend:** Svelte 5, TypeScript, SvelteKit, Vite, Tailwind CSS, Bun
- **Backend:** Python 3.12, FastAPI, uv
- **Data source:** NYC Open Data
- **Database:** Turso locally and Turso Cloud on Vercel
- **Search integration:** Meilisearch
- **Operations:** Nix, Docker Compose, just, pre-commit, Vercel, GitHub Actions
- **Checks:** Prettier, ESLint, svelte-check, Ruff, ty, pytest

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing the repository. Shared contract changes need review from every affected owner.

## License

StudySpot is available under the [MIT License](LICENSE).
