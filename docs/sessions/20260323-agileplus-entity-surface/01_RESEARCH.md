# Research

## Repo Findings

- `src/thegent/planning/workstream_db.py` already owns the canonical SQLite workstream database.
- `src/thegent/planning/workstream_db_schema.py` defines the authoritative tables and indexes.
- `src/thegent/cli/services/work_stream_orchestration.py` already syncs markdown, AgilePlus backlog data, and queue sources into `WorkstreamDB`.
- `src/thegent/cli/commands/governance_agileplus_cmds.py` only exposes cycle/status/watch behavior today.
- `src/thegent/mcp/server_consolidated_tools.py` already consolidates queue/session/workstream tools, but not a generic entity CRUD surface.
- `docs/api/mcp-protocol.md` and `docs/api/mcp-integration.md` describe an `entity_operation` pattern that matches the desired user experience.

## Design Implications

- The right implementation point is a shared entity service, not a new database or seed SQL path.
- Batch import/export should accept JSON and JSONL so agents can move records without hand-editing SQL.
- The CLI should be the obvious human entry point.
- MCP should mirror the CLI operation set instead of inventing a second vocabulary.
