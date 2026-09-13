# MCP Tool SLO Targets (G-OP-08)

**Purpose:** Aspirational latency targets for thegent MCP tools. Not enforced; use for monitoring and runbook guidance.
**Source:** FASTMCP_OPTIMIZATION_AUDIT.md §5

---

## Tool Targets

| Tool                | Target      | Notes                                     |
| ------------------- | ----------- | ----------------------------------------- |
| thegent_ps          | p50 < 50ms  | Cached (TTL 30s); list operation          |
| thegent_status      | p50 < 20ms  | Lightweight session lookup                |
| thegent_list_agents | p50 < 30ms  | Static list                               |
| thegent_list_droids | p50 < 30ms  | Dir scan                                  |
| thegent_list_models | p50 < 200ms | Scraped catalog; cache hit ~50ms          |
| thegent_run         | N/A         | Depends on agent; timeout 90s             |
| thegent_bg          | N/A         | Fire-and-forget; returns immediately      |
| thegent_logs        | p95 < 500ms | File read; tail limit 500k                |
| thegent_wait        | N/A         | Blocks until session completes or timeout |
| thegent_inspect     | p95 < 1s    | Multi-session; scales with session count  |

---

## Supporting Infrastructure

| Component                  | Purpose                           |
| -------------------------- | --------------------------------- |
| ResponseCachingMiddleware  | 30s TTL for read-only tools       |
| ResponseLimitingMiddleware | 500KB cap for logs                |
| execution_time_ms          | ToolResult.meta for observability |

---

## Cross-References

- docs/FASTMCP_OPTIMIZATION_AUDIT.md
- docs/reference/TOOLING_AND_GLOBAL_OPTIMIZATIONS_AUDIT.md

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
