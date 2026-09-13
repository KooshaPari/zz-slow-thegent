# cage API Reference

> **Source**: `src/thegent/infra/cage.py`

WP-33003: External Policy Enforcement (The Cage).

Physically restricts black-box agents using runtime isolation and monitoring.
Provides a 'cage' that enforces governance regardless of the agent's internal logic.

---

## AgentCage

A hardened runtime environment for untrusted or black-box agents.

### Methods

#### AgentCage.**init**

```python
__init__(self: Any, cage_id: str, base_dir: Path)
```

---

#### AgentCage.cleanup

```python
cleanup(self: Any)
```

Tear down the cage and scrub data.

---

#### AgentCage.run_command

```python
run_command(self: Any, cmd: list[str])
```

Execute a command inside the cage with restricted CWD.

---

#### AgentCage.setup

```python
setup(self: Any, allowed_files: list[Path])
```

Initialize the cage by mirroring only allowed files (Copy-on-Write style).

---

---

## cleanup

```python
cleanup(self: Any)
```

Tear down the cage and scrub data.

---

## run_command

```python
run_command(self: Any, cmd: list[str])
```

Execute a command inside the cage with restricted CWD.

---

## setup

```python
setup(self: Any, allowed_files: list[Path])
```

Initialize the cage by mirroring only allowed files (Copy-on-Write style).

---
