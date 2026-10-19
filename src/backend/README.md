# StudySpot API

This uv project holds the Django application that serves the study-spot API.

```text
studyspot/     project configuration: settings, URLs, health, error envelope, middleware
spots/         the shared study-spot model, routes, serializers, migrations, loader
manage.py      Django's command-line entry point
main.py        Vercel entry point
handler.py     AWS Lambda entry points: the API, and a management-command runner
```

One settings module serves every environment and is driven by the environment itself, so there is no settings-per-deployment to keep in sync. The only database variable is `DATABASE_URL`.

```shell
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 127.0.0.1:7501
uv run pytest
uv run ruff check .
uv run ty check
```

The `migrate`, `runserver`, and `pytest` calls all need Postgres running; `just start-db` starts it. The repository commands in the `justfile` (`just migrate`, `just dev-backend`, `just test`, `just load-data`) wrap the same calls and are what CI runs.

Ownership: the API engineer owns `spots/`, including the model that the routes, the loader, and any future search projection share. The search engineer owns the search projection, which does not exist yet. Repository integration owns `studyspot/` and the deployment entry points.

The published contract lives in `docs/source/api.md` and the schema reasoning in `docs/source/database.md`. The route tests assert the shape of every response, because that shape is what the frontend, the importer, and the search index agree on.
