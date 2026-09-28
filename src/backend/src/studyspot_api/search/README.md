# Search boundary

This boundary queries the rebuildable Meilisearch projection. Search uses the
ordered fields `name`, `neighborhood`, `category`, `address`, and `borough`,
with indexing-time prefix search and Meilisearch's default typo tolerance.
The projection is rebuilt from Turso by `just reindex`.
Filtered POST searches combine Meilisearch `_geoRadius` and an `id IN` set of
spots whose opening-hours expressions evaluate to open at request time. Both
filters are applied before the 20-result limit. User coordinates are used only
for the current request and optional straight-line distance in the response.
