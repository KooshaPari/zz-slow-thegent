# direct_agents API Reference

> **Source**: `src/thegent/agents/direct_agents.py`

Direct agent invocation - cursor, claude, copilot, codex, gemini, opencode via CLIs.

---

## DirectAgentRunner

Invokes cursor, claude, copilot, codex, gemini directly via their CLIs.

**Inherits from**: `AgentRunner`

### Methods

#### DirectAgentRunner.**init**

```python
__init__(self: Any, agent_name: str, cli_cmd: Any, default_model: str, use_litellm_router: Any)
```

---

#### DirectAgentRunner.run

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
