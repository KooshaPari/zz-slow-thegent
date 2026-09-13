# enterprise_compliance_tests API Reference

> **Source**: `src/thegent/phases/enterprise_compliance_tests.py`

Phase15: Enterprise compliance test matrix (EC-001–EC-006).

---

## EnterpriseComplianceTestMatrix

Test matrix for enterprise compliance.

### Methods

#### EnterpriseComplianceTestMatrix.**init**

```python
__init__(self: Any)
```

Initialize enterprise compliance test matrix.

---

#### EnterpriseComplianceTestMatrix.get_compliance_status

```python
get_compliance_status(self: Any)
```

Get overall compliance status.

**Returns**: Compliance status

---

#### EnterpriseComplianceTestMatrix.run_test

```python
run_test(self: Any, test_id: str)
```

Run a compliance test.

**Parameters**:

- `test_id`: Test identifier

**Returns**: Test result

---

---

## get_compliance_status

```python
get_compliance_status(self: Any)
```

Get overall compliance status.

**Returns**: Compliance status

---

## run_test

```python
run_test(self: Any, test_id: str)
```

Run a compliance test.

**Parameters**:

- `test_id`: Test identifier

**Returns**: Test result

---
