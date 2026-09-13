# runner API Reference

> **Source**: `src/thegent/maif/runner.py`

MAIFRunner - thin wrapper for recording run lifecycle as MAIF artifacts.

Optional/non-blocking: gated by THGENT_MAIF_ENABLED env var (default disabled).
All errors are caught and logged; this module never raises to the caller.

---

## MAIFRunner

Thin wrapper that records agent run lifecycle as signed MAIF artifacts.

Enabled when `THGENT_MAIF_ENABLED=1` is set in the environment.
The DB path is read from `THGENT_MAIF_DB_PATH` (default:
`~/.thegent/maif/artifacts.db`).

All public methods catch every exception internally and log at DEBUG level
so that MAIF recording never blocks or fails execution.

### Methods

#### MAIFRunner.**init**

```python
__init__(self: Any)
```

---

#### MAIFRunner.record_run_end

```python
record_run_end(self: Any, run_id: str, status: str, output_summary: str)
```

Record the completion of an agent run as a MAIF artifact.

**Parameters**:

- `run_id`: Unique identifier for the run, matching the one passed to
  :meth:`record_run_start`.
- `status`: Final status string (e.g. `"completed"`, `"failed"`,
  `"timed_out"`).
- `output_summary`: Truncated stdout/stderr summary for the artifact.

**Returns**: The artifact `id` (hex UUID) when MAIF is enabled and recording
succeeds; `None` otherwise.

---

#### MAIFRunner.record_run_start

```python
record_run_start(self: Any, run_id: str, owner: str, prompt: str, agent: str)
```

Record the start of an agent run as a MAIF artifact.

**Parameters**:

- `run_id`: Unique identifier for the run (e.g. `run_abc123`).
- `owner`: The user or system that initiated the run.
- `prompt`: The prompt sent to the agent (may be truncated in the artifact).
- `agent`: The agent/provider name (e.g. `"claude"`, `"antigravity"`).

**Returns**: The artifact `id` (hex UUID) when MAIF is enabled and recording
succeeds; `None` otherwise.

---

---

## record_run_end

```python
record_run_end(self: Any, run_id: str, status: str, output_summary: str)
```

Record the completion of an agent run as a MAIF artifact.

**Parameters**:

- `run_id`: Unique identifier for the run, matching the one passed to
  :meth:`record_run_start`.
- `status`: Final status string (e.g. `"completed"`, `"failed"`,
  `"timed_out"`).
- `output_summary`: Truncated stdout/stderr summary for the artifact.

**Returns**: The artifact `id` (hex UUID) when MAIF is enabled and recording
succeeds; `None` otherwise.

---

## record_run_start

```python
record_run_start(self: Any, run_id: str, owner: str, prompt: str, agent: str)
```

Record the start of an agent run as a MAIF artifact.

**Parameters**:

- `run_id`: Unique identifier for the run (e.g. `run_abc123`).
- `owner`: The user or system that initiated the run.
- `prompt`: The prompt sent to the agent (may be truncated in the artifact).
- `agent`: The agent/provider name (e.g. `"claude"`, `"antigravity"`).

**Returns**: The artifact `id` (hex UUID) when MAIF is enabled and recording
succeeds; `None` otherwise.

---
