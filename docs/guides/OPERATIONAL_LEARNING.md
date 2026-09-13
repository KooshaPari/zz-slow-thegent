# Operational Learning Assets (WP-12008)

## Quick Start Runbook

1. **Login**: `thegent cliproxy login <provider>`
2. **Negotiate**: `thegent govern negotiate csm csm-v1`
3. **Plan**: `thegent plan dag list`
4. **Execute**: `thegent orchestrate run "task prompt"`

## Anti-Fatigue Coaching Cards

- **Card 1: Correlation First**: Always check `correlation_id` before escalating. Multiple failures with the same ID are likely one root cause.
- **Card 2: Threshold Check**: If `thegent observe traffic` shows fallback > 15%, prioritize adapter tuning over new task runs.
- **Card 3: Sandbox Safety**: Use `thegent observe replay --sandbox` for all what-if simulations to prevent state mutation.

## Operator Checklist

- [ ] Contract version negotiated and matching client capability.
- [ ] System load level is "normal" or "spike" (not "surge").
- [ ] No pending handoff confirmations for current owner.
- [ ] Confidence scores active for critical lane tasks.

## Enterprise-Grade Intuition (Phase 12)

### Signal vs. Noise

- **High-Severity Escalation**: If the `EscalationManager` triggers a cooldown, transition to **Critical Lane** mode. Only `critical` alerts will surface.
- **Explainability**: Use `thegent observe explain <run-id>` to fetch the v2.0 explanation bundle. Look for the `evidence_links` field to verify the decision's foundation.
- **Evidence Integrity**: All evidence bundles exported via `EvidenceGraph` are tamper-proofed with deterministic SHA-256 hashes. Verify the `bundle_checksum` before starting forensic analysis.

### Federation Awareness (Phase 13)

- **Namespace Lookup**: Policies are resolved via `org.project.env`. If a policy is missing, it falls back to `org.default.default`.
- **Conflict Arbitration**: When multiple namespaces apply, the **most restrictive** policy wins (e.g., if one requires human-in-loop, it becomes mandatory).

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
