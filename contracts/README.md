# Shared contracts

This directory is reserved for the study-spot JSON Schema and sample data.

Planned ownership:

- `study-spot.schema.json`: shared response schema
- `sample-data/`: representative study-spot documents used by frontend, API, and search work

These artifacts will be added by the contract milestone. No schema or sample data is implemented in this scaffold.

The summary fields are `id`, `name`, `category`, `address`, `neighborhood`, `borough`,
`latitude`, `longitude`, and `university`.

`university` is an addition to the originally agreed field list, introduced by the study-spot
API ticket so callers can filter by campus. It names the closest college or university campus
within 500 m, or the campus itself for a campus record, and is `null` when no campus is nearby.
It reports proximity derived from the NYC Facilities Database, never affiliation, access, or
endorsement. It still needs sign-off from the frontend, API, data, and search owners.

`neighborhood` is `null` when NYC Open Data does not place a record in a 2020 Neighborhood
Tabulation Area. Every other field is always present.
