# Thegent MCP Service Level Objectives (SLOs)

**Purpose:** Comprehensive SLO documentation for thegent FastMCP server tools.
**Status:** WP-D FastMCP Polish - Complete
**Last Updated:** 2026-02-18

---

## Overview

This document defines Service Level Objectives (SLOs) for all thegent MCP tools. SLOs are target levels of service measured through Service Level Indicators (SLIs) and tracked via execution metrics.

## Table of Contents

1. [Tool Performance SLOs](#tool-performance-slos)
2. [Availability SLOs](#availability-slos)
3. [Error Rate SLOs](#error-rate-slos)
4. [Response Size SLOs](#response-size-slos)
5. [Measurement and Monitoring](#measurement-and-monitoring)
6. [Error Budgets](#error-budgets)

---

## Tool Performance SLOs

### Read-Only Tools (Idempotent)

| Tool | P50 Target | P95 Target | P99 Target | Notes |
|------|------------|------------|------------|-------|
| `thegent_ps` | < 50ms | < 100ms | < 200ms | Cached (TTL 30s); list operation |
| `thegent_status` | < 20ms | < 50ms | < 100ms | Lightweight session lookup |
| `thegent_list_agents` | < 30ms | < 60ms | < 120ms | Static list from registry |
| `thegent_list_droids` | < 30ms | < 100ms | < 200ms | Directory scan (.factory/droids) |
| `thegent_list_models` | < 200ms | < 500ms | < 1000ms | Scraped catalog; cache hit ~50ms |
| `thegent_logs` | < 100ms | < 500ms | < 1000ms | File read; tail limit 500k |
| `thegent_inspect` | < 200ms | < 1s | < 2s | Multi-session; scales with count |
| `thegent_dag_list` | < 100ms | < 300ms | < 600ms | DAG state enumeration |
| `thegent_session_contracts` | < 50ms | < 150ms | < 300ms | Contract metadata lookup |
| `thegent_observe_summary` | < 100ms | < 300ms | < 600ms | Observation aggregation |

### Execution Tools (Non-Idempotent)

| Tool | Target | Notes |
|------|--------|-------|
| `thegent_run` | Timeout: 90s (default) | Depends on agent execution time; progress updates every 10s |
| `thegent_bg` | < 200ms | Fire-and-forget; returns session_id immediately |
| `thegent_loop` | N/A | Long-running loop; progress updates every 10s |
| `thegent_wait` | Blocks until completion | Waits for session completion or timeout |

### Management Tools

| Tool | P50 Target | P95 Target | Notes |
|------|------------|------------|-------|
| `thegent_stop` | < 100ms | < 300ms | Session termination |
| `thegent_pause` | < 100ms | < 300ms | Session pause |
| `thegent_resume` | < 100ms | < 300ms | Session resume |
| `thegent_retry` | < 200ms | < 500ms | Retry failed session |

---

## Availability SLOs

### MCP Server Availability

**Target: 99.9% uptime**

- **Measurement Window:** 30 days
- **Error Budget:** 0.1% = ~43 minutes/month downtime
- **Measurement Method:** Health check endpoint `/health`

**Acceptable Exclusions:**
- Planned maintenance windows (announced 48 hours in advance)
- Infrastructure failures (network, host)
- DDoS attacks or security incidents

### Tool Availability

**Target: 99.95% success rate per tool**

- **Measurement Window:** 30 days
- **Error Budget:** 0.05% = ~21.6 minutes/month failures
- **Measurement Method:** Percentage of successful tool calls (non-5xx responses)

**SLI Calculation:**
```
tool_availability = (successful_calls / total_calls) * 100
```

---

## Error Rate SLOs

### Overall Error Rate

**Target: Error rate < 0.1%**

- **Measurement Window:** 5 minutes
- **Critical Threshold:** > 1% error rate
- **Measurement Method:** Percentage of failed tool calls

**Error Categories:**
- **Client Errors (4xx):** Not counted against SLO (user error)
- **Server Errors (5xx):** Counted against SLO
- **Timeouts:** Counted against SLO
- **Elicitation Cancellations:** Not counted against SLO

### Per-Tool Error Rate

**Target: < 0.5% error rate per tool**

- **Measurement Window:** 1 hour
- **Warning Threshold:** > 0.5%
- **Critical Threshold:** > 2%

---

## Response Size SLOs

### Response Size Limits

| Tool Category | Max Response Size | Notes |
|---------------|-------------------|-------|
| List operations | 500 KB | Pagination recommended for large lists |
| Log operations | 500 KB | Tail limit enforced |
| Status operations | 10 KB | Lightweight metadata |
| Execution results | 1 MB | Full output; use `full=false` for condensed |

**Enforcement:**
- `ResponseLimitingMiddleware` caps responses at 500KB
- Tools return truncated results with metadata indicating truncation

---

## Measurement and Monitoring

### Metrics Collection

All tools emit `execution_time_ms` in `ToolResult.meta`:

```python
ToolResult(content=json.dumps(result), structured_content=result, meta={"execution_time_ms": elapsed_ms})
```

### Middleware Stack

1. **TimingMiddleware**: Records execution time
2. **ResponseCachingMiddleware**: 30s TTL for read-only tools
3. **ResponseLimitingMiddleware**: 500KB cap
4. **ErrorHandlingMiddleware**: Captures and formats errors
5. **LoggingMiddleware**: Structured logging

### Observability

**Metrics Exposed:**
- `execution_time_ms`: Per-tool execution time
- Tool call counts (via logging)
- Error rates (via error middleware)
- Cache hit rates (via caching middleware)

**Logging:**
- Structured JSON logs for all tool calls
- Error details with context
- Performance warnings for slow operations

---

## Error Budgets

### Monthly Error Budgets

**Server Availability:**
- SLO: 99.9% uptime
- Monthly budget: 43.2 minutes downtime
- Action threshold: > 30 minutes downtime

**Tool Error Rate:**
- SLO: < 0.1% error rate
- Monthly budget: ~432 errors per 100k calls
- Action threshold: > 300 errors per 100k calls

### Error Budget Consumption

**Tracking:**
- Daily error budget consumption reports
- Weekly SLO compliance reviews
- Monthly error budget reset

**Actions on Budget Depletion:**
1. **50% consumed:** Review error patterns
2. **75% consumed:** Investigate root causes
3. **90% consumed:** Implement fixes
4. **100% consumed:** Post-mortem and SLO review

---

## Tool-Specific SLO Details

### thegent_run

**Execution Time:**
- Depends on agent and task complexity
- Progress updates every 10s
- SSE stream closes every 30s to avoid LB timeouts

**Timeout Handling:**
- Default: 90s (configurable 5-3600s)
- Returns `timed_out: true` on timeout
- Structured output includes execution metadata

### thegent_bg

**Fire-and-Forget:**
- Returns immediately with `session_id`
- Background execution tracked via `thegent_ps`
- No blocking; no timeout

### thegent_logs

**Performance:**
- File read operation
- Tail limit: 500k characters
- Response size capped at 500KB
- Performance scales with log file size

### thegent_list_models

**Caching:**
- Model catalog scraping (slow)
- Cache hit: ~50ms
- Cache miss: ~200ms
- Cache TTL: 30s

---

## Cross-References

- `docs/reference/SLO_TARGETS.md` - Original SLO targets
- `docs/FASTMCP_OPTIMIZATION_AUDIT.md` - Performance audit
- `docs/reference/TOOLING_AND_GLOBAL_OPTIMIZATIONS_AUDIT.md` - WP-D work package
- `src/thegent/mcp_server.py` - MCP server implementation

---

## Implementation Status

**WP-D FastMCP Polish:**
- ✅ Tool descriptions: All tools have comprehensive docstrings
- ✅ Structured content: All tools return `structured_content` in ToolResult
- ✅ SLO documentation: This document (complete)

**Next Steps:**
- Monitor SLO compliance via metrics
- Adjust targets based on production data
- Implement alerting for SLO violations
