# sandboxing API Reference

> **Source**: `src/thegent/security/sandboxing.py`

Phase 16: Sandboxing implementation.

Includes bubblewrap (Linux) and seatbelt (macOS) profile generation, and 5-tier autonomy.

---

## AutonomyEnforcer

Enforces 5-tier autonomy levels.

### Methods

#### AutonomyEnforcer.classify_operation

```python
classify_operation(self: Any, command: str, target: str)
```

Determine required tier for an operation.

---

---

## SandboxProvider

Generates and executes sandbox profiles.

### Methods

#### SandboxProvider.**init**

```python
__init__(self: Any)
```

---

#### SandboxProvider.wrap_command

```python
wrap_command(self: Any, command: list[str], tier: int)
```

Wrap command with sandbox according to autonomy tier.

---

---

## classify_operation

```python
classify_operation(self: Any, command: str, target: str)
```

Determine required tier for an operation.

---

## wrap_command

```python
wrap_command(self: Any, command: list[str], tier: int)
```

Wrap command with sandbox according to autonomy tier.

---
