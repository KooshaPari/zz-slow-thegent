# aggregators API Reference

> **Source**: `src/thegent/cost/aggregators.py`

Cost aggregation primitives for thegent.

---

## BudgetAlert

Alerts when cost exceeds a percentage threshold of budget.

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

Set the budget amount.

---

#### BudgetAlert.should_alert

```python
should_alert(self: Any, current_cost: float)
```

Return True if current cost exceeds the threshold percentage of budget.

---

---

## CostCap

Enforces a maximum cost limit.

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

Return True if the cost is within the cap.

---

---

## CostTracker

Tracks costs per session in real time.

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

Get total cost for a session.

---

#### CostTracker.is_within_budget

```python
is_within_budget(self: Any, session_id: str, budget: float)
```

Check if session cost is within budget.

---

#### CostTracker.record_cost

```python
record_cost(self: Any, session_id: str, amount: float)
```

Record a cost for a session.

---

#### CostTracker.start_session

```python
start_session(self: Any, session_id: str)
```

Start tracking a new session.

---

---

## check

```python
check(self: Any, cost: float)
```

Return True if the cost is within the cap.

---

## get_session_cost

```python
get_session_cost(self: Any, session_id: str)
```

Get total cost for a session.

---

## is_within_budget

```python
is_within_budget(self: Any, session_id: str, budget: float)
```

Check if session cost is within budget.

---

## record_cost

```python
record_cost(self: Any, session_id: str, amount: float)
```

Record a cost for a session.

---

## set_budget

```python
set_budget(self: Any, budget: float)
```

Set the budget amount.

---

## should_alert

```python
should_alert(self: Any, current_cost: float)
```

Return True if current cost exceeds the threshold percentage of budget.

---

## start_session

```python
start_session(self: Any, session_id: str)
```

Start tracking a new session.

---
