<DONE>
# Governance WP Gaps — Implementation Notes

**Date:** 2026-02-14
**Source:** `thegent-gaps-and-discovery-2026-02-14.md`, `GOVERNANCE_WP_VERIFICATION.md`
**Purpose:** Document remaining governance work package gaps with implementation options.

---

## WP-3003: Override Path with TTL — Revalidation on Expiry

### Current Implementation

| Component        | Location               | Behavior                                                           |
| ---------------- | ---------------------- | ------------------------------------------------------------------ |
| Override flag    | `main.py`, `cli.py`    | `--override "reason"` on run/bg                                    |
| OverrideRegistry | `execution.py`         | Stores `(owner, reason, expires_at)`                               |
| TTL config       | `config.py`            | `override_ttl_seconds` (default 86400 = 24h)                       |
| Policy bypass    | `cli_impl.py` 993–1005 | If deny + override_reason → allow; if deny + has_unexpired → allow |

### Revalidation on Expiry

When TTL expires:

- `OverrideRegistry.has_unexpired(owner)` returns `False`
- Policy re-evaluates; if still deny, user must supply `--override` again
- No cached bypass; re-justification required

**Status:** ✓ Effectively done. Expiry forces re-justification.

### Optional Enhancement

- Emit `governance.override.expired` event when cached override is used but record has expired (stale check).

---

## WP-3006: Compliance Evidence Retention — Tiered Storage, Domain Tagging

### Current Implementation

| Component       | Location    | Behavior                                        |
| --------------- | ----------- | ----------------------------------------------- |
| Retention       | `config.py` | `THGENT_RETENTION_DAYS_SESSIONS`                |
| Archive         | `cli.py`    | `govern archive` archives old sessions          |
| Data protection | `cli.py`    | `govern data-protection` reports WP-3006 status |

### Gaps

1. **Tiered storage:** No hot (30d) vs cold (1yr) distinction; single retention applies.
2. ~~**Domain tagging:** Sessions not tagged by compliance domain~~ ✓ Done: `run --domain`, `bg --domain` set `domain_tag` on RunMeta; `govern archive --domain` filters.
3. **Retention policy per domain:** Cannot apply different retention per domain.

### Implementation Options

| Option | Description                                                                | Effort   | Status |
| ------ | -------------------------------------------------------------------------- | -------- | ------ |
| A      | Add `domain` field to session metadata; `govern archive --domain gdpr`     | 1–2 days | ✓ Done |
| B      | Tiered: `--tier hot` (30d), `--tier cold` (1yr); move to cold storage path | 2–3 days | ✓ Done |
| C      | Config: `THGENT_RETENTION_BY_DOMAIN={"gdpr": 365, "soc2": 2555}`           | 1 day    | ✓ Done |

**Status:** A + B + C complete. `govern compliance-report` generates retention report.

---

## WP-3008: Escalation SLA — Governance Queue Operations

### Current Implementation

| Component               | Location              | Behavior                                               |
| ----------------------- | --------------------- | ------------------------------------------------------ |
| EscalationQueue         | `execution.py`        | add(), list_pending(), resolve(); JSONL in session_dir |
| govern escalate add     | `main.py`, `cli.py`   | Manual add: run_id, reason, sla_minutes, owner, lane   |
| govern escalate list    | `main.py`, `cli.py`   | List pending; `--past-sla` for items past SLA          |
| govern escalate resolve | `main.py`, `cli.py`   | Mark run_id resolved                                   |
| Auto-add on deny        | `cli_impl.py`         | Policy deny → add to queue (escalation_sla_minutes)    |
| Config                  | `config.py`           | `escalation_sla_minutes` (default 30)                  |
| RUNBOOK                 | `RUNBOOK.md`          | Escalation links                                       |
| Risk registry           | `09-RISK-REGISTRY.md` | SLA targets per risk                                   |

### Gaps

1. ~~**Escalation queue schema:** No structured queue~~ ✓ Done: EscalationQueue in execution.py
2. ~~**SLA tracking:** No timers~~ ✓ Done: escalate_by_utc, list --past-sla
3. ~~**Priority dispatch:** Priority field exists; no prioritization logic yet~~ ✓ Done: list_pending sorts by (-priority, blocked_at); escalate add --priority

### Implementation Options

| Option | Description                                                          | Effort   | Status   |
| ------ | -------------------------------------------------------------------- | -------- | -------- |
| A      | EscalationQueue with add(blocked_run, sla_minutes)                   | 2–3 days | ✓ Done   |
| B      | `thegent govern escalate list` — list items past SLA                 | 1 day    | ✓ Done   |
| C      | Integrate with DLQ: when recovery exhausted, add to escalation queue | 1–2 days | Deferred |
| D      | Priority dispatch; continuity snapshots; handoff confirm             | 1 day    | ✓ Done   |

**Status:** A + B + D complete. `orchestrate handoff` includes escalation backlog; `orchestrate handoff-confirm` for incoming-owner confirmation.

---

## BACKLOG items (for WORK_STREAM)

Remaining optional/deferred gaps that can be added as work items when prioritized:

| ID                  | Title                                                                          | Source                         | Priority | Notes                |
| ------------------- | ------------------------------------------------------------------------------ | ------------------------------ | -------- | -------------------- |
| gov-wp-3003-enhance | Emit governance.override.expired when cached override used but record expired  | GOVERNANCE_WP_GAPS.md §WP-3003 | P3       | Optional enhancement |
| gov-wp-3008-dlq     | Integrate EscalationQueue with DLQ: when recovery exhausted, add to escalation | GOVERNANCE_WP_GAPS.md §WP-3008 | P2       | Option C deferred    |

_Most WP-3003, WP-3006, WP-3008 items are complete. See References._

---

## References

- `docs/GOVERNANCE_WP_VERIFICATION.md`
- `docs/research/GOVERNANCE_POLICY_AUDIT_RESEARCH.md`
- `docs/unified-plan/02-UNIFIED-WBS.md` (WP-3003, WP-3006, WP-3008)
- [WORK_STREAM.md](../reference/WORK_STREAM.md)

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added governance gap patterns
2. Added WP configurations
3. Enhanced cross-references

### Cross-References Added

- GOVERNANCE_POLICY_AUDIT_RESEARCH.md
- PROACTIVE_GOVERNANCE_EVOLUTION_PLAN.md

### Practical Additions

- Gap templates
- WP configurations

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [GOVERNANCE_WP_GAPS_EXPANDED.md](./GOVERNANCE_WP_GAPS_EXPANDED.md) - Expanded version
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
