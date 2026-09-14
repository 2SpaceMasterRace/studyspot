set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

# Install locked application and documentation dependencies and repository hooks.
setup:
    cd src/frontend && bun install --frozen-lockfile
    cd src/backend && uv sync --frozen
    uv sync --project docs --frozen
    uv run --project src/backend pre-commit install --hook-type pre-commit --hook-type pre-push

# Verify the toolchain and run every supported static check and build.
check:
    bun --version
    python3.12 --version
    uv --version
    docker --version
    docker compose version
    python3.12 -c 'import re, subprocess; value = subprocess.check_output(["docker", "compose", "version", "--short"], text=True).strip(); match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", value); assert match and tuple(map(int, match.groups())) >= (2, 23, 0), f"Docker Compose 2.23.0+ is required, found {value}"'
    just --version
    docker info >/dev/null
    docker compose config --quiet
    docker compose watch --help >/dev/null
    cd src/frontend && bun run lint
    cd src/frontend && bun run check
    cd src/frontend && bun run build
    cd src/backend && uv run ruff format --check .
    cd src/backend && uv run ruff check .
    cd src/backend && uv run ty check
    uv run --project docs sphinx-build --fail-on-warning --keep-going --builder html docs/source docs/build/html

# Start the frontend scaffold.
dev-frontend:
    cd src/frontend && bun run dev -- --host 127.0.0.1 --port 7500

# Start the backend scaffold.
dev-backend:
    cd src/backend && uv run uvicorn studyspot_api.main:app --app-dir src --host 127.0.0.1 --port 7501 --reload

# Build and start the complete local system with live source updates.
dev:
    docker compose up --build --watch

# Start the complete local system in the background.
start:
    docker compose up --build --detach --wait

# Stop the local system without deleting data.
shutdown:
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

# Build and serve the Sphinx documentation at http://localhost:7503.
docs:
    uv run --project docs sphinx-build --builder html docs/source docs/build/html
    python3.12 -m http.server 7503 --bind 127.0.0.1 --directory docs/build/html

# Validate the Nix development environment.
nix-check:
    nix --extra-experimental-features "nix-command flakes" flake check --print-build-logs

# Create a Vercel preview deployment.
deploy-preview:
    bunx vercel@59.16.0 deploy

# Deploy the current revision to Vercel production.
deploy-production:
    bunx vercel@59.16.0 deploy --prod
