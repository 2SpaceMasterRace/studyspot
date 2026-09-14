# Testing

Tests live with the code they verify.

| Scope | Location | Runner |
|---|---|---|
| Frontend components | `src/frontend/src/**/*.spec.ts` | Vitest |
| Backend API | `src/backend/tests/` | pytest |
| Turso repository and loader | Beside the backend adapter | pytest with a temporary local database |
| Data import | `data/test_ingest.py` | Python tests (planned) |
| Full system | `tests/e2e/` | Playwright |

Run every currently supported check:

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

The data test module is currently only a placeholder. The Turso milestone must test schema creation, idempotent loading, query behavior, and error mapping against a temporary local database without cloud credentials. The staging deployment will verify the same adapter contract over the remote Turso transport. Each product milestone adds meaningful tests for its public behavior. Once the first suites land, a `just test` command and the pre-push gate must run them.
