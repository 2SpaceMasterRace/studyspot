# Turso database

Turso is StudySpot's selected serving database. The adapter, schema, loader, and study-spot queries are implemented; migrations beyond the initial schema are not.

## Environment model

| Environment | Database | Connection |
|---|---|---|
| Docker Compose | Embedded file at `/app/.local/studyspot.db` | `TURSO_DATABASE_URL=file:/app/.local/studyspot.db` |
| Native local development | Embedded file at `.local/studyspot.db` | `TURSO_DATABASE_URL=file:.local/studyspot.db` |
| Vercel Preview, including `staging` | `studyspot-staging` in Turso Cloud | Remote URL and token |
| Vercel Production from `main` | `studyspot-production` in Turso Cloud | Separate remote URL and token |

Local files require no authentication token and do not consume hosted usage. Preview and Production must never share a writable database or authentication token. Feature previews may share the rebuildable staging dataset while the API is read-only; revisit isolation before adding writes.

## Python adapter

The adapter follows Turso's [Python SDK guidance](https://docs.turso.tech/sdk/python/quickstart):

- `pyturso` serves the local embedded database;
- the `libsql` package serves the Turso Cloud databases from stateless Vercel functions; and
- both sit behind one StudySpot repository interface.

`studyspot_api.spots.database.Database` interprets a local `file:` URL as a filesystem path for `turso.connect()` and passes a hosted URL plus token to `libsql.connect()`. The driver is imported lazily, so a local deployment never loads the remote one. `studyspot_api.spots.repository` holds the interface every deployment satisfies:

```python
class SpotRepository(Protocol):
    def list_spots(self, filters, *, limit, offset) -> tuple[list[Spot], int]: ...
    def get_spot(self, spot_id: str) -> Spot | None: ...
```

Each operation opens and closes its own connection, because neither driver hands out connections that are safe to share across the threads FastAPI runs synchronous endpoints on. Driver failures surface as a `503 database_unavailable` response rather than a stack trace.

`src/backend/tests/test_repository.py` runs the same schema and query contract twice: against a temporary local database, and through the remote `libsql.connect()` call path. The staging deployment verifies the same contract over the real remote transport.

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

## Schema and loading

`src/backend/src/studyspot_api/spots/schema.sql` holds the serving schema. Alongside each contract column the table stores a `_folded` column containing Python `str.casefold()` output, because SQLite's own `lower()` and `LIKE` only fold the ASCII range; filters compare against those columns so case-insensitivity covers every character NYC Open Data contains.

Load or reload the local database with:

```shell
just load-data
```

The loader validates every record against the shared contract before writing it, then replaces the table's contents in one transaction, so the serving table can only ever hold records the API can serve. It is safe to re-run. Pass `--dataset` to load a different snapshot and `--database-url` to target a different database; the auth token is only ever read from the environment, never from the command line.

Normal Compose shutdown preserves the local database volume. `just clean` deletes it. That is safe while all records can be rebuilt from `spots.json`. If StudySpot later stores favorites, corrections, accounts, or import cursors, backups and migration compatibility become release requirements.
