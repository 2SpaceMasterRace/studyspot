# StudySpot

StudySpot helps students discover study spaces and collaborate across campus and New York City.

> **Status:** The local service topology and API liveness endpoint are ready. Search, study-spot routes, migrations, seeding, and indexing are not implemented yet.

## Quick Start

With Nix installed, enter the pinned development environment and install project dependencies:

```shell
nix develop
just setup
```

Without Nix, install Bun, Python 3.12, uv, just, pre-commit, Git, and Docker manually.

Start the complete local system:

```shell
docker compose up --build
```

Open the frontend at <http://localhost:5173>. The API liveness endpoint is available at <http://localhost:8000/health/live>, PostgreSQL at `localhost:5432`, and Meilisearch at <http://localhost:7700>.

To run only the frontend:

```shell
cd src/frontend
bun install
bun run dev
```

To run only the backend:

```shell
cd src/backend
uv sync
uv run uvicorn studyspot_api.main:app --app-dir src --reload
```

## Technology

- **Frontend:** Svelte, TypeScript, Vite, Tailwind CSS, shadcn-svelte, and TanStack Query
- **Backend:** FastAPI and Python
- **Data and search:** PostgreSQL with PostGIS and Meilisearch
- **Development:** Nix, Docker Compose, uv, Bun, Ruff, ty, pytest, pre-commit, and just
- **Continuous integration:** GitHub Actions

## Team Ownership

| Area | Directory |
|---|---|
| Data ingestion and schema | `data/` |
| Search interface | `src/frontend/` |
| HTTP API | `src/backend/src/studyspot_api/spots/` |
| Search indexing | `src/backend/src/studyspot_api/search/` |
| Integration, CI, and deployment | Root files, `.github/`, and `docs/` |

Shared contracts require team review before they change.

## Documentation

Project documentation lives in `docs/` and is added alongside working behavior.

Deployment instructions live in [`docs/deployment.md`](docs/deployment.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contribution guide.

## License

StudySpot is available under the MIT License. See [`LICENSE`](LICENSE).
