# Governance WP Implementation Verification (G-GP-01–09)

**Purpose:** Verify WP-3001–WP-3008 implementation status against research recommendations.
**Date:** 2026-02-14
**Source:** GOVERNANCE_POLICY_AUDIT_RESEARCH.md

---

## 1. Summary

| G-GP    | WP              | Item                   | Status     | Implementation                                             |
| ------- | --------------- | ---------------------- | ---------- | ---------------------------------------------------------- |
| G-GP-01 | WP-3001         | OPA integration        | □ In plan  | PolicyEngine exists; OPA/Rego not wired                    |
| G-GP-02 | —               | NeMo Guardrails        | □ In plan  | Input rails before OPA; not implemented                    |
| G-GP-03 | WP-3004         | Audit trail hash chain | ✓ Done     | RunRegistry prev_hash/hash; Auditor.verify_registry        |
| G-GP-04 | WP-2003         | Circuit breakers       | ✓ Partial  | CircuitBreakerRegistry; per-agent; config threshold/window |
| G-GP-05 | WP-3008, 4004   | HITL patterns          | ⚠ Partial | Override with reason; escalation path; no formal HITL flow |
| G-GP-06 | WP-5003         | Cost governance        | □ In plan  | No per-run cost tracking                                   |
| G-GP-07 | WP-3006, 6002   | Compliance evidence    | ⚠ Partial | closure_pack_cmd; history verify; retention TBD            |
| G-GP-08 | WP-3007, FR-014 | Sandboxing             | □ In plan  | No sandbox isolation; trust boundary checks TBD            |
| G-GP-09 | WP-0004, 4008   | Trust scoring          | ⚠ Partial | trust_score_threshold; feedback; calibration TBD           |

Legend: ✓ Done | ⚠ Partial | □ In plan / Not done

---

## 2. Per-WP Detail

### WP-3001: Policy Pre-Check (G-GP-01)

**Research:** OPA as policy decision point; Rego policies.

**Current:** `PolicyEngine` in `execution.py` — evaluates RunMeta before execution. Policies: critical lane confidence, unknown agents, production trust threshold, override with reason. **Not OPA** — Python logic, not Rego.

**Gap:** Wire OPA for declarative policy; or document PolicyEngine as Phase 1, OPA as Phase 2.

---

### Input Guardrails (G-GP-02)

**Research:** NeMo-style input validation before OPA.

**Current:** `src/thegent/governance/input_guardrails.py` — InputGuardrails (prompt_length, agent_allowlist, cwd_restriction, model_allowlist, prompt_blocklist). Wired before PolicyEngine when `THGENT_INPUT_GUARDRAILS_ENABLED=1`.

**Status:** ⚠ Partial — scaffold in place; default rules; CI tests in test_unit_governance.py.

---

### WP-3004: Audit Trail Hash Chain (G-GP-03)

**Research:** Immutable audit events; hash chain integrity.

**Current:** `RunRegistry.register_start`, `register_end`, `register_feedback`, `register_pause`, `register_resume` — each event has `prev_hash`, `hash`. `Auditor.verify_registry()` checks chain integrity.

**Status:** ✓ Done.

---

### WP-2003: Circuit Breakers (G-GP-04)

**Research:** Per-provider 3-state (closed/open/half-open); configurable thresholds.

**Current:** `CircuitBreakerRegistry` — `record_failure`, `is_open`. Threshold=5, window_s=300, recovery_s=60. Used in `run_with_failover` before invoking runner. Half-open: after recovery_s, allows trial.

**Status:** ✓ Partial — verify per-subsystem config (currently agent-only).

---

### WP-3008, 4004: HITL (G-GP-05)

**Research:** Interrupt & resume; policy-driven approval; escalation SLA.

**Current:** Override with `--override-reason`; policy "deny" can be overridden. No formal interrupt checkpoint or escalation queue.

**Gap:** Add checkpoint-based HITL; escalation path for exhausted retries.

---

### WP-5003: Cost Governance (G-GP-06)

**Research:** Per-run cost aggregation; budget alerts; cost-per-quality.

**Current:** `src/thegent/governance/cost.py` — CostEstimator, CostAggregator; RunRegistry.register_end(cost_usd=); THGENT_COST_TRACKING env.

**Status:** ⚠ Partial — scaffold in place; budget alerts and daily rollup TBD.

---

### WP-3006, 6002: Compliance Evidence (G-GP-07)

**Research:** Retention by domain; closure pack with evidence.

**Current:** `closure_pack_cmd` generates signoff package; `history verify` checks registry integrity. No automated retention policy.

**Gap:** Retention policies; domain tagging; tier transitions.

---

### WP-3007, FR-014: Sandboxing (G-GP-08)

**Research:** Network egress, filesystem write protection, trust boundary for env transitions.

**Current:** None. Agents run in host process; no isolation.

**Gap:** Sandbox design; Firecracker/gVisor/Docker integration; trust boundary validation.

---

### WP-0004, 4008: Trust Scoring (G-GP-09)

**Research:** Confidence calibration; trust_score; feedback loop.

**Current:** `trust_score_threshold` in config; `govern feedback` records score; PolicyEngine uses confidence for production gate. No calibration curve or calibration factor persistence.

**Status:** ⚠ Partial — `CircuitBreakerRegistry.get_calibration_factor` exists; feedback stored.

---

## 3. Recommended Next Steps

| Priority | Action                                                       | Status                                             |
| -------- | ------------------------------------------------------------ | -------------------------------------------------- |
| P1       | Document PolicyEngine as Phase 1 PDP; OPA as Phase 2 option  | Done — `docs/governance/OPA_INTEGRATION_DESIGN.md` |
| P1       | Verify circuit breaker used for all agent invocations        | In progress                                        |
| P2       | Add retention policy config; domain tagging for audit events | TBD                                                |
| P2       | Expand closure pack with retention/evidence matrix           | TBD                                                |
| P3       | OPA integration design doc                                   | Done                                               |
| P3       | Sandboxing design doc (Firecracker/gVisor)                   | Done — `docs/governance/SANDBOXING_DESIGN.md`      |
| P3       | Cost tracking design                                         | Done — `docs/governance/COST_GOVERNANCE_DESIGN.md` |
| P3       | NeMo Guardrails design                                       | Done — `docs/governance/NEMO_GUARDRAILS_DESIGN.md` |

---

## 4. References

- `docs/research/GOVERNANCE_POLICY_AUDIT_RESEARCH.md`
- `src/thegent/execution.py` — PolicyEngine, RunRegistry, Auditor, CircuitBreakerRegistry
- `src/thegent/config.py` — trust_score_threshold
- **Design docs:** `docs/governance/OPA_INTEGRATION_DESIGN.md`, `NEMO_GUARDRAILS_DESIGN.md`, `COST_GOVERNANCE_DESIGN.md`, `SANDBOXING_DESIGN.md`

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->

## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.
