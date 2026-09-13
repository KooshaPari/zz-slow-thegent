# codex_proxy API Reference

> **Source**: `src/thegent/agents/codex_proxy.py`

Codex via CLIProxyAPIPlus - claude, codex, gemini, copilot, antigravity through our proxy. Native gemini/copilot swapped to Codex (proxy API).

---

## CodexProxyRunner

Runs claude, codex, gemini, copilot, antigravity via Codex CLI pointing at our CLIProxyAPIPlus. gemini/copilot route via proxy (no native CLI).

**Inherits from**: `AgentRunner`

### Methods

#### CodexProxyRunner.**init**

```python
__init__(self: Any, agent_name: str, settings: Any, model: str, use_litellm_router: Any)
```

---

#### CodexProxyRunner.run

```python
run(self: Any, prompt: str, cwd: Any, mode: str, timeout: int)
```

---

#### CodexProxyRunner.run_with_metadata

```python
run_with_metadata(self: Any, prompt: str, cwd: Any, mode: str, timeout: int)
```

Run agent using resolved routing from TaskMetadata.

This method consumes resolved_provider and resolved_model_alias
from the routing classification.

**Parameters**:

- `prompt`: User prompt
- `cwd`: Working directory
- `mode`: Execution mode (read/write/full)
- `timeout`: Timeout in seconds
- `metadata`: TaskMetadata with resolved routing

**Returns**: RunResult from execution

---

---

## run

```python
run(self: Any, prompt: str, cwd: Any, mode: str, timeout: int) -> RunResult
```

---

## run_with_metadata

```python
run_with_metadata(self: Any, prompt: str, cwd: Any, mode: str, timeout: int)
```

Run agent using resolved routing from TaskMetadata.

This method consumes resolved_provider and resolved_model_alias
from the routing classification.

**Parameters**:

- `prompt`: User prompt
- `cwd`: Working directory
- `mode`: Execution mode (read/write/full)
- `timeout`: Timeout in seconds
- `metadata`: TaskMetadata with resolved routing

**Returns**: RunResult from execution

---
