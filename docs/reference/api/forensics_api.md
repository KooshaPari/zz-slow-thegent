# forensics API Reference

> **Source**: `src/thegent/governance/forensics.py`

Forensic incident replay and post-mortem analysis (WP-15002).

---

## IncidentReplayer

Replays agent execution traces from immutable ledger entries (WP-15002).

### Methods

#### IncidentReplayer.**init**

```python
__init__(self: Any, ledger: IncidentLedger)
```

---

#### IncidentReplayer.generate_incident_report

```python
generate_incident_report(self: Any, run_id: str)
```

Generate a human-readable incident report from replayed data.

---

#### IncidentReplayer.replay

```python
replay(self: Any, run_id: str)
```

Reconstruct the execution trace for a specific run from the ledger.

**Parameters**:

- `run_id`: The ID of the run to replay

**Returns**: Reconstructed trace dictionary

---

---

## generate_incident_report

```python
generate_incident_report(self: Any, run_id: str)
```

Generate a human-readable incident report from replayed data.

---

## replay

```python
replay(self: Any, run_id: str)
```

Reconstruct the execution trace for a specific run from the ledger.

**Parameters**:

- `run_id`: The ID of the run to replay

**Returns**: Reconstructed trace dictionary

---
