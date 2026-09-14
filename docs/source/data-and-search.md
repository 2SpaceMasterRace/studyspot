# Data and search

No public-data snapshot, runtime store, or search index is implemented yet. The planned design makes a versioned, normalized public-data snapshot authoritative and treats runtime stores and indexes as rebuildable projections.

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

Local PostgreSQL and Meilisearch data use Docker volumes so integration work survives normal restarts. Vercel staging and production currently receive no dataset or search state. Once the import and search milestones land, deployment must prove that the normalized snapshot is packaged and that runtime search state can be rebuilt before relying on this stateless design. A hosted database becomes necessary when StudySpot owns data that cannot be regenerated from its public sources.
