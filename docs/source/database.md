# Turso database

Turso is StudySpot's selected serving database. The connection adapter (`studyspot_api.db`), the `spots` table schema, and the loader (`studyspot_api.spots.loader`) are implemented. Schema migrations and the API query layer are not implemented yet.

## Environment model

| Environment | Database | Connection |
|---|---|---|
| Docker Compose | Embedded file at `/app/.local/studyspot.db` | `TURSO_DATABASE_URL=file:/app/.local/studyspot.db` |
| Native local development | Embedded file at `.local/studyspot.db` | `TURSO_DATABASE_URL=file:.local/studyspot.db` |
| Vercel Preview, including `staging` | `studyspot-staging` in Turso Cloud | Remote URL and token |
| Vercel Production from `main` | `studyspot-production` in Turso Cloud | Separate remote URL and token |

Local files require no authentication token and do not consume hosted usage. Preview and Production must never share a writable database or authentication token. Feature previews may share the rebuildable staging dataset while the API is read-only; revisit isolation before adding writes.

## Python adapter

Follow Turso's current [Python SDK guidance](https://docs.turso.tech/sdk/python/quickstart):

- the `libsql` package handles both the local embedded file and remote Turso
  Cloud access from stateless Vercel functions; and
- both live behind one StudySpot interface (`studyspot_api.db.connect`).

`studyspot_api.db.connect` interprets a local `file:` URL as a filesystem path and passes any other URL plus token to Turso Cloud. A single `libsql` dependency covers both cases, so `pyturso` is not required. The loader's schema tests run against a temporary local database and exercise the same contract the remote boundary must satisfy.

The application configuration has exactly two database variables:

```text
TURSO_DATABASE_URL
TURSO_AUTH_TOKEN
```

`TURSO_AUTH_TOKEN` is empty for a local file and required for Turso Cloud. Never expose either value to browser code; FastAPI owns all database access.

## Data lifecycle

```text
NYC Open Data -> data/ingest.py -> data/spots.json -> Turso loader -> spots table
                                                              \-> search projection
```

`data/spots.json` is the reproducible normalized snapshot. Turso is the serving projection used by API queries. Any Meilisearch index is another projection, not an independent source of truth.

Normal Compose shutdown preserves the local database volume. `just clean` deletes it. That is safe while all records can be rebuilt from `spots.json`. If StudySpot later stores favorites, corrections, accounts, or import cursors, backups and migration compatibility become release requirements.
