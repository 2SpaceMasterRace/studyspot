# Testing

Tests live with the code they verify.

| Scope | Location | Runner |
|---|---|---|
| Frontend components | `src/frontend/src/**/*.spec.ts` | Vitest |
| Backend API | `src/backend/tests/` | pytest |
| Data import | `data/tests/` | pytest |
| Full system | `tests/e2e/` | Playwright |

The scaffold does not include placeholder tests. Each ticket adds meaningful tests for its public behavior. Once the first tests land, `just test` and the pre-push test gate must run all existing suites.
