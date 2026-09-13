# tool_adapter API Reference

> **Source**: `src/thegent/agents/tool_adapter.py`

WP-24002: Recursive Tool Discovery & Adaptation.

Enables agents to discover, wrap, and use new tools dynamically at runtime.
Includes automatic interface adaptation for foreign tool protocols.

---

## ToolAdapter

Adapts foreign tool interfaces to thegent's canonical tool protocol.

### Methods

#### ToolAdapter.**init**

```python
__init__(self: Any, agent_id: str)
```

---

#### ToolAdapter.discover_tools

```python
discover_tools(self: Any, target_path: str)
```

Scan a path or endpoint for new tools.

---

#### ToolAdapter.generate_binding

```python
generate_binding(self: Any, tool_id: str)
```

Generate a Python/JSON binding for the tool to be used in prompts.

---

#### ToolAdapter.wrap_tool

```python
wrap_tool(self: Any, tool_id: str)
```

Wrap a discovered tool into a standard execution function.

---

---

## ToolDefinition

Metadata for a dynamically discovered tool.

**Inherits from**: `BaseModel`

---

## discover_tools

```python
discover_tools(self: Any, target_path: str)
```

Scan a path or endpoint for new tools.

---

## generate_binding

```python
generate_binding(self: Any, tool_id: str)
```

Generate a Python/JSON binding for the tool to be used in prompts.

---

## wrap_tool

```python
wrap_tool(self: Any, tool_id: str)
```

Wrap a discovered tool into a standard execution function.

---
