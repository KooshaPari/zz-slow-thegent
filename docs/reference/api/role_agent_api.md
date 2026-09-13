# role_agent API Reference

> **Source**: `src/thegent/agents/role_agent.py`

Role-based agent runner - wraps another runner and injects a system prompt.

---

## RoleAgentRunner

Wraps another runner and injects a role-based system prompt.

**Inherits from**: `AgentRunner`

### Methods

#### RoleAgentRunner.**init**

```python
__init__(self: Any, role: TaskRole, base_runner: AgentRunner)
```

---

#### RoleAgentRunner.run

```python
run(self: Any, prompt: str, cwd: Any, mode: str, timeout: int)
```

---

---

## run

```python
run(self: Any, prompt: str, cwd: Any, mode: str, timeout: int) -> RunResult
```

---
