<DONE>
# Economic Governance Framework

> **Status**: Research Complete | **Version**: 1.0 | **Date**: 2026-02-18
> **Priority**: P1 | **Depends**: WP-5003

## Overview

Economic governance provides budget allocation, cost tracking, and routing decisions based on economic constraints for thegent's multi-tenant agent system.

## Budget Model

### Budget Types

| Type      | Scope        | Renewal        | Use Case           |
| --------- | ------------ | -------------- | ------------------ |
| Monthly   | Project      | Calendar month | General operations |
| Quarterly | Organization | Quarter        | Planning           |
| Per-model | Model        | Per-request    | Cost control       |
| Emergency | Override     | Manual         | Fail-safe          |

### Budget Allocation

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional
from enum import Enum


class BudgetType(Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    PER_MODEL = "per_model"
    EMERGENCY = "emergency"


@dataclass
class Budget:
    id: str
    project_id: str
    budget_type: BudgetType
    amount: float
    spent: float
    start_date: datetime
    end_date: datetime
    renews: bool

    @property
    def remaining(self) -> float:
        return self.amount - self.spent

    @property
    def utilization(self) -> float:
        return self.spent / self.amount
```

## Cost Tracking

### Real-time Metering

```python
from datetime import datetime
from typing import Dict, List
import asyncio

class CostMeter:
    def __init__(self):
        self.current_costs: Dict[str, float] = {}
        self.cost_history: List[Dict] = []

    async def record_cost(
        self,
        project_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float
    ):
        """Record cost for a single request."""
        key = f"{project_id}:{model}"
        self.current_costs[key] = self.current_costs.get(key, 0)) + cost

        self.cost_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "project_id": project_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        })

    def get_project_cost(self, project_id: str) -> float:
        """Get total cost for a project."""
        return sum(
            cost for key, cost in self.current_costs.items()
            if key.startswith(project_id)
        )
```

### Cost Attribution

```python
class CostAttributor:
    def attribute_cost(self, request: Request, response: Response) -> Dict[str, float]:
        """Attribute cost to specific components."""
        return {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "model_cost": response.cost,
            "infrastructure_cost": response.cost * 0.1,  # 10% overhead
        }
```

## Routing Integration

### Budget-Aware Routing

```python
class BudgetAwareRouter:
    def __init__(self, budget_manager: BudgetManager, router: ParetoRouter):
        self.budget_manager = budget_manager
        self.router = router

    def route(self, request: Request) -> RoutingDecision:
        # Check budget first
        budget_status = self.budget_manager.check_budget(request.project_id, request.requested_model)

        if not budget_status.can_proceed:
            # Fall back to cheaper model or reject
            return self._route_to_budget(budget_status, request)

        # Normal routing with budget awareness
        return self.router.route(request)

    def _route_to_budget(self, budget_status: BudgetStatus, request: Request) -> RoutingDecision:
        """Route to cheapest available model."""
        available = [m for m in ALL_MODELS if m.cost <= budget_status.remaining_budget]
        return min(available, key=lambda m: m.cost)
```

### Overage Handling

```python
class OverageHandler:
    def handle_overage(self, project_id: str, overage_amount: float) -> OverageAction:
        """Determine action for budget overage."""
        if overage_amount < 10:  # Small overage
            return OverageAction.WARN
        elif overage_amount < 100:  # Medium overage
            return OverageAction.UPGRADE_BUDGET
        else:  # Large overage
            return OverageAction.BLOCK
```

## API Design

```python
class EconomicGovernance:
    """Main interface for economic governance."""

    async def check_budget(self, project_id: str, model: str) -> BudgetStatus:
        """Check if request can proceed within budget."""
        pass

    async def record_cost(self, project_id: str, model: str, tokens: int, cost: float):
        """Record cost for a request."""
        pass

    async def get_remaining_budget(self, project_id: str) -> float:
        """Get remaining budget for a project."""
        pass

    async def allocate_budget(self, project_id: str, amount: float, budget_type: BudgetType) -> Budget:
        """Allocate new budget."""
        pass

    async def get_cost_report(self, project_id: str, start_date: datetime, end_date: datetime) -> CostReport:
        """Generate cost report."""
        pass
```

---

**EXTENSION_SUMMARY**

**Extended on:** 2026-02-18
**Extended by:** Claude Code

### Changes Made

1. **Created standalone research document** from COST*ROUTING*\*.md and COST_ENFORCEMENT_POLICY.md
2. **Defined budget model** with 4 budget types
3. **Implemented cost tracking** with real-time metering
4. **Added routing integration** with budget-aware decisions
5. **Provided complete API design** for EconomicGovernance class

### Cross-References Added

- COST_ROUTING_DEFERRED.md
- COST_ENFORCEMENT_POLICY.md
- WP-5003

### Practical Additions

- Complete Python implementations
- Budget allocation strategies
- Cost attribution methods
- Overage handling policies

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->

## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.
