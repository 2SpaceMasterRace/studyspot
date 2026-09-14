set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

# Install locked application and documentation dependencies and repository hooks.
setup:
    cd src/frontend && bun install --frozen-lockfile
    cd src/backend && uv sync --frozen
    uv sync --project docs --frozen
    uv run --project src/backend pre-commit install --hook-type pre-commit --hook-type pre-push

# Verify the local toolchain, Docker daemon, Compose file, and Watch support.
doctor:
    bun --version
    python3.12 --version
    uv --version
    docker --version
    docker compose version
    just --version
    docker info >/dev/null
    docker compose config --quiet
    docker compose watch --help >/dev/null

# Start the frontend scaffold.
dev-frontend:
    cd src/frontend && bun run dev

# Start the backend scaffold.
dev-backend:
    cd src/backend && uv run uvicorn studyspot_api.main:app --app-dir src --reload

# Build and start the complete local system with live source updates.
dev:
    docker compose up --build --watch

# Start the complete local system in the background.
up:
    docker compose up --build --detach --wait

# Stop the local system without deleting data.
down:
    docker compose down

# Follow logs from the local system.
logs:
    docker compose logs --follow

# Stop the local system and delete its local database and search data.
clean:
    docker compose down --volumes --remove-orphans

# Format supported source files.
format:
    cd src/frontend && bun run format
    cd src/backend && uv run ruff format .

# Run every check currently supported by the scaffold.
check: audit check-frontend check-backend check-docs

# Build the Sphinx documentation and fail on warnings.
check-docs:
    uv run --project docs sphinx-build --fail-on-warning --keep-going --builder html docs/source docs/build/html

# Build the Sphinx documentation.
docs:
    uv run --project docs sphinx-build --builder html docs/source docs/build/html

# Build and serve the documentation at http://localhost:8001.
docs-serve: docs
    python3.12 -m http.server 8001 --bind 127.0.0.1 --directory docs/build/html

# Validate the Nix development environment.
nix-check:
    nix --extra-experimental-features "nix-command flakes" flake check --print-build-logs

# Create a Vercel preview deployment.
deploy-preview:
    bunx vercel@59.16.0 deploy

# Build and deploy using the staging branch's Vercel preview configuration.
deploy-staging:
    bunx vercel@59.16.0 pull --yes --environment=preview --git-branch=staging
    bunx vercel@59.16.0 build
    bunx vercel@59.16.0 deploy --prebuilt --meta githubDeployment=1 --meta githubCommitRef=staging

# Deploy the current revision to Vercel production.
deploy-production:
    bunx vercel@59.16.0 deploy --prod

# Check frontend formatting, linting, types, and production compilation.
check-frontend:
    cd src/frontend && bun run lint
    cd src/frontend && bun run check
    cd src/frontend && bun run build

# Check backend formatting, linting, and types.
check-backend:
    cd src/backend && uv run ruff format --check .
    cd src/backend && uv run ruff check .
    cd src/backend && uv run ty check

# Verify required scaffold files and forbidden generated files.
audit:
    test -f AGENTS.md
    test -f CLAUDE.md
    test -f contracts/README.md
    test -f src/frontend/AGENTS.md
    test -f src/backend/AGENTS.md
    test -f compose.yaml
    test -f src/frontend/Dockerfile
    test -f src/backend/Dockerfile
    test -f docs/pyproject.toml
    test -f docs/.python-version
    test -f docs/README.md
    test -f docs/uv.lock
    test -f docs/source/conf.py
    test -f docs/source/index.md
    test -f docs/source/docker.md
    test -f docs/source/nix.md
    test -f flake.nix
    test -f flake.lock
    test -f .github/workflows/ci.yml
    test -f .github/branch-protection.json
    test -f .github/workflows/compose.yml
    test -f .github/workflows/docs.yml
    test -f .github/workflows/nix.yml
    test -f vercel.json
    test -f .vercelignore
    test ! -f src/frontend/drizzle.config.ts
    test ! -f src/frontend/auth-schema.ts
    test ! -f src/frontend/compose.yaml
