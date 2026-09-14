# Search boundary

This boundary queries the rebuildable Meilisearch projection. Search uses the
ordered fields `name`, `neighborhood`, `category`, `address`, and `borough`,
with indexing-time prefix search and Meilisearch's default typo tolerance.
The projection is rebuilt from Turso by `just reindex`.
