# router_manager API Reference

> **Source**: `src/thegent/agent/router_manager.py`

Router manager for agent routing.

---

## RouterManager

Manage routing of tasks to agents.

### Methods

#### RouterManager.**init**

```python
__init__(self: Any)
```

Initialize router manager.

---

#### RouterManager.register_route

```python
register_route(self: Any, pattern: str, agent: Any)
```

Register a routing pattern.

**Parameters**:

- `pattern`: Route pattern
- `agent`: Agent to route to

---

#### RouterManager.route

```python
route(self: Any, task: dict[(str, Any)])
```

Route a task to an agent.

**Parameters**:

- `task`: Task dictionary

**Returns**: Routed agent

---

---

## register_route

```python
register_route(self: Any, pattern: str, agent: Any)
```

Register a routing pattern.

**Parameters**:

- `pattern`: Route pattern
- `agent`: Agent to route to

---

## route

```python
route(self: Any, task: dict[(str, Any)])
```

Route a task to an agent.

**Parameters**:

- `task`: Task dictionary

**Returns**: Routed agent

---
