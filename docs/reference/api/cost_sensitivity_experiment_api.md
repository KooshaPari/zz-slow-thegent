# cost_sensitivity_experiment API Reference

> **Source**: `src/thegent/research/cost_sensitivity_experiment.py`

Phase 13: Cost-sensitivity experiment framework.

Evaluates impact of policy federation on system latency and model routing costs.
Ref: docs/research/phase13-cost-sensitivity-experiment-plan.md

---

## ExperimentRunner

Runs cost-sensitivity experiments.

### Methods

#### ExperimentRunner.**init**

```python
__init__(self: Any)
```

---

#### ExperimentRunner.run_scenario

```python
run_scenario(self: Any, name: str, engine: FederatedPolicyEngineSim, leaf_ns: str)
```

---

---

## FederatedPolicyEngineSim

Simulates FederatedPolicyEngine with namespace inheritance.

### Methods

#### FederatedPolicyEngineSim.**init**

```python
__init__(self: Any, namespaces: list[PolicyNamespace])
```

---

#### FederatedPolicyEngineSim.resolve_effective_policy

```python
resolve_effective_policy(self: Any, leaf_namespace_name: str)
```

Resolves effective policy by traversing up the tree.

---

---

## PolicyNamespace

---

## resolve_effective_policy

```python
resolve_effective_policy(self: Any, leaf_namespace_name: str)
```

Resolves effective policy by traversing up the tree.

---

## run_scenario

```python
run_scenario(self: Any, name: str, engine: FederatedPolicyEngineSim, leaf_ns: str)
```

---

## setup_baseline

---

## setup_experiment_a

---

## setup_experiment_b

---
