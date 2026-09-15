# Testing

Tests live with the code they verify.

| Scope | Location | Runner |
|---|---|---|
| Frontend components | `src/frontend/src/**/*.spec.ts` | Vitest |
| Backend API | `src/backend/tests/` | pytest |
| Turso repository and loader | Beside the backend adapter | pytest with a temporary local database |
| Data import | `data/test_ingest.py` | pytest |
| Full system | `tests/e2e/` | Playwright |

Run every currently supported check:

```shell
just check
```

This verifies the toolchain and Compose configuration, then runs the frontend formatting/linting/type checks/build, backend formatting/linting/type checks, and a warning-free Sphinx documentation build.

Run the test suites:

```shell
just test
```

Both `just check` and `just test` run on every pull request and on the pre-push hook.

Run the local container smoke boundary with:

```shell
just start
curl --fail http://localhost:7500/
curl --fail http://localhost:7501/health/live
just shutdown
```

The backend suite covers the study-spot routes end to end against a temporary local Turso database: pagination windows, every filter, the structured error envelope, and the OpenAPI surface. The repository contract tests run twice, once against a local database file and once through the remote `libsql.connect()` call path, so both deployments are held to one contract without cloud credentials. The loader tests cover schema creation, idempotent reloading, and the rejection of any record the API could not serve. The data tests cover source mapping, coordinate and borough validation, university derivation, and the committed `spots.json` itself.

The staging deployment verifies the same adapter contract over the real remote Turso transport. Each product milestone adds meaningful tests for its public behavior.
