# gardening API Reference

> **Source**: `src/thegent/sitback/gardening.py`

Gardening manager for never-idle loop.

Manages proactive gardening checks: governance health, backlog, test failures,
traceability, escalations, quality, and DAG sync.

---

## GardeningManager

Manages aggressive gardening checks in never-idle loop.

Runs governance health, backlog checks, test failure detection,
traceability verification, escalation monitoring, quality gates,
and DAG synchronization.

### Methods

#### GardeningManager.**init**

```python
__init__(self: Any, project_root: Any)
```

Initialize the gardening manager.

**Parameters**:

- `project_root`: Root directory for the project. Defaults to cwd.

---

#### GardeningManager.clear_findings

```python
clear_findings(self: Any)
```

Clear stored findings.

---

#### GardeningManager.get_findings

```python
get_findings(self: Any)
```

Return gardening findings that need attention.

---

#### GardeningManager.get_last_results

```python
get_last_results(self: Any)
```

Return results from last run of each step.

---

#### GardeningManager.get_summary

```python
get_summary(self: Any)
```

Return a summary of gardening status.

---

---

## clear_findings

```python
clear_findings(self: Any)
```

Clear stored findings.

---

## get_findings

```python
get_findings(self: Any)
```

Return gardening findings that need attention.

---

## get_last_results

```python
get_last_results(self: Any)
```

Return results from last run of each step.

---

## get_summary

```python
get_summary(self: Any)
```

Return a summary of gardening status.

---
