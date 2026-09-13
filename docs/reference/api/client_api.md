# client API Reference

> **Source**: `src/thegent/acp/client.py`

ACP client adapter for spawning external ACP agents.

---

## ACPClientAdapter

AgentRunner implementation that spawns external ACP agents.

**Inherits from**: `AgentRunner`

### Methods

#### ACPClientAdapter.**init**

```python
__init__(self: Any, acp_command: list[str], agent_name: str)
```

Initialize ACP client adapter.

**Parameters**:

- `acp_command`: Command to spawn ACP agent (e.g., ["npx", "-y", "@zed-industries/claude-agent-acp"])
- `agent_name`: Name of the agent (for logging/identification)

---

#### ACPClientAdapter.run

```python
run(self: Any, prompt: str, cwd: Any, mode: str, timeout: int)
```

Run ACP agent via subprocess.

**Parameters**:

- `prompt`: User prompt/request
- `cwd`: Working directory
- `mode`: Agent mode (unused for ACP)
- `timeout`: Timeout in seconds
- `use_stream`: Whether to stream responses (unused for ACP)
- `live_output`: Whether to show live output (unused for ACP)
- `on_stdout`: Callback for stdout (unused for ACP)
- `on_stderr`: Callback for stderr (unused for ACP)

**Returns**: RunResult with stdout, stderr, exit_code

---

---

## run

```python
run(self: Any, prompt: str, cwd: Any, mode: str, timeout: int)
```

Run ACP agent via subprocess.

**Parameters**:

- `prompt`: User prompt/request
- `cwd`: Working directory
- `mode`: Agent mode (unused for ACP)
- `timeout`: Timeout in seconds
- `use_stream`: Whether to stream responses (unused for ACP)
- `live_output`: Whether to show live output (unused for ACP)
- `on_stdout`: Callback for stdout (unused for ACP)
- `on_stderr`: Callback for stderr (unused for ACP)

**Returns**: RunResult with stdout, stderr, exit_code

---
