# consistency_checker API Reference

> **Source**: `src/thegent/integration/consistency_checker.py`

System-wide consistency checker.

---

## ConsistencyChecker

Check consistency across system.

This class verifies that all system components are consistent,
including version consistency, path consistency, and configuration consistency.

### Methods

#### ConsistencyChecker.**init**

```python
__init__(self: Any)
```

Initialize consistency checker.

---

#### ConsistencyChecker.check_all

```python
check_all(self: Any)
```

Check all consistency rules.

**Returns**: List of consistency violations

---

---

## ConsistencyRule

Consistency rule definition.

---

## check_all

```python
check_all(self: Any)
```

Check all consistency rules.

**Returns**: List of consistency violations

---
