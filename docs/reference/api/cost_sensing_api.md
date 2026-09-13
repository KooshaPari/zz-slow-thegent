# cost_sensing API Reference

> **Source**: `src/thegent/phases/cost_sensing.py`

Cost sensing and learning test matrix.

---

## CostSensingTestMatrix

Test matrix for cost sensing and learning.

### Methods

#### CostSensingTestMatrix.**init**

```python
__init__(self: Any)
```

Initialize cost sensing test matrix.

---

#### CostSensingTestMatrix.get_test_status

```python
get_test_status(self: Any)
```

Get status of all tests.

**Returns**: Status dictionary

---

#### CostSensingTestMatrix.run_test

```python
run_test(self: Any, test_id: str)
```

Run a test.

**Parameters**:

- `test_id`: Test identifier

**Returns**: Test result

---

---

## get_test_status

```python
get_test_status(self: Any)
```

Get status of all tests.

**Returns**: Status dictionary

---

## run_test

```python
run_test(self: Any, test_id: str)
```

Run a test.

**Parameters**:

- `test_id`: Test identifier

**Returns**: Test result

---
