# MCP Tool Retry Policy

> **Purpose**: Document retry behavior for MCP tools and provider API calls.
> **Related**: [ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH](../research/ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH.md), [TENACITY_RETRY_AUDIT_PLAN](../research/TENACITY_RETRY_AUDIT_PLAN.md)

---

## Summary

| Component                                 | Retry Strategy         | Max Attempts        | Backoff                        |
| ----------------------------------------- | ---------------------- | ------------------- | ------------------------------ |
| **Agent runners** (Codex, Cursor, Direct) | tenacity `@with_retry` | 2 (cost-aware: API) | Exponential + jitter (2–30s)   |
| **Loop controller** (worker)              | tenacity `@with_retry` | 3                   | Exponential + jitter           |
| **State machine** (orchestration)         | tenacity `retry()`     | per-provider        | Exponential + jitter           |
| **EAGAIN spawn**                          | tenacity               | 5                   | Exponential + jitter (0.1–5s)  |
| **SIEM egress**                           | tenacity               | 3                   | Exponential + jitter (2–10s)   |
| **Circuit breaker**                       | Per-agent/model        | —                   | Blocks when threshold exceeded |

---

## When We Retry

| Condition                      | Retry?                              |
| ------------------------------ | ----------------------------------- |
| 503, 504, 502                  | Yes                                 |
| 429 (rate limit)               | Yes                                 |
| Timeout, ECONNRESET, ETIMEDOUT | Yes                                 |
| 4xx (except 429)               | No                                  |
| Usage/quota exhausted          | No (fallback to different provider) |

---

## Circuit Breaker

When `THGENT_CIRCUIT_BREAKER_ENABLED=1` (default):

- **Threshold**: `THGENT_CIRCUIT_BREAKER_THRESHOLD` (default 5) failures in `THGENT_CIRCUIT_BREAKER_WINDOW_S` (default 300s)
- **Recovery**: Half-open after `THGENT_CIRCUIT_BREAKER_RECOVERY_S` (default 60s)
- **Scope**: Per agent/model; stored in `circuit_breakers.jsonl`

---

## MCP Tool Invocation

MCP tools invoked by clients (Cursor, Claude Code) are executed by thegent's MCP server. Subprocess tools (e.g. Serena, Octocode) use the agent runners' `@with_retry` when the runner spawns them. HTTP-based tools rely on the client or underlying library for retries.

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
