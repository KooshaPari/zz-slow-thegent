# enterprise_lifecycle API Reference

> **Source**: `src/thegent/phases/enterprise_lifecycle.py`

Enterprise lifecycle and compliance surface map.

---

## EnterpriseLifecycleManager

Manager for enterprise lifecycle and compliance.

### Methods

#### EnterpriseLifecycleManager.**init**

```python
__init__(self: Any)
```

Initialize enterprise lifecycle manager.

---

#### EnterpriseLifecycleManager.get_lifecycle_map

```python
get_lifecycle_map(self: Any)
```

Get complete lifecycle map.

**Returns**: Lifecycle map dictionary

---

#### EnterpriseLifecycleManager.get_stage_compliance

```python
get_stage_compliance(self: Any, stage: str)
```

Get compliance checks for a stage.

**Parameters**:

- `stage`: Lifecycle stage

**Returns**: List of compliance checks

---

#### EnterpriseLifecycleManager.register_compliance_check

```python
register_compliance_check(self: Any, stage: str, check: str)
```

Register a compliance check for a stage.

**Parameters**:

- `stage`: Lifecycle stage
- `check`: Compliance check name

---

---

## get_lifecycle_map

```python
get_lifecycle_map(self: Any)
```

Get complete lifecycle map.

**Returns**: Lifecycle map dictionary

---

## get_stage_compliance

```python
get_stage_compliance(self: Any, stage: str)
```

Get compliance checks for a stage.

**Parameters**:

- `stage`: Lifecycle stage

**Returns**: List of compliance checks

---

## register_compliance_check

```python
register_compliance_check(self: Any, stage: str, check: str)
```

Register a compliance check for a stage.

**Parameters**:

- `stage`: Lifecycle stage
- `check`: Compliance check name

---
