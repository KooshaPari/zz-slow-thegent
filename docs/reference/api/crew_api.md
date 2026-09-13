# crew API Reference

> **Source**: `src/thegent/agent/crew.py`

Agent Crew stack implementation.

---

## Crew

Agent crew for coordinating multiple agents.

### Methods

#### Crew.**init**

```python
__init__(self: Any, agents: list[Any])
```

Initialize crew.

**Parameters**:

- `agents`: List of agents in the crew

---

#### Crew.add_agent

```python
add_agent(self: Any, agent: Any)
```

Add an agent to the crew.

**Parameters**:

- `agent`: Agent to add

---

#### Crew.execute

```python
execute(self: Any, task: dict[(str, Any)])
```

Execute a task with the crew.

**Parameters**:

- `task`: Task dictionary

**Returns**: Execution result

---

---

## add_agent

```python
add_agent(self: Any, agent: Any)
```

Add an agent to the crew.

**Parameters**:

- `agent`: Agent to add

---

## execute

```python
execute(self: Any, task: dict[(str, Any)])
```

Execute a task with the crew.

**Parameters**:

- `task`: Task dictionary

**Returns**: Execution result

---
