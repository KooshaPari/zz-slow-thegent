# tool_router API Reference

> **Source**: `src/thegent/routing/tool_router.py`

Central Tool Router for thegent.

Implements the "Routed Toolset" pattern to bypass LLM tool limits (e.g., 128 tools).
Semantically selects and injects only relevant tools into the active context.

---

## ToolDefinition

Metadata for a registered tool.

**Inherits from**: `BaseModel`

---

## ToolRouter

Manages tool discovery and semantic routing.

### Methods

#### ToolRouter.**init**

```python
__init__(self: Any, registry_path: Optional[Path])
```

---

#### ToolRouter.get_tool_prompt_injection

```python
get_tool_prompt_injection(self: Any, prompt: str)
```

Generate a string of tool definitions to inject into the LLM context.

---

#### ToolRouter.register_tool

```python
register_tool(self: Any, tool: ToolDefinition)
```

Register a new tool in the router.

---

#### ToolRouter.route

```python
route(self: Any, prompt: str, limit: int)
```

Perform keyword-based routing to select relevant tools.

(Future: Upgrade to semantic search with embeddings)

---

#### ToolRouter.save_registry

```python
save_registry(self: Any)
```

Persist current tool registry to the filesystem.

---

---

## get_tool_prompt_injection

```python
get_tool_prompt_injection(self: Any, prompt: str)
```

Generate a string of tool definitions to inject into the LLM context.

---

## register_tool

```python
register_tool(self: Any, tool: ToolDefinition)
```

Register a new tool in the router.

---

## route

```python
route(self: Any, prompt: str, limit: int)
```

Perform keyword-based routing to select relevant tools.

(Future: Upgrade to semantic search with embeddings)

---

## save_registry

```python
save_registry(self: Any)
```

Persist current tool registry to the filesystem.

---
