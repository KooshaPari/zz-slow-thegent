# offload API Reference

> **Source**: `src/thegent/compute/offload.py`

Compute Offloading Mac↔PC.

---

## ComputeOffload

Compute offloading between Mac and PC.

### Methods

#### ComputeOffload.**init**

```python
__init__(self: Any)
```

Initialize compute offload.

---

#### ComputeOffload.offload

```python
offload(self: Any, target_id: str, command: str)
```

Offload computation to target.

**Parameters**:

- `target_id`: Target identifier
- `command`: Command to execute

**Returns**: Execution result

---

#### ComputeOffload.register_target

```python
register_target(self: Any, target_id: str, host: str, port: int)
```

Register an offload target.

**Parameters**:

- `target_id`: Target identifier
- `host`: Host address
- `port`: SSH port

---

---

## offload

```python
offload(self: Any, target_id: str, command: str)
```

Offload computation to target.

**Parameters**:

- `target_id`: Target identifier
- `command`: Command to execute

**Returns**: Execution result

---

## register_target

```python
register_target(self: Any, target_id: str, host: str, port: int)
```

Register an offload target.

**Parameters**:

- `target_id`: Target identifier
- `host`: Host address
- `port`: SSH port

---
