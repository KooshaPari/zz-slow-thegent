<DONE>
# Advanced Strategies & Resilience — Full-Depth Research & Plan

> **Purpose**: Wider, deeper research on smart/robust strategies: retry, backoff, circuit breaker, fairness, adaptive control, and resilience patterns for multi-agent swarms.
> **Status**: Implemented (Phases 1–2) | **Date**: 2026-02-16
> **Related**: [SMART_ROBUST_STRATEGIES_RESEARCH](./SMART_ROBUST_STRATEGIES_RESEARCH.md), [SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH](./SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md), [SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH](./SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md)

### Implementation Status (2026-02-16)

| Strategy                      | Component                                                               | Status                                   |
| ----------------------------- | ----------------------------------------------------------------------- | ---------------------------------------- |
| Exponential backoff + jitter  | resilience.with_retry, loop_controller, state_machine, cli_impl, egress | ✓ tenacity wait_random_exponential       |
| Jitter on prune cooldown      | prune-orphans-stop.sh                                                   | ✓ THGENT_AUTO_PRUNE_COOLDOWN_JITTER      |
| Graceful SIGTERM              | main.mcp_prune                                                          | ✓ THGENT_PRUNE_GRACE_PERIOD              |
| MCP retry policy doc          | docs/reference/MCP_RETRY_POLICY.md                                      | ✓                                        |
| Circuit breaker               | execution.CircuitBreakerRegistry, config                                | ✓ threshold, window, recovery            |
| Per-owner bulkhead            | ConcurrencyController.max_slots_per_owner                               | ✓ THGENT_CONCURRENCY_MAX_SLOTS_PER_OWNER |
| Cost-aware retry              | Agent runners (API: 2 attempts, local: 5)                               | ✓                                        |
| /health endpoint              | mcp_server                                                              | ✓ GET /health                            |
| Prune retry on failure        | prune-orphans-stop.sh                                                   | ✓ 3 attempts, backoff 2^attempt s        |
| Gardener spawn backoff        | gardener-spawn-manager.sh                                               | ✓ GARDENER_SPAWN_BACKOFF_SEC             |
| Retry budget (per-min cap)    | resilience.RetryBudgetPerMinute, with_retry                             | ✓ THGENT_RETRY_BUDGET_PER_MINUTE         |
| Token bucket (API rate limit) | resilience.TokenBucket, get_token_bucket                                | ✓ THGENT_TOKEN_BUCKET_CAPACITY           |
| Adaptive load thresholds      | execution.AdaptiveLoadThresholds, LoadClassifier                        | ✓ THGENT_LOAD_ADAPTIVE_ENABLED           |

---

## Table of Contents

| §   | Section                                     |
| --- | ------------------------------------------- |
| 1   | Executive Summary                           |
| 2   | Retry & Exponential Backoff                 |
| 3   | Jitter Strategies (Thundering Herd)         |
| 4   | Circuit Breaker Pattern                     |
| 5   | Bulkhead & Isolation                        |
| 6   | Restart Policies (Kubernetes, systemd)      |
| 7   | Fairness & Multi-Tenant Isolation           |
| 8   | Adaptive & Telemetry-Driven Strategies      |
| 9   | Backpressure & Rate Limiting                |
| 10  | **Timeout Strategies** _(new)_              |
| 11  | **Health Checks & Liveness Probes** _(new)_ |
| 12  | **Retry Exhaustion & Dead Letter** _(new)_  |
| 13  | **Cascading Failure Prevention** _(new)_    |
| 14  | **Cost-Aware & Hybrid Strategies** _(new)_  |
| 15  | thegent Mapping & Roadmap                   |
| 16  | Decision Trees & Quick Reference            |
| 17  | Cross-References & Bibliography             |

---

## 1. Executive Summary

This document extends thegent's strategy research with **industry-standard resilience patterns** and **adaptive control methods**:

| Pattern                          | Purpose                                                          |
| -------------------------------- | ---------------------------------------------------------------- |
| **Retry + exponential backoff**  | Transient failures, rate limits, API throttling                  |
| **Jitter**                       | Avoid thundering herd when many clients retry simultaneously     |
| **Circuit breaker**              | Stop hammering failing services; half-open probe for recovery    |
| **Bulkhead**                     | Isolate failures so one bad tenant doesn't cascade               |
| **Restart policies**             | Kubernetes CrashLoopBackOff, systemd Restart=, launchd KeepAlive |
| **Fairness**                     | Per-owner quotas, retry budgets, starvation prevention           |
| **Adaptive strategies**          | Telemetry-driven thresholds, dynamic backoff                     |
| **Timeout strategies**           | Fixed vs adaptive; deadline propagation                          |
| **Health checks**                | Liveness, readiness, startup probes                              |
| **Retry exhaustion**             | Dead letter, fallback, fail-fast semantics                       |
| **Cascading failure prevention** | Circuit breaker + bulkhead + timeout                             |
| **Cost-aware retry**             | Fewer retries for expensive ops (LLM API)                        |

**thegent applicability**: ConcurrencyController, prune triggers, MCP tool retries, gardener spawn, DAG task retries.

---

## 2. Retry & Exponential Backoff

### 2.1 Core Formula

```
delay = initialDelay × (factor ^ retryNumber)
```

- **factor = 2** → 1s, 2s, 4s, 8s, 16s (typical)
- **Cap**: `min(delay, maxDelay)` — e.g. 30–60s max

### 2.2 When to Retry vs Not

| Retry                               | Don't Retry            |
| ----------------------------------- | ---------------------- |
| 503, 504, 429                       | 4xx (except 429)       |
| ECONNRESET, ETIMEDOUT, ECONNREFUSED | ENOENT, EACCES         |
| Transient network                   | Permanent config error |
| Rate limit (429)                    | Auth failure (401)     |

### 2.3 Retry Budget (Global Cap)

Prevent retry storms: cap total retries across all callers per time window.

```
retry_budget = max_retries_per_minute  # e.g. 60
if retries_this_minute >= retry_budget:
    fail_fast()  # Don't retry; report
```

- **Use case**: Many agents retrying same failing API → exhaust budget → fail fast, surface to user.
- **thegent**: Per-provider retry budget; when exhausted, circuit-break or return "service overloaded".

### 2.4 thegent Mapping

| Component              | Current               | Enhancement                          |
| ---------------------- | --------------------- | ------------------------------------ |
| **MCP tool calls**     | Best-effort; may fail | Retry with backoff for 503/429       |
| **API provider calls** | tenacity (if used)    | Ensure exponential backoff + jitter  |
| **Prune trigger**      | Cooldown (fixed 300s) | Exponential backoff when prune fails |
| **Gardener spawn**     | Retry on failure      | Backoff between spawn attempts       |
| **DAG task retry**     | Retry count           | Backoff between retries              |

---

## 3. Jitter Strategies (Thundering Herd)

### 3.1 Problem

Multiple clients fail simultaneously → all retry at same time → overwhelm recovering service.

### 3.2 Jitter Types

| Strategy         | Formula                          | Use Case                       |
| ---------------- | -------------------------------- | ------------------------------ |
| **Full jitter**  | `random(0, exponentialDelay)`    | Best in practice; spreads load |
| **Equal jitter** | `(delay/2) + random(0, delay/2)` | Bounded minimum wait           |
| **Decorrelated** | `random(baseDelay, 3×baseDelay)` | Builds on prior delay          |

**Recommendation**: Full jitter. AWS, Google Cloud recommend exponential backoff **with jitter**.

### 3.4 Jitter Comparison (Tradeoffs)

| Strategy         | Min Wait   | Max Wait   | Load Spread | Use When               |
| ---------------- | ---------- | ---------- | ----------- | ---------------------- |
| **None**         | full delay | full delay | Poor        | Single client          |
| **Full jitter**  | 0          | full delay | Best        | Multi-client (default) |
| **Equal jitter** | delay/2    | delay      | Good        | Need bounded min       |
| **Decorrelated** | base       | 3×base     | Good        | Prior delay known      |

### 3.5 thegent Mapping

- **Prune cooldown**: Add jitter so multiple Stop events don't all trigger prune at once.
- **Periodic prune**: Stagger start time (random offset 0–60s) to avoid sync with other cron jobs.
- **ConcurrencyController acquire**: If many waiters, jitter before retry to avoid thundering herd on slot release.

---

## 4. Circuit Breaker Pattern

### 4.1 States

```
CLOSED ──(failures ≥ threshold)──► OPEN
   ▲                                    │
   │                                    │ (timeout)
   │                                    ▼
   └────(probe success)──────── HALF-OPEN
```

- **CLOSED**: Requests flow; count failures.
- **OPEN**: Reject immediately; no requests.
- **HALF-OPEN**: Allow one probe; success → CLOSED, failure → OPEN.

### 4.2 Parameters

| Param            | Typical | Description                     |
| ---------------- | ------- | ------------------------------- |
| failureThreshold | 5       | Failures before OPEN            |
| resetTimeout     | 30s     | Time before HALF-OPEN probe     |
| successThreshold | 1       | Successes in HALF-OPEN to close |

### 4.3 thegent Mapping

| Component                 | Circuit Breaker Use                                      |
| ------------------------- | -------------------------------------------------------- |
| **Provider API**          | Open when 5xx rate > X%; block requests 30s              |
| **MCP tool (external)**   | Open when tool fails N times; skip for 60s               |
| **Prune**                 | Not applicable (prune is local)                          |
| **ConcurrencyController** | Could circuit-break "acquire" when load chronically high |

**Note**: thegent has `CIRCUIT_BREAKER_*` config for agents/models — align with this pattern.

### 4.4 Sliding vs Fixed Window

| Window Type       | Failure Count   | Pros             | Cons                  |
| ----------------- | --------------- | ---------------- | --------------------- |
| **Fixed**         | Last N requests | Simple           | Burst at boundary     |
| **Sliding**       | Last N seconds  | Smoother         | More state            |
| **Percent-based** | % of last N     | Adaptive to load | Needs min sample size |

**Recommendation**: Sliding window (e.g. 5 failures in 30s) for API; fixed count for MCP tools.

---

## 5. Bulkhead & Isolation

### 5.1 Concept

Isolate components so failure in one doesn't consume all resources. Named after ship compartments.

### 5.2 Practices

| Practice                         | Description                |
| -------------------------------- | -------------------------- |
| **Separate connection pools**    | MCP vs API vs hooks        |
| **Per-tenant limits**            | Cap slots per owner        |
| **Independent circuit breakers** | One per provider, per tool |
| **Thread/process pools**         | Dedicated pool per domain  |

### 5.3 thegent Mapping

| Current                        | Bulkhead Enhancement                                  |
| ------------------------------ | ----------------------------------------------------- |
| ConcurrencyController (global) | Per-owner or per-project sub-limits                   |
| Single prune path              | Isolate LSP prune from MCP prune (different patterns) |
| Gardener spawn                 | Per-project disk gate already isolates                |
| MCP server                     | Separate timeouts per tool namespace                  |

---

## 6. Restart Policies (Kubernetes, systemd)

### 6.1 Kubernetes

| Policy    | Behavior                      |
| --------- | ----------------------------- |
| Always    | Restart on any exit           |
| OnFailure | Restart only on non-zero exit |
| Never     | No restart                    |

**CrashLoopBackOff**: Exponential backoff between restarts (10s, 20s, 40s, … cap 5min).

### 6.2 systemd

| Directive              | Example                    |
| ---------------------- | -------------------------- |
| Restart=               | on-failure, always, no     |
| RestartSec=            | 2 (seconds before restart) |
| StartLimitIntervalSec= | 60                         |
| StartLimitBurst=       | 5                          |

### 6.3 launchd (macOS)

| Key              | Behavior                                    |
| ---------------- | ------------------------------------------- |
| KeepAlive        | true, false, or dict (SuccessfulExit, etc.) |
| RunAtLoad        | Start at load                               |
| ThrottleInterval | Min seconds between restarts                |

### 6.4 thegent Mapping

| Component            | Restart Policy                                            |
| -------------------- | --------------------------------------------------------- |
| prune-periodic       | launchd KeepAlive=false (run periodically, don't restart) |
| thegent serve        | process-compose restart policy                            |
| MCP subprocess tools | Optional: restart on crash with backoff                   |
| Gardener workers     | Restart with limit (avoid spawn storm)                    |

---

## 7. Fairness & Multi-Tenant Isolation

### 7.1 Fairness Goals

| Goal                   | Mechanism                                              |
| ---------------------- | ------------------------------------------------------ |
| **No starvation**      | Per-owner min share or max wait time                   |
| **Proportional share** | Weighted fair queuing                                  |
| **Retry fairness**     | Retry budget per owner; don't let one consumer exhaust |

### 7.2 Algorithms

| Algorithm             | Idea                            |
| --------------------- | ------------------------------- |
| **Max-Min Fairness**  | Maximize minimum share          |
| **Proportional Fair** | Allocate proportional to demand |
| **Token Bucket**      | Refill rate; burst capacity     |
| **Leaky Bucket**      | Smooth output rate              |

### 7.3 thegent Mapping

| Component             | Fairness Enhancement                                                      |
| --------------------- | ------------------------------------------------------------------------- |
| ConcurrencyController | Per-owner quota; FCFS within quota                                        |
| Prune                 | No fairness (system-wide); could add per-project "don't prune my project" |
| DAG tasks             | Prioritize by critical path; fair within priority                         |
| API rate limits       | Token bucket per provider                                                 |

---

## 8. Adaptive & Telemetry-Driven Strategies

### 8.1 Principles

- **Observe**: Failure rate, latency, retry success rate.
- **Adapt**: Adjust initialDelay, maxRetries, circuit breaker threshold.
- **Log**: Retry attempts, delays, outcomes for pattern analysis.

### 8.2 Adaptive Backoff

If endpoint consistently needs 3–4 retries → start with higher initial delay for that service.

### 8.3 Observability for Resilience

| Metric                  | Purpose                       |
| ----------------------- | ----------------------------- |
| `retry_count`           | How often retries occur       |
| `retry_exhausted_count` | Failures after max retries    |
| `circuit_breaker_state` | CLOSED / OPEN / HALF_OPEN     |
| `circuit_breaker_trips` | Count of OPEN transitions     |
| `latency_p99`           | For adaptive timeout          |
| `failure_rate_5m`       | For circuit breaker threshold |

**thegent**: Expose via `thegent mcp metrics` or provider metrics endpoint; use for adaptive thresholds.

### 8.4 thegent Mapping

| Component             | Adaptive Enhancement                                 |
| --------------------- | ---------------------------------------------------- |
| HysteresisController  | Already adaptive (dwell, thresholds)                 |
| ConcurrencyController | Dynamic fd_utilization_max from observed FD pressure |
| Prune threshold       | Lower when memory trend is declining                 |
| Load thresholds       | Adjust spike/surge from observed load patterns       |

---

## 9. Backpressure & Rate Limiting

### 9.1 Token Bucket

- **Capacity**: Max burst.
- **Refill rate**: Tokens per second.
- **Acquire**: Take 1 token; if none, wait or reject.

### 9.2 Leaky Bucket

- **Leak rate**: Output rate.
- **Queue**: Requests wait; leak at constant rate.

### 9.3 thegent Mapping

| Component             | Rate Limit                               |
| --------------------- | ---------------------------------------- |
| ConcurrencyController | Slot limit (admission control)           |
| Load thresholds       | Traffic shaping when spike/surge         |
| API providers         | Token bucket per provider (future)       |
| Prune                 | Cooldown = rate limit on prune frequency |

---

## 10. Timeout Strategies

### 10.1 Fixed vs Adaptive Timeouts

| Type                     | Formula                             | Use Case                     |
| ------------------------ | ----------------------------------- | ---------------------------- |
| **Fixed**                | `timeout = 30s`                     | Predictable ops              |
| **Per-call**             | `timeout = base + k × payload_size` | Variable payload             |
| **Percentile-based**     | `timeout = p99_latency × 2`         | Adaptive to observed latency |
| **Deadline propagation** | Parent passes deadline to children  | Distributed traces           |

### 10.2 Timeout + Retry Interaction

```
total_time = sum(retry_i) + sum(timeout_i)
```

- **Risk**: 5 retries × 30s timeout = 150s max before failure.
- **Mitigation**: Shorter timeout per attempt (e.g. 10s) so retries fail fast; backoff between retries.

### 10.3 thegent Mapping

| Component     | Timeout Strategy                             |
| ------------- | -------------------------------------------- |
| MCP tool call | Fixed (e.g. 60s); consider per-tool override |
| API provider  | Adaptive from p99; fallback fixed            |
| Prune scan    | Fixed (e.g. 10s); don't block Stop           |
| DAG task      | Per-task timeout; propagate to subtasks      |

---

## 11. Health Checks & Liveness Probes

### 11.1 Probe Types

| Probe         | Purpose            | Failure Action      |
| ------------- | ------------------ | ------------------- |
| **Liveness**  | Is process alive?  | Restart             |
| **Readiness** | Can accept work?   | Don't route traffic |
| **Startup**   | Has init finished? | Restart if stuck    |

### 11.2 Patterns

| Pattern              | Description                          |
| -------------------- | ------------------------------------ |
| **HTTP GET /health** | Simple; 200 = healthy                |
| **TCP connect**      | Port open = alive                    |
| **Command**          | Run `thegent mcp ping` or similar    |
| **Dependency check** | Verify Redis, provider API reachable |

### 11.3 thegent Mapping

| Component      | Health Check                      |
| -------------- | --------------------------------- |
| thegent serve  | HTTP /health or MCP ping          |
| prune-periodic | launchd/systemd monitors exit     |
| MCP tools      | Optional: ping before invoke      |
| Provider API   | Circuit breaker = implicit health |

---

## 12. Retry Exhaustion & Dead Letter

### 12.1 When Retries Are Exhausted

| Action                | Use Case                             |
| --------------------- | ------------------------------------ |
| **Fail fast**         | User sees error; can retry manually  |
| **Dead letter queue** | Store for later replay (async jobs)  |
| **Fallback**          | Use backup provider or cached result |
| **Alert**             | Notify operator; don't silently drop |

### 12.2 Dead Letter Handling

```
if retries_exhausted:
    if has_dlq:
        enqueue(msg, dlq)
        return "queued for retry"
    else:
        log_error(msg)
        raise RetryExhaustedError
```

### 12.3 thegent Mapping

| Component    | Exhaustion Behavior                     |
| ------------ | --------------------------------------- |
| MCP tool     | Fail fast; surface to agent             |
| DAG task     | Mark failed; optional DLQ for replay    |
| API provider | Fallback to cached/backup if configured |
| Prune        | Never exhaust (local); cooldown only    |

---

## 13. Cascading Failure Prevention

### 13.1 Cascade Pattern

```
Service A fails → clients retry → A overloaded → A fails more
    → clients retry more → A dies → clients fail → clients' callers retry
    → cascade spreads
```

### 13.2 Mitigations

| Mitigation          | How                                |
| ------------------- | ---------------------------------- |
| **Circuit breaker** | Stop sending to A when it fails    |
| **Bulkhead**        | Limit concurrent calls to A        |
| **Timeout**         | Don't wait forever; fail fast      |
| **Fallback**        | Return cached or degraded response |
| **Load shed**       | Reject new work when overloaded    |

### 13.3 thegent Mapping

| Risk                  | Mitigation                           |
| --------------------- | ------------------------------------ |
| Provider API overload | Circuit breaker + bulkhead           |
| MCP server overload   | ConcurrencyController slots          |
| Prune during load     | Cooldown + memory threshold          |
| DAG task storm        | Admission control; queue depth limit |

---

## 14. Cost-Aware & Hybrid Strategies

### 14.1 Cost-Aware Retry

When retries have cost (API $, tokens):

| Condition               | Action                       |
| ----------------------- | ---------------------------- |
| Cheap op (local)        | Retry freely                 |
| Expensive op (API call) | Retry 1–2×; then fail        |
| Rate limit (429)        | Backoff; respect Retry-After |
| Quota exceeded          | Don't retry; report          |

### 14.2 Hybrid: Retry + Circuit Breaker

```
1. Retry with backoff (per request)
2. If many requests fail → circuit opens
3. When circuit half-open → single probe (no retry on probe)
4. Probe success → circuit close; resume retries
```

### 14.3 Hybrid: Bulkhead + Fairness

```
Per-owner pool: 5 slots max
Global pool: 20 slots max
Acquire: try owner pool first; else global if under cap
```

### 14.4 thegent Mapping

| Strategy            | thegent Use                                     |
| ------------------- | ----------------------------------------------- |
| Cost-aware retry    | LLM API: 1–2 retries; local tools: 5            |
| Retry + CB          | Provider API: retry per call; CB when 5xx spike |
| Bulkhead + fairness | ConcurrencyController: per-owner + global       |

---

## 15. thegent Mapping & Roadmap

### 15.1 Priority Matrix

| Strategy                     | Component               | Effort | Impact |
| ---------------------------- | ----------------------- | ------ | ------ |
| Exponential backoff + jitter | MCP/API retries         | 6–10   | High   |
| Circuit breaker              | Provider API, MCP tools | 8–12   | High   |
| Jitter on prune cooldown     | prune-orphans-stop      | 2–4    | Medium |
| Per-owner fairness           | ConcurrencyController   | 15–20  | Medium |
| Bulkhead (per-owner limits)  | ConcurrencyController   | 10–15  | Medium |
| Adaptive thresholds          | HysteresisController    | 8–12   | Medium |
| Restart with backoff         | Gardener, MCP tools     | 6–10   | Medium |

### 15.2 Phased Roadmap

**Phase 1 (Quick)**:

- Jitter on prune cooldown
- Graceful SIGTERM in prune (already planned)
- Document retry policy for MCP tools

**Phase 2 (Structural)**:

- Exponential backoff for MCP tool retries (with jitter)
- Circuit breaker for provider API (align with existing config)
- Per-owner slot cap (bulkhead)

**Phase 3 (Advanced)**:

- Adaptive load thresholds from telemetry
- Token bucket for API rate limiting
- Retry budget (global cap on retries/min)

---

## 16. Decision Trees & Quick Reference

### 16.1 When to Use Which Pattern

```
Operation fails?
├─ Transient (5xx, timeout, ECONNRESET)? → Retry with exponential backoff + jitter
├─ Rate limit (429)? → Retry with backoff; consider longer initial delay
├─ Permanent (4xx except 429)? → Don't retry; report
└─ Unknown? → Retry with limit (e.g. 3); then fail

Many clients failing at once?
└─ Add jitter to avoid thundering herd

Service chronically failing?
└─ Circuit breaker: OPEN → no requests for N seconds

One tenant consuming all resources?
└─ Bulkhead: per-owner limits

Need fairness across tenants?
└─ Per-owner quota; FCFS within quota
```

### 16.2 Parameter Quick Reference

| Pattern               | Key Params                                 | Typical Values                           |
| --------------------- | ------------------------------------------ | ---------------------------------------- |
| Exponential backoff   | initialDelay, factor, maxDelay, maxRetries | 1s, 2, 60s, 5                            |
| Jitter                | full / equal / decorrelated                | full                                     |
| Circuit breaker       | failureThreshold, resetTimeout             | 5, 30s                                   |
| Cooldown (prune)      | cooldown, jitter                           | 300s, ±30s                               |
| Timeout (per attempt) | timeout                                    | 10–30s (shorter than total retry window) |
| Retry budget          | maxRetriesPerMinute                        | 60                                       |

### 16.3 Failure Mode Quick Matrix

| Failure             | Primary Strategy                             | Fallback                 |
| ------------------- | -------------------------------------------- | ------------------------ |
| Transient 5xx       | Retry + backoff + jitter                     | Circuit breaker          |
| 429 rate limit      | Retry with longer delay; respect Retry-After | Circuit breaker          |
| Timeout             | Shorter per-attempt timeout; retry           | Fail fast after N        |
| Service down        | Circuit breaker                              | Bulkhead limits exposure |
| One tenant overload | Bulkhead (per-owner cap)                     | Fairness queue           |
| Retry storm         | Retry budget                                 | Circuit breaker          |
| Cascade risk        | Circuit breaker + timeout + bulkhead         | Load shed                |

---

## 17. Cross-References & Bibliography

### 17.1 Related Docs

| Doc                                                                                             | Relevance                                             |
| ----------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| [SMART_ROBUST_STRATEGIES_RESEARCH](./SMART_ROBUST_STRATEGIES_RESEARCH.md)                       | Process lifecycle, LSP multiplexing, prune strategies |
| [SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH](./SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md) | Scheduling theory, admission control, backpressure    |
| [SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH](./SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md)             | FD, CPU, resource gates                               |
| [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md)           | Prune, triggers, platform ecosystem                   |

### 17.2 External Sources

| Source                                                                                                                       | Topic                                    |
| ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| [Better Stack: Exponential Backoff](https://betterstack.com/community/guides/monitoring/exponential-backoff/)                | Retry, jitter, circuit breaker, bulkhead |
| [Kubernetes: Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)                               | CrashLoopBackOff, restart policy         |
| [AWS: Retry with Backoff](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html) | Transient errors, rate limits            |
| [Google Cloud: Retry Strategy](https://docs.cloud.google.com/storage/docs/retry-strategy)                                    | Exponential backoff with jitter          |
| [Polly: Retry](https://www.pollydocs.org/strategies/retry)                                                                   | .NET resilience; backoff types           |

---

## 10. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added resilience patterns
2. Added circuit breaker implementations
3. Enhanced cross-references

### Cross-References Added

- TENACITY_RETRY_AUDIT_PLAN.md
- GOVERNANCE_POLICY_AUDIT_RESEARCH.md

### Practical Additions

- Retry strategies
- Circuit breaker configuration

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [TENACITY_RETRY_AUDIT_PLAN.md](./TENACITY_RETRY_AUDIT_PLAN.md) - Retry audit
- [SMART_ROBUST_STRATEGIES_RESEARCH.md](./SMART_ROBUST_STRATEGIES_RESEARCH.md) - Smart strategies
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
