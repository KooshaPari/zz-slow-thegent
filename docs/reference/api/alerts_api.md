# alerts API Reference

> **Source**: `src/thegent/ux/alerts.py`

WP-4004: Interruption taxonomy and fatigue controls.

---

## AlertFatigueController

Manages alert volume and prevents operator fatigue.

### Methods

#### AlertFatigueController.**init**

```python
__init__(self: Any, settings: ThegentSettings)
```

---

#### AlertFatigueController.get_fatigue_level

```python
get_fatigue_level(self: Any)
```

Return fatigue level from 0.0 to 1.0.

---

#### AlertFatigueController.record_alert

```python
record_alert(self: Any, kind: InterruptionKind)
```

Record an alert and return True if it should be suppressed due to fatigue.

---

---

## InterruptionKind

Kinds of system interruptions.

**Inherits from**: `enum.StrEnum`

---

## get_fatigue_level

```python
get_fatigue_level(self: Any)
```

Return fatigue level from 0.0 to 1.0.

---

## record_alert

```python
record_alert(self: Any, kind: InterruptionKind)
```

Record an alert and return True if it should be suppressed due to fatigue.

---
