# retention API Reference

> **Source**: `src/thegent/governance/retention.py`

WP-3006: Compliance evidence retention.

---

## EvidenceRetentionManager

Manages retention and archival of compliance evidence.

### Methods

#### EvidenceRetentionManager.**init**

```python
__init__(self: Any, settings: ThegentSettings)
```

---

#### EvidenceRetentionManager.enforce_retention

```python
enforce_retention(self: Any)
```

Scan evidence and archive or delete based on policy.

Returns counts of processed items.

---

#### EvidenceRetentionManager.list_archived

```python
list_archived(self: Any)
```

Return list of archived evidence files.

---

---

## enforce_retention

```python
enforce_retention(self: Any)
```

Scan evidence and archive or delete based on policy.

Returns counts of processed items.

---

## list_archived

```python
list_archived(self: Any)
```

Return list of archived evidence files.

---
