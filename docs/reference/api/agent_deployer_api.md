# agent_deployer API Reference

> **Source**: `src/thegent/governance/agent_deployer.py`

Agent deployment from remediation DAG.

Walks the DAG topologically, groups independent tasks into ready batches,
checks budget, and spawns agents via the canonical entry point.

---

## AgentDeployer

Deploys remediation tasks from a DAG, respecting dependencies and budget.

### Methods

#### AgentDeployer.**init**

```python
__init__(self: Any, cost_controller: CostControllerProtocol, verification_gate: Any, max_concurrent: int, lifecycle_mode: str, checker_agent_name: str)
```

---

#### AgentDeployer.deploy

```python
deploy(self: Any, plan: Any, pre_scan: Any, cycle_id: str)
```

Execute a full remediation plan.

Walks DAG topologically, groups ready tasks into batches,
spawns agents for each batch respecting max_concurrent.

---

#### AgentDeployer.get_ready_batch

```python
get_ready_batch(self: Any, plan: Any, completed_task_ids: set[str])
```

Get tasks ready to execute (all dependencies completed).

---

---

## CostControllerProtocol

Protocol for cost controller.

**Inherits from**: `Protocol`

### Methods

#### CostControllerProtocol.can_spawn

```python
can_spawn(self: Any, estimated_calls: int)
```

---

#### CostControllerProtocol.get_tier

```python
get_tier(self: Any)
```

---

#### CostControllerProtocol.record_call

```python
record_call(self: Any, dimension: str, agent_type: str)
```

---

---

## DeploymentResult

Result of deploying a full remediation plan.

**Inherits from**: `BaseModel`

---

## TaskExecutionResult

Result of executing a single remediation task.

**Inherits from**: `BaseModel`

---

## VerificationGateProtocol

Protocol for verification gate.

**Inherits from**: `Protocol`

### Methods

#### VerificationGateProtocol.should_reroll

```python
should_reroll(self: Any, attempts: int)
```

---

#### VerificationGateProtocol.verify_task

```python
verify_task(self: Any, task: Any, execution: Any, pre_scan: Any)
```

---

---

## can_spawn

```python
can_spawn(self: Any, estimated_calls: int) -> bool
```

---

## deploy

```python
deploy(self: Any, plan: Any, pre_scan: Any, cycle_id: str)
```

Execute a full remediation plan.

Walks DAG topologically, groups ready tasks into batches,
spawns agents for each batch respecting max_concurrent.

---

## get_ready_batch

```python
get_ready_batch(self: Any, plan: Any, completed_task_ids: set[str])
```

Get tasks ready to execute (all dependencies completed).

---

## get_tier

```python
get_tier(self: Any) -> str
```

---

## record_call

```python
record_call(self: Any, dimension: str, agent_type: str) -> None
```

---

## should_reroll

```python
should_reroll(self: Any, attempts: int) -> bool
```

---

## verify_task

```python
verify_task(self: Any, task: Any, execution: Any, pre_scan: Any) -> Any
```

---
