# self_healing API Reference

> **Source**: `src/thegent/agents/self_healing.py`

WP-2004: Automated recovery and self-healing orchestration.

---

## RecoveryRouter

Routes failed runs to automated recovery playbooks.

### Methods

#### RecoveryRouter.**init**

```python
__init__(self: Any)
```

---

#### RecoveryRouter.attempt_recovery

```python
attempt_recovery(self: Any, result: RunResult)
```

Suggest a recovery action based on the failure classification.

---

#### RecoveryRouter.back_project_failure

```python
back_project_failure(self: Any, run_id: str, prompt: str, failure_type: str)
```

WP-16002: Analyze failure and project fix into instructions.

---

---

## StabilityTracker

Monitors session stability and performance over time.

### Methods

#### StabilityTracker.**init**

```python
__init__(self: Any, window_size: int)
```

---

#### StabilityTracker.get_stability_score

```python
get_stability_score(self: Any)
```

Calculate stability score (0.0 - 1.0) based on success rate.

---

#### StabilityTracker.record_result

```python
record_result(self: Any, result: RunResult)
```

Record a run result and prune old history.

---

---

## attempt_recovery

```python
attempt_recovery(self: Any, result: RunResult)
```

Suggest a recovery action based on the failure classification.

---

## back_project_failure

```python
back_project_failure(self: Any, run_id: str, prompt: str, failure_type: str)
```

WP-16002: Analyze failure and project fix into instructions.

---

## get_stability_score

```python
get_stability_score(self: Any)
```

Calculate stability score (0.0 - 1.0) based on success rate.

---

## record_result

```python
record_result(self: Any, result: RunResult)
```

Record a run result and prune old history.

---
