# StudySpot Agent Guide

## Mission

Ship an instant study-space search demo backed by NYC library and NYU building data. Keep the repository small enough for five engineers to work independently.

The repository has a runnable local container topology and API liveness endpoint. Study-spot routes, dependency readiness, migrations, seeding, indexing, and search behavior are not implemented.

## Product boundaries

The first demo supports discovery and search only. Do not add authentication, maps, Redis, Kafka, Kubernetes, WebSockets, background workers, or unrelated feature modules.

## Stack

- Frontend: Svelte 5, TypeScript, Vite, Tailwind CSS, Bun
- Backend: Python 3.12, FastAPI, uv
- Data: PostgreSQL with PostGIS
- Search: Meilisearch
- Operations: Nix, Docker Compose, just, pre-commit, GitHub Actions
- Checks: Prettier, ESLint, svelte-check, Ruff, ty, pytest

## Ownership boundaries

| Area | Primary paths |
|---|---|
| Frontend | `src/frontend/` |
| HTTP API | `src/backend/src/studyspot_api/spots/` |
| Search | `src/backend/src/studyspot_api/search/` |
| Data | `data/` |
| Integration | Root files, `.github/`, `docs/`, `tests/e2e/` |
| Shared contract | `contracts/` |

Read the nearest nested `AGENTS.md` before editing within one of these areas. Shared contract changes require review from affected owners.

## Shared contract

Study-spot summaries have exactly these fields:

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

HTTP boundaries:

- `GET /spots`
- `GET /spots/{id}`
- `GET /spots/search?q=bobst`

## Working rules

1. Inspect the worktree before editing and preserve unrelated changes.
2. Implement the smallest complete behavior required by the active ticket.
3. Add dependencies only when working code uses them.
4. Keep types explicit at network, database, environment, and sample-data boundaries.
5. Keep tests beside the code they verify; reserve `tests/e2e/` for full-system behavior.
6. Run the checks listed in the nearest `AGENTS.md` before handing off work.
7. Update documentation when a supported command, boundary, or ownership rule changes.
8. Never commit secrets, generated build output, local databases, or editor-specific agent instructions.
9. Do not bypass a failing check or hide failures with shell fallbacks.

## Repository commands

Run `just --list` from the repository root. Only listed commands are supported. If a command is missing, add it alongside the behavior it runs.

- `just dev`: build and start the complete local system in the foreground.
- `just start`: build, start, and wait for a healthy local system in the background.
- `just shutdown`: stop containers while preserving local data.
- `just clean`: stop containers and delete local PostgreSQL and Meilisearch data.
- `just check`: verify the toolchain and run the repository's supported static checks and builds.
- `just docs`: build and serve the Sphinx documentation at `localhost:7504`.
- `just nix-check`: validate the pinned Nix development environment.
- `just deploy-preview`: create a Vercel preview deployment.
- `just deploy-production`: deploy the current revision to Vercel production.

## Definition of ready for review

- The requested behavior works through its public boundary.
- Relevant formatting, linting, type checks, and tests pass.
- Errors are explicit and actionable.
- No unrelated architecture or dependencies were added.
- The commit is focused and uses an imperative message.
