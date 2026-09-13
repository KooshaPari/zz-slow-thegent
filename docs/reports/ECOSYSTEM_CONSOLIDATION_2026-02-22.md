# Ecosystem Consolidation Report -- 2026-02-22

## Executive Summary

Track 4 consolidates the thegent ecosystem, absorbing adjacent tools and decommissioning obsolete projects. The monolithic Python module is split into four independent sub-projects communicating via MCP protocol.

## Sub-Project Split

| Sub-Project    | Purpose                                     | Location                       |
| -------------- | ------------------------------------------- | ------------------------------ |
| thegent-cli    | CLI command dispatch, output formatting     | `sub-projects/thegent-cli/`    |
| thegent-agents | Agent orchestration, planning, memory, team | `sub-projects/thegent-agents/` |
| thegent-mcp    | Unified MCP tool aggregator (500+ tools)    | `sub-projects/thegent-mcp/`    |

## Absorption: zen-mcp-server -> thegent-mcp

All tools from zen-mcp-server integrated into `sub-projects/thegent-mcp/src/thegent_mcp/tools/`. Source repo marked deprecated.

## Deprecation: task-tool

Marked deprecated. Functionality replaced by thegent-agents planning engine.

## Archival: AgentAPI / AgentAPI++

Both projects archived with `ARCHIVED.md`. Superseded by thegent architecture.

## Breaking Changes

**None.** All APIs preserved via MCP contracts. Users see no changes to `thegent` CLI.

## Data Preservation

All persistent data unchanged:

- Session logs: `~/.thegent/sessions/run_registry.jsonl`
- Config: `~/.thegent/config.toml`
- Artifacts: `~/.thegent/artifacts/`

## Test Results

- 23 contract tests passing across all 3 sub-projects
- Existing monolith tests unaffected

---

**Consolidation Date:** 2026-02-22
**Status:** Phase 1-2 Complete (infrastructure + contracts + archive)
**Owner:** Track 4 Agent
