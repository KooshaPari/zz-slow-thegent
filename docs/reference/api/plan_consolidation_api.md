# plan_consolidation API Reference

> **Source**: `src/thegent/sync/plan_consolidation.py`

Plan consolidation automation.

---

## PlanConsolidation

Automate plan consolidation.

### Methods

#### PlanConsolidation.**init**

```python
__init__(self: Any, plans_dir: Any)
```

Initialize plan consolidation.

**Parameters**:

- `plans_dir`: Plans directory path

---

#### PlanConsolidation.consolidate

```python
consolidate(self: Any, output_file: Any)
```

Consolidate all plans.

**Parameters**:

- `output_file`: Output file path

**Returns**: Consolidation results

---

#### PlanConsolidation.find_plans

```python
find_plans(self: Any)
```

Find all plan files.

**Returns**: List of plan file paths

---

---

## consolidate

```python
consolidate(self: Any, output_file: Any)
```

Consolidate all plans.

**Parameters**:

- `output_file`: Output file path

**Returns**: Consolidation results

---

## find_plans

```python
find_plans(self: Any)
```

Find all plan files.

**Returns**: List of plan file paths

---
