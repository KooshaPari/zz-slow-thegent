# HITL (Human-in-the-Loop) Design (G-GP-05)

**Purpose:** Design checkpoint-based HITL, escalation path, and policy-driven approval.
**Date:** 2026-02-14
**Status:** Design
**Source:** GOVERNANCE_POLICY_AUDIT_RESEARCH, WP-3008, 4004

---

## 1. Current State

- **Override:** `--override-reason` bypasses policy deny; OverrideRegistry with TTL.
- **Gap:** No formal interrupt checkpoint; no escalation queue for exhausted retries.

---

## 2. Design Goals

1. **Checkpoint-based HITL:** Pause at defined checkpoints; await human approval.
2. **Escalation path:** When retries exhausted, route to escalation queue with SLA.
3. **Policy-driven approval:** Policy "deny" can require HITL approval before override.

---

## 3. Architecture

```
Run start
    ↓
[Checkpoint 1: Pre-execution] Policy deny? → EscalationQueue.add(run_meta, reason)
    ↓
Run execution
    ↓
[Checkpoint 2: Post-execution] Low confidence? → HITL gate (optional)
    ↓
Run end
```

**EscalationQueue:** `list_pending(past_sla_only)` — already exists in cli_impl.
**HITL gate:** New — block run completion until human approves or rejects.

---

## 4. Implementation Phases

| Phase | Deliverable                                     | Effort   |
| ----- | ----------------------------------------------- | -------- |
| P1    | Design doc (this)                               | Done     |
| P2    | Escalation SLA config; SLA breach alert         | 1–2 days |
| P3    | HITL checkpoint enum; optional pause before run | 2–3 days |
| P4    | Approval workflow (CLI: govern approve/reject)  | 2–3 days |

---

## 5. Configuration

```yaml
governance:
  hitl:
    enabled: false
    checkpoints: [pre_execution, post_execution]
    escalation_sla_minutes: 60
  escalation:
    sla_breach_alert: true
```

---

## 6. References

- `docs/GOVERNANCE_WP_VERIFICATION.md` — G-GP-05
- `src/thegent/cli_impl.py` — EscalationQueue, escalate_add_impl
- `src/thegent/execution.py` — PolicyEngine, OverrideRegistry
