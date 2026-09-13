# Session Overview

## Goal

Build a canonical, non-SQL-seed path for AgilePlus/workstream data entities that is usable from CLI, MCP, and future HTTP/API surfaces.

## Success Criteria

- CLI can list, read, search, upsert, import, export, delete, and sync canonical workstream entities.
- MCP exposes the same entity operations through one tool surface.
- Batch imports accept JSON and JSONL records.
- Sync paths use existing canonical sources instead of seed SQL.
- Behavior stays centered on `WorkstreamDB` and the existing workstream schema.

## Current Scope

- In scope:
  - `workstream_items`
  - `sessions`
  - `launches`
  - `backlog_items`
  - `deferred_tasks`
  - `dependencies`
  - other schema tables that already exist in `workstream_db_schema.py`
- Out of scope for this pass:
  - Cross-repo GitHub branch automation
  - CI/CD provider-specific rollout wiring
  - Seed SQL generation

## Key Decisions

- Keep one canonical entity service in `src/thegent/planning/workstream_entities.py`.
- Treat `WorkstreamDB` as the persistence anchor and avoid introducing a parallel store.
- Route CLI and MCP through the same helper module.
- Prefer fail-fast behavior on unsupported entity types or invalid keys.
