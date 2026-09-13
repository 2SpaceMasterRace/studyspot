# Backend Agent Guide

Instructions for code under `src/backend/`. Explicit user instructions override this file.

## Mission

Build the smallest production-credible FastAPI backend for StudySpot search.

Current boundaries:

- `GET /spots`
- `GET /spots/{id}`
- `GET /spots/search?q=bobst`
- PostgreSQL is the authoritative store.
- Meilisearch is a rebuildable search index.
- The API must support an in-memory repository for isolated tests.

Do not add authentication, background workers, Redis, Kafka, WebSockets, or unrelated service layers.

## Before Editing

- Read the relevant files before making changes.
- Confirm which public contract the change affects.
- Preserve the shared study-spot schema in `contracts/`.
- Prefer the smallest complete change.
- Do not create abstractions for hypothetical future features.
- Ask before adding dependencies or changing HTTP response shapes.
- Leave unrelated work unchanged.

## Package Boundaries

- `studyspot_api/spots/` owns study-spot models, repositories, and HTTP behavior.
- `studyspot_api/search/` owns Meilisearch indexing and querying.
- The application entry point owns only application creation, router registration, configuration, and lifecycle.
- Database migrations and seed scripts belong under `data/`.
- Tests belong under `src/backend/tests/`.

Keep dependency direction simple:

```text
HTTP route
    ↓
application operation
    ↓
repository or search interface
    ↓
PostgreSQL or Meilisearch adapter
```

Routes must not contain SQL, indexing logic, or vendor-specific exception handling.

## Python Standards

- Target Python 3.12.
- Add type annotations to public functions, methods, and important local values.
- Use Pydantic models at HTTP and configuration boundaries.
- Use dataclasses or small value objects for internal domain data when they improve clarity.
- Use `Protocol` for the study-spot repository because both in-memory and PostgreSQL implementations are required.
- Avoid `Any` and unstructured dictionaries when the data has a known shape.
- Parse and validate external input at the boundary.
- Do not silently coerce malformed values into valid domain data.
- Prefer composition over inheritance.
- Keep functions focused and names explicit.
- Use constants for repeated values that carry meaning.
- Never use mutable default arguments.
- Do not use `assert` for production validation.
- Do not catch `Exception` unless the application boundary must prevent a crash and the error is logged and translated.
- Chain translated exceptions with `raise ... from exc`.
- Comments should explain why a decision exists.
- Add docstrings to public or non-obvious functions and classes.

## FastAPI Standards

- Use explicit request and response models.
- Declare response models on public routes.
- Keep status codes and error response shapes consistent.
- Return `404` when a study spot does not exist.
- Return `422` for invalid query parameters through FastAPI validation.
- Return a structured `503` when PostgreSQL or Meilisearch is required but unavailable.
- Never expose raw database or Meilisearch exceptions to callers.
- Create external clients during application lifespan and close them during shutdown.
- Give every network operation an explicit timeout.
- Do not perform blocking I/O directly inside asynchronous routes.
- Keep `/health/live` independent of external dependencies.
- Make `/health/ready` report required dependency failures clearly.

## Data and Search Standards

- Use parameterized SQL exclusively.
- Make pagination limits explicit and bounded.
- Make result ordering deterministic.
- Keep PostgreSQL as the source of truth.
- Treat Meilisearch as a projection that can be rebuilt.
- Keep reindexing repeatable.
- Keep seeding idempotent.
- Store latitude and longitude without converting them to formatted strings.
- Preserve nullable `university` values.
- Keep vendor-specific models and exceptions inside their adapters.

## Error Handling

Define narrow application errors for expected failures, such as:

- study spot not found
- database unavailable
- search unavailable
- invalid search request
- indexing failure

Translate infrastructure exceptions once at the adapter boundary. Translate application errors into HTTP responses once at the HTTP boundary.

Log enough context to diagnose a failure without logging secrets or complete dependency payloads.

## Testing

- Test observable behavior through public interfaces.
- Use pytest functions named `test_*`.
- Use the in-memory repository for route and application tests.
- Mock only external boundaries.
- Keep real PostgreSQL and Meilisearch tests in `tests/integration/`.
- Keep the browser-to-API search flow in `tests/e2e/`.
- Mark tests that require external services.
- Never require live internet access for the normal test suite.

For changed behavior, cover:

- the normal result
- malformed or missing input
- empty results
- unknown study-spot IDs
- deterministic ordering
- pagination boundaries
- required dependency failure

Test contracts rather than private helper functions.

## Verification

Run from `src/backend/`:

```shell
uv run ruff format --check .
uv run ruff check .
uv run ty check
```

After the first backend test is added, also run:

```shell
uv run pytest
```

Do not report checks as passing unless their output was observed.

## Change Safety

- Do not add or upgrade dependencies without approval.
- Do not change the shared contract without coordinating with every ticket owner.
- Do not hand-edit generated files.
- Never commit credentials or local environment files.
- Keep commits focused and leave the application runnable after each commit.
- Update documentation when commands, configuration, routes, or public behavior change.
