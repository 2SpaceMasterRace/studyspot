# Study-spots API boundary

The repository here owns the eight-field `StudySpotSummary` contract and the
minimal `spots` schema. Local and remote Turso connections satisfy the same
repository contract; the latter uses `libsql` while local `file:` URLs use
`pyturso`.
Opening hours live in a separate `spot_hours` table keyed by spot ID. They are
optional OpenStreetMap `opening_hours` expressions with an IANA timezone;
missing or invalid hours have unknown status. `load_snapshot.py` replaces the
populated source snapshot without changing the eight-field summary contract.
