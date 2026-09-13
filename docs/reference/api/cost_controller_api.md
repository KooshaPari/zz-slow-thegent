# cost_controller API Reference

> **Source**: `src/thegent/governance/cost_controller.py`

## BudgetTier

Throttle tier based on daily budget utilization percentage.

**Inherits from**: `StrEnum`

---

## CostController

Manages daily agent-call budgets with tiered throttling.

Budget is measured in agent trigger count (not dollars). When utilization
crosses tier thresholds the controller progressively restricts which agent
types may be spawned, ultimately halting all spawns at 95%+ utilization.

### Methods

#### CostController.**init**

```python
__init__(self: Any, session_dir: Path, health_targets_path: Path)
```

---

#### CostController.calls_remaining

```python
calls_remaining(self: Any)
```

Number of agent calls remaining in today's budget.

---

#### CostController.can_spawn

```python
can_spawn(self: Any, estimated_calls: int)
```

Return False when budget exhausted or insufficient for estimated_calls.

---

#### CostController.get_tier

```python
get_tier(self: Any)
```

Determine the current budget tier from today's utilization.

---

#### CostController.get_today_usage

```python
get_today_usage(self: Any)
```

Load or create today's usage record from the JSONL ledger.

---

#### CostController.record_call

```python
record_call(self: Any, dimension: str, agent: str)
```

Record one agent trigger against today's budget.

---

#### CostController.usage_path

```python
usage_path(self: Any)
```

---

---

## DailyUsage

Snapshot of agent call consumption for a single calendar day.

**Inherits from**: `BaseModel`

---

## calls_remaining

```python
calls_remaining(self: Any)
```

Number of agent calls remaining in today's budget.

---

## can_spawn

```python
can_spawn(self: Any, estimated_calls: int)
```

Return False when budget exhausted or insufficient for estimated_calls.

---

## get_tier

```python
get_tier(self: Any)
```

Determine the current budget tier from today's utilization.

---

## get_today_usage

```python
get_today_usage(self: Any)
```

Load or create today's usage record from the JSONL ledger.

---

## record_call

```python
record_call(self: Any, dimension: str, agent: str)
```

Record one agent trigger against today's budget.

---

## usage_path

```python
usage_path(self: Any) -> Path
```

---
