# tenant_boundary_tests API Reference

> **Source**: `src/thegent/phases/tenant_boundary_tests.py`

Phase13: Tenant boundary test matrix (TB-001–TB-005).

---

## TenantBoundaryTestMatrix

Test matrix for tenant boundary validation.

### Methods

#### TenantBoundaryTestMatrix.**init**

```python
__init__(self: Any)
```

Initialize tenant boundary test matrix.

---

#### TenantBoundaryTestMatrix.run_all_tests

```python
run_all_tests(self: Any)
```

Run all tenant boundary tests.

**Returns**: Test results

---

#### TenantBoundaryTestMatrix.run_test

```python
run_test(self: Any, test_id: str)
```

Run a tenant boundary test.

**Parameters**:

- `test_id`: Test identifier

**Returns**: Test result

---

---

## run_all_tests

```python
run_all_tests(self: Any)
```

Run all tenant boundary tests.

**Returns**: Test results

---

## run_test

```python
run_test(self: Any, test_id: str)
```

Run a tenant boundary test.

**Parameters**:

- `test_id`: Test identifier

**Returns**: Test result

---
