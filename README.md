# [StudySpot](https://studyspot-nyu.vercel.app/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

StudySpot is an open-source search demo for discovering cafés and other third places across New York City. The goal is to make finding a useful place feel immediate: search by a name, category, or neighborhood and get a small, consistent set of results derived from NYC Open Data.

> [!IMPORTANT]
> StudySpot is early but no longer empty. The frontend, the Django API, the shared study-spot model and its migrations, the dataset loader, the listing and detail routes, the Meilisearch service, CI, and both deployment targets are in place. The NYC Open Data importer is still a placeholder, so `data/spots.json` is an empty array; indexing and search behavior are not implemented yet.

## How will it work?

StudySpot is designed as a small modular monolith with two deployed applications and a versioned public-data snapshot:

```text
Browser -> SvelteKit -> Django REST Framework -> Postgres

NYC Open Data -> ingest.py -> spots.json -> Postgres
                                      \-> search index
```

The [Svelte 5](https://svelte.dev/) frontend owns the search experience. A [Django](https://www.djangoproject.com/) application with [Django REST Framework](https://www.django-rest-framework.org/) provides the HTTP boundary, and one model defines the study spot that the routes, the loader, and any future search projection all share. [Postgres](https://www.postgresql.org/) is the serving database. The normalized NYC Open Data snapshot remains the reproducible source used to load it and to rebuild any search index.

Local development uses Docker Compose for the browser app, API, Postgres, and Meilisearch. The same Postgres is published on `127.0.0.1:5432`, so a backend run outside Compose uses the same database as one run inside it. Deployments run the same application against the same schema: on [AWS](https://aws.amazon.com/) the API is a Lambda function behind CloudFront with an RDS Postgres instance in private subnets, and on [Vercel](https://vercel.com/) it is a Python service — which has no database until the RDS instance is made publicly reachable.

The shared study-spot summary contract is intentionally small:

```json
{
  "id": "facdb:eec118768e15a5e03d3354abda7b00da",
  "name": "125th Street Library",
  "category": "library",
  "address": "224 East 125 Street, New York, NY 10035",
  "neighborhood": "East Harlem (North)",
  "borough": "Manhattan",
  "latitude": 40.803027,
  "longitude": -73.934853,
  "university": "Touro University - Harlem"
}
```

`GET /spots` and `GET /spots/{id}` are available alongside `GET /health/live`, none of them with a trailing slash. `GET /spots` pages with `limit` and `offset` and filters on `name`, `neighborhood`, `borough`, and `university`. `GET /spots/search?q=coffee` is still planned. See the [HTTP API guide](docs/source/api.md).

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

Build and start all four container services with live source updates:

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
| Postgres | `127.0.0.1:5432` |

The backend applies its migrations before it starts serving, so a fresh checkout gets a working schema without a separate step. Follow logs with `just logs`, stop services while preserving local data with `just shutdown`, or remove the Postgres and Meilisearch volumes with `just clean`.

### Running one application

Run the frontend development server:

```shell
just dev-frontend
```

Run the backend development server, which needs only the database:

```shell
just start-db
just migrate
just dev-backend
```

`just start-db` starts the Postgres container alone and waits for it; `just migrate` brings the schema up to date, and `just makemigrations` generates a migration after a model change. The frontend proxies `/api/*` requests to the Django API during local development.

### Loading data

The data boundary lives in [`data/`](data/): `ingest.py` normalizes NYC Open Data into `spots.json`, and `test_ingest.py` verifies the mapping. Both are still placeholders, and the real importer lands on its own branch. Copy the snapshot into the local database before using the study-spot routes:

```shell
just load-data
```

The loader validates every record against the shared model and replaces the table's contents in one transaction, so it is safe to re-run and the table can only ever hold records the API can serve. Deriving a search index remains a separate backend concern.

### Checks

Verify the toolchain, Docker daemon, Compose configuration, formatting, linting, type checking, production frontend build, and warning-strict documentation build:

```shell
just check
```

Run the backend and data test suites, which need the database running:

```shell
just start-db
just test
```

The suites run against a real Postgres because the schema depends on Postgres behaviour; pytest-django creates and drops its own test database, so loaded data is left alone.

Run `just nix-check` to validate the pinned development environment. Tests live beside the behavior they verify.

## Deployment

There are two targets, and one revision deploys to both.

**Vercel** owns the automatic path through its Git integration:

- feature pull requests receive isolated Preview deployments;
- pushes to `staging` update the shared staging deployment; and
- pushes to `main` update production.

Vercel Services deploy the SvelteKit frontend and the Django application together, splitting on the same `/api/*` boundary the frontend proxy uses locally. The Vercel deployment status is a required pull-request check. Create an out-of-band preview with `just deploy-preview`, or release manually with `just deploy-production`.

**AWS** is the deployment that has a database: CloudFront in front of S3 for the prerendered frontend and a Lambda function for the API, with RDS Postgres in private subnets. It is Terraform in [`infra/`](infra/), applied deliberately from a checkout rather than from CI, which would need long-lived AWS credentials in the repository:

```shell
just aws-init aws-build aws-apply aws-migrate aws-load aws-frontend aws-verify
```

Because the RDS instance has no public endpoint, migrations and data loads run as Lambda invocations, and the Vercel deployment has no database: it serves the frontend and `/api/health/live`, while `/api/spots` answers `503`. [`infra/README.md`](infra/README.md) covers the stack, what it costs, and how to stop the database when it is not in use.

GitHub Actions runs repository, container, documentation, Nix, and Terraform checks, and performs no deployment of its own. Feature pull requests target `staging`; release pull requests merge `staging` into `main`. See the [deployment guide](docs/source/deployment.md) for the environment model and rollback behavior.

## Documentation

The documentation is written in MyST Markdown, built with Sphinx, and rendered with the Furo theme. Sources live in [`docs/source/`](docs/source/).

Run `just docs`, then open <http://localhost:7503>. The command builds the documentation before starting the local server.

Documentation is published alongside the staging app at <https://dev-studyspot-nyu.vercel.app/docs/>.

Useful starting points include the [architecture](docs/source/architecture.md), [local development](docs/source/local-development.md), [deployment](docs/source/deployment.md), [testing](docs/source/testing.md), and [contribution guide](CONTRIBUTING.md).

## Technology

- **Frontend:** Svelte 5, TypeScript, SvelteKit, Vite, Tailwind CSS, Bun
- **Backend:** Python 3.12, Django 5.2, Django REST Framework, uv
- **Data source:** NYC Open Data
- **Database:** Postgres — a container locally, Amazon RDS on AWS
- **Search integration:** Meilisearch
- **Deployment:** Vercel, and AWS (CloudFront, S3, Lambda, RDS) with Terraform
- **Operations:** Nix, Docker Compose, just, pre-commit, GitHub Actions
- **Checks:** Prettier, ESLint, svelte-check, Ruff, ty, pytest, Django system checks, `terraform validate`

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing the repository. Shared contract changes need review from every affected owner.

## License

StudySpot is available under the [MIT License](LICENSE).
