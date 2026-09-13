# evidence_graph API Reference

> **Source**: `src/thegent/governance/evidence_graph.py`

WP-12006: Evidence graph and export bundling.

Builds a closed-loop graph of all evidence artifacts and provides deterministic export bundling.

---

## EvidenceGraph

Graph of evidence artifacts with deterministic bundling.

### Methods

#### EvidenceGraph.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### EvidenceGraph.add_link

```python
add_link(self: Any, parent_id: str, child_id: str)
```

Add a link between two evidence artifacts.

---

#### EvidenceGraph.bundle_evidence

```python
bundle_evidence(self: Any, target_path: Path)
```

WP-12006: Deterministic export of the evidence graph and artifacts.

---

---

## add_link

```python
add_link(self: Any, parent_id: str, child_id: str)
```

Add a link between two evidence artifacts.

---

## bundle_evidence

```python
bundle_evidence(self: Any, target_path: Path)
```

WP-12006: Deterministic export of the evidence graph and artifacts.

---
