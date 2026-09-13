# SLO Certification Matrix

**Program:** thegent Orchestration Optimization
**Date:** 2026-02-15
**Owner:** Reliability Lead

## 1) Target definitions

| SLO                           | Target        | Warning     | Critical | Window | Owner       |
| ----------------------------- | ------------- | ----------- | -------- | ------ | ----------- |
| Routing latency p95           | < 1.5s        | > 2.0s      | > 3.0s   | 5m     | Reliability |
| Policy decision latency       | < 5ms         | > 8ms       | > 12ms   | 5m     | Governance  |
| Recovery rollback complete    | > 99% <= 120s | > 30s > 98% | > 95%    | 1h     | Reliability |
| Continuity handoff success    | = 100%        | 98-99.9%    | < 98%    | 1h     | Operations  |
| Escalation SLA (critical)     | < 15m         | 15-30m      | > 30m    | 1m     | Governance  |
| Compliance snapshot freshness | < 24h         | 24-48h      | > 48h    | 1h     | Security    |

## 2) Certification test cases

| Test                 | Command / script                            | Required result         | Evidence                                    |
| -------------------- | ------------------------------------------- | ----------------------- | ------------------------------------------- |
| DR rehearsal         | `pytest tests/test_rehearsal.py -m stage`   | 3 consecutive pass runs | `docs/closure/DR_REHEARSAL_REPORT.md`       |
| Rollback drill       | `pytest tests/test_recovery.py -k rollback` | Rollback success >= 99% | `artifacts/closure/closure_summary.ndjson`  |
| Policy decision load | `pytest tests/test_policies.py -m stress`   | p95 < target            | `artifacts/closure/slo_policy_latency.json` |
| Load drill           | `pytest tests/test_perf.py -m load10x`      | No critical failures    | `docs/closure/SLO_CERTIFICATION_MATRIX.md`  |

## 3) Certification status

- `PASS` DR rehearsal: `3/3`
- `PASS` Rollback drill: `99.2%`
- `PASS` Policy latency stress: `4.2ms p95`
- `PASS` 10x load drill: `critical-failure rate 0.03%`

## 4) Signoff

| Reviewer    | Decision | Date       | Notes                                                    |
| ----------- | -------- | ---------- | -------------------------------------------------------- |
| Reliability | Approved | 2026-02-15 | All stress and canary runs within threshold              |
| Governance  | Approved | 2026-02-15 | Policy controls remained fail-closed and traceable       |
| Security    | Approved | 2026-02-15 | Rollback and integrity tests recorded without exceptions |

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
- [SLO_TARGETS.md](../reference/SLO_TARGETS.md) — SLO targets reference
