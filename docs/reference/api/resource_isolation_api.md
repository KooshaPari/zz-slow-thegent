# resource_isolation API Reference

> **Source**: `src/thegent/isolation/resource_isolation.py`

Phase 10: Resource Isolation implementation.

Includes per-agent TMPDIR, port allocation, and environment isolation.

---

## EnvIsolator

Helper to wrap execution with isolated environment variables.

### Methods

#### EnvIsolator.wrap_env

```python
wrap_env(agent_id: str, custom_vars: dict[(str, str)])
```

---

---

## ResourceIsolator

Manages isolated resources for agents.

### Methods

#### ResourceIsolator.**init**

```python
__init__(self: Any, base_tmp_dir: Path)
```

---

#### ResourceIsolator.allocate_ports

```python
allocate_ports(self: Any, agent_id: str, count: int)
```

Dynamically allocate available ports for an agent.

---

#### ResourceIsolator.cleanup_agent

```python
cleanup_agent(self: Any, agent_id: str)
```

Cleanup isolated resources for an agent.

---

#### ResourceIsolator.setup_agent_env

```python
setup_agent_env(self: Any, agent_id: str)
```

Set up isolated environment for an agent.

---

---

## allocate_ports

```python
allocate_ports(self: Any, agent_id: str, count: int)
```

Dynamically allocate available ports for an agent.

---

## cleanup_agent

```python
cleanup_agent(self: Any, agent_id: str)
```

Cleanup isolated resources for an agent.

---

## setup_agent_env

```python
setup_agent_env(self: Any, agent_id: str)
```

Set up isolated environment for an agent.

---

## wrap_env

```python
wrap_env(agent_id: str, custom_vars: dict[(str, str)]) -> dict[(str, str)]
```

---
