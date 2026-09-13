# shell_injection API Reference

> **Source**: `src/thegent/infra/shell_injection.py`

Phase 13: Shell Injection implementation.

Includes tmux session detection, command injection via send-keys, and readiness detection.

---

## AgentReadinessDetector

Advanced readiness detection using process state and output analysis.

### Methods

#### AgentReadinessDetector.get_agent_state

```python
get_agent_state(pid: int)
```

Determine agent state: idle, busy, error.

---

---

## TmuxInjector

Injects commands into tmux sessions.

### Methods

#### TmuxInjector.**init**

```python
__init__(self: Any, session_prefix: str)
```

---

#### TmuxInjector.inject_command

```python
inject_command(self: Any, session_id: str, command: str, wait_for_readiness: bool)
```

Inject command into tmux session using send-keys.

---

#### TmuxInjector.is_ready

```python
is_ready(self: Any, session_id: str)
```

Check if session is at a prompt (idle).

---

#### TmuxInjector.list_agent_sessions

```python
list_agent_sessions(self: Any)
```

List all tmux sessions matching agent prefix.

---

#### TmuxInjector.wait_for_ready

```python
wait_for_ready(self: Any, session_id: str, timeout: float)
```

Detect agent readiness by looking for prompt patterns.

---

---

## get_agent_state

```python
get_agent_state(pid: int)
```

Determine agent state: idle, busy, error.

---

## inject_command

```python
inject_command(self: Any, session_id: str, command: str, wait_for_readiness: bool)
```

Inject command into tmux session using send-keys.

---

## is_ready

```python
is_ready(self: Any, session_id: str)
```

Check if session is at a prompt (idle).

---

## list_agent_sessions

```python
list_agent_sessions(self: Any)
```

List all tmux sessions matching agent prefix.

---

## wait_for_ready

```python
wait_for_ready(self: Any, session_id: str, timeout: float)
```

Detect agent readiness by looking for prompt patterns.

---
