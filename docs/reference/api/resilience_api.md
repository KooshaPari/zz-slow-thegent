# resilience API Reference

> **Source**: `src/thegent/agents/resilience.py`

Retry and fallback logic for agent runs.

Distinguishes:

- rate_limit / transient: retry same provider (429, 502/503/504, etc.)
- usage_limit: subscription/quota exhausted; fallback to different provider.

---

## FailureKind

Classification of agent run failure.

**Inherits from**: `StrEnum`

---

## FailureTaxonomy

WP-2005: Granular taxonomy of failures for root cause analysis.

**Inherits from**: `StrEnum`

---

## RecoveryEngine

WP-2004: Automated recovery playbooks for known failure patterns.

### Methods

#### RecoveryEngine.suggest_playbook

```python
suggest_playbook(self: Any, failure_type: str)
```

Return a recovery playbook for the given failure type.

---

---

## RetryBudget

WP-2002: SLO-aware retry budget.

---

## ToolCircuitBreaker

WP-2003: Circuit breaker for individual tools and models. Uses pybreaker.

### Methods

#### ToolCircuitBreaker.**init**

```python
__init__(self: Any, name: str, threshold: int, window_s: int)
```

---

#### ToolCircuitBreaker.is_open

```python
is_open(self: Any)
```

True if the circuit is open (too many recent failures).

---

#### ToolCircuitBreaker.record_failure

```python
record_failure(self: Any)
```

Record a failure event.

---

---

## ToolClass

WP-2002: Classification of tool calls for specialized retries.

**Inherits from**: `StrEnum`

---

## TransientAgentError

Raised when agent failed due to retryable condition (rate limit, 502, etc.).

**Inherits from**: `Exception`

### Methods

#### TransientAgentError.**init**

```python
__init__(self: Any, result: RunResult)
```

---

---

## UsageLimitError

Raised when provider hit usage/quota limit; caller should fallback to different provider.

**Inherits from**: `Exception`

### Methods

#### UsageLimitError.**init**

```python
__init__(self: Any, result: RunResult, agent: str)
```

---

---

## classify_failure

```python
classify_failure(result: RunResult)
```

Classify failure as rate_limit (retry), usage_limit (fallback), or unknown.

---

## classify_to_taxonomy

```python
classify_to_taxonomy(error_msg: str)
```

Classify a raw error message into the failure taxonomy.

---

## decorator

```python
decorator(fn: Callable[(Ellipsis, T)]) -> Callable[(Ellipsis, T)]
```

---

## is_open

```python
is_open(self: Any)
```

True if the circuit is open (too many recent failures).

---

## is_retryable

```python
is_retryable(result: RunResult)
```

Return True if failure is rate_limit or transient (retry same provider).

---

## is_usage_limit

```python
is_usage_limit(result: RunResult)
```

Return True if failure indicates usage/quota limit (fallback to different provider).

---

## record_failure

```python
record_failure(self: Any)
```

Record a failure event.

---

## suggest_playbook

```python
suggest_playbook(self: Any, failure_type: str)
```

Return a recovery playbook for the given failure type.

---

## with_retry

```python
with_retry(max_attempts: int, min_wait: float, max_wait: float)
```

Decorator that retries on TransientAgentError with exponential backoff.

---
