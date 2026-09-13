# plangent_subagents API Reference

> **Source**: `src/thegent/cross_project/plangent_subagents.py`

Integrate plangent sub-agents into thegent.

---

## PlangentSubagents

Plangent sub-agents integration.

### Methods

#### PlangentSubagents.**init**

```python
__init__(self: Any)
```

Initialize plangent subagents.

---

#### PlangentSubagents.execute

```python
execute(self: Any, subagent_name: str, task: dict[(str, Any)])
```

Execute task with subagent.

**Parameters**:

- `subagent_name`: Subagent name
- `task`: Task dictionary

**Returns**: Execution result

---

#### PlangentSubagents.register_subagent

```python
register_subagent(self: Any, name: str, agent: Any)
```

Register a plangent subagent.

**Parameters**:

- `name`: Subagent name
- `agent`: Agent implementation

---

---

## execute

```python
execute(self: Any, subagent_name: str, task: dict[(str, Any)])
```

Execute task with subagent.

**Parameters**:

- `subagent_name`: Subagent name
- `task`: Task dictionary

**Returns**: Execution result

---

## register_subagent

```python
register_subagent(self: Any, name: str, agent: Any)
```

Register a plangent subagent.

**Parameters**:

- `name`: Subagent name
- `agent`: Agent implementation

---
