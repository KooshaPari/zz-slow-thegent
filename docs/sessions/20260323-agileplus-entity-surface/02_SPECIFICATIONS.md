# Specifications

## Functional Requirements

- The system SHALL support canonical entity CRUD for schema-backed workstream tables.
- The system SHALL support batch import from JSON and JSONL.
- The system SHALL support export to JSON.
- The system SHALL support sync from markdown, AgilePlus backlog, and queue sources.
- The system SHALL fail loudly for unsupported entity types or invalid composite keys.

## Contract Shape

- CLI:
  - `thegent plan entity list`
  - `thegent plan entity read`
  - `thegent plan entity search`
  - `thegent plan entity upsert`
  - `thegent plan entity delete`
  - `thegent plan entity import`
  - `thegent plan entity export`
  - `thegent plan entity sync`
- MCP:
  - `thegent_entity(operation=...)`

## ARUs

- Assumption: current schema tables are sufficient for the first canonical entity surface.
- Risk: composite-key handling can be inconsistent across table types.
- Uncertainty: additional API routes may be needed later, but they are not required for the first working slice.
