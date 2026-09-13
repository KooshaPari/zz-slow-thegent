# Implementation Strategy

## Architecture

- Keep all entity logic in `src/thegent/planning/workstream_entities.py`.
- Keep CLI and MCP layers thin.
- Use `WorkstreamDB` as the only persistence anchor.
- Preserve the existing workstream sync flow and extend it, rather than replacing it.

## Data Handling

- Treat table names as the entity type boundary.
- Parse `metadata`-like JSON text back into structured data when possible.
- Serialize dict/list inputs back to JSON text before writing to SQLite.

## UX

- Prefer one command family over separate ad hoc commands.
- Make batch import and export path-based for CLI, record-based for MCP.
- Keep sync explicit so the user always knows which source set is being refreshed.

## Future Work

- Extend the same entity service to any new schema tables added later.
- Add a future HTTP API only if a real consumer needs it; do not duplicate the service logic.
