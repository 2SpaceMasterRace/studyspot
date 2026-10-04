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
Meilisearch relevance order. It remains available for text-only callers. Blank
GET queries return HTTP 422.

`POST /spots/search` applies text, distance, and hours filters together. The
body accepts optional `q`, `latitude`, `longitude`, `radius_miles`, and
`open_now` fields:

```json
{
  "q": "coffee",
  "latitude": 40.7295,
  "longitude": -73.9965,
  "radius_miles": 1,
  "open_now": true
}
```

An empty `q` searches all spots, so filters work without text. Coordinates
must be provided together; radius requires coordinates and must be greater
than zero and no more than 25 miles. The API applies both filters before the
20-result limit and preserves relevance order. Each result includes
`distance_miles` when coordinates were supplied and `hours_status` (`open`,
`closed`, or `unknown`). Distance is a straight-line estimate. `open_now`
includes only records with a known open status at request time; missing or
unparseable hours are excluded. Hours are based on published OpenStreetMap
expressions and may differ from temporary closures.

Invalid filter requests return HTTP 422. An unavailable search service returns
HTTP 503. The API does not contact Meilisearch during startup.

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

The first records will represent cafés and other public third places from NYC Open Data. They are candidate gathering and study locations; the API must not imply that unverified amenities are available. The eight-field summary remains the GET response; filtered POST results add only computed distance and hours status. Changes to either public response require review from frontend, API, data, and search owners.
