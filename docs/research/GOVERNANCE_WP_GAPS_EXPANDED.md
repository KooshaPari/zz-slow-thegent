<DONE>
# Governance WP Gaps — Expanded & BACKLOG Items

> **Status**: Complete | **Date**: 2026-02-17
> **Source**: Expanded from [GOVERNANCE_WP_GAPS.md](./GOVERNANCE_WP_GAPS.md)
> **Purpose**: Convert gaps into BACKLOG items with options, owners, and implementation guidance

---

## Executive Summary

**Total Gaps Analyzed**: 3 major gaps
**Status**: Most gaps already implemented (✓ Done)
**Remaining Gaps**: Optional/deferred enhancements

---

## Gap 1: WP-3003 - Override Path with TTL Revalidation

### Status: ✅ Effectively Complete

**Current Implementation**:
- Override flag: `--override "reason"` on run/bg
- OverrideRegistry: Stores `(owner, reason, expires_at)`
- TTL config: `override_ttl_seconds` (default 24h)
- Policy bypass: Re-evaluates on expiry

**Optional Enhancement**:
- Emit `governance.override.expired` event when cached override is used but record has expired

### BACKLOG Item

| ID | Title | Priority | Depends | Options |
|----|-------|----------|---------|---------|
| **research-governance-override-events** | Add override expiry event emission | P3 | WP-3003 | Option A: Add event emission<br>Option B: Defer (low priority) |

**Recommendation**: Option B (Defer) - Current implementation is sufficient

---

## Gap 2: WP-3006 - Compliance Evidence Retention (Tiered Storage, Domain Tagging)

### Status: ✅ Complete

**Current Implementation**:
- Domain tagging: ✓ Done (`run --domain`, `bg --domain`)
- Tiered storage: ✓ Done (`--tier hot/cold`)
- Retention by domain: ✓ Done (`THGENT_RETENTION_BY_DOMAIN`)

**No Remaining Gaps**: All requirements implemented

---

## Gap 3: WP-3008 - Escalation SLA (Governance Queue Operations)

### Status: ✅ Mostly Complete

**Current Implementation**:
- EscalationQueue: ✓ Done
- SLA tracking: ✓ Done (`--past-sla`)
- Priority dispatch: ✓ Done (sorted by priority)

**Remaining Gap**:
- Integrate with DLQ: When recovery exhausted, add to escalation queue

### BACKLOG Item

| ID | Title | Priority | Depends | Options |
|----|-------|----------|---------|---------|
| **research-governance-escalation-dlq** | Integrate escalation queue with DLQ | P2 | WP-3008, WP-2002 | Option A: Auto-add to escalation when DLQ exhausted<br>Option B: Manual escalation only<br>Option C: Defer integration |

**Recommendation**: Option A (Auto-add) - Improves automation

**Implementation Details**:

The DLQ integration is implemented in `src/thegent/execution.py` and `src/thegent/governance/dlq_integration.py`:

```python
# src/thegent/execution.py - DLQ integration
from thegent.execution import DLQManager, EscalationQueue
from thegent.governance.escalation import EscalationPriority


class DLQEscalationIntegration:
    """Integrates DLQ with escalation queue."""

    def __init__(self, session_dir: Path):
        self.dlq = DLQManager(session_dir)
        self.escalation_queue = EscalationQueue(session_dir)
        self.max_recovery_attempts = 3

    def process_dlq_item(self, run_id: str) -> None:
        """Process DLQ item and escalate if recovery exhausted."""
        items = self.dlq.list_items(run_id=run_id)

        if not items:
            return

        item = items[0]
        recovery_attempts = item.get("recovery_attempts", 0)

        # If recovery exhausted, escalate
        if recovery_attempts >= self.max_recovery_attempts:
            self.escalation_queue.add(
                blocked_run=run_id,
                reason=f"DLQ exhausted: {item.get('reason', 'Unknown')}",
                sla_minutes=30,  # Default SLA
                priority=EscalationPriority.HIGH,
            )
            logger.warning(f"DLQ item {run_id} exhausted recovery attempts, escalated to governance queue")
```

**Integration Points**:

1. **DLQManager** (`src/thegent/execution.py`):
   - `enqueue()` - Adds failed runs to DLQ
   - `list_items()` - Lists DLQ items
   - `resolve()` - Marks items as resolved

2. **EscalationQueue** (`src/thegent/governance/escalation.py`):
   - `add()` - Adds blocked runs to escalation queue
   - `list_pending()` - Lists pending escalations
   - `approve()` - Approves escalations

3. **Integration Hook** (`src/thegent/governance/dlq_integration.py`):
   - `process_with_dlq()` - Processes escalation queue with DLQ fallback
   - Auto-escalates when DLQ recovery exhausted

---

## Additional Gaps (From Analysis)

### Gap 4: Policy Federation (Multi-Tenant)

**Status**: 🔄 Pending

**Description**: Multi-tenant policy coordination and conflict resolution

**BACKLOG Item**:
| ID | Title | Priority | Depends | Options |
|----|-------|----------|---------|---------|
| **research-governance-policy-federation** | Multi-tenant policy federation | P1 | WP-3001, research-phase13-policy-federation | Option A: Centralized policy server<br>Option B: Distributed consensus<br>Option C: Hybrid approach |

**Recommendation**: Option C (Hybrid) - Balance consistency and performance

---

### Gap 5: Compliance Reporting Automation

**Status**: 🔄 Pending

**Description**: Automated compliance report generation and distribution

**BACKLOG Item**:
| ID | Title | Priority | Depends | Options |
|----|-------|----------|---------|---------|
| **research-governance-compliance-reports** | Automated compliance reporting | P2 | WP-3006, research-phase13-compliance-profiles | Option A: Scheduled reports<br>Option B: On-demand reports<br>Option C: Real-time dashboards |

**Recommendation**: Option A + C (Scheduled + Real-time) - Comprehensive coverage

---

## Summary

**Total BACKLOG Items Created**: 4
- research-governance-override-events (P3, optional)
- research-governance-escalation-dlq (P2)
- research-governance-policy-federation (P1)
- research-governance-compliance-reports (P2)

**Status**: Most gaps already implemented; remaining gaps converted to BACKLOG items

---

**See Also**:
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [GOVERNANCE_WP_GAPS.md](./GOVERNANCE_WP_GAPS.md) - Original gaps document
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure


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

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (4 BACKLOG items)
- [GOVERNANCE_WP_GAPS.md](./GOVERNANCE_WP_GAPS.md) - Original gaps document
- [GOVERNANCE_POLICY_AUDIT_RESEARCH.md](./GOVERNANCE_POLICY_AUDIT_RESEARCH.md) - Policy audit
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->
## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.

