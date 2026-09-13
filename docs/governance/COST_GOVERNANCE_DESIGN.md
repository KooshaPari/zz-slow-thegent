# Cost Governance Design (G-GP-06)

**Purpose:** Design per-run cost tracking and budget governance.
**Date:** 2026-02-14
**Status:** Design
**Source:** GOVERNANCE_POLICY_AUDIT_RESEARCH, WP-5003

---

## 1. Current State

- **Gap:** No per-run cost tracking; no budget alerts.
- **Existing:** `cost_weight` on Route in catalog (static, for routing preference).

---

## 2. Design Goals

1. **Per-run cost:** Estimate or record cost per run (tokens, API calls).
2. **Budget alerts:** Warn when daily/run budget exceeded.
3. **Cost-per-quality:** Optional cost vs. confidence/quality correlation.

---

## 3. Architecture

```
Run start
    ↓
RunRegistry.register_start(..., estimated_cost=0)
    ↓
Run end
    ↓
CostEstimator.estimate(run_meta, tokens_in, tokens_out, model) → cost_usd
    ↓
RunRegistry.register_end(..., cost_usd=cost)
    ↓
CostAggregator.daily_total(owner) → sum
    ↓
[If daily_total > budget] → emit alert, optional block
```

---

## 4. Cost Estimation

| Source                 | Method                                           |
| ---------------------- | ------------------------------------------------ |
| Provider pricing table | Static $/1k tokens per model                     |
| Run metadata           | tokens_in, tokens_out from runner (if available) |
| Fallback               | Heuristic: prompt_length \* 1.3 + 500 for output |

---

## 5. Implementation Phases

| Phase | Deliverable                                   | Effort   |
| ----- | --------------------------------------------- | -------- |
| P1    | Design doc (this)                             | Done     |
| P2    | CostEstimator; pricing table (config)         | 2–3 days |
| P3    | RunRegistry cost fields; register_end cost    | 1–2 days |
| P4    | CostAggregator; daily rollup; budget config   | 2–3 days |
| P5    | Alert emission; optional pre-run budget check | 1–2 days |

---

## 6. Configuration

```yaml
governance:
  cost:
    enabled: false
    daily_budget_usd: 10.0
    budget_scope: owner # owner | global
    alert_on_exceed: true
    block_on_exceed: false
  pricing:
    # $ per 1k tokens (input, output)
    claude-sonnet-4: [0.003, 0.015]
    gemini-3-flash: [0.0001, 0.0004]
```

---

## 7. References

- `docs/GOVERNANCE_WP_VERIFICATION.md` — G-GP-06
- `src/thegent/execution.py` — RunRegistry
- `docs/research/COST_ROUTING_DEFERRED.md`

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->

## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.
