# economic_governance API Reference

> **Source**: `src/thegent/research/economic_governance.py`

Economic Governance (Cost-Aware Routing).

---

## EconomicGovernance

Economic governance for cost-aware routing.

### Methods

#### EconomicGovernance.**init**

```python
__init__(self: Any)
```

Initialize economic governance.

---

#### EconomicGovernance.check_budget

```python
check_budget(self: Any, tenant_id: str, cost: float)
```

Check if operation is within budget.

**Parameters**:

- `tenant_id`: Tenant identifier
- `cost`: Operation cost

**Returns**: True if within budget

---

#### EconomicGovernance.route_with_governance

```python
route_with_governance(self: Any, tenant_id: str, options: list[dict[(str, Any)]])
```

Route with economic governance constraints.

**Parameters**:

- `tenant_id`: Tenant identifier
- `options`: Routing options

**Returns**: Selected route or None

---

#### EconomicGovernance.set_budget_limit

```python
set_budget_limit(self: Any, tenant_id: str, limit: float)
```

Set budget limit for a tenant.

**Parameters**:

- `tenant_id`: Tenant identifier
- `limit`: Budget limit

---

---

## check_budget

```python
check_budget(self: Any, tenant_id: str, cost: float)
```

Check if operation is within budget.

**Parameters**:

- `tenant_id`: Tenant identifier
- `cost`: Operation cost

**Returns**: True if within budget

---

## route_with_governance

```python
route_with_governance(self: Any, tenant_id: str, options: list[dict[(str, Any)]])
```

Route with economic governance constraints.

**Parameters**:

- `tenant_id`: Tenant identifier
- `options`: Routing options

**Returns**: Selected route or None

---

## set_budget_limit

```python
set_budget_limit(self: Any, tenant_id: str, limit: float)
```

Set budget limit for a tenant.

**Parameters**:

- `tenant_id`: Tenant identifier
- `limit`: Budget limit

---
