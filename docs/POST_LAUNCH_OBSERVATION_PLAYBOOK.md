# Post-Launch Observation Playbook

**Scope:** thegent orchestration platform
**Date:** 2026-02-14
**Related:** WP-6007, `docs/RUNBOOK.md` §4, `docs/enterprise/OPERATING_MODEL.md`

---

## 1. Overview

This playbook defines incident severity classification, escalation SLA mapping, and rollback capacity for post-launch observation. It complements the RUNBOOK and OPERATING_MODEL for launch readiness.

---

## 2. Incident Severity Classification

| Severity          | Definition                                             | Examples                                                       |
| ----------------- | ------------------------------------------------------ | -------------------------------------------------------------- |
| **P1 – Critical** | Production down; data loss/corruption; security breach | Run registry corrupted; policy bypass; audit chain broken      |
| **P2 – High**     | Major feature unavailable; significant degradation     | All providers failing; DAG run blocked; drift > 20%            |
| **P3 – Medium**   | Partial degradation; workaround available              | Single provider down; fallback rate > 30%; health gate failing |
| **P4 – Low**      | Minor issue; no user impact                            | Cosmetic; non-critical telemetry gap                           |

---

## 3. Severity → SLA Mapping

| Severity | First Response | Resolution Target | Escalation                                      |
| -------- | -------------- | ----------------- | ----------------------------------------------- |
| **P1**   | 15 min         | 4 hours           | Immediate: Tech Lead + Product Owner + Security |
| **P2**   | 30 min         | 8 hours           | Tech Lead within 1 hr; Product Owner if > 4 hr  |
| **P3**   | 2 hours        | 24 hours          | Tech Lead; Operator can resolve                 |
| **P4**   | 24 hours       | Next sprint       | Backlog                                         |

---

## 4. Observation Cadence

| Cadence      | Action                                               | Owner     |
| ------------ | ---------------------------------------------------- | --------- |
| **Daily**    | `thegent benchmark` — success rate > 90%             | Operator  |
| **Daily**    | `thegent govern escalate list --past-sla`            | Operator  |
| **Weekly**   | `thegent observe drift` — structural/semantic budget | Operator  |
| **Weekly**   | `thegent govern sweep` — drift + past-SLA            | Operator  |
| **Weekly**   | `thegent archive` — prune old sessions               | Operator  |
| **Per DAG**  | `thegent closure-pack` at session end                | Operator  |
| **Pre-prod** | Rollback capacity checklist (below)                  | Tech Lead |

---

## 5. Rollback Capacity Checklist

Before production cutover, verify:

- [ ] `thegent dag checkpoints` returns at least one recent baseline
- [ ] `thegent dag rollback <checkpoint_id>` tested in staging
- [ ] Session data under `THGENT_RETENTION_DAYS_SESSIONS` (default 30d)
- [ ] Override TTL understood (`THGENT_OVERRIDE_TTL_SECONDS` = 24h)
- [ ] Escalation queue empty or all past-SLA items assigned
- [ ] Trust boundary (WP-3007): no skip-level promotion without audit
- [ ] Drift block (XC2): `thegent dag run --check-drift` blocks when drift exceeds budget

---

## 6. Escalation Triggers

| Trigger                        | Action                                             |
| ------------------------------ | -------------------------------------------------- |
| Success rate < 85% for 24h     | P2; escalate to Tech Lead                          |
| Escalation queue > 5 past-SLA  | P2; escalate to Product Owner                      |
| Audit verify fails             | P1; escalate to Security                           |
| Critical lane blocked by drift | P2; run `thegent observe drift`; remediate adapter |
| Circuit open for > 1 hr        | P3; investigate provider; consider failover        |

---

## 7. References

- `docs/RUNBOOK.md` — Recovery, escalation, post-launch §4
- `docs/enterprise/OPERATING_MODEL.md` — RACI, escalation paths
- `docs/enterprise/DECOMMISSIONING_PLAN.md` — Rollback strategy
