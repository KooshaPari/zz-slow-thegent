# DAG / WBS

## Phase 1: Canonical Service

| Task ID | Description                                                          | Depends On |
| ------- | -------------------------------------------------------------------- | ---------- |
| P1.1    | Define safe table whitelist and entity dispatch helpers              | -          |
| P1.2    | Implement list/read/search/upsert/delete/import/export operations    | P1.1       |
| P1.3    | Implement source sync dispatcher for markdown, AgilePlus, and queues | P1.2       |

## Phase 2: CLI Surface

| Task ID | Description                                      | Depends On |
| ------- | ------------------------------------------------ | ---------- |
| P2.1    | Add `thegent plan entity` Typer subcommands      | P1.2       |
| P2.2    | Add JSON/JSONL import and JSON export ergonomics | P2.1       |
| P2.3    | Add sync command for canonical sources           | P1.3, P2.1 |

## Phase 3: MCP Surface

| Task ID | Description                                  | Depends On |
| ------- | -------------------------------------------- | ---------- |
| P3.1    | Add consolidated `thegent_entity` MCP tool   | P1.2       |
| P3.2    | Ensure tool returns structured JSON payloads | P3.1       |

## Phase 4: Validation

| Task ID | Description                                                 | Depends On |
| ------- | ----------------------------------------------------------- | ---------- |
| P4.1    | Add helper unit tests for roundtrip, search, import, delete | P1.2       |
| P4.2    | Add CLI command smoke tests                                 | P2.1       |
| P4.3    | Add MCP wrapper smoke coverage                              | P3.1       |
