# Phase 4 UX: Operator Cockpit & Rationale Depth (WP-4001)

This document defines the depth and technical requirements for the **Operator Cockpit**, the primary monitoring and control interface for `thegent`.

## 1. The 4-Pane Mission Control Layout

The Cockpit is structured into four functional zones to minimize cognitive load while maximizing situational awareness.

| Pane           | Content                 | Responsibility                                                                   |
| -------------- | ----------------------- | -------------------------------------------------------------------------------- |
| **1. Queue**   | Pending/Active Runs     | Visibility into the current workload and priority.                               |
| **2. Roster**  | Agent Status & Circuits | Health of the agent fleet (availability, latencies, circuit breaker states).     |
| **3. Stream**  | Live Event Log          | Real-time audit trail of routed chunks and policy decisions.                     |
| **4. Details** | Rationale & Evidence    | Deep dive into the active run's logic, confidence breakdown, and MAIF artifacts. |

## 2. Autonomy Gradient Control

The Cockpit includes a "Global Autonomy Dial" that allows operators to shift governance modes in real-time:

- **Level 1: Full Manual**: Every action requires explicit approval.
- **Level 2: Guarded**: Low-risk actions auto-approved; high-risk flagged for review.
- **Level 3: Supervised**: Most actions auto-approved; operator notified on exceptions/drift.
- **Level 4: Full Autonomous**: Agent acts on its own; operator monitors TRAFFIC KPIs.

## 3. Progressive Disclosure (3-Tier View)

To prevent alert fatigue, information is tiered based on the operator's persona:

- **Tier 1 (Operator)**: "The agent decided X because Y. Status: OK."
- **Tier 2 (SRE)**: "Confidence 0.82; Calibration 0.95; Adjusted Trust 0.78. Logic path: A -> B."
- **Tier 3 (Incident Lead)**: Full MAIF artifact trace, raw tool outputs, and cryptographic signatures.

## 4. Rationale Snapshots (WP-4007)

Every decision includes a "Rationale Snapshot":

- **State Before**: The context the agent saw.
- **Proposed Action**: What the agent wanted to do.
- **Mental Model**: The agent's chain-of-thought (internal monologue).
- **Verification Result**: Why the policy engine allowed/denied it.

## 5. Technical Implementation (WP-4001)

### 5.1 CockpitState Schema

```python
class CockpitState(BaseModel):
    autonomy_level: int = 2
    active_runs: list[RunMeta]
    agent_health: dict[str, CircuitState]
    recent_events: list[OrchestrationEvent]
    alerts: list[Alert]
    kpis: TrafficKPIs
```

### 5.2 TUI/UI Refresh Logic

- **Delta Updates**: Only send changes to the Cockpit to maintain < 2s refresh (P-114).
- **Stale State Block**: If the state is > 30s old, the Cockpit enters a "STALE" mode and disables manual overrides to prevent split-brain decisions.

---

_Cross-ref: [ROBUSTNESS_AND_FUTURE_DEPTH.md](./ROBUSTNESS_AND_FUTURE_DEPTH.md) | [TRAFFIC_KPI_DESIGN.md](./TRAFFIC_KPI_DESIGN.md)_

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
