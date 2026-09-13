# costs API Reference

> **Source**: `src/thegent/governance/costs.py`

Cost capping, tracking, and budget alerts (WP-5001, WP-5003).

---

## BudgetAlert

Triggers alerts when cost reaches a threshold of the budget.

### Methods

#### BudgetAlert.**init**

```python
__init__(self: Any, threshold: float)
```

---

#### BudgetAlert.set_budget

```python
set_budget(self: Any, budget: float)
```

Set the total budget.

---

#### BudgetAlert.should_alert

```python
should_alert(self: Any, current_cost: float)
```

Check if an alert should be triggered.

---

---

## CostCap

Enforces a hard limit on action or session costs.

### Methods

#### CostCap.**init**

```python
__init__(self: Any, max_cost: float)
```

---

#### CostCap.check

```python
check(self: Any, cost: float)
```

Check if the given cost is within the cap.

---

---

## CostSensing

Provides cost-based feedback loops for autonomous learning.

### Methods

#### CostSensing.**init**

```python
__init__(self: Any, slo_regulator: Any)
```

---

#### CostSensing.check_cost_cap

```python
check_cost_cap(self: Any, action_cost: float, cap: float)
```

Check if action exceeds cost cap.

---

#### CostSensing.get_cost_feedback

```python
get_cost_feedback(self: Any, model_id: str)
```

Get cost feedback for learning system.

---

---

## CostTracker

Tracks real-time cost accumulation across sessions.

### Methods

#### CostTracker.**init**

```python
__init__(self: Any)
```

---

#### CostTracker.get_session_cost

```python
get_session_cost(self: Any, session_id: str)
```

Get the total accumulated cost for a session.

---

#### CostTracker.is_within_budget

```python
is_within_budget(self: Any, session_id: str, budget: float)
```

Check if a session is still within the provided budget.

---

#### CostTracker.record_cost

```python
record_cost(self: Any, session_id: str, cost: float)
```

Add cost to a session's total.

---

#### CostTracker.start_session

```python
start_session(self: Any, session_id: str)
```

Initialize tracking for a new session.

---

---

## check

```python
check(self: Any, cost: float)
```

Check if the given cost is within the cap.

---

## check_cost_cap

```python
check_cost_cap(self: Any, action_cost: float, cap: float)
```

Check if action exceeds cost cap.

---

## get_cost_feedback

```python
get_cost_feedback(self: Any, model_id: str)
```

Get cost feedback for learning system.

---

## get_session_cost

```python
get_session_cost(self: Any, session_id: str)
```

Get the total accumulated cost for a session.

---

## is_within_budget

```python
is_within_budget(self: Any, session_id: str, budget: float)
```

Check if a session is still within the provided budget.

---

## record_cost

```python
record_cost(self: Any, session_id: str, cost: float)
```

Add cost to a session's total.

---

## set_budget

```python
set_budget(self: Any, budget: float)
```

Set the total budget.

---

## should_alert

```python
should_alert(self: Any, current_cost: float)
```

Check if an alert should be triggered.

---

## start_session

```python
start_session(self: Any, session_id: str)
```

Initialize tracking for a new session.

---
