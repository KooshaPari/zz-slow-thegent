# Resilience Pattern Comparison & Decision Trees

**Document Version**: 1.0
**Date**: 2026-02-19
**Category**: Reference, Decision Support
**Purpose**: Quick lookup for pattern selection and configuration

---

## Quick Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│ What's your problem?                                        │
└─────────────────────────────────────────────────────────────┘
        ↓
┌───────────────────────┬───────────────────────┬─────────────────────┐
│ FAILING               │ SLOW                  │ OVERLOADED          │
│ (errors, crashes)     │ (high latency)        │ (high load)         │
└───────────────────────┴───────────────────────┴─────────────────────┘
        ↓                       ↓                       ↓
   ┌────────────┐          ┌──────────────┐      ┌──────────────────┐
   │ Temporary? │          │ Dependency?  │      │ Traffic spike?   │
   └────────────┘          └──────────────┘      └──────────────────┘
       ↙    ↘                  ↙    ↘                  ↙    ↘
      YES   NO               YES   NO               YES   NO
      ↓     ↓                ↓     ↓                ↓     ↓
   RETRY  CIRCUIT          TIMEOUT  SCALE       SHED  ADAPT
   BACKOFF  BREAKER        FALLBACK  WORKERS    LOAD  CONC
```

---

## Pattern Comparison Table

### Complete Feature Matrix

| Feature                  | Retry | Circuit Breaker | Bulkhead | Timeout | Throttle | Load Shed | Adaptive |
| ------------------------ | ----- | --------------- | -------- | ------- | -------- | --------- | -------- |
| **Transient Failures**   | ✅    | -               | -        | -       | -        | -         | -        |
| **Cascading Failure**    | -     | ✅              | ✅       | -       | -        | ✅        | -        |
| **Slow Responses**       | -     | -               | ✅       | ✅      | -        | -         | ✅       |
| **Resource Exhaustion**  | -     | -               | ✅       | -       | ✅       | ✅        | -        |
| **Overload Protection**  | -     | -               | -        | -       | ✅       | ✅        | ✅       |
| **Auto Recovery**        | -     | ✅              | -        | ✅      | -        | -         | ✅       |
| **Fair Share**           | -     | -               | ✅       | ✅      | ✅       | -         | ✅       |
| **Fast Failure**         | -     | ✅              | -        | ✅      | -        | -         | -        |
| **Config Complexity**    | Low   | Medium          | Low      | Low     | Medium   | Medium    | High     |
| **Operational Overhead** | Low   | Medium          | Low      | Low     | Medium   | Medium    | High     |

### Implementation Complexity

| Pattern              | Lines of Code | Maintenance | Learning Curve |
| -------------------- | ------------- | ----------- | -------------- |
| Retry                | < 10          | Minimal     | Beginner       |
| Circuit Breaker      | 50-100        | Medium      | Intermediate   |
| Bulkhead             | 20-50         | Low         | Beginner       |
| Timeout              | < 5           | Minimal     | Beginner       |
| Throttle             | 30-80         | Low-Medium  | Intermediate   |
| Load Shed            | 40-100        | Medium      | Intermediate   |
| Adaptive Concurrency | 100-200       | High        | Advanced       |

### Performance Impact

| Pattern         | CPU Overhead | Memory Overhead | Latency     | Throughput |
| --------------- | ------------ | --------------- | ----------- | ---------- |
| Retry           | Low          | Low             | +100-1000ms | -10-30%    |
| Circuit Breaker | Very Low     | Low             | 0-5ms       | +5-20%     |
| Bulkhead        | Low          | Medium          | 0-10ms      | +10-30%    |
| Timeout         | Very Low     | Low             | 0ms         | 0%         |
| Throttle        | Very Low     | Medium          | +50-500ms   | -5-50%     |
| Load Shed       | Low          | Low             | 0-5ms       | +5-20%     |
| Adaptive Conc   | Medium       | High            | -5-20%      | +20-40%    |

---

## Pattern Scenario Matrix

### When to Use Each Pattern

#### SCENARIO: External API Integration

| Aspect        | Pattern                            | Recommendation                              |
| ------------- | ---------------------------------- | ------------------------------------------- |
| **Primary**   | Circuit Breaker                    | Prevent cascading failures when API is down |
| **Secondary** | Retry + Backoff                    | Handle transient network errors             |
| **Tertiary**  | Timeout                            | Prevent hanging requests                    |
| **Fallback**  | Cached Response                    | Use stale data if API down                  |
| **Config**    | CB: fail_max=5, timeout=60s        |                                             |
|               | Retry: max_attempts=3, exp_backoff |                                             |
|               | Timeout: 30s HTTP, 5s DB           |                                             |

#### SCENARIO: Database Connection Management

| Aspect         | Pattern              | Recommendation                        |
| -------------- | -------------------- | ------------------------------------- |
| **Primary**    | Connection Pool      | Reuse connections; prevent exhaustion |
| **Secondary**  | Bulkhead             | Separate pools for OLTP vs OLAP       |
| **Tertiary**   | Timeout              | Kill slow queries                     |
| **Quaternary** | Circuit Breaker      | Detect DB unavailability              |
| **Config**     | Pool size: 20-50     |                                       |
|                | Max wait: 5-30s      |                                       |
|                | Query timeout: 5-10s |                                       |

#### SCENARIO: Microservice Mesh

| Aspect         | Pattern                         | Recommendation                       |
| -------------- | ------------------------------- | ------------------------------------ |
| **Primary**    | Circuit Breaker                 | Service-to-service failure isolation |
| **Secondary**  | Retry + Backoff                 | Transient service restarts           |
| **Tertiary**   | Timeout                         | Prevent resource exhaustion          |
| **Quaternary** | Bulkhead                        | Isolate critical paths               |
| **Quinary**    | Load Shed                       | Graceful degradation under spike     |
| **Config**     | Per-service circuit breaker     |                                      |
|                | Deadline propagation (timeouts) |                                      |

#### SCENARIO: Background Task Queue

| Aspect         | Pattern                    | Recommendation                    |
| -------------- | -------------------------- | --------------------------------- |
| **Primary**    | Retry + Backoff            | Eventually consistent execution   |
| **Secondary**  | Circuit Breaker            | Prevent queue saturation          |
| **Tertiary**   | Load Shed                  | Drop low-priority tasks when full |
| **Quaternary** | Timeout                    | Prevent runaway tasks             |
| **Config**     | Max retries: 3-10          |                                   |
|                | Backoff: exponential 2^n   |                                   |
|                | Max queue size: 1000-10000 |                                   |

#### SCENARIO: Real-Time Analytics

| Aspect         | Pattern                      | Recommendation                |
| -------------- | ---------------------------- | ----------------------------- |
| **Primary**    | Timeout                      | Must complete within deadline |
| **Secondary**  | Adaptive Concurrency         | Scale with load               |
| **Tertiary**   | Bulkhead                     | Prevent OLAP blocking OLTP    |
| **Quaternary** | Load Shed                    | Drop low-priority queries     |
| **Config**     | Query timeout: 10-30s        |                               |
|                | Concurrency: adaptive 10-100 |                               |

---

## Configuration Reference

### By Programming Language

#### Python (FastAPI/Django)

```python
# Quick setup: Tenacity + PyBreaker
from tenacity import retry, stop_after_attempt, wait_exponential
from pybreaker import CircuitBreaker


# Retry
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=60))
async def api_call():
    pass


# Circuit Breaker
breaker = CircuitBreaker(fail_max=5, timeout_seconds=60)
result = await breaker.call(api_call)
```

#### Go

```go
// Quick setup: Go's standard library + hystrix-go
import "github.com/grpc-ecosystem/go-grpc-middleware/retry"

// Retry with exponential backoff
grpc.WithUnaryInterceptor(
    grpc_retry.UnaryClientInterceptor(
        grpc_retry.WithMax(3),
        grpc_retry.WithBackoff(grpc_retry.BackoffExponential(time.Second)),
    ),
)

// Circuit Breaker (hystrix-go)
import "github.com/afex/hystrix-go/hystrix"

hystrix.Do("my-command", func() error {
    return doWork()
}, func(err error) error {
    return fallback()
})
```

#### Java/Spring

```java
// Quick setup: Resilience4j or Spring Cloud CircuitBreaker
@CircuitBreaker(name = "api-service")
@Retry(name = "api-service", fallback = "fallback")
@Timeout(name = "api-service")
public CompletableFuture<String> callApi() {
    return CompletableFuture.completedFuture("data");
}

public String fallback(Exception e) {
    return "fallback";
}
```

#### Node.js

```javascript
// Quick setup: node-retry + circuit-breaker-js
const retry = require("async-retry");
const CircuitBreaker = require("opossum");

// Retry
const data = await retry(
  async (bail) => {
    return await fetchApi();
  },
  { retries: 3, minTimeout: 2000, maxTimeout: 60000 },
);

// Circuit Breaker
const breaker = new CircuitBreaker(
  async () => {
    return await fetchApi();
  },
  { timeout: 3000, errorThresholdPercentage: 50, resetTimeout: 60000 },
);
```

---

## Failure Mode Analysis

### By Error Type

#### Transient Network Errors (Should Retry)

| Error                   | Pattern         | Max Retries | Backoff     |
| ----------------------- | --------------- | ----------- | ----------- |
| Connection Refused      | Retry + CB      | 3           | Exponential |
| Timeout                 | Retry + CB      | 3           | Exponential |
| DNS Failure             | Retry + CB      | 2           | Linear      |
| SSL Error (self-signed) | Fallback        | 0           | N/A         |
| Socket Reset            | Retry + CB      | 3           | Exponential |
| Rate Limit (429)        | Retry + Backoff | 3-5         | Exponential |

#### Permanent Failures (Should Not Retry)

| Error            | Pattern    | Action                    |
| ---------------- | ---------- | ------------------------- |
| 400 Bad Request  | Fail Fast  | Log error, don't retry    |
| 401 Unauthorized | Fail Fast  | Refresh token, retry once |
| 403 Forbidden    | Fail Fast  | Log error, don't retry    |
| 404 Not Found    | Fail Fast  | Log error, don't retry    |
| 500 Server Error | Retry + CB | Retry if transient        |
| 502 Bad Gateway  | Retry + CB | Likely transient          |
| 503 Unavailable  | Retry + CB | Service down, wait        |

---

## Configuration Decision Tree

### Circuit Breaker Configuration

```
START: Configure Circuit Breaker
    ↓
Q1: How critical is this service?
    CRITICAL → fail_max=3, timeout=30s
    NORMAL   → fail_max=5, timeout=60s
    NON-CRIT → fail_max=10, timeout=120s
    ↓
Q2: How fast should it recover?
    FAST     → success_threshold=1
    MEDIUM   → success_threshold=2
    SLOW     → success_threshold=5
    ↓
Q3: Network timeout?
    SLOW NET → timeout=120s
    NORMAL   → timeout=60s
    FAST NET → timeout=30s
    ↓
END: Apply config to CircuitBreaker()
```

### Retry Configuration

```
START: Configure Retry
    ↓
Q1: Is operation idempotent?
    YES  → Can retry safely
    NO   → Limit retries to 1-2, add request ID
    ↓
Q2: Expected failure rate?
    HIGH (>10%)  → max_retries=5
    MEDIUM (1-10%) → max_retries=3
    LOW (<1%)      → max_retries=2
    ↓
Q3: How fast should backoff be?
    FAST   → base_wait=0.5s, max=30s
    NORMAL → base_wait=2s, max=60s
    SLOW   → base_wait=5s, max=300s
    ↓
END: Apply config to @retry decorator
```

### Timeout Configuration

```
START: Configure Timeout
    ↓
Q1: Service SLO?
    P99 < 1s  → timeout=2s
    P99 < 5s  → timeout=10s
    P99 < 30s → timeout=60s
    ↓
Q2: Network latency?
    < 50ms   → timeout=2 × P99
    < 500ms  → timeout=2 × P99 + 1000ms
    > 500ms  → timeout=2 × P99 + 2000ms
    ↓
Q3: Must complete?
    HARD DEADLINE → SLO × 0.9
    SOFT DEADLINE → SLO × 1.5
    NO DEADLINE   → 2 × P99
    ↓
END: Apply timeout to async/await or HTTP client
```

---

## Monitoring Metrics Reference

### Key Metrics by Pattern

#### Circuit Breaker Metrics

```
Metric: circuit_breaker_state
  Values: CLOSED (0), HALF_OPEN (1), OPEN (2)
  Alert: state == OPEN for > 60s

Metric: circuit_breaker_calls_total
  Type: Counter
  Labels: circuit_name, outcome (success, failure, rejected)

Metric: circuit_breaker_state_transitions
  Type: Counter
  Labels: circuit_name, from_state, to_state
  Alert: repeated transitions (flapping)

Metric: circuit_breaker_failure_rate
  Type: Gauge
  Formula: failures / (failures + successes)
  Alert: failure_rate > threshold
```

#### Retry Metrics

```
Metric: retries_total
  Type: Counter
  Labels: operation, result (success, failure)
  Alert: failure_rate > 5%

Metric: retry_attempts_distribution
  Type: Histogram
  Buckets: [1, 2, 3, 4, 5]
  Alert: p95_attempts > 3

Metric: retry_latency_added
  Type: Histogram
  Formula: actual_latency - optimal_latency
  Alert: p95_added_latency > 5s
```

#### Bulkhead Metrics

```
Metric: bulkhead_utilization
  Type: Gauge
  Formula: active_tasks / max_concurrent
  Alert: utilization > 0.9 for > 30s

Metric: bulkhead_rejected
  Type: Counter
  Labels: bulkhead_name, reason
  Alert: rejected_count > 0 (indicates overload)

Metric: bulkhead_wait_time
  Type: Histogram
  Alert: p99_wait > SLO × 0.1
```

#### Timeout Metrics

```
Metric: timeouts_total
  Type: Counter
  Labels: operation, outcome (timeout, success)
  Alert: timeout_rate > 1%

Metric: timeout_latency
  Type: Histogram
  Alert: p99_latency > timeout_value × 0.8
```

#### Load Shed Metrics

```
Metric: load_shed_total
  Type: Counter
  Labels: reason (queue_full, overload, priority)
  Alert: shed_count > 0 (indicates persistent overload)

Metric: queue_depth
  Type: Gauge
  Alert: depth > 0.9 × max_capacity

Metric: queue_wait_time
  Type: Histogram
  Alert: p99_wait > 5s
```

---

## Troubleshooting Decision Tree

### Circuit Breaker Problems

```
ISSUE: Circuit Breaker always OPEN
├─ Q1: Last failure time?
│  ├─ > timeout? → Set state to HALF_OPEN manually
│  └─ < timeout? → Wait for timeout to elapse
├─ Q2: Failure count?
│  ├─ > fail_max? → Reset counter or increase threshold
│  └─ ≤ fail_max? → Check for repeated failures
└─ Q3: Dependencies healthy?
   ├─ YES → Circuit Breaker is working (protecting you)
   └─ NO → Fix dependency, then reset circuit

ISSUE: Circuit Breaker oscillating (flapping)
├─ Q1: Service intermittently failing?
│  ├─ YES → Increase timeout; add retry before CB
│  └─ NO → Check monitoring (false positives?)
├─ Q2: Threshold too low?
│  ├─ YES → Increase fail_max from 5 to 10
│  └─ NO → Analyze failure pattern
└─ → Increase success_threshold from 2 to 5
```

### Retry Problems

```
ISSUE: Retry storms (too many retries)
├─ Q1: Max retries > 3?
│  ├─ YES → Reduce to 2-3
│  └─ NO → Check backoff multiplier
├─ Q2: Backoff too short?
│  ├─ YES → Increase min from 1s to 5s
│  └─ NO → Check error type
└─ → Limit retry to idempotent operations only

ISSUE: Retries causing duplicate work
├─ Q1: Operation idempotent?
│  ├─ YES → Retries are safe
│  └─ NO → Add idempotency key (request ID)
├─ Q2: Database constraint failures?
│  ├─ YES → Use UPSERT instead of INSERT
│  └─ NO → Add application-level dedup
└─ → Consider circuit breaker instead
```

### Timeout Problems

```
ISSUE: Timeouts happening even with fast operations
├─ Q1: What's the P99 latency?
│  ├─ < timeout? → Timeout is too short
│  └─ > timeout? → Operation is actually slow
├─ Q2: Network variable?
│  ├─ YES → Add 2-3s buffer to timeout
│  └─ NO → Timeout matches data
└─ → Increase timeout to P99 + 2-3s

ISSUE: Operations timeout when load spikes
├─ Q1: Timeout global or per-operation?
│  ├─ GLOBAL → Too aggressive; adjust
│  └─ PER-OP → Individual operation is slow
├─ Q2: Overloaded system?
│  ├─ YES → Add load shedding or bulkhead
│  └─ NO → Increase timeout temporarily
└─ → Scale horizontally
```

---

## Quick Reference Cheat Sheet

### Retry Configuration Quick Copy

```python
# Conservative (safe)
@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=5, max=60))

# Standard (recommended)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=60))

# Aggressive (for transient-heavy systems)
@retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=30))
```

### Circuit Breaker Configuration Quick Copy

```python
# Conservative
CircuitBreaker(fail_max=3, timeout_seconds=30)

# Standard (recommended)
CircuitBreaker(fail_max=5, timeout_seconds=60)

# Lenient (for flaky services)
CircuitBreaker(fail_max=10, timeout_seconds=120)
```

### Timeout Configuration Quick Copy

```python
# API calls
timeout_sec = 30  # 30s for external APIs

# Database queries
timeout_sec = 5  # 5s for queries

# Background tasks
timeout_sec = 300  # 5 min for long tasks

# Microservices
timeout_sec = 10  # 10s inter-service
```

### Bulkhead Configuration Quick Copy

```python
# CPU-bound
max_workers = cpu_count  # 8 on 8-core

# I/O-bound
max_workers = cpu_count * 2  # 16 on 8-core

# Database
pool_size = 20  # Conservative
pool_size = 50  # Aggressive
```

---

## Conclusion

Use this reference to:

1. **Find your scenario** in the scenario matrix
2. **Choose patterns** from the recommendation
3. **Configure quickly** using the provided settings
4. **Monitor with** the listed metrics
5. **Troubleshoot using** the decision tree

For detailed explanations, see: `/docs/research/DYNAMIC_SCALING_AND_SELF_HEALING_PATTERNS.md`

For quick implementation, see: `/docs/guides/RESILIENCE_IMPLEMENTATION_QUICKSTART.md`

---

**Document Version**: 1.0
**Last Updated**: 2026-02-19
**Status**: Ready for Reference
