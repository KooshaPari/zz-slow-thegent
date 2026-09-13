# Retention Policy Design (G-GP-07)

**Purpose:** Design retention by domain, tier transitions, and compliance evidence.
**Date:** 2026-02-14
**Status:** Design
**Source:** GOVERNANCE_POLICY_AUDIT_RESEARCH, WP-3006, 6002

---

## 1. Current State

- **closure_pack:** Generates signoff package.
- **history verify:** Checks registry integrity.
- **Gap:** No automated retention policy; no domain tagging; retention TBD.

---

## 2. Design Goals

1. **Retention by domain:** Different retention per domain_tag (e.g. project-id, compliance-domain).
2. **Tier transitions:** Dev → staging → prod may have different retention.
3. **Automated purge:** Background job or on-startup purge of expired events.

---

## 3. Architecture

```
RunRegistry events (run_registry.jsonl)
    ↓
Each event has domain_tag (optional)
    ↓
RetentionPolicy: domain_tag → retention_days
    ↓
Purge: events older than retention_days for their domain
```

**Default:** retention_days_sessions, retention_days_registry (already in config).

---

## 4. Implementation Phases

| Phase | Deliverable                                               | Effort   |
| ----- | --------------------------------------------------------- | -------- |
| P1    | Design doc (this)                                         | Done     |
| P2    | domain_tag in RunMeta; retention_days_registry per domain | 1–2 days |
| P3    | Purge command: `thegent govern purge --dry-run`           | 1–2 days |
| P4    | Closure pack expansion with retention/evidence matrix     | 2–3 days |

---

## 5. Configuration

```yaml
governance:
  retention:
    default_days: 90
    by_domain:
      project-alpha: 365
      compliance-audit: 730
```

---

## 6. References

- `docs/GOVERNANCE_WP_VERIFICATION.md` — G-GP-07
- `src/thegent/execution.py` — RunRegistry, RunMeta
- `src/thegent/config.py` — retention_days_sessions, retention_days_registry
