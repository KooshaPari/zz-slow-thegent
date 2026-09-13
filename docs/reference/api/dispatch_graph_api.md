# dispatch_graph API Reference

> **Source**: `src/thegent/routing/dispatch_graph.py`

WP-10003: Dispatch graph implementation.

Provides deterministic resolution of operations through a policy-aware dispatch graph.

---

## DispatchResolver

Resolves an OperationEnvelopeV2 to a specific execution path.

### Methods

#### DispatchResolver.**init**

```python
__init__(self: Any, registry: Any)
```

---

#### DispatchResolver.add_alias

```python
add_alias(self: Any, alias: str, target_command: str)
```

Register an alias for a command (WP-10005).

---

#### DispatchResolver.resolve

```python
resolve(self: Any, envelope: Any)
```

Resolve the operation to a dispatch path.

**Returns**: Dict with 'dispatch_path', 'resolved_command', 'status'.

---

---

## add_alias

```python
add_alias(self: Any, alias: str, target_command: str)
```

Register an alias for a command (WP-10005).

---

## resolve

```python
resolve(self: Any, envelope: Any)
```

Resolve the operation to a dispatch path.

**Returns**: Dict with 'dispatch_path', 'resolved_command', 'status'.

---
