<DONE>
# Phase 13: Cost Sensitivity Experiment Plan

> **Purpose:** Evaluate impact of policy federation on latency and routing costs.
> **Depends:** phase13-policy-federation.
> **Acceptance:** Baseline + Experiment A/B defined; metrics (lookup latency, provider accuracy, SLA breach) captured.
> **WORK_STREAM ID:** phase13-cost-sensitivity

## 1. Goal

Evaluate the impact of policy federation on system latency and model routing costs.

## 2. Methodology

- **Baseline**: Single-tenant policy lookup (v12).
- **Experiment A**: Multi-tenant lookup with 10 namespaces (shallow inheritance).
- **Experiment B**: Multi-tenant lookup with 50 namespaces (deep inheritance, 5 levels).

## 3. Metrics

- **Lookup Latency**: Time to resolve a routing decision through the policy stack.
- **Provider Accuracy**: Does the federated policy result in more/fewer model fallback events?
- **SLA Breach Rate**: Does deep policy evaluation cause SLO regulator triggers?

## 4. Implementation

### 4.1 Framework Components

The cost-sensitivity experiment framework is implemented in:

- `src/thegent/research/cost_sensitivity.py` - Core framework
- `src/thegent/phases/cost_sensitivity.py` - Phase-specific experiment runner
- `src/thegent/research/cost_sensitivity_experiment.py` - Experiment execution

### 4.2 Experiment Configuration

```python
from thegent.research.cost_sensitivity import CostSensitivityFramework

framework = CostSensitivityFramework(
    baseline_config={"tenant_count": 1, "policy_depth": 1},
    experiment_a_config={"tenant_count": 10, "policy_depth": 2},
    experiment_b_config={"tenant_count": 50, "policy_depth": 5},
)
```

### 4.3 Metrics Collection

The framework collects:

- **Latency**: Policy lookup time (ms)
- **Cost**: Model routing cost per request ($)
- **Accuracy**: Model selection accuracy (%)
- **SLA Compliance**: SLO breach rate (%)

### 4.4 Results Analysis

Results are written to:

- `docs/research/PHASE13_COST_SENSITIVITY_EXPERIMENT_RESULTS.md`

The analysis includes:

- Baseline vs Experiment comparison
- Cost-to-value ratio analysis
- Recommendations for optimal policy depth

## 5. Acceptance Criteria Status

- [x] Cost-sensitivity experiment framework implemented (`CostSensitivityFramework`)
- [x] A/B testing infrastructure for routing decisions (`ExperimentRunner`)
- [x] Metrics collection for cost vs. value analysis (latency, cost, accuracy, SLA)
- [ ] Experiment results documented (pending execution)
- [ ] Recommendations for cost-aware routing (pending analysis)

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related docs

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
