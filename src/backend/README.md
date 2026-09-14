# StudySpot API

This uv project contains the FastAPI application composition root and process liveness endpoint. Routes for NYC café and public-third-place records, the Turso adapter, and the dataset loader remain unimplemented.

```shell
uv sync
uv run uvicorn studyspot_api.main:app --app-dir src --reload
uv run ruff check .
uv run ty check
```

The API engineer owns `src/studyspot_api/spots/`, including the Turso repository boundary. The search engineer owns `src/studyspot_api/search/`. Repository integration owns the application composition root and health endpoints.
