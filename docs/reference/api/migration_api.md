# migration API Reference

> **Source**: `src/thegent/contracts/migration.py`

Contract Migration Controller.

Manages the transition between contract versions, enforces deprecation policies,
and evaluates migration window compliance.

---

## MigrationController

Controls and monitors contract version migrations (WP-7008).

### Methods

#### MigrationController.**init**

```python
__init__(self: Any, registry: Any)
```

---

#### MigrationController.evaluate_version

```python
evaluate_version(self: Any, contract_id: str, version: str)
```

Evaluate if a contract version is suitable for current use.

**Returns**: Dictionary with keys: 'allowed', 'status', 'reason', 'migration_days_left'.

---

#### MigrationController.get_preferred_version

```python
get_preferred_version(self: Any, contract_id: str)
```

Return the latest non-deprecated version for a contract ID.

---

#### MigrationController.set_canary

```python
set_canary(self: Any, percentage: float)
```

Set canary rollout percentage (WP-7008).

---

#### MigrationController.set_dual_write

```python
set_dual_write(self: Any, enabled: bool)
```

Enable or disable dual-write mode (WP-7008).

---

#### MigrationController.should_use_new_version

```python
should_use_new_version(self: Any, run_id: str)
```

Determine if a run should use the target migration version based on canary.

---

---

## evaluate_version

```python
evaluate_version(self: Any, contract_id: str, version: str)
```

Evaluate if a contract version is suitable for current use.

**Returns**: Dictionary with keys: 'allowed', 'status', 'reason', 'migration_days_left'.

---

## get_preferred_version

```python
get_preferred_version(self: Any, contract_id: str)
```

Return the latest non-deprecated version for a contract ID.

---

## set_canary

```python
set_canary(self: Any, percentage: float)
```

Set canary rollout percentage (WP-7008).

---

## set_dual_write

```python
set_dual_write(self: Any, enabled: bool)
```

Enable or disable dual-write mode (WP-7008).

---

## should_use_new_version

```python
should_use_new_version(self: Any, run_id: str)
```

Determine if a run should use the target migration version based on canary.

---
