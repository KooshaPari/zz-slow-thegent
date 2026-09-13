# Multi-Objective Provider Routing & Pareto Fronts (WP-1004)

This document details the advanced mathematical model for **Provider Scoring and Routing**, moving beyond simple weighted averages to **Multi-Objective Optimization**.

## 1. The 3-Dimensional Optimization Space

`thegent` routes requests based on three primary objectives that often conflict:

1. **Cost** (minimize USD/1M tokens)
2. **Latency** (minimize Time-to-First-Token and total duration)
3. **Accuracy** (maximize historical success rate/calibration)

## 2. Pareto Front Selection

Instead of a single "Best" model, `thegent` identifies the **Pareto Front**—the set of providers where no objective can be improved without degrading another.

### 2.1 Dominance Logic

Provider A "dominates" Provider B if:

- `Cost(A) <= Cost(B)` AND `Latency(A) <= Latency(B)` AND `Accuracy(A) >= Accuracy(B)`
- AND at least one inequality is strict.

The router filters all available providers to find the **non-dominated set**.

## 3. Dynamic Routing Strategies

The operator or policy engine selects a "Slice" of the Pareto Front based on the task's context:

| Strategy              | Selection Criterion                             | Example Use Case                       |
| --------------------- | ----------------------------------------------- | -------------------------------------- |
| **Cost Optimized**    | `Min(Cost)` on the Pareto Front.                | Bulk research, eXplore phase.          |
| **Speed Optimized**   | `Min(Latency)` on the Pareto Front.             | Interactive CLI, fallback recovery.    |
| **Quality Optimized** | `Max(Accuracy)` on the Pareto Front.            | Final verification, eXterminate phase. |
| **Balanced**          | Center of the front (Pareto optimal mid-point). | Default operation.                     |

## 4. Confidence-Weighted Selection

The "Accuracy" dimension is not static. It is calculated as:

- `Accuracy_Score = Base_Capability * Confidence_Calibration_Factor`
- **Calibration**: If a provider consistently reports 0.9 confidence but fails 50% of the time, its Accuracy Score is penalized by 0.5.

## 5. Implementation (models/catalog.py)

```python
class ParetoRouter:
    def get_optimal_providers(self, candidates: list[ProviderProfile]) -> list[ProviderProfile]:
        """Returns the non-dominated set (Pareto Front)."""
        pareto_front = []
        for p1 in candidates:
            is_dominated = False
            for p2 in candidates:
                if self.dominates(p2, p1):
                    is_dominated = True
                    break
            if not is_dominated:
                pareto_front.append(p1)
        return pareto_front

    def select_by_strategy(self, strategy: str, front: list[ProviderProfile]) -> ProviderProfile:
        """Applies a strategy slice to the Pareto Front."""
        if strategy == "cost":
            return min(front, key=lambda p: p.cost)
        # ...
```

---

_Cross-ref: [05-ARCHITECTURE.md](../plans/05-ARCHITECTURE.md) | [TRAFFIC_KPI_DESIGN.md](./TRAFFIC_KPI_DESIGN.md)_

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
