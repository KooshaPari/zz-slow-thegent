# health_check API Reference

> **Source**: `src/thegent/monitoring/health_check.py`

Health check utilities.

---

## HealthChecker

Health check system.

### Methods

#### HealthChecker.**init**

```python
__init__(self: Any)
```

Initialize health checker.

---

#### HealthChecker.register_check

```python
register_check(self: Any, name: str, check_fn: callable)
```

Register a health check.

**Parameters**:

- `name`: Check name
- `check_fn`: Check function

---

#### HealthChecker.run_checks

```python
run_checks(self: Any)
```

Run all health checks.

**Returns**: Health check results

---

---

## register_check

```python
register_check(self: Any, name: str, check_fn: callable)
```

Register a health check.

**Parameters**:

- `name`: Check name
- `check_fn`: Check function

---

## run_checks

```python
run_checks(self: Any)
```

Run all health checks.

**Returns**: Health check results

---
