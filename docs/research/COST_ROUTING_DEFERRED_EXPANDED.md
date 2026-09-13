<DONE>
# Cost Routing Deferred — Formal Decision Record

> **Status**: Complete | **Date**: 2026-02-17
> **Source**: Expanded from [COST_ROUTING_DEFERRED.md](./COST_ROUTING_DEFERRED.md)
> **Purpose**: Formal decision record for cost routing deferral with unblock criteria

---

## Executive Summary

**Decision**: Defer cost routing implementation
**Rationale**: Current routing sufficient; cost routing requires additional infrastructure
**Unblock Criteria**: Defined below
**Status**: Documented for future implementation

---

## Current State

**Existing Routing**:

- Provider selection based on reliability, latency
- Cost-aware routing partially implemented (WP-5003)
- Economic governance framework exists

**What's Deferred**:

- Advanced cost-to-value ratio routing
- Real-time cost tracking and optimization
- Budget-aware routing with hard limits

---

## Deferral Rationale

### Technical Reasons

1. **Infrastructure Dependency**: Requires cost tracking infrastructure
2. **Data Requirements**: Need historical cost data for optimization
3. **Complexity**: Cost routing adds complexity to decision-making
4. **Current Sufficiency**: Existing routing meets current needs

### Business Reasons

1. **Priority**: Other features have higher priority
2. **ROI**: Cost savings not yet quantified
3. **Risk**: Complex routing may introduce instability

---

## Unblock Criteria

### Must-Have (All Required)

- [ ] Cost tracking infrastructure implemented (WP-5003)
- [ ] Historical cost data available (30+ days)
- [ ] Cost-to-value ratio calculation validated
- [ ] Performance impact assessed (<5% latency increase)
- [ ] Budget limits infrastructure ready

### Should-Have (At Least 2)

- [ ] Cost savings quantified (>20% reduction)
- [ ] User feedback indicates cost concerns
- [ ] Provider cost differences significant (>2x)
- [ ] Routing infrastructure stable (6+ months)

### Nice-to-Have (Optional)

- [ ] Real-time cost monitoring dashboard
- [ ] Cost prediction models trained
- [ ] A/B testing framework ready

---

## Implementation Plan (When Unblocked)

### Phase 1: Foundation (Week 1-2)

- [ ] Cost tracking integration
- [ ] Cost-to-value ratio calculation
- [ ] Basic cost-aware routing

### Phase 2: Optimization (Week 3-4)

- [ ] Budget limits enforcement
- [ ] Cost prediction integration
- [ ] Performance optimization

### Phase 3: Advanced Features (Week 5-6)

- [ ] Real-time cost monitoring
- [ ] A/B testing for cost routing
- [ ] Cost reporting and analytics

---

## Alternative Approaches

### Option A: Defer Completely

**Pros**:

- Focus on higher-priority features
- Avoid premature optimization

**Cons**:

- Miss potential cost savings
- May need to retrofit later

**Recommendation**: Current choice

### Option B: Implement Now

**Pros**:

- Early cost optimization
- Competitive advantage

**Cons**:

- Diverts resources from higher priorities
- May introduce complexity prematurely

**Recommendation**: Not recommended

### Option C: Phased Implementation

**Pros**:

- Gradual rollout
- Lower risk

**Cons**:

- Longer timeline
- More coordination needed

**Recommendation**: Use when unblocked

---

## Monitoring & Review

**Review Schedule**: Quarterly
**Next Review**: 2026-05-17
**Review Criteria**: Check unblock criteria status

**Metrics to Track**:

- Cost tracking infrastructure status
- Historical cost data availability
- User cost concerns (support tickets, feedback)
- Provider cost differences

---

## BACKLOG Item

| ID                                       | Title                           | Priority | Depends                               | Unblock Criteria           |
| ---------------------------------------- | ------------------------------- | -------- | ------------------------------------- | -------------------------- |
| **research-cost-routing-implementation** | Implement advanced cost routing | P2       | WP-5003, research-economic-governance | See unblock criteria above |

**Status**: Deferred until unblock criteria met

## Implementation Research

### Architecture Overview

When unblocked, the cost routing implementation will provide:

1. **Cost-Aware Model Selection**: Select models based on cost-to-quality ratio
2. **Budget Enforcement**: Enforce per-run and per-session cost budgets
3. **Cost Optimization**: Route to cheaper models when quality requirements allow
4. **Cost Tracking**: Real-time cost tracking and aggregation

### Implementation Structure

```python
# src/thegent/routing/cost_router.py (future)
from thegent.governance.costs import CostTracker
from thegent.planning.selector import ObjectiveSelector


class CostRouter:
    """Cost-aware routing for model selection."""

    def __init__(self, cost_tracker: CostTracker):
        self.cost_tracker = cost_tracker
        self.selector = ObjectiveSelector()

    def select_model(self, requirements: dict, budget: float, objective: str = "cost_quality") -> str:
        """Select model based on cost and quality requirements."""
        # Get available models with cost estimates
        models = self._get_available_models(requirements)

        # Filter by budget
        affordable_models = [m for m in models if m["estimated_cost"] <= budget]

        if not affordable_models:
            raise BudgetExceededError(f"No models within budget: {budget}")

        # Select based on objective
        if objective == "cost_quality":
            return self.selector.select_cost_quality(affordable_models)
        elif objective == "cheapest":
            return min(affordable_models, key=lambda m: m["estimated_cost"])
        elif objective == "fastest":
            return min(affordable_models, key=lambda m: m["latency"])
        else:
            return affordable_models[0]
```

### Unblock Criteria Status

**Current Status**: Monitoring unblock criteria

**Metrics to Track**:

- [ ] Cost tracking infrastructure complete (WP-5003)
- [ ] Historical cost data available (30+ days)
- [ ] User cost concerns identified (support tickets)
- [ ] Provider cost differences documented

**Review Schedule**: Quarterly review of unblock criteria

---

## References

- [COST_ROUTING_DEFERRED.md](./COST_ROUTING_DEFERRED.md) - Original deferral document
- [WP-5003](../plans/02-UNIFIED-WBS.md#wp-5003) - Economic Governance
- [research-economic-governance](./SESSION_RESEARCH_FRAGMENTS_EXPANDED.md#3-economic-governance) - Economic governance research
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (1 BACKLOG item)
- [COST_ROUTING_DEFERRED.md](./COST_ROUTING_DEFERRED.md) - Original deferral document
- [SESSION_RESEARCH_FRAGMENTS_EXPANDED.md](./SESSION_RESEARCH_FRAGMENTS_EXPANDED.md) - Economic governance research
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

---

**Status**: Formal decision record complete
**Next Steps**: Monitor unblock criteria, review quarterly

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added planning patterns
2. Added implementation roadmap
3. Enhanced cross-references

### Cross-References Added

- WORK_STREAM.md
- Implementation guides

### Practical Additions

- Planning templates
- Roadmap configurations
