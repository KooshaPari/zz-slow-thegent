# aggregator_controller API Reference

> **Source**: `src/thegent/cost/aggregator_controller.py`

Budget tier management and cost controller for thegent.

---

## BudgetTier

Budget utilization tiers (FR-GOV-002).

**Inherits from**: `Enum`

---

## CostController

Manages daily agent call budgets and tier enforcement (FR-GOV-002).

### Methods

#### CostController.**init**

```python
__init__(self: Any, session_dir: Path, health_targets_path: Any)
```

---

#### CostController.can_spawn

```python
can_spawn(self: Any)
```

Check if new agent spawns are allowed.

---

#### CostController.get_tier

```python
get_tier(self: Any)
```

Determine current budget tier based on utilization.

---

#### CostController.get_today_usage

```python
get_today_usage(self: Any)
```

Return current usage snapshot.

---

#### CostController.record_call

```python
record_call(self: Any, dimension: str, agent: str)
```

Record a single agent call.

---

---

## UsageSnapshot

Current usage state.

### Methods

#### UsageSnapshot.utilization_pct

```python
utilization_pct(self: Any)
```

---

---

## can_spawn

```python
can_spawn(self: Any)
```

Check if new agent spawns are allowed.

---

## get_tier

```python
get_tier(self: Any)
```

Determine current budget tier based on utilization.

---

## get_today_usage

```python
get_today_usage(self: Any)
```

Return current usage snapshot.

---

## record_call

```python
record_call(self: Any, dimension: str, agent: str)
```

Record a single agent call.

---

## utilization_pct

```python
utilization_pct(self: Any) -> float
```

---
