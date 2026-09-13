# drift API Reference

> **Source**: `src/thegent/governance/drift.py`

WP-3005: Policy drift detection and sweep.

---

## DriftDetector

Detects drift in policy state and cleans up stale overrides.

### Methods

#### DriftDetector.**init**

```python
__init__(self: Any, settings: ThegentSettings)
```

---

#### DriftDetector.detect_drift

```python
detect_drift(self: Any)
```

Check for drift between current state and baseline.

Returns a report of detected issues.

---

#### DriftDetector.sweep

```python
sweep(self: Any)
```

Perform a sweep to correct detected drift.

Returns counts of corrected items.

---

---

## detect_drift

```python
detect_drift(self: Any)
```

Check for drift between current state and baseline.

Returns a report of detected issues.

---

## sweep

```python
sweep(self: Any)
```

Perform a sweep to correct detected drift.

Returns counts of corrected items.

---
