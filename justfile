set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

# Install locked frontend and backend dependencies and repository hooks.
setup:
    cd src/frontend && bun install --frozen-lockfile
    cd src/backend && uv sync --frozen
    uv run --project src/backend pre-commit install --hook-type pre-commit --hook-type pre-push

# Start the frontend scaffold.
dev-frontend:
    cd src/frontend && bun run dev

# Start the backend scaffold.
dev-backend:
    cd src/backend && uv run uvicorn studyspot_api.main:app --app-dir src --reload

# Build and start the complete local system.
dev:
    docker compose up --build

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
check: audit check-frontend check-backend

# Validate the Nix development environment.
nix-check:
    nix flake check --print-build-logs

# Create a Vercel preview deployment.
deploy-preview:
    bunx vercel@59.16.0 deploy

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
    test -f flake.nix
    test -f flake.lock
    test -f .github/workflows/ci.yml
    test -f .github/workflows/compose.yml
    test -f .github/workflows/nix.yml
    test -f vercel.json
    test -f .vercelignore
    test ! -f src/frontend/drizzle.config.ts
    test ! -f src/frontend/auth-schema.ts
    test ! -f src/frontend/compose.yaml
