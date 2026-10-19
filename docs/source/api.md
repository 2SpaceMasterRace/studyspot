# HTTP API

The API is available directly at `http://localhost:7501` and through the frontend proxy under `http://localhost:7500/api`. Deployments publish it under `/api`, and both edges strip that prefix before the request reaches the application, so the routes below are the same everywhere.

No route has a trailing slash, and the application does not redirect one onto the other: `/spots/` is a 404 rather than a 301 to `/spots`.

## Implemented routes

| Route | Purpose |
|---|---|
| `GET /health/live` | Reports whether the API process can serve requests. It intentionally does not contact Postgres or Meilisearch. |
| `GET /spots` | Returns a filtered, paginated page of study spots. |
| `GET /spots/{id}` | Returns one study spot. |

`GET /health/live` returns:

```json
{
  "status": "ok"
}
```

## Study-spot summary

```json
{
  "id": "facdb:eec118768e15a5e03d3354abda7b00da",
  "name": "125th Street Library",
  "category": "library",
  "address": "224 East 125 Street, New York, NY 10035",
  "neighborhood": "East Harlem (North)",
  "borough": "Manhattan",
  "latitude": 40.803027,
  "longitude": -73.934853,
  "university": "Touro University - Harlem"
}
```

The records represent cafés and other public third places from NYC Open Data. They are candidate gathering and study locations; the API must not imply that unverified amenities are available. This response shape belongs to the shared contract. Changes require review from frontend, API, data, and search owners.

`category` currently takes one of `library`, `academic_library`, `university`, or `cafe`. The API does not constrain it: the vocabulary belongs to the importer, and pinning it in the serving schema would put every category change through a migration. `borough` is one of the five borough names and the database refuses any other. `neighborhood` is the 2020 Neighborhood Tabulation Area name and is `null` when NYC Open Data does not place the record in one.

```{important}
`university` is an addition to the previously agreed contract and still needs owner sign-off. It names the institution a spot belongs to, and only for records the importer takes from a curated campus list; it is never inferred, so every other spot leaves it `null`. It is not an endorsement or an access claim: a named campus does not mean the public may use the room.
```

## Listing study spots

`GET /spots` returns one page of spots inside a stable envelope:

```json
{
  "items": [],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "count": 0,
    "total": 1900,
    "has_more": false
  }
}
```

`total` counts every spot matching the filters, ignoring the page window. `count` is the number of items on this page, and `has_more` is true when `offset + count < total`.

Results are ordered by name, then by identifier. Because the identifier is unique, that sort key is total, so paging over an unchanged dataset never repeats or skips a spot. What the contract promises is that the order does not move between requests, not the exact sequence: where in the alphabet punctuation and digits fall is the database collation's business.

### Query parameters

| Parameter | Type | Default | Behavior |
|---|---|---|---|
| `name` | string | — | Case-insensitive substring match. `%` and `_` are matched literally. |
| `neighborhood` | string | — | Case-insensitive exact match. |
| `borough` | string | — | Case-insensitive exact match on one of the five borough names. |
| `university` | string | — | Case-insensitive exact match. Spots with no curated campus affiliation are excluded. |
| `limit` | integer | `20` | Page size, between 1 and 100. |
| `offset` | integer | `0` | Rows to skip before the page starts. |

Filters combine with AND. Text filters are trimmed, must not be blank, and are limited to 120 characters. A `borough` value is also normalized for internal spacing, so `?borough=brooklyn` and `?borough=  Staten   Island ` both resolve.

Case-insensitivity covers the whole of Unicode, not only ASCII, so `?name=café` and `?name=CAFÉ` return the same spots. Folding is the database's, applied identically to the stored value and the filter value, and every environment runs a UTF-8 cluster; the one place it is less aggressive than the previous implementation is `ß`, which Postgres does not fold to `ss`, so "strasse" does not match "Straße". See [Why no column declares a collation](database.md#why-no-column-declares-a-collation).

Unknown query parameters are rejected rather than ignored, so a misspelled filter fails loudly instead of silently returning unfiltered results:

```shell
curl --fail 'http://localhost:7501/spots?borough=Brooklyn&name=library&limit=5'
```

## Errors

Every non-2xx response uses one envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request could not be validated.",
    "details": [
      {
        "field": "query.limit",
        "message": "Ensure this value is less than or equal to 100.",
        "type": "max_value"
      }
    ]
  }
}
```

`code` is stable and machine-readable; `message` is for people. `details` lists one entry per offending input and is empty when no single input is at fault.

| Status | `code` | Raised when |
|---|---|---|
| 404 | `not_found` | No spot has the requested identifier. |
| 405 | `method_not_allowed` | The route exists but the method does not. |
| 422 | `validation_error` | A parameter is missing, malformed, out of range, or unrecognized. |
| 500 | `internal_error` | An unhandled failure. The cause is logged, never returned. |
| 503 | `database_unavailable` | Postgres could not answer the query, or has never been migrated. |

## Planned routes

- `GET /spots/search?q=coffee`
- `GET /health/ready`

The readiness route will report required dependency failures.
