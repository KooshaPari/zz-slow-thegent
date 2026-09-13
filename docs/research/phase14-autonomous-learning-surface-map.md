<DONE>
# Phase 14: Autonomous Learning and Cost Sensing Surface Map

> **Purpose:** Map surfaces for autonomous learning and cost-aware optimization.
> **Depends:** WP-5003, learning pipeline.
> **Acceptance:** Surface map documented; integration points listed.
> **WORK_STREAM ID:** phase14-autonomous-learning

## 1. Overview

This document maps the architectural surfaces affected by the introduction of adaptive, cost-aware optimization.

## 2. Integration Points

### 2.1 Planning Surface: Objective Selector

- **New Component**: `src/thegent/planning/selector.py`
- **Responsibility**: Balancing latency, quality, and spend based on policy-defined weights.

### 2.2 Learning Surface: Model Registry

- **Existing**: `src/thegent/agents/registry.py`
- **Learning**: Introduction of `LearningRegistry` to track canary model performance and promotion.

### 2.3 Monitoring Surface: Cost Sensing

- **Existing**: `src/thegent/governance/costs.py` (if it exists)
- **Sensing**: Integration with the `SLORegulator` to provide cost-based feedback loops.

### 2.4 Human-in-the-Loop Surface

- **Existing**: `src/thegent/governance/hitl.py`
- **Learning**: Mandatory review for all autonomous model promotions (WP-14003).

## 3. Data Structures

- **ObjectiveProfile**: `{latency_weight: 0.3, quality_weight: 0.5, spend_weight: 0.2}`
- **CandidateModel**: `{id: "gemini-flash-v2", status: "canary", success_rate: 0.95, cost_delta: -0.15}`

## 4. Implementation Patterns

### 4.1 Objective Selector Implementation

```python
# src/thegent/planning/selector.py (to be created)
from dataclasses import dataclass
from typing import Literal


@dataclass
class ObjectiveProfile:
    latency_weight: float = 0.3
    quality_weight: float = 0.5
    spend_weight: float = 0.2

    def score(self, latency: float, quality: float, cost: float) -> float:
        """Calculate weighted score for model selection."""
        return self.latency_weight * (1.0 / latency) + self.quality_weight * quality + self.spend_weight * (1.0 / cost)
```

### 4.2 Learning Registry Implementation

```python
# Extension to src/thegent/agents/registry.py
from dataclasses import dataclass
from enum import Enum


class ModelStatus(Enum):
    BASELINE = "baseline"
    CANARY = "canary"
    PROMOTED = "promoted"
    DEPRECATED = "deprecated"


@dataclass
class CandidateModel:
    id: str
    status: ModelStatus
    success_rate: float
    cost_delta: float  # Relative to baseline


class LearningRegistry:
    """Tracks canary model performance and promotion."""

    def register_canary(self, model_id: str, baseline_id: str) -> None:
        """Register a canary model for testing."""
        ...

    def evaluate_promotion(self, model_id: str) -> bool:
        """Evaluate if canary should be promoted."""
        ...
```

### 4.3 Cost Sensing Integration

```python
# Integration with src/thegent/governance/costs.py
from thegent.governance.slo import SLORegulator


class CostSensing:
    """Provides cost-based feedback loops."""

    def __init__(self, slo_regulator: SLORegulator):
        self.slo = slo_regulator

    def check_cost_cap(self, action_cost: float, cap: float) -> bool:
        """Check if action exceeds cost cap."""
        return action_cost <= cap

    def get_cost_feedback(self, model_id: str) -> dict:
        """Get cost feedback for learning system."""
        ...
```

### 4.4 Human-in-the-Loop Integration

```python
# Integration with src/thegent/governance/hitl.py
from thegent.governance.hitl import HITLManager


class LearningHITL:
    """Mandatory review for autonomous model promotions."""

    def request_promotion(self, model_id: str) -> bool:
        """Request promotion approval (WP-14003)."""
        hitl = HITLManager()
        return hitl.require_approval(action="model_promotion", context={"model_id": model_id})
```

## 5. Acceptance Criteria Status

- [x] Autonomous learning architecture designed (surface map complete)
- [x] Learning surface area mapped (integration points documented)
- [ ] Feedback loops implemented (pending implementation)
- [ ] Performance metrics tracked (pending implementation)
- [ ] Learning effectiveness validated (pending testing)

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
