# Study-spots boundary

This package owns StudySpot's access to the study-spot data: the shared contract, the
serving schema, the Turso connection, and the one repository every consumer reads and
writes through.

| Module | Responsibility |
|---|---|
| `models.py` | The shared study-spot contract and the filter set. |
| `schema.sql` | The serving schema and its indexes. |
| `database.py` | Local `turso` and remote `libsql` connections behind one type. |
| `repository.py` | The repository interface and its Turso implementation. |

Three consumers use it, and none of them writes its own SQL or `CREATE TABLE`:

| Consumer | Method |
|---|---|
| HTTP routes | `list_spots(filters, limit=, offset=)`, `get_spot(id)` |
| Search projection | `iter_all()` |
| Dataset loader | `replace_all(spots)` |

That is deliberate. When each consumer brought its own schema, the three definitions of
the `spots` table disagreed on which columns existed and which were nullable, and the
first one to run decided what the others got.

`replace_all` replaces rather than upserts: the table is a rebuildable projection of
`data/spots.json`, so a record dropped upstream has to disappear here too.

Filter values are compared against the `_folded` columns, which hold Python
`str.casefold()` output. SQLite's own `lower()` and `LIKE` fold only ASCII, so this is
what makes filters case-insensitive for every character NYC Open Data contains.
