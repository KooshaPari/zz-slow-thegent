# Thegent Orchestration Runbook (v1.0)

(WP-6004: Runbook finalization and on-call readiness)

## 1. On-Call Readiness

- **Cockpit Monitoring:** Run `thegent cockpit` to check overall health.
- **Failures:** Check `thegent history --events` or `thegent benchmark` for failure patterns.
- **Circuits:** If a circuit is OPEN (red in cockpit), investigate the provider/agent. Circuits half-open automatically after 60s.
- **MCP Verification:** See `docs/VERIFICATION_RUNBOOK.md` for FastMCP server and tool checks.

## 2. Recovery Procedures

- **Stuck Tasks:** Run `thegent dag reconcile` to fix tasks marked as `running` but whose processes are dead.
- **Failed Tasks (Retry):** Run `thegent dag recover --action retry-failed`.
- **Failed Tasks (Fallback):** Run `thegent dag recover --action fallback` to swap the agent to its defined backup.
- **Corruption:** Use `thegent history verify` to check if the run registry has been tampered with.
- **Rollback:** Use `thegent plan rollback` to restore from checkpoint.

## 3. Escalation

- **Feedback:** `thegent govern feedback <run_id> <score> [note]` to record operator feedback.
- **Health Gate:** `thegent govern health-gate` for session contract health evaluation.
- **Drift Alarms:** `thegent govern conformance --check-drift` fails exit code when drift detected.
- **Data Protection:** `thegent govern data-protection` to audit WP-3006 controls (permissions, masking, retention).
- **Override TTL (WP-3003):** `--override` stores a policy override for `THGENT_OVERRIDE_TTL_SECONDS` (default 24h). Within TTL, subsequent runs auto-allow without re-supplying `--override`. After expiry, re-justify required.
- **Escalation Queue (WP-3008):** Policy-denied runs are added automatically. List with `thegent govern escalate list`; filter past-SLA with `--past-sla`. Resolve with `thegent govern escalate resolve <run_id>`.
- **Policy Drift Sweep (WP-3005):** `thegent govern sweep` runs drift detection, budget check, and past-SLA escalations. Cron-ready; exit 1 if issues found.

## 4. Post-Launch Observation (WP-6007)

See `docs/POST_LAUNCH_OBSERVATION_PLAYBOOK.md` for severity→SLA mapping and rollback checklist.

- **Daily:** Run `thegent benchmark` and verify success rates are > 90%.
- **Contract Health:** Monitor `thegent session-contract-health-report` for normalization quality.
- **Drift Detection:** Run `thegent observe drift` to identify degrading provider adapters.
- **Drift Block (XC2):** Use `thegent dag run --check-drift` to block DAG execution when drift detected.
- **Weekly:** Run `thegent archive` to prune old session data (tiered: THGENT_RETENTION_DAYS_SESSIONS).
- **Audit:** Generate a `thegent closure-pack` at the end of every major DAG session.
- **Rollback Reserve:** Before production cutover, ensure `thegent dag checkpoints` has a recent baseline; use `thegent dag rollback <checkpoint_id>` if needed.
- **Trust Boundary (WP-3007):** Skip-level promotions (dev→prod) require explicit audit; env transitions are validated.

## 5. Decommissioning (WP-6006)

- **Sunset Plan:** See `docs/enterprise/DECOMMISSIONING_PLAN.md` for target components and migration path.
- **Legacy Commands:** The `history-legacy` command is hidden and scheduled for sunset in v1.1.
- **Temporary Sessions:** All sessions in `.thegent/sessions` older than 30 days should be archived.

---

## See also

- [WORK_STREAM.md](reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](plans/00-MASTER-INDEX.md) — plan index
