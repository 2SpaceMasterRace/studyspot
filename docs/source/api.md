# HTTP API

The FastAPI application is available directly at `http://localhost:7501` and through the frontend proxy under `http://localhost:7500/api`.

## Implemented route

`GET /health/live` reports whether the API process can serve requests. It intentionally does not contact Turso or Meilisearch.

```json
{
  "status": "ok"
}
```

## Search route

`GET /spots/search?q=coffee` trims the query and returns up to 20 summaries in
Meilisearch relevance order. Prefixes and ordinary Meilisearch typo tolerance
are enabled. Blank queries return HTTP 422; an unavailable search service
returns HTTP 503. The API does not contact Meilisearch during startup.

## Planned routes

- `GET /spots`
- `GET /spots/{id}`
- `GET /health/ready`

The readiness route will report required dependency failures. The study-spot routes are public contracts but are not implemented yet.

## Study-spot summary

```json
{
  "id": "string",
  "name": "string",
  "category": "cafe",
  "address": "string",
  "neighborhood": "string",
  "borough": "string",
  "latitude": 40.7128,
  "longitude": -74.006
}
```

The first records will represent cafés and other public third places from NYC Open Data. They are candidate gathering and study locations; the API must not imply that unverified amenities are available. This response shape belongs to the shared contract. Changes require review from frontend, API, data, and search owners.
