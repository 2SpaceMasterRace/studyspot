FROM ghcr.io/astral-sh/uv:0.11.3-python3.12-trixie-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "--frozen", "uvicorn", "studyspot_api.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]

FROM ghcr.io/astral-sh/uv:0.11.3-python3.12-trixie-slim AS test
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY tests ./tests
RUN uv sync --frozen
CMD ["uv", "run", "--frozen", "pytest", "-m", "integration"]

FROM runtime AS application
