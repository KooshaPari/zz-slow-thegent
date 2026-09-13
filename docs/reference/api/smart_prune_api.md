# smart_prune API Reference

> **Source**: `src/thegent/orchestration/pruning/smart_prune.py`

Smart pruning logic for agent resource reclamation.

Implements the strategy defined in docs/research/SMART_PRUNING_STRATEGY.md.

---

## SessionSnapshot

Snapshot of a session's state for idle detection.

---

## SmartPruner

Intelligent agent resource reclaimer.

### Methods

#### SmartPruner.**init**

```python
__init__(self: Any, project_root: Any)
```

---

#### SmartPruner.check_docs_written

```python
check_docs_written(self: Any, session_start_time: float)
```

Check if any docs were modified since session start.

---

#### SmartPruner.detect_completion

```python
detect_completion(self: Any, output: str)
```

Search output for completion markers.

---

#### SmartPruner.discover_sessions

```python
discover_sessions(self: Any)
```

Find all active managed and IDE sessions.

---

#### SmartPruner.run_cycle

```python
run_cycle(self: Any, force_prune: bool, reprompt: bool)
```

Run one pruning cycle.

---

---

## check_docs_written

```python
check_docs_written(self: Any, session_start_time: float)
```

Check if any docs were modified since session start.

---

## detect_completion

```python
detect_completion(self: Any, output: str)
```

Search output for completion markers.

---

## discover_sessions

```python
discover_sessions(self: Any)
```

Find all active managed and IDE sessions.

---

## get_tty_path

```python
get_tty_path(tty: str)
```

Get absolute path for TTY.

---

## pause_process

```python
pause_process(pid: int)
```

Pause a process (SIGSTOP).

---

## resume_process

```python
resume_process(pid: int)
```

Resume a process (SIGCONT).

---

## run_cycle

```python
run_cycle(self: Any, force_prune: bool, reprompt: bool)
```

Run one pruning cycle.

---

## smart_prune_main

```python
smart_prune_main(force: bool, reprompt: bool)
```

Entry point for smart pruning.

---
