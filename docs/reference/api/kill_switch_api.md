# kill_switch API Reference

> **Source**: `src/thegent/governance/kill_switch.py`

WP-39001: Super-intelligence Safety Break (Kill-Switch).

Provides an emergency override to immediately halt all agent operations if recursive self-improvement
exceeds human-defined safety bounds.

---

## SafetyKillSwitch

Hard-wired emergency stop for all agent processes.

### Methods

#### SafetyKillSwitch.**init**

```python
__init__(self: Any, workspace_root: str)
```

---

#### SafetyKillSwitch.activate

```python
activate(self: Any, reason: str)
```

WP-39001: Trigger the global kill-switch.

---

#### SafetyKillSwitch.check_status

```python
check_status(self: Any)
```

Check if the system is currently halted.

---

#### SafetyKillSwitch.verify_alignment_drift

```python
verify_alignment_drift(self: Any, self_improvement_rate: float)
```

Monitor for dangerous recursive improvement speed.

---

---

## activate

```python
activate(self: Any, reason: str)
```

WP-39001: Trigger the global kill-switch.

---

## check_status

```python
check_status(self: Any)
```

Check if the system is currently halted.

---

## verify_alignment_drift

```python
verify_alignment_drift(self: Any, self_improvement_rate: float)
```

Monitor for dangerous recursive improvement speed.

---
