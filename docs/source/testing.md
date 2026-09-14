# Testing

Tests live with the code they verify.

| Scope | Location | Runner |
|---|---|---|
| Frontend components | `src/frontend/src/**/*.spec.ts` | Vitest |
| Backend API | `src/backend/tests/` | pytest |
| Data import | `data/tests/` | pytest |
| Full system | `tests/e2e/` | Playwright |

Run every currently supported check:

```shell
just check
```

This includes repository auditing, frontend formatting/linting/type checks/build, backend formatting/linting/type checks, and a warning-free Sphinx documentation build.

Run the local container smoke boundary with:

```shell
just up
curl --fail http://localhost:7500/
curl --fail http://localhost:7501/health/live
just down
```

The scaffold does not include placeholder tests. Each product milestone adds meaningful tests for its public behavior. Once the first suites land, a `just test` command and the pre-push gate must run them.
