# agileplus API Reference

> **Source**: `src/thegent/governance/agileplus.py`

AgilePlus core loop orchestrator.

State machine: IDLE -> SCANNING -> ANALYZING -> PLANNING -> DEPLOYING -> VERIFYING -> COMMITTING -> IDLE

The loop composes scanner, analyzer, planner, deployer, verifier, and evidence
ledger to form a complete autonomous governance cycle.

---

## AgilePlusLoop

Orchestrates the complete 4X governance cycle.

States:

- IDLE: Health >= threshold, no action needed
- SCANNING: Running dimension scans
- ANALYZING: Prioritizing findings
- PLANNING: Generating remediation DAG
- DEPLOYING: Spawning agents
- VERIFYING: Post-task verification
- COMMITTING: Recording to evidence ledger

### Methods

#### AgilePlusLoop.**init**

```python
__init__(self: Any, project_dir: Path, health_targets_path: Path, health_threshold: float, max_tasks_per_cycle: int, max_rerolls: int, lifecycle_mode: str)
```

---

#### AgilePlusLoop.cycle_id

```python
cycle_id(self: Any)
```

Current cycle ID.

---

#### AgilePlusLoop.get_status

```python
get_status(self: Any)
```

Get current status without running a cycle.

---

#### AgilePlusLoop.request_shutdown

```python
request_shutdown(self: Any)
```

Request graceful shutdown.

---

#### AgilePlusLoop.run_continuous

```python
run_continuous(self: Any, interval_seconds: int, max_cycles: Any)
```

Run continuous governance cycles.

**Parameters**:

- `interval_seconds`: Seconds between cycles
- `max_cycles`: Maximum cycles to run (None = infinite)

**Returns**: List of CycleResult for each completed cycle

---

#### AgilePlusLoop.run_once

```python
run_once(self: Any, force: bool)
```

Run a single governance cycle.

Returns a CycleResult with the outcome of the complete
scan-analyze-plan-deploy-verify-commit loop.

---

#### AgilePlusLoop.state

```python
state(self: Any)
```

Current cycle state.

---

---

## CycleResult

Result of a single AgilePlus cycle.

**Inherits from**: `BaseModel`

---

## CycleState

AgilePlus cycle states.

**Inherits from**: `StrEnum`

---

## cycle_id

```python
cycle_id(self: Any)
```

Current cycle ID.

---

## get_status

```python
get_status(self: Any)
```

Get current status without running a cycle.

---

## request_shutdown

```python
request_shutdown(self: Any)
```

Request graceful shutdown.

---

## run_continuous

```python
run_continuous(self: Any, interval_seconds: int, max_cycles: Any)
```

Run continuous governance cycles.

**Parameters**:

- `interval_seconds`: Seconds between cycles
- `max_cycles`: Maximum cycles to run (None = infinite)

**Returns**: List of CycleResult for each completed cycle

---

## run_once

```python
run_once(self: Any, force: bool)
```

Run a single governance cycle.

Returns a CycleResult with the outcome of the complete
scan-analyze-plan-deploy-verify-commit loop.

---

## state

```python
state(self: Any)
```

Current cycle state.

---
