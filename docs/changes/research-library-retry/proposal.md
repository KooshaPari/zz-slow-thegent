# Standardized Retry Library Proposal

## Overview

This proposal establishes a standardized, centralized retry logic library for **thegent** using **tenacity** as the foundation. The library will provide consistent exponential backoff, built-in observability (via OpenTelemetry), and configurable resilience patterns across all agent services, API clients, and distributed system components.

## Problem Statement

### Current State

- **No unified retry strategy**: Scattered implementations across codebase (manual loops, custom backoff logic)
- **Poor observability**: Retry attempts not instrumented; no metrics or tracing
- **Inconsistent behavior**: Different services retry with different strategies, exponential bases, max attempts
- **Code duplication**: Retry logic reimplemented per use case
- **Missed library investment**: `tenacity>=8.3.0` already in `pyproject.toml`, underutilized

### Risks

- Silent failures during transient faults (network hiccups, service restarts)
- Cascading failures due to aggressive retry patterns
- Difficulty debugging transient issues (no visibility into retries)
- Maintenance burden: updating retry logic requires changes in N places

## Goals

1. **Reduce code duplication**: Centralize retry logic into a thin, reusable library
2. **Improve observability**: Instrument all retries with OpenTelemetry metrics and traces
3. **Standardize resilience patterns**: Exponential backoff + jitter by default, configurable per use case
4. **Enable quick integration**: Drop-in decorator/context manager for new services
5. **Support domain-specific configurations**: HTTP timeouts, database transients, agent service retries

## Scope

### In Scope

- Retry library (`src/thegent/resilience/retry.py`) with tenacity wrapper
- Default exponential backoff strategy (base 2, max jitter)
- OpenTelemetry instrumentation (span attributes, metrics)
- Pre-built retry strategies for common cases:
  - HTTP requests (4xx transients, 5xx, timeouts)
  - Database operations (connection errors, transient locks)
  - Agent service calls (temporary unavailability)
- Configuration via pydantic settings (`RetryConfig`)
- Comprehensive test suite (unit + integration)
- Documentation and usage examples

### Out of Scope

- Circuit breaker logic (separate concern; `pybreaker` already present)
- Rate limiting (separate concern; tenacity + asyncio.Semaphore for advanced cases)
- Custom backoff algorithms beyond exponential (extend in future if needed)
- Automatic retry on all exceptions (explicit opt-in only)

## Non-Functional Requirements

- **Performance**: Retry overhead <1ms for typical (non-failing) path
- **Observability**: Every retry attempt emitted as span event + metric
- **Type safety**: Full type hints; strict mode compatible
- **Backward compatibility**: No breaking changes to existing APIs
- **Testability**: 100% unit test coverage for core retry logic

## Library Approach

**Library-first principle**: Use `tenacity` as the foundation, build thin wrapper exposing project conventions. No custom retry logic.

**Architecture**:

```
src/thegent/resilience/
├── __init__.py              # Public API (retry, retry_config, decorators)
├── retry.py                 # Core RetryStrategy, RetryConfig, decorators
├── strategies.py            # Pre-built strategies (http, db, agent)
├── observability.py         # OpenTelemetry instrumentation
└── exceptions.py            # Retry-specific exceptions (RetryExhausted, etc.)
```

## Success Criteria

1. **Adoption**: 3+ services migrated to library (with metrics showing >80% retry success)
2. **Observability**: All retries traced + metricated (zero dark spans)
3. **Coverage**: Retry code 100% unit tested
4. **Docs**: Usage guide + 5 worked examples (HTTP, DB, agent, async, custom)
5. **Performance**: Latency regression <1% for nominal path

## Timeline

**Phase 1 (Research & Design)**: 1 phase
**Phase 2 (Implementation)**: Core library + strategies
**Phase 3 (Integration)**: Migrate 3 service + docs
**Phase 4 (Validation)**: Test + review

Estimated: 2–3 agent work blocks (~20–30 min wall clock for autonomous agents).

---

## Related Work

- **tenacity** (8.3.0): Library of choice; battle-tested, well-documented
- **OpenTelemetry** (1.24.0): Instrumentation foundation (already a dependency)
- **Existing pybreaker**: Circuit breaker; complements retry strategy
- **Existing cachetools/diskcache**: Caching layer (separate from retry)
- **CLAUDE.md library standard**: Mandates tenacity for retry/resilience

## Decision

**DECISION: Adopt library-first approach with tenacity wrapper**

**Rationale**:

- Tenacity is proven, widely adopted, and already a project dependency
- Thin wrapper ensures project conventions are enforced
- OpenTelemetry integration provides production observability
- Pre-built strategies lower migration barrier
- Aligns with CLAUDE.md mandate: "No manual retry loops; use tenacity"
