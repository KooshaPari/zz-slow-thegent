# context_injection API Reference

> **Source**: `src/thegent/context/context_injection.py`

Phase 14: Context Injection implementation.

Includes AGENT.md template system, tool-specific context symlinks, and dynamic updates.

---

## ContextInjector

Manages injection of context into agents.

### Methods

#### ContextInjector.**init**

```python
__init__(self: Any, project_root: Path)
```

---

#### ContextInjector.render_agent_md

```python
render_agent_md(self: Any, agent_info: dict[(str, Any)], mesh_state: dict[(str, Any)])
```

Render AGENT.md from template with current mesh state.

---

#### ContextInjector.setup_tool_context

```python
setup_tool_context(self: Any, agent_dir: Path, agent_type: str)
```

Set up tool-specific context files (symlinks).

---

#### ContextInjector.update_context

```python
update_context(self: Any, agent_id: str, agent_dir: Path, mesh_state: dict[(str, Any)])
```

Dynamically update AGENT.md when mesh state changes.

---

---

## render_agent_md

```python
render_agent_md(self: Any, agent_info: dict[(str, Any)], mesh_state: dict[(str, Any)])
```

Render AGENT.md from template with current mesh state.

---

## setup_tool_context

```python
setup_tool_context(self: Any, agent_dir: Path, agent_type: str)
```

Set up tool-specific context files (symlinks).

---

## update_context

```python
update_context(self: Any, agent_id: str, agent_dir: Path, mesh_state: dict[(str, Any)])
```

Dynamically update AGENT.md when mesh state changes.

---
