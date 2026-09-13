# evidence_ledger API Reference

> **Source**: `src/thegent/governance/evidence_ledger.py`

Hash-chained JSONL evidence ledger for AgilePlus cycles.

Records evidence events with cryptographic hash chaining for tamper detection,
following the RunRegistry pattern from execution.py.

---

## EvidenceEvent

A single evidence event in the hash-chained ledger.

**Inherits from**: `BaseModel`

---

## EvidenceLedger

Hash-chained JSONL evidence ledger for AgilePlus cycles.

Follows the RunRegistry pattern: each record contains a prev_hash linking
to the previous record's hash, forming a tamper-evident chain.

### Methods

#### EvidenceLedger.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### EvidenceLedger.ledger_path

```python
ledger_path(self: Any)
```

---

#### EvidenceLedger.link_to_graph

```python
link_to_graph(self: Any, graph: EvidenceGraph, event_hash: str, artifact_id: str)
```

Link an evidence event to an artifact in the EvidenceGraph.

---

#### EvidenceLedger.query

```python
query(self: Any, cycle_id: Any, event_type: Any)
```

Query evidence events, optionally filtering by cycle_id and/or event_type.

---

#### EvidenceLedger.record

```python
record(self: Any, event_type: str, cycle_id: str, payload: dict[(str, Any)])
```

Record an evidence event with hash chaining.

Returns the hash of the newly recorded event.

---

#### EvidenceLedger.verify_chain

```python
verify_chain(self: Any)
```

Verify the integrity of the hash chain.

Returns True if every record's hash is correct and prev_hash links
form an unbroken chain. Returns False on any inconsistency.

---

---

## ledger_path

```python
ledger_path(self: Any) -> Path
```

---

## link_to_graph

```python
link_to_graph(self: Any, graph: EvidenceGraph, event_hash: str, artifact_id: str)
```

Link an evidence event to an artifact in the EvidenceGraph.

---

## query

```python
query(self: Any, cycle_id: Any, event_type: Any)
```

Query evidence events, optionally filtering by cycle_id and/or event_type.

---

## record

```python
record(self: Any, event_type: str, cycle_id: str, payload: dict[(str, Any)])
```

Record an evidence event with hash chaining.

Returns the hash of the newly recorded event.

---

## verify_chain

```python
verify_chain(self: Any)
```

Verify the integrity of the hash chain.

Returns True if every record's hash is correct and prev_hash links
form an unbroken chain. Returns False on any inconsistency.

---
