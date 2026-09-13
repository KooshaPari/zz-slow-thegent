# budget_alerts API Reference

> **Source**: `src/thegent/orchestration/budget_alerts.py`

Budget alerts and cost-overage gates for the orchestration layer.

---

## BudgetAlertSystem

Check budgets and emit alerts.

### Methods

#### BudgetAlertSystem.**init**

```python
__init__(self: Any, cost_dir: Any, config: Any)
```

Initialize budget alert system.

**Parameters**:

- `cost_dir`: Directory where cost summaries are stored.
- `config`: Budget configuration.

---

#### BudgetAlertSystem.check_budget

```python
check_budget(self: Any, current_cost: float, context: str)
```

Check if cost exceeds budget.

**Parameters**:

- `current_cost`: Current cost in USD.
- `context`: Context for limit ("run", "hourly", "daily").

**Returns**: Tuple of (alert_level, is_blocking).
alert_level is one of "OK", "WARN", "BLOCK".

---

#### BudgetAlertSystem.from_settings

```python
from_settings(cls: Any, settings: ThegentSettings)
```

Create budget alert system from settings.

---

#### BudgetAlertSystem.get_daily_spend

```python
get_daily_spend(self: Any)
```

Get total spend in the current day.

Calculated by scanning the aggregate.jsonl log.

---

#### BudgetAlertSystem.get_hourly_spend

```python
get_hourly_spend(self: Any)
```

Get total spend in the current hour.

Calculated by scanning the aggregate.jsonl log.

---

---

## BudgetConfig

Budget configuration.

---

## check_budget

```python
check_budget(self: Any, current_cost: float, context: str)
```

Check if cost exceeds budget.

**Parameters**:

- `current_cost`: Current cost in USD.
- `context`: Context for limit ("run", "hourly", "daily").

**Returns**: Tuple of (alert_level, is_blocking).
alert_level is one of "OK", "WARN", "BLOCK".

---

## from_settings

```python
from_settings(cls: Any, settings: ThegentSettings)
```

Create budget alert system from settings.

---

## get_daily_spend

```python
get_daily_spend(self: Any)
```

Get total spend in the current day.

Calculated by scanning the aggregate.jsonl log.

---

## get_hourly_spend

```python
get_hourly_spend(self: Any)
```

Get total spend in the current hour.

Calculated by scanning the aggregate.jsonl log.

---
