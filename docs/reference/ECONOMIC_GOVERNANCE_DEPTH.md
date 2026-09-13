# Economic Governance & Token ROI Modeling (WP-5003)

This document defines the depth for **Economic Governance** within `thegent`, focusing on token unit economics, cost attribution, and ROI-driven routing.

## 1. Token Unit Economics & Cost Attribution

`thegent` treats AI compute as a finite economic resource. Every `RunMeta` and `OrchestrationEvent` must attribute costs to specific project entities.

### 1.1 Attribution Hierarchy

Costs are rolled up in a 3-tier hierarchy:

1. **Work Package (WP)**: The direct cost to complete a specific task (e.g., `WP-3002`).
2. **Batch/Epic**: The cumulative cost of a sequential batch of agents.
3. **Session/Project**: The total burn rate for the current user or project.

### 1.2 Resource Metering (WP-5003)

The `thegent` core tracks:

- `tokens_in`: Prompt tokens.
- `tokens_out`: Completion tokens.
- `cost_usd`: Calculated based on the provider's specific rate (scraped via `models/scrapers.py`).
- `compute_s`: Wall-clock execution time.

## 2. ROI-Driven Routing & Task Scoring

Not all tasks justify the use of a flagship model (e.g., GPT-4o, Claude 3.5 Sonnet). `thegent` uses **ROI Scoring** to determine the appropriate model tier.

### 2.1 Task Value Scoring

Tasks in the **Unified Work Stream** are assigned a `Value_Score` (0.0–1.0):

- **High Value (0.8–1.0)**: Final verification, complex architecture, critical security fixes.
- **Medium Value (0.4–0.7)**: Implementation, unit testing, documentation synthesis.
- **Low Value (0.0–0.3)**: Initial research (eXplore), style fixes, boilerplate generation.

### 2.2 ROI Thresholds

The router applies the following logic:

- `ROI = (Value_Score * Expected_Accuracy) / Cost`
- The `thegent` orchestrator selects the provider on the **Pareto Front** that maximizes ROI within the current budget.

## 3. Budget Caps & Hard Stops (WP-5003)

To prevent runaway loops (e.g., recursive research), `thegent` implements multi-level budget gates:

| Level                | Action                         | Rationale                            |
| -------------------- | ------------------------------ | ------------------------------------ |
| **Warning (80%)**    | Notify Cockpit & Alert Log.    | Operator awareness.                  |
| **Soft Cap (95%)**   | Route to cheaper models only.  | Degraded performance to save budget. |
| **Hard Stop (100%)** | Terminate run & pause session. | Prevent financial overburn.          |

## 4. Economic Reporting

The **Operator Cockpit** provides a real-time "Burn Rate" visualization, showing:

- **MTD Spend** vs. **Monthly Budget**.
- **Project ROI**: Estimated value delivered vs. tokens consumed.
- **Top 5 Costly WPs**: Identifying bottlenecks for model-tier optimization.

---

_Cross-ref: [PARETO_ROUTING_DESIGN.md](./PARETO_ROUTING_DESIGN.md) | [05-ARCHITECTURE.md](../plans/05-ARCHITECTURE.md)_

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

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->

## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.
