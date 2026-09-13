# universal_adapter API Reference

> **Source**: `src/thegent/tools/universal_adapter.py`

WP-9005: Universal tool adapter layer.

Maps direct tool calls to unified operation envelopes with validation.

---

## UniversalToolAdapter

Adapts disparate tools to the unified operation surface.

### Methods

#### UniversalToolAdapter.**init**

```python
__init__(self: Any)
```

---

#### UniversalToolAdapter.call_tool

```python
call_tool(self: Any, command: str)
```

Call a tool through its operation-mapped adapter.

---

#### UniversalToolAdapter.register_adapter

```python
register_adapter(self: Any, command: str, adapter_fn: Callable[(Ellipsis, Any)])
```

Register an adapter for a specific CLI command.

---

---

## call_tool

```python
call_tool(self: Any, command: str)
```

Call a tool through its operation-mapped adapter.

---

## register_adapter

```python
register_adapter(self: Any, command: str, adapter_fn: Callable[(Ellipsis, Any)])
```

Register an adapter for a specific CLI command.

---

## validate_tool_schema

```python
validate_tool_schema(operation: Operation, payload: dict[(str, Any)])
```

WP-9005: Validate tool call payload against operation-specific schema.

---
