# Testing

Tests live with the code they verify.

| Scope | Location | Runner |
|---|---|---|
| Frontend components | `src/frontend/src/**/*.spec.ts` | Vitest |
| Study-spot routes | `src/backend/spots/tests/test_spots_api.py` | pytest with pytest-django |
| Dataset loader | `src/backend/spots/tests/test_load_spots.py` | pytest with pytest-django |
| Data import | `data/test_ingest.py` | pytest |
| Full system | `tests/e2e/` | Playwright |

Run every currently supported check:

```shell
just check
```

This verifies the toolchain and Compose configuration, then runs the frontend formatting/linting/type checks/build, the backend formatting/linting/type checks, Django's own system checks, the proof that the models and migrations agree, and a warning-free Sphinx documentation build.

Run the test suites:

```shell
just start-db
just test
```

Both `just check` and `just test` run on every pull request and on the pre-push hook.

## The tests need Postgres

The backend suite runs against a real Postgres rather than a substitute, because the behaviour under test is Postgres behaviour: the database's own case folding on both sides of every case-insensitive filter, the expression indexes those filters need, and the check constraints the loader relies on the database to enforce. A test double would pass while leaving exactly those properties unverified.

`just start-db` is enough to satisfy that. pytest-django creates and drops its own test database on the same server, so the suite never touches the one `just load-data` fills, and no fixture has to clean up after itself. CI does the same thing with a Postgres service container.

Nothing else has to be exported. `pyproject.toml` points pytest at `studyspot.settings_test`, which supplies the debug flag and a test secret key and then defers to the real settings module, so `uv run pytest` works in a fresh checkout and the suite still exercises the configuration every other environment uses. That cannot be done from a `conftest.py`: pytest-django sets Django up from `pytest_load_initial_conftests`, before any conftest module is imported. An explicit `DATABASE_URL` still wins, which is how CI points the suite at its service container.

`just test` also runs the data suite in `data/`. pytest exits 5 when it collects nothing, which `just test` treats as success rather than failure: the importer and its tests arrive on their own branch, and the API suite should not fail because they have not landed yet.

## Validating the Terraform

```shell
just infra-check
```

This formats and validates `infra/terraform/` without touching an AWS account. `terraform validate` evaluates the deployment package's hash, so build the package with `just aws-build` first, or create a placeholder at `infra/build/studyspot-api.zip`. CI creates a placeholder, which is why its Terraform job needs no credentials.

## Container smoke test

```shell
just start
curl --fail http://localhost:7500/
curl --fail http://localhost:7501/health/live
just shutdown
```

This is the boundary CI's `Container smoke test` probes: that the images build, that every health check passes in order, and that both public boundaries answer.

## What the suites cover

The route tests exercise the published contract end to end: the pagination envelope and its `total`, `count`, and `has_more` fields, every filter, deterministic ordering across pages, LIKE wildcards matched literally, the structured error envelope, `422` for an unknown query parameter, identifiers that keep their dataset prefix through URL routing, and routes that reverse without a trailing slash. They assert the shape of each response and not only its contents, because that shape is what the frontend, the importer, and any future search index agree on — and because they are the check that the move from a previous framework did not quietly change the API.

The loader tests cover repeatable loading, records dropped upstream disappearing from the table, an empty snapshot emptying it, borough casing and spacing normalization, and the rejection of any record the API could not serve — including the proof that a rejected snapshot leaves the previous contents untouched.

The data tests cover source mapping, coordinate and borough validation, university derivation, and the committed `spots.json` itself.

Each product milestone adds meaningful tests for its public behavior. Readiness reporting and search have none yet, because neither is implemented.
