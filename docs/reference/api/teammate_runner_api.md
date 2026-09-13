# teammate_runner API Reference

> **Source**: `src/thegent/agents/teammate_runner.py`

Teammate agent runner (WP-16001).

---

## TeammateRunner

Runner that executes a teammate persona by delegating to its underlying model/provider.

**Inherits from**: `AgentRunner`

### Methods

#### TeammateRunner.**init**

```python
__init__(self: Any, teammate_id: str, settings: Any)
```

---

#### TeammateRunner.run

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
