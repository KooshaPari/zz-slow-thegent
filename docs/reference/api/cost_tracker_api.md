# cost_tracker API Reference

> **Source**: `src/thegent/routing/cost_tracker.py`

Cost tracking for LiteLLM routing.

Tracks LLM costs across sessions with budget alerts and JSONL logging
for integration with the Donut Architecture harvest system.

---

## CostEntry

Single cost tracking entry.

### Methods

#### CostEntry.to_json

```python
to_json(self: Any)
```

Serialize entry to JSON dict.

---

---

## CostTracker

Track LLM costs across sessions.

### Methods

#### CostTracker.**init**

```python
__init__(self: Any, log_path: Any, daily_budget: Any)
```

Initialize cost tracker.

**Parameters**:

- `log_path`: Path to JSONL cost log file.
- `daily_budget`: Optional daily budget limit in USD.

---

#### CostTracker.clear

```python
clear(self: Any)
```

Reset all tracking state.

---

#### CostTracker.daily_budget

```python
daily_budget(self: Any)
```

Configured daily budget.

---

#### CostTracker.get_budget_burn_ratio

```python
get_budget_burn_ratio(self: Any)
```

Get budget burn ratio (0-1). None if no budget set. 0.85+ triggers degraded mode.

---

#### CostTracker.get_budget_remaining

```python
get_budget_remaining(self: Any)
```

Get remaining budget, or None if no budget set.

---

#### CostTracker.get_daily_spend

```python
get_daily_spend(self: Any)
```

Get today's total spend in USD.

---

#### CostTracker.get_stats

```python
get_stats(self: Any)
```

Get cost statistics summary.

---

#### CostTracker.is_over_budget

```python
is_over_budget(self: Any)
```

Check if daily budget is exceeded.

---

#### CostTracker.log_path

```python
log_path(self: Any)
```

Path to the cost log file.

---

#### CostTracker.track

```python
track(self: Any, provider: str, model: str, usage: dict[(str, int)], cost: float, latency_ms: float, session_id: Any, is_error: bool, is_fallback: bool)
```

Track a single LLM call cost.

**Parameters**:

- `provider`: Provider name (e.g., "openai", "anthropic")
- `model`: Model name (e.g., "gpt-4", "claude-opus")
- `usage`: Dict with prompt_tokens and completion_tokens
- `cost`: Cost in USD
- `latency_ms`: Request latency in milliseconds
- `session_id`: Optional session identifier
- `is_error`: Whether the request resulted in an error
- `is_fallback`: Whether this was a fallback routing

**Returns**: The created CostEntry

---

---

## RoutingStats

Routing statistics summary.

---

## clear

```python
clear(self: Any)
```

Reset all tracking state.

---

## daily_budget

```python
daily_budget(self: Any)
```

Configured daily budget.

---

## get_budget_burn_ratio

```python
get_budget_burn_ratio(self: Any)
```

Get budget burn ratio (0-1). None if no budget set. 0.85+ triggers degraded mode.

---

## get_budget_remaining

```python
get_budget_remaining(self: Any)
```

Get remaining budget, or None if no budget set.

---

## get_cost_tracker

Get global cost tracker instance.

Initializes with settings from config on first call.

---

## get_daily_spend

```python
get_daily_spend(self: Any)
```

Get today's total spend in USD.

---

## get_stats

```python
get_stats(self: Any)
```

Get cost statistics summary.

---

## is_over_budget

```python
is_over_budget(self: Any)
```

Check if daily budget is exceeded.

---

## log_path

```python
log_path(self: Any)
```

Path to the cost log file.

---

## reset_cost_tracker

Reset the global cost tracker (useful for testing).

---

## to_json

```python
to_json(self: Any)
```

Serialize entry to JSON dict.

---

## track

```python
track(self: Any, provider: str, model: str, usage: dict[(str, int)], cost: float, latency_ms: float, session_id: Any, is_error: bool, is_fallback: bool)
```

Track a single LLM call cost.

**Parameters**:

- `provider`: Provider name (e.g., "openai", "anthropic")
- `model`: Model name (e.g., "gpt-4", "claude-opus")
- `usage`: Dict with prompt_tokens and completion_tokens
- `cost`: Cost in USD
- `latency_ms`: Request latency in milliseconds
- `session_id`: Optional session identifier
- `is_error`: Whether the request resulted in an error
- `is_fallback`: Whether this was a fallback routing

**Returns**: The created CostEntry

---
