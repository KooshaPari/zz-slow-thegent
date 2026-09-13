# droid API Reference

> **Source**: `src/thegent/agents/droid.py`

Droid runner - invokes Factory droid exec, OpenAI Codex CLI, or custom CLI backends.

---

## CodexRunner

Runs droids via OpenAI Codex CLI (codex exec).

**Inherits from**: `AgentRunner`

### Methods

#### CodexRunner.**init**

```python
__init__(self: Any, droid_name: str, droids_dir: Path, codex_cmd: str, model: str, use_litellm_router: Any)
```

---

#### CodexRunner.run

```python
run(self: Any, prompt: str, cwd: Any, mode: str, timeout: int)
```

Run droid via codex exec.

---

---

## CustomCliRunner

Runs droids via a generic custom CLI (e.g. claudemax, claudeglm in ~/.local/bin).

**Inherits from**: `AgentRunner`

### Methods

#### CustomCliRunner.**init**

```python
__init__(self: Any, droid_name: str, droids_dir: Path, custom_cmd: str, model: str)
```

---

#### CustomCliRunner.run

```python
run(self: Any, prompt: str, cwd: Any, mode: str, timeout: int)
```

Run droid via custom CLI. Prompt sent via stdin; expects --model and --cd support.

---

---

## DroidRunner

Runs droids via Factory droid exec.

**Inherits from**: `AgentRunner`

### Methods

#### DroidRunner.**init**

```python
__init__(self: Any, droid_name: str, droids_dir: Path, droid_cmd: str, model: str, use_litellm_router: Any)
```

---

#### DroidRunner.run

```python
run(self: Any, prompt: str, cwd: Any, mode: str, timeout: int)
```

Run droid via droid exec.

---

---

## get_droid_runner

```python
get_droid_runner(backend: str, droid_name: str, droids_dir: Path)
```

Factory: return the appropriate droid runner for the given backend.

---

## run

```python
run(self: Any, prompt: str, cwd: Any, mode: str, timeout: int)
```

Run droid via custom CLI. Prompt sent via stdin; expects --model and --cd support.

---
