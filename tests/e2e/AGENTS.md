# End-to-End Test Instructions

This area verifies the complete browser-to-data search path and is owned by repository integration.

- Exercise real local services started through the documented root command.
- Do not mock FastAPI, PostgreSQL, or Meilisearch here.
- Test one representative successful search plus loading, empty, and dependency-failure behavior.
- Capture screenshots and traces on browser-test failure.
- Keep latency assertions separate from functional assertions so failures are diagnosable.
