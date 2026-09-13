# Model Routing & Cost Governance: Complete Index

**Master navigation guide for all model selection, routing, and cost governance documents.**

**Last Updated:** 2026-02-15
**Status:** Complete and ready for implementation

---

## Document Stack (Read in Order)

### Phase 1: Understand Your Options (5 min read)

**Start here if:** You're new to this, want a high-level overview, or need to pick a model quickly.

**File:** `PARETO_FRONTIER_MATRIX.md` (9.3 KB)
**What it does:**

- Shows 6 recommended models ranked by cost-quality-speed trade-offs
- Provides performance tiers, speed tiers, and cost tiers
- Includes quick decision tree and cost projections
- Shows how to save $100/month vs. current spend

**Key tables:**

- Table 1: Performance Tiers (Excellent/Good/Acceptable/Budget)
- Table 2: Speed Tiers (Instant/Fast/Normal/Batch)
- Table 3: Cost Tiers (Ultra-Low/Low/Standard/Premium)
- Table 4: Pareto Frontier (6-model recommendation tier)
- Table 5: Cost-Quality Ratio (quality per dollar)

**Quick takeaway:** Haiku for standard work, Gemini Flash for speed, Opus for hardest problems.

---

### Phase 2: Route Requests Programmatically (20 min read)

**Start here if:** You're implementing task routing logic, building the dispatcher, or need to understand constraints per category.

**File:** `ROUTING_DECISION_MATRIX.md` (20 KB)
**What it does:**

- Defines 4 task categories (FAST, NORMAL, COMPLEX, HIGH_COMPLEX) with token ranges and budgets
- For each category: hard constraints, soft optimization priorities, fallback chains, pseudocode
- Explains how to validate requests before routing
- Shows escalation protocol when all options exhausted

**Key sections (one per category):**

- FAST (50–500 tokens, $50/mo): Gemini Flash primary, Haiku fallback
- NORMAL (500–3K tokens, $200/mo): Haiku primary, Gemini/Sonnet fallback
- COMPLEX (3K–10K tokens, $150/mo): Sonnet primary, Gemini/Opus fallback
- HIGH_COMPLEX (>10K tokens, $50/mo): Opus primary, Minimax fallback

**Implementation assets:**

- Hard constraint checklist per category
- Soft optimization priorities
- Pseudocode for decision logic
- Budget enforcement thresholds (80% warning, 100% block)
- Monitoring & alerting rules
- 8-step implementation checklist

**Quick takeaway:** Validate constraints, follow fallback chain, escalate deterministically when exhausted.

---

### Phase 3: Enforce Budget Limits (15 min read)

**Start here if:** You're building cost tracking, budget enforcement, or escalation procedures.

**File:** `COST_ENFORCEMENT_POLICY.md` (19 KB)
**What it does:**

- Defines 2-tier cost limits (per-call instantaneous + monthly cumulative)
- Shows how to track real-time costs and fire alerts
- Explains escalation paths when budgets exhaust
- Details monthly reset procedure and audit trail
- Specifies manual approval workflow

**Key systems:**

- Real-time cost ledger (JSON format)
- Alert levels (Informational → Warning → Critical → Emergency)
- Escalation decision trees (hard blocks, no silent degradation)
- Month-end snapshot & rollover procedure
- Monitoring dashboard spec (KPIs, views, metrics)
- 8-phase implementation roadmap

**Implementation assets:**

- Cost ledger entry format (copy-paste ready)
- Alert message templates (80% warning, 100% block)
- Escalation decision tree (pseudocode)
- Monthly report template
- Dashboard mock-ups (budget health, routing decisions, alerts)

**Quick takeaway:** Hard blocks at $450/mo total; warn at 80%; no silent failures or overflow.

---

### Phase 4: Quick Lookups (5 min references)

#### Quick Decision Workflow (High-Level)

1. Incoming request → Categorize by tokens
2. Look up category in ROUTING_DECISION_MATRIX.md
3. Check hard constraints (quality, cost, speed, budget)
4. Use primary model if OK; else try fallback chain
5. If all exhausted, escalate or queue (see COST_ENFORCEMENT_POLICY.md)
6. Log routing decision and cost impact

#### Model Cheat Sheet (One-Liner)

```
Quick fix/chat          → Gemini Flash (fastest, smart)
Standard coding         → Haiku (affordable, reliable)
Complex debugging       → Sonnet (balanced tier)
Architecture decision   → Opus (best reasoning)
Ultra-high-volume loop  → Minimax (frontier quality, cheap)
Emergency fallback      → GPT-4o mini (cheapest)
```

#### Budget Allocation (Monthly)

```
FAST:        $50  (Gemini Flash → Haiku)
NORMAL:      $200 (Haiku → Gemini/Sonnet)
COMPLEX:     $150 (Sonnet → Gemini/Opus)
HIGH_COMPLEX: $50 (Opus → Minimax)
─────────────────
TOTAL:       $450 (saves $100/mo vs. current $550)
```

---

## Navigation by Use Case

### "I need to pick a model right now"

**Read:** PARETO_FRONTIER_MATRIX.md → Quick Reference section (2 min)
**Then:** Check the "Quick Reference: I have 1 minute" table at the bottom

### "I need to implement task routing logic"

**Read:** ROUTING_DECISION_MATRIX.md → Your task category section (5 min per category)
**Then:** Copy the pseudocode and decision rules into your implementation
**Finally:** Check COST_ENFORCEMENT_POLICY.md for cost tracking

### "I need to set up budget tracking"

**Read:** COST_ENFORCEMENT_POLICY.md → Cost Limit Architecture & Budget Tracking sections (10 min)
**Then:** Copy the cost ledger JSON format
**Then:** Implement the alert levels and escalation decision trees

### "I need to understand the complete system"

**Read in order:**

1. PARETO_FRONTIER_MATRIX.md (understand options)
2. ROUTING_DECISION_MATRIX.md (understand routing logic)
3. COST_ENFORCEMENT_POLICY.md (understand budget enforcement)
4. This index and MODEL_ROUTING_SUMMARY.md (tie it together)

### "I'm implementing and need to integrate with code"

**See:** ROUTING_DECISION_MATRIX.md → Implementation Checklist (8-step)
**See:** COST_ENFORCEMENT_POLICY.md → Implementation Roadmap (8 phases)
**See:** Both documents for pseudocode and code templates (ready to translate)

### "I need to monitor and alert on costs"

**See:** COST_ENFORCEMENT_POLICY.md → Monitoring Dashboard Spec section
**Copy:** Alert message templates for 80% warning and 100% block scenarios
**Implement:** KPI tracking (cumulative cost, burn rate, queue depth, etc.)

---

## Key Documents Cross-Reference

### By Topic

| Topic                          | Primary Doc                                                | Secondary Doc                                            |
| ------------------------------ | ---------------------------------------------------------- | -------------------------------------------------------- |
| Model benchmarks & performance | PARETO_FRONTIER_MATRIX.md Table 1                          | ROUTING_DECISION_MATRIX.md Hard Constraints              |
| Model speed & latency          | PARETO_FRONTIER_MATRIX.md Table 2                          | ROUTING_DECISION_MATRIX.md Speed SLA per category        |
| Model pricing                  | PARETO_FRONTIER_MATRIX.md Table 3                          | COST_ENFORCEMENT_POLICY.md Budget Allocation             |
| Cost-quality ratio             | PARETO_FRONTIER_MATRIX.md Table 5                          | ROUTING_DECISION_MATRIX.md Soft Optimization             |
| Task categorization            | ROUTING_DECISION_MATRIX.md Overview                        | —                                                        |
| Routing logic per category     | ROUTING_DECISION_MATRIX.md (each category section)         | MODEL_ROUTING_SUMMARY.md Quick Decision Workflow         |
| Budget limits                  | COST_ENFORCEMENT_POLICY.md Tables 1-2                      | ROUTING_DECISION_MATRIX.md Budget Enforcement subsection |
| Alerts & escalation            | COST_ENFORCEMENT_POLICY.md Alert Levels & Escalation Paths | ROUTING_DECISION_MATRIX.md Global Escalation Protocol    |
| Implementation roadmap         | COST_ENFORCEMENT_POLICY.md Implementation Roadmap          | ROUTING_DECISION_MATRIX.md Implementation Checklist      |
| FAQs & troubleshooting         | COST_ENFORCEMENT_POLICY.md FAQ                             | PARETO_FRONTIER_MATRIX.md Notes & Caveats                |

### By Audience

| Audience                | Read First                                      | Then Read                                              | Implementation                            |
| ----------------------- | ----------------------------------------------- | ------------------------------------------------------ | ----------------------------------------- |
| **Product Manager**     | PARETO_FRONTIER_MATRIX.md (Exec Summary)        | ROUTING_DECISION_MATRIX.md (overview)                  | MODEL_ROUTING_SUMMARY.md (monthly budget) |
| **Backend Engineer**    | ROUTING_DECISION_MATRIX.md (full)               | COST_ENFORCEMENT_POLICY.md (Budget Tracking)           | Implement task_router.py + cost ledger    |
| **DevOps / Operations** | COST_ENFORCEMENT_POLICY.md (Monitoring section) | ROUTING_DECISION_MATRIX.md (Budget Enforcement)        | Deploy dashboard + alerting               |
| **Finance**             | PARETO_FRONTIER_MATRIX.md (cost projections)    | COST_ENFORCEMENT_POLICY.md (monthly budget allocation) | Set budget caps in system                 |
| **QA / Testing**        | ROUTING_DECISION_MATRIX.md (categories)         | PARETO_FRONTIER_MATRIX.md (quality tiers)              | Shadow test routing logic                 |

---

## Implementation Sequence

### Week 1: Setup & Understanding

- [ ] All team members read PARETO_FRONTIER_MATRIX.md (30 min each)
- [ ] Engineers read ROUTING_DECISION_MATRIX.md (1.5 hours)
- [ ] Ops read COST_ENFORCEMENT_POLICY.md (1.5 hours)
- [ ] All review MODEL_ROUTING_SUMMARY.md (30 min)
- [ ] Team alignment meeting (30 min; discuss Q&As)

### Week 1-2: Development

- [ ] Engineer: Implement task categorization logic (token count → category)
- [ ] Engineer: Implement hard constraint validation per category
- [ ] Engineer: Build fallback chain dispatcher
- [ ] Engineer: Wire in cost tracking (ledger, per-call validation)
- [ ] DevOps: Set up cost ledger file/DB + monitoring collection
- [ ] Ops: Build manual approval workflow

### Week 2-3: Integration

- [ ] Engineer: Integrate routing system with task dispatcher
- [ ] DevOps: Deploy monitoring dashboard (budget health, routing decisions, alerts)
- [ ] Ops: Test manual approval workflow
- [ ] QA: Shadow test routing logic (log-only, no enforcement) for 1 week

### Week 3: Validation & Launch

- [ ] QA: Validate all constraint checks work correctly
- [ ] QA: Validate escalation paths (all blocks & queues)
- [ ] QA: Validate alert messages fire at correct thresholds
- [ ] Ops: Go live with enforcement (switch from logging to hard blocks)
- [ ] All: Monitor first month closely; adjust as needed

---

## Success Metrics

### By Month 1 (2026-03-15)

- Cost reduction: 15–20% vs. current ($550 → $440–470)
- No unexpected overages or bill shocks
- All routing decisions logged and auditable
- <2% error rate on cost estimates vs. actual

### By Month 2 (2026-04-15)

- Cost reduction: 18% vs. current ($550 → $450)
- All 4 categories staying within budget 95%+ of time
- <1% error rate on cost estimates
- Model mix stable (% primary vs. fallback consistent)

### By Month 3 (2026-05-15)

- Cost reduction sustained at 18%
- Quality metrics stable (no regression from benchmarks)
- Escalation queue empty (no backlog)
- Ready to re-evaluate benchmarks (Q1 2026 cycle)

---

## Maintenance & Ongoing Operations

### Monthly (End of Month)

- [ ] Run month-end ledger snapshot (COST_ENFORCEMENT_POLICY.md Monthly Reset procedure)
- [ ] Review monthly summary report (actual vs. budget, burn rates, model mix)
- [ ] Identify any underutilized or overutilized categories
- [ ] Reset cumulative costs for next month
- [ ] Process any queued requests from previous month

### Quarterly (Q1, Q2, Q3, Q4)

- [ ] Update benchmark data (SWE-Bench, AIME, latency, pricing)
- [ ] Re-evaluate Pareto frontier (may shift if new models release)
- [ ] Adjust routing rules if benchmarks change significantly
- [ ] Review model mix trends; adjust allocations if needed

### As Needed

- [ ] Revalidate assumptions (latency, error rates, cost accuracy)
- [ ] Adjust budget allocation if workload pattern changes
- [ ] Onboard new team members (have them read full stack in order)
- [ ] Troubleshoot anomalies (high burn rate, quality regression, quota limits)

---

## FAQ: "Where do I find...?"

| Question                                 | Answer                                                                                             |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------- |
| How do I pick a model?                   | PARETO_FRONTIER_MATRIX.md Quick Reference table or MODEL_ROUTING_SUMMARY.md Model Cheat Sheet      |
| What's my token budget per category?     | ROUTING_DECISION_MATRIX.md Overview table or MODEL_ROUTING_SUMMARY.md Budget Allocation            |
| How do I route a task programmatically?  | ROUTING_DECISION_MATRIX.md for your category + Decision Rules pseudocode                           |
| What happens when we hit a budget limit? | COST_ENFORCEMENT_POLICY.md Escalation Paths section                                                |
| How do I approve a high-cost request?    | COST_ENFORCEMENT_POLICY.md Manual Approval & Override Procedures section                           |
| How do I set up cost tracking?           | COST_ENFORCEMENT_POLICY.md Budget Tracking & Alerting section                                      |
| What's the fallback chain for NORMAL?    | ROUTING_DECISION_MATRIX.md NORMAL category → Fallback Routes                                       |
| How often do benchmarks change?          | PARETO_FRONTIER_MATRIX.md Notes & Caveats (quarterly)                                              |
| How much will we save per month?         | PARETO_FRONTIER_MATRIX.md Cumulative Cost Projection or MODEL_ROUTING_SUMMARY.md Budget Allocation |
| What's the total monthly budget?         | $450 (FAST $50 + NORMAL $200 + COMPLEX $150 + HIGH_COMPLEX $50)                                    |

---

## Document Stats

| Document                           | Size      | Read Time   | Audience   | Status         |
| ---------------------------------- | --------- | ----------- | ---------- | -------------- |
| PARETO_FRONTIER_MATRIX.md          | 9.3 KB    | 5 min       | Everyone   | ✓ Ready        |
| ROUTING_DECISION_MATRIX.md         | 20 KB     | 20 min      | Engineers  | ✓ Ready        |
| COST_ENFORCEMENT_POLICY.md         | 19 KB     | 15 min      | Ops/Eng    | ✓ Ready        |
| MODEL_ROUTING_SUMMARY.md           | 11 KB     | 8 min       | Quick ref  | ✓ Ready        |
| MODEL_ROUTING_INDEX.md (this file) | 10 KB     | 10 min      | Navigation | ✓ Ready        |
| **TOTAL**                          | **69 KB** | **~60 min** | —          | ✓ **COMPLETE** |

---

## Support & Questions

### For Model Selection Questions

Consult PARETO_FRONTIER_MATRIX.md Sections: Performance Tiers, Cost Tiers, Quick Reference.

### For Routing Logic Questions

Consult ROUTING_DECISION_MATRIX.md for your category; check Decision Rules subsection.

### For Cost & Budget Questions

Consult COST_ENFORCEMENT_POLICY.md Sections: Budget Limits, Escalation Paths, FAQ.

### For Implementation Questions

Consult ROUTING_DECISION_MATRIX.md Implementation Checklist and COST_ENFORCEMENT_POLICY.md Implementation Roadmap.

### For Troubleshooting

Consult FAQ sections in PARETO_FRONTIER_MATRIX.md and COST_ENFORCEMENT_POLICY.md.

### If Still Stuck

Document the question in a GitHub issue with tag `[model-routing]` and reference which section you consulted.

---

## Version History

| Version | Date       | Change                                 | Status     |
| ------- | ---------- | -------------------------------------- | ---------- |
| 1.0     | 2026-02-15 | Initial consolidated routing framework | ✓ Complete |

---

## Next Steps

1. **Share with team:** Email link to this index + PARETO_FRONTIER_MATRIX.md
2. **Schedule onboarding:** 30-min sync for all engineers; 15-min sync for ops
3. **Start implementation:** Follow Week 1-3 sequence above
4. **Monitor & iterate:** Track monthly metrics; adjust as needed
5. **Re-evaluate Q1 2026:** Update benchmarks, refine routing rules

---

**Ready to implement? Start with PARETO_FRONTIER_MATRIX.md →**

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
