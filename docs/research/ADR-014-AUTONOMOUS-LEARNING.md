<DONE>
# ADR-014: Autonomous Learning and Cost Sensing

## Status

Proposed

## Context

The current model selection is mostly static or based on simple fallback chains. To optimize for enterprise-grade operations, the system needs to adapt to changing provider costs, performance (latency), and quality outcomes.

## Decision

Implement a policy-safe autonomous learning framework that optimizes model routing based on real-time sensing.

## Technical Approach

1. **Objective Selector**: A weighted optimization engine for multi-objective model selection.
2. **Learning Registry**: A versioned registry for candidate models with "canary" and "default" statuses.
3. **Financial Boundaries**: Explicit spend caps on learning actions to prevent runaway costs.
4. **Handoff for Promotion**: Human-in-the-loop is mandatory for promoting any model from canary to default.
5. **Closed-Loop Feedback**: Integration with the `SLORegulator` and user feedback for continuous calibration.

## Consequences

- **Pros**: Lower operational costs, better performance tuning, adaptive resilience.
- **Cons**: Complexity in debugging non-deterministic model selection, potential for "flapping" between models if not correctly damped.

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## 5. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added autonomous learning patterns
2. Added configuration examples
3. Enhanced cross-references

### Cross-References Added

- PROACTIVE_GOVERNANCE_EVOLUTION_PLAN.md
- ECONOMIC_GOVERNANCE_DEPTH.md

### Practical Additions

- Learning templates
- Configuration examples

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [phase14-autonomous-learning-surface-map.md](./phase14-autonomous-learning-surface-map.md) - Surface map
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
