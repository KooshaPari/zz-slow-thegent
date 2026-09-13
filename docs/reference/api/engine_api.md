# engine API Reference

> **Source**: `src/thegent/orchestration/execution/engine.py`

ExecutionEngine for coordinating agent runs with MAIF, policies, and resource management.

---

## ExecutionEngine

Orchestrates agent execution with integrated MAIF artifact generation.

This engine coordinates:

1. Pre-execution signing (MAIF run_start)
2. Agent execution (via AgentRunner)
3. Post-execution artifact generation (MAIF run_complete)

### Methods

#### ExecutionEngine.**init**

```python
__init__(self: Any, settings: Any)
```

---

#### ExecutionEngine.execute

```python
execute(self: Any, runner: AgentRunner, run_meta: RunMeta, cwd: Any, mode: str, timeout: int)
```

Execute an agent task and generate MAIF artifacts.

**Parameters**:

- `runner`: The AgentRunner implementation to use.
- `run_meta`: Metadata for the run (run_id, prompt, owner, etc.).
- `cwd`: Working directory for the agent.
- `mode`: Execution mode (e.g. "read-only", "write").
- `timeout`: Time budget in seconds.
- `**kwargs`: Additional options for the runner.

**Returns**: RunResult from the agent execution.

---

---

## execute

```python
execute(self: Any, runner: AgentRunner, run_meta: RunMeta, cwd: Any, mode: str, timeout: int)
```

Execute an agent task and generate MAIF artifacts.

**Parameters**:

- `runner`: The AgentRunner implementation to use.
- `run_meta`: Metadata for the run (run_id, prompt, owner, etc.).
- `cwd`: Working directory for the agent.
- `mode`: Execution mode (e.g. "read-only", "write").
- `timeout`: Time budget in seconds.
- `**kwargs`: Additional options for the runner.

**Returns**: RunResult from the agent execution.

---
