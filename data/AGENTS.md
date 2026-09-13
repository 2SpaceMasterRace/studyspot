# Data Instructions

This area owns PostgreSQL/PostGIS migrations and repeatable seed imports.

- Keep migrations ordered, forward-only, and narrowly scoped.
- Make seed commands idempotent.
- Preserve stable source identifiers across repeated imports.
- Keep Socrata mapping code independent from the API and frontend.
- Never put credentials or production data exports in the repository.
- Add data tests with the data implementation they verify.
