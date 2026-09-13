FROM ghcr.io/astral-sh/uv:0.11.3-python3.12-trixie-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src

EXPOSE 8000

CMD ["uv", "run", "--frozen", "uvicorn", "studyspot_api.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
