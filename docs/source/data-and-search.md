# Data and search

The versioned, normalized public-data snapshot is the first release's authoritative input. Runtime stores and indexes are projections that can be deleted and rebuilt.

```text
NYC library data --\
                    -> normalize -> versioned snapshot -> in-memory search
NYU building data -/                         |
                                               -> API detail/list queries
```

The data implementation has not landed yet. It will provide:

- a versioned normalized snapshot under `data/`
- repeatable imports in `data/seeds/`
- explicit validation at each external-data boundary
- idempotent seeding
- deterministic, repeatable search indexing
- tests for source mapping and malformed records

Local PostgreSQL and Meilisearch data use Docker volumes so integration work survives normal restarts. Vercel staging and production instead receive the same immutable snapshot in their deployment artifacts and rebuild runtime search state from it. A hosted database becomes necessary only when StudySpot owns data that cannot be regenerated from its public sources.
