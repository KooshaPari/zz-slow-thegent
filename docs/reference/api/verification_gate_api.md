# verification_gate API Reference

> **Source**: `src/thegent/governance/verification_gate.py`

Post-agent verification gate for AgilePlus cycles.

Re-runs targeted scanner dimensions after each agent task completes to verify
improvement, detect regressions, and determine pass/fail verdicts.

---

## DimensionScanResult

Protocol for a single dimension's scan output.

**Inherits from**: `Protocol`

---

## HealthComputerProtocol

Protocol for HealthScoreComputer -- used to get dimension weights.

**Inherits from**: `Protocol`

### Methods

#### HealthComputerProtocol.compute

```python
compute(self: Any, scan_result: Any)
```

---

---

## RemediationTaskProtocol

Protocol for a remediation task from the planner.

**Inherits from**: `Protocol`

---

## ScanResultProtocol

Protocol for a full codebase scan result.

**Inherits from**: `Protocol`

### Methods

#### ScanResultProtocol.get_dimension

```python
get_dimension(self: Any, dimension: str)
```

---

---

## ScannerProtocol

Protocol for CodebaseScanner -- only scan_dimension is needed here.

**Inherits from**: `Protocol`

### Methods

#### ScannerProtocol.scan

```python
scan(self: Any)
```

---

#### ScannerProtocol.scan_dimension

```python
scan_dimension(self: Any, dimension: str)
```

---

---

## TaskExecutionProtocol

Protocol for the result of executing a remediation task.

**Inherits from**: `Protocol`

---

## TaskVerification

Result of verifying a single task's effect on codebase health.

**Inherits from**: `BaseModel`

---

## VerificationGate

Verifies that agent tasks actually improved the targeted dimension.

After each task execution, re-scans the targeted dimension and compares
against the pre-scan baseline. Detects regressions in other dimensions.

### Methods

#### VerificationGate.**init**

```python
__init__(self: Any, scanner: ScannerProtocol, health_computer: HealthComputerProtocol, max_rerolls: int)
```

---

#### VerificationGate.get_escalated_tier

```python
get_escalated_tier(self: Any, current_tier: str)
```

Return the next agent tier for reroll escalation.

Returns None if already at the highest tier.

---

#### VerificationGate.should_reroll

```python
should_reroll(self: Any, attempts: int)
```

Return True if the task should be retried based on attempt count.

---

#### VerificationGate.verify_task

```python
verify_task(self: Any, task: RemediationTaskProtocol, execution: TaskExecutionProtocol, pre_scan: ScanResultProtocol)
```

Verify a completed task by re-scanning its target dimension.

Compares post-execution metrics against the pre-scan baseline to
determine whether the task improved, regressed, or had no effect.

---

---

## VerificationVerdict

Outcome of post-task verification.

**Inherits from**: `StrEnum`

---

## compute

```python
compute(self: Any, scan_result: Any) -> Any
```

---

## get_dimension

```python
get_dimension(self: Any, dimension: str) -> Any
```

---

## get_escalated_tier

```python
get_escalated_tier(self: Any, current_tier: str)
```

Return the next agent tier for reroll escalation.

Returns None if already at the highest tier.

---

## scan

```python
scan(self: Any) -> ScanResultProtocol
```

---

## scan_dimension

```python
scan_dimension(self: Any, dimension: str) -> DimensionScanResult
```

---

## should_reroll

```python
should_reroll(self: Any, attempts: int)
```

Return True if the task should be retried based on attempt count.

---

## verify_task

```python
verify_task(self: Any, task: RemediationTaskProtocol, execution: TaskExecutionProtocol, pre_scan: ScanResultProtocol)
```

Verify a completed task by re-scanning its target dimension.

Compares post-execution metrics against the pre-scan baseline to
determine whether the task improved, regressed, or had no effect.

---
