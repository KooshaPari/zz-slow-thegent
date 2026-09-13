# conformance API Reference

> **Source**: `src/thegent/contracts/conformance.py`

Conformance test suite for provider adapters.

Ensures that adapters correctly normalize common provider output patterns
and handle edge cases/malformed input gracefully. Supports optional drift
alarm checks via ContractTelemetry.

---

## ConformanceTest

---

## run_conformance_suite

```python
run_conformance_suite(session_dir: Any, drift_window: int)
```

Run a suite of conformance tests against registered adapters.

**Parameters**:

- `session_dir`: If provided, run drift detection on contract telemetry
  and include drift_issues in the report (drift alarm).
- `drift_window`: Window size for drift detection when session_dir is set.

**Returns**: Report dict with total, passed, failed, results, and optionally drift_issues.

---
