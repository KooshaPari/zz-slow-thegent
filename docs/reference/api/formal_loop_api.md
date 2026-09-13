# formal_loop API Reference

> **Source**: `src/thegent/verification/formal_loop.py`

WP-18004: Automated Formal Verification Loop.

Continously runs symbolic execution and logical verification on the active plan.

---

## FormalVerificationLoop

Automated loop that periodically verifies the agent's plan for logical consistency.

### Methods

#### FormalVerificationLoop.**init**

```python
__init__(self: Any, plan_dag: Any)
```

---

#### FormalVerificationLoop.get_history

```python
get_history(self: Any)
```

Return history of verification passes.

---

#### FormalVerificationLoop.run

```python
run(self: Any, start_task: str)
```

Execute a formal verification pass.

---

---

## get_history

```python
get_history(self: Any)
```

Return history of verification passes.

---

## run

```python
run(self: Any, start_task: str)
```

Execute a formal verification pass.

---
