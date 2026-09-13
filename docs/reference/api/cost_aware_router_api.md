# cost_aware_router API Reference

> **Source**: `src/thegent/routing/cost_aware_router.py`

Budget-aware routing and economic governance for thegent.

Implements the Economic Governance Framework (WP-5003).

---

## Budget

A budget allocation for a project or session (FR-COST-001).

### Methods

#### Budget.remaining

```python
remaining(self: Any)
```

Return remaining budget in USD.

---

#### Budget.utilization

```python
utilization(self: Any)
```

Return fraction of budget spent.

---

---

## BudgetAwareRouter

Routes to optimal candidates while respecting cost budgets (FR-COST-003, WP-1004).

### Methods

#### BudgetAwareRouter.**init**

```python
__init__(self: Any, budget_manager: BudgetManager, pareto_router: Any, warn_at_pct: float, degraded_at_pct: float)
```

---

#### BudgetAwareRouter.route

```python
route(self: Any, project_id: str, candidates: list[RouteCandidate], strategy: str)
```

Select the best candidate given current budget state and Pareto strategy.

---

---

## BudgetExceededError

Raised when spend has exceeded a configured budget limit (FR-COST-002).

**Inherits from**: `Exception`

### Methods

#### BudgetExceededError.**init**

```python
__init__(self: Any, budget_type: str, limit: float, current: float)
```

---

---

## BudgetManager

Manages budget allocations and enforcement (FR-COST-003).

### Methods

#### BudgetManager.**init**

```python
__init__(self: Any)
```

---

#### BudgetManager.add_budget

```python
add_budget(self: Any, budget: Budget)
```

Add a budget allocation.

---

#### BudgetManager.check_budget

```python
check_budget(self: Any, project_id: str, requested_cost: float)
```

Check if any budget for project_id is exceeded.

---

#### BudgetManager.record_spend

```python
record_spend(self: Any, project_id: str, cost: float)
```

Update all relevant budgets for project_id with recorded cost.

---

---

## BudgetStatus

Status of a budget check.

---

## BudgetType

Supported budget scopes (SCLI-P9.1).

**Inherits from**: `Enum`

---

## CostAwareRouter

Simplified cost-aware router that selects candidates based on budget state.

### Methods

#### CostAwareRouter.**init**

```python
__init__(self: Any, budget: CostBudget, tracker: SimpleCostTracker)
```

---

#### CostAwareRouter.select

```python
select(self: Any, candidates: list[_SimpleCandidate])
```

Select the best candidate given current budget state.

---

---

## CostBudget

Simple budget specification with daily and session limits.

---

## CostMeter

Real-time cost metering for projects and models (FR-COST-001).

### Methods

#### CostMeter.**init**

```python
__init__(self: Any)
```

---

#### CostMeter.get_project_cost

```python
get_project_cost(self: Any, project_id: str)
```

Get total cost for a project across all models.

---

---

## SimpleCostTracker

Tracks session and daily cost totals.

### Methods

#### SimpleCostTracker.**init**

```python
__init__(self: Any)
```

---

#### SimpleCostTracker.daily_total

```python
daily_total(self: Any)
```

---

#### SimpleCostTracker.record

```python
record(self: Any, amount: float)
```

---

#### SimpleCostTracker.reset_session

```python
reset_session(self: Any)
```

---

#### SimpleCostTracker.session_total

```python
session_total(self: Any)
```

---

---

## \_SimpleCandidate

Route candidate for simplified CostAwareRouter.

---

## add_budget

```python
add_budget(self: Any, budget: Budget)
```

Add a budget allocation.

---

## check_budget

```python
check_budget(self: Any, project_id: str, requested_cost: float)
```

Check if any budget for project_id is exceeded.

---

## daily_total

```python
daily_total(self: Any) -> float
```

---

## get_project_cost

```python
get_project_cost(self: Any, project_id: str)
```

Get total cost for a project across all models.

---

## record

```python
record(self: Any, amount: float) -> None
```

---

## record_spend

```python
record_spend(self: Any, project_id: str, cost: float)
```

Update all relevant budgets for project_id with recorded cost.

---

## remaining

```python
remaining(self: Any)
```

Return remaining budget in USD.

---

## reset_session

```python
reset_session(self: Any) -> None
```

---

## route

```python
route(self: Any, project_id: str, candidates: list[RouteCandidate], strategy: str)
```

Select the best candidate given current budget state and Pareto strategy.

---

## select

```python
select(self: Any, candidates: list[_SimpleCandidate])
```

Select the best candidate given current budget state.

---

## session_total

```python
session_total(self: Any) -> float
```

---

## utilization

```python
utilization(self: Any)
```

Return fraction of budget spent.

---
