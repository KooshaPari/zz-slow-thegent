# work_stream_integration API Reference

> **Source**: `src/thegent/sync/work_stream_integration.py`

Work stream auto-incorporation.

---

## WorkStreamIntegration

Auto-incorporate items into work stream.

### Methods

#### WorkStreamIntegration.**init**

```python
__init__(self: Any, work_stream_path: Any)
```

Initialize work stream integration.

**Parameters**:

- `work_stream_path`: Path to WORK_STREAM.md

---

#### WorkStreamIntegration.incorporate_from_plans

```python
incorporate_from_plans(self: Any, plan_files: list[Path])
```

Incorporate items from plan files.

**Parameters**:

- `plan_files`: List of plan markdown files

**Returns**: Incorporation results

---

#### WorkStreamIntegration.update_work_stream

```python
update_work_stream(self: Any, items: list[dict[(str, Any)]])
```

Update work stream with new items.

**Parameters**:

- `items`: List of items to add

**Returns**: True if successful

---

---

## incorporate_from_plans

```python
incorporate_from_plans(self: Any, plan_files: list[Path])
```

Incorporate items from plan files.

**Parameters**:

- `plan_files`: List of plan markdown files

**Returns**: Incorporation results

---

## update_work_stream

```python
update_work_stream(self: Any, items: list[dict[(str, Any)]])
```

Update work stream with new items.

**Parameters**:

- `items`: List of items to add

**Returns**: True if successful

---
