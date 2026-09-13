# Data and search

PostgreSQL with PostGIS is the authoritative store. Meilisearch is a projection that can be deleted and rebuilt.

```text
NYC library data --\
                    -> normalize -> PostgreSQL/PostGIS -> Meilisearch
NYU building data -/                         |
                                               -> API detail/list queries
```

The data implementation has not landed yet. It will provide:

- versioned migrations in `data/migrations/`
- repeatable imports in `data/seeds/`
- explicit validation at each external-data boundary
- idempotent seeding
- deterministic, repeatable search indexing
- tests for source mapping and malformed records

Local PostgreSQL and Meilisearch data use Docker volumes. Staging and production must use separate databases and either separate search instances or strictly separated index names and credentials.
