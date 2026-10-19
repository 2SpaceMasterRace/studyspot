FROM ghcr.io/astral-sh/uv:0.11.3-python3.12-trixie-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY studyspot ./studyspot
COPY spots ./spots
COPY manage.py handler.py ./

EXPOSE 8000

# compose.yaml replaces this to run migrations first. On its own, this is the
# development server: a production container would want gunicorn, which the AWS
# deployment does not need because Lambda invokes the ASGI application directly.
CMD ["uv", "run", "--frozen", "python", "manage.py", "runserver", "0.0.0.0:8000"]
