# Contributing to StudySpot

Thank you for taking the time to contribute. StudySpot welcomes bug fixes, features,
documentation improvements, tests, and code review.

Before starting, confirm the issue's public contract and definition of done. Shared contract
or root configuration changes affect multiple parts of the project, so ask the affected owners
to review them.

## Project structure

```text
studyspot/
├── .github/
│   ├── ISSUE_TEMPLATE/          # Bug and feature request templates
│   ├── workflows/               # GitHub Actions checks and documentation publishing
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── branch-protection.json   # Required checks and protected-branch settings
├── contracts/                   # Shared schemas and representative API data
├── data/                        # NYC Open Data ingestion and normalized spots snapshot
│   ├── ingest.py
│   ├── spots.json
│   └── test_ingest.py
├── docs/
│   ├── source/                  # MyST Markdown and Sphinx configuration
│   ├── pyproject.toml
│   └── uv.lock
├── src/
│   ├── backend/                 # FastAPI application and backend tests
│   │   ├── src/studyspot_api/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── uv.lock
│   └── frontend/                # SvelteKit application and frontend tests
│       ├── src/
│       ├── static/
│       ├── package.json
│       └── bun.lock
├── tests/e2e/                   # Full browser-to-API tests
├── compose.yaml                 # Local frontend, API, and Meilisearch services
├── flake.nix                    # Pinned Nix development environment
├── justfile                     # Canonical development commands
└── vercel.json                  # Vercel frontend and backend deployment configuration
```

Tests live with the behavior they verify: frontend tests belong beside frontend components,
backend tests belong in `src/backend/tests/`, data-import tests belong in `data/`, and complete
user-flow tests belong in `tests/e2e/`.

The shared contract in `contracts/` is the boundary between the frontend, API, data importer,
database, and search implementation. Coordinate changes to it with every affected owner. Tool
configuration stays with its relevant package; repository-wide commands belong in `justfile`.

## Making changes

### Create a branch

Feature work starts from `staging`, not `main`. Update `staging`, then create a short-lived branch
for one issue:

```shell
git switch staging
git pull origin staging
git switch -c feat/short-description
```

Use a short, descriptive branch name. Useful prefixes include `feat/`, `fix/`, `docs/`, `test/`,
and `refactor/`.

### Keep the change focused

- Stay within the issue's ownership boundary when possible.
- Add dependencies only when the change uses them, and commit the appropriate lockfile.
- Add or update tests for changed behavior.
- Update documentation when behavior, setup, configuration, or a public contract changes.
- Never commit credentials, `.env` files, local databases, or generated search data. Copy
  `.env.example` to `.env` only when local overrides are needed.
- Use `just clean` carefully: it stops the Compose services and deletes their local Turso and
  Meilisearch volumes.

Write small commits in the imperative mood:

```text
add neighborhood filter to spot search
fix API liveness error response
document local Turso configuration
```

Avoid vague messages such as `updates`, `fixed stuff`, or `WIP` in the final branch history.

### Check the change

Set up the locked dependencies and Git hooks once:

```shell
just setup
```

If you use Nix, enter `nix develop` first. Without Nix, install the prerequisites listed in the
README: Bun, Python 3.12, uv, just, pre-commit, Git, and Docker Compose 2.23 or newer.

Before pushing, run the repository's complete supported check suite:

```shell
just check
```

This verifies the toolchain and Compose configuration, checks and builds the frontend, formats,
lints, and type-checks the backend, and builds the Sphinx documentation with warnings treated as
errors. Also run the tests relevant to your change. For suites that currently exist, use:

```shell
cd src/frontend && bun run test
cd src/backend && uv run pytest
```

Use `just start` for a local container smoke test, `just dev` for live source updates, and
`just nix-check` when changing the Nix environment. See `just --list` for all supported commands.

## Opening a pull request

1. Push the feature branch and open a pull request into `staging`.
2. Link the issue with a closing keyword such as `Closes #123`.
3. Complete `.github/PULL_REQUEST_TEMPLATE.md`: explain the rationale, summarize the changes,
   describe the tests run, and identify user-facing or breaking API changes.
4. Review the Vercel Preview deployment for user-facing changes. Include screenshots when they
   help reviewers evaluate the result.
5. Wait for all required checks to pass and resolve every review conversation before merging.
6. Do not push feature work directly to `staging` or `main`.

Keep pull requests small and focused. If a change is too large to review comfortably, divide it
into independently useful pull requests. Respond to every review comment; if you disagree with a
suggestion, explain the tradeoff instead of silently ignoring it.

Use this checklist before requesting review:

- [ ] The branch started from and is up to date with `staging`.
- [ ] The pull request closes or links the relevant issue.
- [ ] `just check` passes locally.
- [ ] Relevant behavioral tests pass, and new behavior has appropriate coverage.
- [ ] User-facing or contract changes are documented.
- [ ] No credentials, `.env` files, local databases, or generated search indexes are committed.
- [ ] The Vercel Preview has been checked when the change affects deployed behavior.
- [ ] All review conversations are resolved.

Release pull requests merge `staging` into `main` after the shared staging deployment has been
verified. If an emergency fix lands on `main`, merge it back into `staging` immediately so the
branches do not diverge.

## Reporting issues

Search [existing issues](https://github.com/2SpaceMasterRace/studyspot/issues) before opening a
new one. Use the repository's bug report or feature request template.

A useful bug report includes:

- a concise description of the problem;
- exact steps and commands that reproduce it;
- expected and actual behavior;
- complete error output or relevant logs;
- screenshots for visual problems;
- operating system, runtime versions, and relevant package versions; and
- the smallest reproduction you can provide.

A useful feature request explains the user problem, why existing behavior does not solve it, the
proposed outcome, and any public contract or user-interface changes. Include a concrete example
when possible. Do not include secrets, access tokens, private deployment URLs, or sensitive data
in issues, logs, or screenshots.

Security vulnerabilities should not be disclosed in a public issue. Contact the maintainers
privately through the repository owner's security-reporting channel instead.

## CI/CD

StudySpot uses GitHub Actions for validation and documentation publishing. Vercel's Git
integration is the only automatic application deployment path; CI does not store a Vercel token
or perform a duplicate deployment.

| Check or workflow | What it does | When it runs |
|---|---|---|
| `Repository checks` | Installs locked dependencies and runs `just check` | Every pull request and pushes to `staging` or `main` |
| `Container smoke test` | Builds the Compose services, waits for health checks, and probes the frontend and API | Every pull request and pushes to `staging` or `main` |
| `Nix flake` | Evaluates the pinned Nix development environment | Every pull request and pushes to `staging` or `main` |
| `Documentation` | Builds warning-strict Sphinx docs and publishes them to GitHub Pages | Documentation changes merged to `main`, or manual dispatch |
| `Vercel` | Creates application deployments through the repository's Git integration | Pull requests and configured branch deployments |

`Repository checks`, `Container smoke test`, `Nix flake`, and `Vercel` are protected-branch
requirements. Branches must also be current, review conversations must be resolved, and force
pushes and branch deletion are disabled.

The deployment flow is:

- feature pull requests receive isolated Vercel Preview deployments;
- pushes to `staging` update the shared staging deployment;
- release pull requests merge `staging` into `main`; and
- pushes to `main` update production and publish changed documentation to GitHub Pages.

Preview and staging deployments use staging services and credentials; production uses separate
Turso configuration. Never copy production secrets into a feature environment. For an explicit
manual preview or recovery deployment, maintainers can use `just deploy-preview` or
`just deploy-production`; normal contributions should rely on the Git integration.
