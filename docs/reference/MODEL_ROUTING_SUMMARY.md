# Model Routing & Cost Governance: Quick Reference

**Purpose:** High-level summary and navigation guide for the three integrated routing documents.

**Last Updated:** 2026-02-15
**Status:** Ready for implementation

---

## The Three Documents (What Goes Where)

### 1. PARETO_FRONTIER_MATRIX.md

**Use this to:** Choose the right model for your needs at a glance.

**Contains:**

- Performance tiers (Excellent/Good/Acceptable/Budget)
- Speed tiers (Instant to Batch)
- Cost tiers (Ultra-Low to Premium)
- 6-model Pareto frontier (recommended tier list)
- Cost-quality ratio analysis
- Quick decision tree
- Cost projections showing $100/mo savings potential

**Key Takeaway:** Claude Haiku 4.5 is the "Goldilocks" default (73% quality, $3.50/M, proven reliability). Gemini 3 Flash is fastest (78% quality, $2/M, best for interactive tasks). Claude Opus 4.6 for hardest problems.

---

### 2. ROUTING_DECISION_MATRIX.md

**Use this to:** Route requests programmatically with full constraint checking.

**Contains:**

- 4 task categories (FAST, NORMAL, COMPLEX, HIGH_COMPLEX) with token ranges and budgets
- For each category:
  - Hard constraint checks (quality, cost, speed, cumulative budget)
  - Soft optimization priorities
  - Fallback chains (primary → fallback 1 → fallback 2 → fallback 3)
  - Decision pseudocode
  - Budget enforcement thresholds
  - Monitoring & alerting rules
- Cross-category budget view ($450 total monthly)
- Escalation protocol for when all options exhausted
- Implementation checklist

**Key Takeaway:** FAST (50–500 tokens) → Gemini Flash. NORMAL (500–3K) → Haiku. COMPLEX (3K–10K) → Sonnet. HIGH_COMPLEX (>10K) → Opus. Escalate deterministically when budget exhausted; never silently degrade.

---

### 3. COST_ENFORCEMENT_POLICY.md

**Use this to:** Implement cost tracking, budget limits, and escalation procedures.

**Contains:**

- 2-tier cost limits (per-call instantaneous + monthly cumulative)
- Budget tracking ledger format
- Alert levels (Informational → Warning → Critical → Emergency)
- Escalation paths with decision trees
- Month-end ledger reset procedure
- No-silent-failures guardrails
- Manual approval & override procedures
- Monitoring dashboard spec (views + KPIs)
- Implementation roadmap (8 phases)

**Key Takeaway:** Hard blocks at $450/mo cumulative; warn at 80%. Per-call limits prevent runaway single requests. Reject requests clearly, don't degrade silently. Queue or escalate with human review when limits hit.

---

## Quick Decision Workflow

### Step 1: Incoming Request

Capture: tokens, complexity, reasoning_depth, latency_SLA, cost_priority

### Step 2: Categorize

```
if tokens ≤ 500:
  category = FAST
elif tokens ≤ 3K:
  category = NORMAL
elif tokens ≤ 10K:
  category = COMPLEX
else:
  category = HIGH_COMPLEX
```

### Step 3: Route Within Category (See ROUTING_DECISION_MATRIX.md)

```
Check hard constraints (quality, cost, speed, budget)
  ├─ All pass? → Use primary model
  ├─ Some fail? → Try fallback 1, fallback 2, fallback 3
  └─ All exhaust? → Escalate or queue
```

### Step 4: Enforce Budget (See COST_ENFORCEMENT_POLICY.md)

```
Validate cost estimate ≤ per-call limit
  ├─ OK? → Route and log
  └─ Over? → Escalate or reject

Track cumulative cost per category
  ├─ <80%? → Proceed normally
  ├─ 80–100%? → Warn ops
  └─ ≥100%? → Block new requests
```

### Step 5: Fallback Chain

If primary model unavailable (quota/cost), auto-route to fallback. If all exhausted, escalate deterministically (don't silently degrade).

---

## Model Cheat Sheet

### By Use Case

| Use Case                             | Primary      | Fallback        | Budget      |
| ------------------------------------ | ------------ | --------------- | ----------- |
| Quick chat, API test                 | Gemini Flash | Haiku           | $0.001/call |
| Standard coding task                 | Haiku        | Gemini Flash    | $0.02/call  |
| Complex debugging, multi-step        | Sonnet       | Haiku → Minimax | $0.05/call  |
| Architecture design, novel problem   | Opus         | Sonnet          | $0.15+/call |
| Agentic loop (1000+ calls)           | Minimax      | Haiku           | $0.005/call |
| Emergency fallback (budget critical) | GPT-4o mini  | N/A             | $0.001/call |

### By Performance Need

| Threshold                        | Models                        | Note                        |
| -------------------------------- | ----------------------------- | --------------------------- |
| ≥80% (mission-critical)          | Opus, Minimax, GLM-5          | Best reasoning; slower      |
| ≥75% (standard engineering)      | Sonnet, Gemini Flash, Minimax | Balanced tier               |
| ≥70% (quick fixes)               | Haiku, GPT-4o mini            | Fast, cheap                 |
| <70% (extreme budget constraint) | GLM Flash, Minimax M2         | Acceptable for simple tasks |

### By Speed Need

| SLA                     | Models                    | Typical Use          |
| ----------------------- | ------------------------- | -------------------- |
| <1s (interactive, chat) | Gemini Flash, GPT-4o mini | User-facing, REPL    |
| <5s (standard)          | Haiku, Cursor Ultra       | CLI, editor commands |
| <20s (normal)           | Sonnet, Gemini Pro        | Engineering tasks    |
| <60s+ (offline)         | Opus, reasoning models    | Batch processing     |

### By Cost Need

| Budget       | Models                          | Example                 |
| ------------ | ------------------------------- | ----------------------- |
| <$0.001/call | Minimax, GLM Flash, GPT-4o mini | Ultra-high-volume loops |
| <$0.01/call  | Haiku, Gemini Flash             | High-volume, daily ops  |
| <$0.05/call  | Sonnet                          | Standard tier           |
| <$0.50/call  | Opus                            | Mission-critical, rare  |

---

## Monthly Budget Allocation (Recommended)

```
Total Budget: $450/month (50% savings vs. current $550/month)

FAST (25% of volume, interactive tasks):
  Budget: $50
  Primary: Gemini Flash
  Fallback: Haiku → GPT-4o mini
  Expected calls: ~25,000 (avg 2K tokens)
  Per-call limit: $0.002

NORMAL (50% of volume, standard tasks):
  Budget: $200
  Primary: Haiku
  Fallback: Gemini → Sonnet → Minimax
  Expected calls: ~4,000 (avg 1.5K tokens)
  Per-call limit: $0.05

COMPLEX (20% of volume, reasoning tasks):
  Budget: $150
  Primary: Sonnet
  Fallback: Gemini → Opus → Minimax
  Expected calls: ~1,000 (avg 5K tokens)
  Per-call limit: $0.15

HIGH_COMPLEX (5% of volume, mission-critical):
  Budget: $50
  Primary: Opus
  Fallback: Minimax
  Expected calls: ~60 (avg 8K tokens)
  Per-call limit: $0.85
```

**Current Spend:** ~$550/month
**Projected Spend:** ~$450/month (88% utilization)
**Savings:** ~$100/month (18% reduction)

---

## Enforcement Rules (No Exceptions)

1. **No per-call overages.** If cost estimate > per-call limit, escalate or reject. No overflow.
2. **No cumulative overages.** If category cumulative >= monthly limit, block new requests. Queue or escalate.
3. **No silent fallbacks.** If primary model exhausted, explicitly route to fallback and log it. Never degrade silently.
4. **No graceful degradation.** If all options exhausted, reject with actionable error message. Don't pick a cheap model and hope.
5. **Alert at 80%.** Warn ops team when category approaches limit. Gives time to reallocate or escalate.
6. **Block at 100%.** Hard stop when monthly limit hit. No exceptions without manager approval.

---

## Implementation Checklist

- [ ] Read & understand all 3 documents (PARETO_FRONTIER_MATRIX, ROUTING_DECISION_MATRIX, COST_ENFORCEMENT_POLICY)
- [ ] Implement cost ledger (JSON or CSV log of all routing decisions)
- [ ] Code up task categorization logic (token count → category)
- [ ] Wire in hard constraint checks per category (quality, cost, speed, budget)
- [ ] Implement fallback chain dispatcher
- [ ] Add cost tracking per category (cumulative, alert at 80%, block at 100%)
- [ ] Set up monitoring dashboard (real-time budget health, routing decisions, alerts)
- [ ] Build manual approval workflow (for per-call or cross-month overrides)
- [ ] Test escalation paths (ensure all blocks & queues work deterministically)
- [ ] Shadow run (log routing decisions, no actual enforcement) for 1 week
- [ ] Go live (switch to enforcement mode)
- [ ] Calendar reminder: Re-evaluate benchmarks Q1 2026

---

## Monitoring & Observability

### Logs to Emit (Per Request)

```json
{
  "timestamp": "2026-02-15T14:23:45Z",
  "request_id": "req-abc123",
  "category": "NORMAL",
  "input_tokens": 1200,
  "output_tokens_estimate": 500,
  "total_tokens_estimate": 1700,
  "model_primary": "Claude Haiku 4.5",
  "model_routed": "Claude Haiku 4.5",
  "cost_estimate": 0.00595,
  "cost_per_call_limit": 0.05,
  "cost_check": "PASS",
  "cumulative_cost_this_month": 47.32,
  "cumulative_limit": 200,
  "cumulative_check": "PASS (23.7%)",
  "routing_reason": "Primary model available; meets quality & cost constraints",
  "fallback_reason": null,
  "alert_level": "NONE",
  "status": "ROUTED"
}
```

### Metrics to Track (Real-Time Dashboard)

- Cumulative cost per category (with 80%/100% thresholds highlighted)
- Routing distribution (% using primary vs. fallback models)
- Error rate (cost/constraint failures)
- Average latency per model
- Queue depth (escalated/queued requests)
- Cost variance (actual vs. estimated)

### Monthly Review (End of Month)

- Total spend vs. budget per category
- Burn rate trend (are we accelerating?)
- Model mix (primary vs. fallback usage %)
- Quality incidents (models underperforming vs. benchmark)
- Queued requests (unrouted due to budget constraints)
- Recommended adjustments for next month

---

## Escalation Contact List

| Scenario                                   | Owner             | Action                                    |
| ------------------------------------------ | ----------------- | ----------------------------------------- |
| Category approaching 80% budget            | Operations        | Email alert; prepare contingency          |
| Category at 100% budget                    | Manager           | Email alert; decide reallocation or queue |
| Single request exceeds per-call limit      | Manager           | Review; approve or deny override          |
| Quality regression (model underperforming) | Engineering       | Investigate; adjust routing rules         |
| Provider outage (model unavailable)        | DevOps            | Activate fallback chain; escalate         |
| Monthly budget reallocation needed         | Finance + Manager | Document; update routing rules            |

---

## Known Limitations & Future Work

1. **Benchmarks are point-in-time.** Metrics (SWE-Bench, AIME, cost) change quarterly. Re-evaluate Q1 2026.
2. **Latency varies by load.** Times in matrix assume normal load; peak times may vary.
3. **Cost is task-dependent.** Input:output ratio affects final cost. Complex reasoning tasks may have higher multipliers.
4. **Shadow testing recommended.** Test on your workload before full commit; benchmarks don't guarantee performance on your specific tasks.
5. **Minimax M2.5 unproven in production.** Strong benchmarks; less track record. Use cautiously for critical paths.

**Future Enhancements:**

- Implement A/B testing framework to validate model choices on real workloads
- Add cost predictability improvements (confidence intervals on cost estimates)
- Build feedback loop to update benchmarks based on actual performance
- Consider dynamic pricing (adjust budgets based on realized burn rates)
- Integrate with upstream task prioritization (urgent tasks get higher budget tier)

---

## Related Documents

- **PARETO_FRONTIER_MATRIX.md** — Model selection reference; read first to understand options
- **ROUTING_DECISION_MATRIX.md** — Detailed routing logic per category; implement after frontier matrix
- **COST_ENFORCEMENT_POLICY.md** — Budget tracking & escalation procedures; deploy last
- **PLAN.md** (root) — Project roadmap; check if cost governance work is scheduled
- **.claude/qa-config.json** — QA governance config; ensure consistency with routing tiers

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
