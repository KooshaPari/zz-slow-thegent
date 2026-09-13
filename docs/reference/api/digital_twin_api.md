# digital_twin API Reference

> **Source**: `src/thegent/agents/digital_twin.py`

WP-41003: Legacy Identity Preservation (Digital Twin).

Maintains a persistent, evolving digital twin of a human user or agent persona.
Ensures continuity of 'intent' and 'values' across different hardware or model migrations.

---

## DigitalTwinManager

Manages the creation and synchronization of digital identity twins.

### Methods

#### DigitalTwinManager.**init**

```python
__init__(self: Any, storage_dir: str)
```

---

#### DigitalTwinManager.capture_snapshot

```python
capture_snapshot(self: Any, identity_id: str, values: dict[(str, float)])
```

WP-41003: Capture the current state of a persona for preservation.

---

#### DigitalTwinManager.reconcile_twin

```python
reconcile_twin(self: Any, twin_a_id: str, twin_b_id: str)
```

Merge traits from two snapshots (e.g. from different project instances).

---

---

## PersonaSnapshot

A point-in-time snapshot of an identity's values and memory.

---

## capture_snapshot

```python
capture_snapshot(self: Any, identity_id: str, values: dict[(str, float)])
```

WP-41003: Capture the current state of a persona for preservation.

---

## reconcile_twin

```python
reconcile_twin(self: Any, twin_a_id: str, twin_b_id: str)
```

Merge traits from two snapshots (e.g. from different project instances).

---
