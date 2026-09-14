# Study-spots API boundary

The repository here owns the eight-field `StudySpotSummary` contract and the
minimal `spots` schema. Local and remote Turso connections satisfy the same
repository contract; the latter uses `libsql` while local `file:` URLs use
`pyturso`.
