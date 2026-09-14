# HTTP API

The FastAPI application is available directly at `http://localhost:7501` and through the frontend proxy under `http://localhost:7500/api`.

## Implemented route

`GET /health/live` reports whether the API process can serve requests. It intentionally does not contact Turso or Meilisearch.

```json
{
  "status": "ok"
}
```

## Planned routes

- `GET /spots`
- `GET /spots/{id}`
- `GET /spots/search?q=coffee`
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
