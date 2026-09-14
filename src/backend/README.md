# StudySpot API

This uv project contains the FastAPI application, the Turso-backed `spots`
repository, and the Meilisearch search boundary. Search is exposed at
`GET /spots/search?q=...`; `python -m studyspot_api.reindex` rebuilds its
derived index from Turso.

```shell
uv sync
uv run uvicorn studyspot_api.main:app --app-dir src --reload
uv run ruff check .
uv run ty check
```

The API engineer owns `src/studyspot_api/spots/`, including the Turso
repository boundary. The search engineer owns `src/studyspot_api/search/` and
the reindex command. Repository integration owns application composition and
health endpoints.
