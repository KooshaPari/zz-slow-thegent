# dex_flash_agents API Reference

> **Source**: `src/thegent/cross_project/dex_flash_agents.py`

Port dex flash agents to other projects.

---

## DexFlashAgents

Dex flash agents port.

### Methods

#### DexFlashAgents.**init**

```python
__init__(self: Any)
```

Initialize dex flash agents.

---

#### DexFlashAgents.flash_execute

```python
flash_execute(self: Any, agent_name: str, command: str)
```

Execute flash command.

**Parameters**:

- `agent_name`: Agent name
- `command`: Command to execute

**Returns**: Execution result

---

#### DexFlashAgents.register_flash_agent

```python
register_flash_agent(self: Any, name: str, agent: Any)
```

Register a flash agent.

**Parameters**:

- `name`: Agent name
- `agent`: Agent implementation

---

---

## flash_execute

```python
flash_execute(self: Any, agent_name: str, command: str)
```

Execute flash command.

**Parameters**:

- `agent_name`: Agent name
- `command`: Command to execute

**Returns**: Execution result

---

## register_flash_agent

```python
register_flash_agent(self: Any, name: str, agent: Any)
```

Register a flash agent.

**Parameters**:

- `name`: Agent name
- `agent`: Agent implementation

---
