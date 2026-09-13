# drift_corrector API Reference

> **Source**: `src/thegent/infra/drift_corrector.py`

WP-31003: Infra Drift Self-Correction Loop.

Monitors provisioned resources and automatically corrects deviations from the target spec.
Ensures agent infrastructure remains stable and compliant over time.

---

## DriftCorrector

Orchestrates self-correction of agent infrastructure drift.

### Methods

#### DriftCorrector.**init**

```python
__init__(self: Any, provisioner: InfraProvisioner)
```

---

#### DriftCorrector.check_drift

```python
check_drift(self: Any, resource_id: str, target_spec: ResourceSpec)
```

Check if a resource has drifted from its target specification.

---

#### DriftCorrector.correct_drift

```python
correct_drift(self: Any, resource_id: str, target_spec: ResourceSpec)
```

Automatically correct detected infrastructure drift.

---

---

## check_drift

```python
check_drift(self: Any, resource_id: str, target_spec: ResourceSpec)
```

Check if a resource has drifted from its target specification.

---

## correct_drift

```python
correct_drift(self: Any, resource_id: str, target_spec: ResourceSpec)
```

Automatically correct detected infrastructure drift.

---
