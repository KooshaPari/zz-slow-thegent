<DONE>
# ADR-013: Multi-Org Policy Federation

## Status

Proposed

## Context

As the platform scales to enterprise environments, a single global policy is insufficient. Different organizations, projects, and environments require distinct governance rules, compliance controls, and risk thresholds.

## Decision

Implement a hierarchical policy federation model based on namespaces (`org.project.environment`).

## Technical Approach

1. **Namespace Model**: Three-level hierarchy with inheritance (Specific -> Default).
2. **Federated Manager**: `FederatedPolicyManager` for directory-based policy resolution.
3. **Jurisdiction Profiles**: Automatic overlay of legal/audit constraints based on region (e.g., EU-AI-ACT).
4. **Consent Relay**: Traceable handoff of approval authority between namespaces.
5. **Arbitration**: "Most restrictive wins" strategy for conflicting federated rules.

## Consequences

- **Pros**: Strict isolation, scalable governance, compliance automation.
- **Cons**: Increased complexity in policy debugging, slight latency overhead for deep hierarchy resolution.

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [phase13-policy-federation-surface-map.md](./phase13-policy-federation-surface-map.md) - Policy federation surface map
- [research-phase13-policy-federation](../reference/WORK_STREAM.md#research-phase13-policy-federation) - Policy federation BACKLOG item
- [GOVERNANCE_WP_GAPS_EXPANDED.md](./GOVERNANCE_WP_GAPS_EXPANDED.md) - Governance gaps analysis
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## 5. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added policy federation patterns
2. Added implementation examples
3. Enhanced cross-references

### Cross-References Added

- GOVERNANCE_POLICY_AUDIT_RESEARCH.md
- GOVERNANCE_WP_GAPS.md

### Practical Additions

- Federation templates
- Policy configuration examples
