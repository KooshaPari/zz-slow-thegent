# billing API Reference

> **Source**: `src/thegent/orchestration/billing.py`

WP-19004: Quota & Billing for Multi-Tenant Teams.

Enforces resource quotas (runs, tokens, storage) per team/tenant.

---

## TeamBillingManager

Manages resource quotas and billing for multi-tenant teams.

### Methods

#### TeamBillingManager.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### TeamBillingManager.check_quota

```python
check_quota(self: Any, team_id: str, resource: str, cost: float)
```

Check if a team has enough quota for a resource.

---

#### TeamBillingManager.get_billing_report

```python
get_billing_report(self: Any, team_id: str)
```

Generate a billing report for a team.

---

#### TeamBillingManager.record_usage

```python
record_usage(self: Any, team_id: str, resource: str, amount: float)
```

Record resource usage for a team.

---

---

## check_quota

```python
check_quota(self: Any, team_id: str, resource: str, cost: float)
```

Check if a team has enough quota for a resource.

---

## get_billing_report

```python
get_billing_report(self: Any, team_id: str)
```

Generate a billing report for a team.

---

## record_usage

```python
record_usage(self: Any, team_id: str, resource: str, amount: float)
```

Record resource usage for a team.

---
