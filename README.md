# [StudySpot](https://studyspot-nyu.vercel.app/)

_I just want somewhere nearby to study, but finding a library or campus space means checking scattered websites and guessing what is actually useful._

StudySpot is an open-source search demo for discovering study spaces across NYU and New York City. The goal is to make finding a useful place feel immediate: search by a library, building, or neighborhood and get a small, consistent set of results instead of hunting through separate catalogs.

> [!IMPORTANT]
> StudySpot is currently a scaffold. The frontend, FastAPI liveness endpoint, local PostgreSQL/PostGIS and Meilisearch services, CI, and Vercel deployment are in place. Study-spot routes, dependency readiness, migrations, data import, indexing, and search behavior are not implemented yet.

## How will it work?

StudySpot is designed as a small modular monolith with two deployed applications and a versioned public-data snapshot:

```text
Browser -> SvelteKit -> FastAPI -> normalized NYC/NYU data
                                      -> in-memory search index
```

The [Svelte 5](https://svelte.dev/) frontend owns the search experience. A [FastAPI](https://fastapi.tiangolo.com/) service provides the HTTP boundary. The first release will package normalized public NYC and NYU data with the application and build its runtime search structures from that reproducible snapshot.

Local development uses Docker Compose so the browser app, API, PostgreSQL/PostGIS, and Meilisearch start as one topology. The database and external search engine remain available for integration work, but the first release does not require their state to survive. The frontend and API deploy together on [Vercel](https://vercel.com/) without another hosting provider.

The shared study-spot summary contract is intentionally small:

```json
{
  "id": "string",
  "name": "string",
  "address": "string",
  "neighborhood": "string",
  "borough": "string",
  "university": null,
  "latitude": 40.7128,
  "longitude": -74.006
}
```

The planned public routes are `GET /spots`, `GET /spots/{id}`, and `GET /spots/search?q=bobst`. Today, only `GET /health/live` is available.

### FAQ

**Why make this?** Study spaces are spread across university buildings, public libraries, and separate information systems. StudySpot explores what happens when that information has one predictable shape and one fast search interface.

**Why keep PostgreSQL and PostGIS locally?** They provide the intended path for durable data and advanced geographic queries once StudySpot stores user-generated or non-reproducible state. Public source data does not require that infrastructure for the first release.

**Why keep Meilisearch locally?** It provides a realistic integration target for dedicated typo-tolerant search. Its index is derived data, so the first release can build a smaller in-memory index from the packaged dataset instead of operating a permanent search server.

**Where will the data come from?** The data layer is reserved for imports from publicly available NYC library data and NYU building data. Importers, migrations, and seed files have not landed yet; they will live in [`data/`](data/).

**Can I add another school or city?** That is a natural future direction, but the current scope is the NYC and NYU demo. New sources should normalize into the shared contract rather than introduce source-specific fields at the HTTP boundary.

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

Build and start all four services with live source updates:

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
| PostgreSQL | `localhost:7502` |
| Meilisearch | <http://localhost:7503> |
| Documentation (`just docs`) | <http://localhost:7504> |

Follow logs with `just logs`, stop services while preserving local data with `just shutdown`, or remove the local PostgreSQL and Meilisearch volumes with `just clean`.

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

There is no supported download or seed command yet. The planned import code belongs in `data/seeds/`, database migrations in `data/migrations/`, and search indexing in `src/backend/src/studyspot_api/search/`. When these workflows are implemented, their public commands will be added to the `justfile` and documented here.

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

The project uses Vercel Services to deploy the SvelteKit frontend and FastAPI backend together. Feature pull requests target `staging`; release pull requests merge `staging` into `main`. See the [deployment guide](docs/source/deployment.md) for environment configuration, stateful dependencies, and rollback instructions.

## Documentation

The documentation is written in MyST Markdown, built with Sphinx, and rendered with the Furo theme. Sources live in [`docs/source/`](docs/source/).

Run `just docs`, then open <http://localhost:7504>. The command builds the documentation before starting the local server.

Documentation from `main` is published to <https://2spacemasterrace.github.io/studyspot/>.

Useful starting points include the [architecture](docs/source/architecture.md), [local development](docs/source/local-development.md), [deployment](docs/source/deployment.md), [testing](docs/source/testing.md), and [contribution guide](CONTRIBUTING.md).

## Technology

- **Frontend:** Svelte 5, TypeScript, SvelteKit, Vite, Tailwind CSS, Bun
- **Backend:** Python 3.12, FastAPI, uv
- **Data and search:** PostgreSQL with PostGIS, Meilisearch
- **Operations:** Nix, Docker Compose, just, pre-commit, Vercel, GitHub Actions
- **Checks:** Prettier, ESLint, svelte-check, Ruff, ty, pytest

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and the nearest `AGENTS.md` before changing an owned area. Shared contract changes need review from every affected owner.

## License

StudySpot is available under the [MIT License](LICENSE).
