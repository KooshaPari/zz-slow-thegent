# Rollback Reserve Plan

**Program:** thegent Orchestration Optimization
**Date:** 2026-02-15
**Owner:** Site Reliability Engineering Lead

## 1) Purpose

Define controlled rollback behavior and decision logic for launch-phase anomalies.

## 2) Rollback triggers

- [x] KPI critical breach: TRAFFIC critical metric violated for > 3 minutes
- [x] Escalation queue aging: P95 > 30 minutes with unresolved criticals
- [x] Audit/signature verification failure rate > 0.5% over 10-minute window
- [x] SLO rollback threshold breach (as defined in `docs/closure/SLO_CERTIFICATION_MATRIX.md`)

## 3) Trigger severity mapping

| Trigger severity | Response target                                     | Max time to action | Owner                       |
| ---------------- | --------------------------------------------------- | ------------------ | --------------------------- |
| SEV-1            | Immediate rollback decision                         | 5 minutes          | Platform On-call + Gov Lead |
| SEV-2            | Control-plane mitigation + evaluate rollback window | 15 minutes         | Release + Reliability       |
| SEV-3            | Investigate + mitigation first                      | 30 minutes         | Product + Governance        |
| SEV-4            | Review in daily cadence                             | 24 hours           | Program                     |

## 4) Rollback steps

1. Announce incident and severity in status channel.
2. Lock non-essential releases and stop ramp-up.
3. Validate canary rollback command and artifact integrity.
4. Execute rollback procedure:
   - restore prior policy/feature set
   - confirm checkpoint integrity
   - re-run readiness smoke checks.
5. Verify incident scope and capture evidence in `artifacts/closure/closure_summary.ndjson`.
6. Resume with post-incident follow-up and residual fix plan.

## 5) Pre-approved rollback bundle

- `WP-3001`..`WP-3008` policy controls
- `WP-6001` rehearsal and incident fallback profile
- `WP-5001` adaptive concurrency controls
- `WP-5006` handoff integrity rules

## 6) Post-rollback acceptance

- No runbook breach
- Escalation queue drained to acceptable depth
- Compliance/audit artifacts remain intact and coherent

## 7) Dry-run cadence

- [x] Weekly rollback rehearsal
- [x] Monthly full rollback drill with production-like load profile

## 8) Signoff

| Role             | Name               | Decision   | Date         |
| ---------------- | ------------------ | ---------- | ------------ |
| Reliability Lead | `reliability-lead` | `Approved` | `2026-02-15` |
| Governance Lead  | `governance-lead`  | `Approved` | `2026-02-15` |
| Security Lead    | `security-lead`    | `Approved` | `2026-02-15` |
| Product Lead     | `product-lead`     | `Approved` | `2026-02-15` |

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
- [DR_REHEARSAL_REPORT.md](./DR_REHEARSAL_REPORT.md) — DR rehearsal
