# Testing

Tests live with the code they verify.

| Scope | Location | Runner |
|---|---|---|
| Frontend components | `src/frontend/src/**/*.spec.ts` | Vitest |
| Backend API | `src/backend/tests/` | pytest |
| Turso repository and loader | Beside the backend adapter | pytest with a temporary local database |
| Data import | `data/test_ingest.py` | Python tests (planned) |
| Full system | `tests/e2e/` | Playwright |

Run backend tests with:

```shell
just test
```

Run the real Meilisearch integration suite with:

```shell
just test-search
```

The search command builds a test container in a uniquely named Compose
project with no published ports or shared development volumes. It removes
only that project's resources on exit. Missing or failing Meilisearch causes
the integration test to fail, never skip.

CI runs `just test` in Repository checks and `just test-search` in Search
integration. The integration test runs the installed reindex module against
a temporary Turso database, verifies repeatability, updates, deletions, and
an empty source, then checks prefix, typo, category, neighborhood, address,
and no-match searches. Hosted Turso connection wiring is tested with a mock;
live cloud credentials are not required.

Backend containers use Linux AMD64 (also the CI architecture), including on
Apple Silicon, because the pinned libsql package has no Linux ARM wheel.

Run every supported static and build check:

```shell
just check
```

This verifies the toolchain and Compose configuration, then runs the frontend formatting/linting/type checks/build, backend formatting/linting/type checks, and a warning-free Sphinx documentation build.

Run the local container smoke boundary with:

```shell
just start
curl --fail http://localhost:7500/
curl --fail http://localhost:7501/health/live
just shutdown
```

Repository tests cover schema/row conversion, cleanup, query validation, error
mapping, result order, and fixed public response fields. Integration tests use
deterministic NYC-like rows and a real Compose Meilisearch service.
