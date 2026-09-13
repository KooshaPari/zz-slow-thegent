# Cost Enforcement Policy: 2x Limit & Escalation Framework

**Purpose:** Define how cost budgets are tracked, when alerts fire, and what happens when limits are exceeded.

**Last Updated:** 2026-02-15
**Framework:** Deterministic cost governance with no silent failures or graceful degradation.

---

## Executive Summary

- **Monthly Budget Cap:** $450 total across all 4 categories (50% reduction from current $550/mo spend)
- **Enforcement Model:** Two-tier limits per category (instantaneous cap + cumulative cap)
- **Policy:** Hard blocks at cumulative limit, warnings at 80%, no overages or silent routing
- **Escalation:** Clear, loud failure when limits hit; queue requests for next month or manual review
- **Audit Trail:** Log all routing decisions, cost impacts, and overflow events

---

## Cost Limit Architecture: 2-Tier Model

### Tier 1: Instantaneous Limit (Per-Call Cap)

Prevents single requests from consuming disproportionate budget.

| Category         | Per-Call Limit | Typical Request Cost | Safety Margin   |
| ---------------- | -------------- | -------------------- | --------------- |
| **FAST**         | $0.002         | $0.0005–0.001        | 2–4x headroom   |
| **NORMAL**       | $0.05          | $0.015–0.03          | 1.5–3x headroom |
| **COMPLEX**      | $0.15          | $0.05–0.08           | 1.8–3x headroom |
| **HIGH_COMPLEX** | $0.85          | $0.14–0.25           | 3–6x headroom   |

**Enforcement:** Before routing, validate `cost_estimate ≤ per_call_limit`. If exceeded, escalate to higher category or reject with error.

**Example Enforcement (Pseudocode):**

```python
def validate_cost_estimate(category, model, tokens):
    estimated_cost = tokens / 1M * MODEL_COSTS[model]
    limit = INSTANTANEOUS_LIMITS[category]

    if estimated_cost > limit:
        log(f"Cost estimate ${estimated_cost} exceeds {category} limit ${limit}")
        raise CostExceededError(f"Request requires escalation; try {next_category}")

    return estimated_cost
```

### Tier 2: Cumulative Limit (Monthly Cap)

Prevents category from exceeding monthly budget allocation.

| Category         | Monthly Budget | Alert Threshold (80%) | Hard Block (100%) | Expected Volume |
| ---------------- | -------------- | --------------------- | ----------------- | --------------- |
| **FAST**         | $50            | $40                   | $50               | ~25,000 calls   |
| **NORMAL**       | $200           | $160                  | $200              | ~4,000 calls    |
| **COMPLEX**      | $150           | $120                  | $150              | ~1,000 calls    |
| **HIGH_COMPLEX** | $50            | $40                   | $50               | ~60 calls       |

**Enforcement:** Track cumulative cost per category. Fire alerts at 80%, hard-block new requests at 100%.

**Example Enforcement (Pseudocode):**

```python
def check_cumulative_budget(category):
    cumulative = sum_costs_this_month(category)
    limit = CUMULATIVE_LIMITS[category]

    if cumulative >= limit:
        log(f"Category {category} cumulative cost ${cumulative} AT LIMIT ${limit}")
        raise BudgetExhaustedError(f"Cannot route new {category} requests; queue or escalate")

    if cumulative >= 0.8 * limit:
        alert(f"WARNING: {category} at 80% of budget (${cumulative}/${limit})")

    return cumulative
```

---

## Budget Tracking & Alerting

### Real-Time Cost Ledger

Maintain a ledger file (JSON or CSV) with entries for every routed request:

```json
{
  "timestamp": "2026-02-15T14:23:45Z",
  "category": "NORMAL",
  "model": "Claude Haiku 4.5",
  "input_tokens": 1200,
  "output_tokens": 500,
  "cost": 0.0203,
  "cumulative_this_month": 47.32,
  "budget": 200,
  "pct_budget": 23.66,
  "status": "ROUTED"
}
```

### Alert Levels

| Alert Level       | Trigger                                         | Response                                       | Audience         |
| ----------------- | ----------------------------------------------- | ---------------------------------------------- | ---------------- |
| **INFORMATIONAL** | New routing decision                            | Log to audit trail; no action                  | Automated logs   |
| **WARNING**       | Category at 80% cumulative                      | Email ops; prepare to escalate                 | Operations team  |
| **CRITICAL**      | Category at 100% cumulative                     | Email ops + manager; all new requests blocked  | Ops + Manager    |
| **EMERGENCY**     | Single request would exceed instantaneous limit | Reject request immediately; suggest escalation | Automated system |

### Example Alert Messages

**80% Warning (Cumulative):**

```
ALERT [2026-02-15 14:45]: NORMAL category at 80% budget
  Current: $160.00 / $200.00
  Burn rate: $8.00/day (if continues, exhausted 2026-02-20)
  Action: Switch new requests to cheaper models (Minimax) or escalate to COMPLEX
```

**100% Block (Cumulative):**

```
CRITICAL [2026-02-15 16:30]: NORMAL category BUDGET EXHAUSTED
  Current: $200.00 / $200.00
  Incoming request: NORMAL task, 2500 tokens, est. cost $0.035
  Status: REJECTED
  Options:
    1. Escalate to COMPLEX (higher quality, higher cost)
    2. Queue request for 2026-03-01 (next month)
    3. Manual budget reallocation (requires manager approval)
```

**Instantaneous Block (Per-Call):**

```
ERROR [2026-02-15 12:15]: HIGH_COMPLEX request exceeds per-call limit
  Estimated cost: $1.20 (for 12K tokens × Opus)
  Per-call limit: $0.85
  Status: REJECTED
  Options:
    1. Reduce token count (chunk into smaller requests)
    2. Manually approve high-cost request (requires manager)
    3. Queue request for later
```

---

## Escalation Paths & Decision Trees

### Path 1: Category Budget Exhausted (Cumulative)

```
Request arrives for NORMAL category
  ↓
Check cumulative cost: $200 >= $200 (LIMIT)
  ↓
[DECISION POINT]
  ├─ Is task genuinely NORMAL (500–3K tokens)?
  │  ├─ YES → Try escalate to COMPLEX
  │  │  ├─ COMPLEX budget available?
  │  │  │  ├─ YES → Escalate with cost note ("This costs 3x, OK?")
  │  │  │  └─ NO → Route to QUEUE with "ESCALATION" tag
  │  │  └─ End
  │  │
  │  └─ NO → Re-categorize (if <500 tokens, try FAST; if >3K, already COMPLEX)
  │     └─ Route appropriately
  │
  └─ [FINAL FALLBACK] QUEUE request for next month
     └─ Alert ops + manager; human review required
```

### Path 2: Instantaneous Limit Exceeded (Per-Call)

```
Request arrives with estimated cost $0.95 for COMPLEX category
  ↓
Check per-call limit: $0.95 > $0.15 (LIMIT)
  ↓
[DECISION POINT]
  ├─ Can reduce token count?
  │  ├─ Split into smaller requests?
  │  │  ├─ YES → Split and route separately
  │  │  └─ NO → Continue
  │  └─ End
  │
  ├─ Escalate to HIGH_COMPLEX?
  │  ├─ HIGH_COMPLEX cost limit ($0.85) still exceeded?
  │  │  ├─ YES (e.g., cost is $1.00)
  │  │  │  └─ Require manager approval before routing
  │  │  └─ NO (e.g., cost is $0.70)
  │  │     └─ Escalate to HIGH_COMPLEX
  │  └─ End
  │
  └─ [FINAL] REJECT with error message
     └─ Alert user; suggest splitting or deferring
```

### Path 3: All Categories Exhausted

```
NORMAL budget exhausted ($200)
COMPLEX budget exhausted ($150)
HIGH_COMPLEX budget exhausted ($50)
FAST budget OK ($30 remaining)
  ↓
Request arrives: 1500 tokens (NORMAL range)
  ↓
[DECISION POINT]
  ├─ Can downgrade to FAST quality (70%)?
  │  ├─ YES (task is simple) → Route to FAST (save cost)
  │  └─ NO (task needs 73%+) → Continue
  │
  └─ QUEUE request for next month
     └─ Priority: "ESCALATION_QUEUE"
     └─ Alert ops + manager; requires manual triage on 2026-03-01
```

---

## Monthly Reset & Ledger Rollover

### Month-End Procedure (Last day of month)

1. **Snapshot Current Ledger**
   - Export all costs for current month to archive
   - Validate total spend against budget ($450 or less)
   - Flag any overages or unexpected patterns

2. **Audit Trail Report**
   - Count requests per category, model, outcome
   - Calculate actual cost/call vs. estimate
   - Identify categories under/over budget

3. **Reset Counters for New Month**
   - Zero out cumulative costs per category
   - Clear all 80%/100% alerts
   - Reopen all category queues

4. **Deferred Request Processing**
   - Process any queued "ESCALATION_QUEUE" requests from previous month
   - Notify users of queued request status

### Example Monthly Summary Report

```
=== JANUARY 2026 COST SUMMARY ===

FAST Category:
  Budget: $50.00
  Spent: $47.32 (94.6%)
  Requests: 24,800
  Avg cost/call: $0.0019
  Primary model: Gemini Flash (80%)
  Status: ✓ UNDER BUDGET

NORMAL Category:
  Budget: $200.00
  Spent: $198.50 (99.3%)
  Requests: 3,920
  Avg cost/call: $0.0506
  Primary model: Haiku (75%), Gemini (20%), Sonnet (5%)
  Status: ⚠ NEAR LIMIT (1 request away from exhaustion)

COMPLEX Category:
  Budget: $150.00
  Spent: $119.40 (79.6%)
  Requests: 987
  Avg cost/call: $0.1208
  Primary model: Sonnet (60%), Gemini (25%), Opus (15%)
  Status: ✓ UNDER BUDGET

HIGH_COMPLEX Category:
  Budget: $50.00
  Spent: $31.20 (62.4%)
  Requests: 58
  Avg cost/call: $0.5379
  Primary model: Opus (85%), Minimax (15%)
  Status: ✓ UNDER BUDGET

TOTAL:
  Budget: $450.00
  Spent: $396.42 (88.1%)
  Savings vs. budget: $53.58
  Savings vs. current ($550): $153.58 (27.9%)

QUEUED REQUESTS (waiting for next month):
  None (all requests routed successfully)

NOTES:
  - NORMAL category is hot; Haiku budget exhausted Jan 28
  - Shifted NORMAL overflow to Minimax on Jan 28–31 (saved $12)
  - HIGH_COMPLEX lower than expected (only 58 calls vs. budgeted 60 avg)
  - Recommend increasing COMPLEX budget by $30 in Feb (reduce FAST by $20, NORMAL by $10)
```

---

## No Silent Failures: Enforcement Standards

### Anti-Pattern: Graceful Degradation

**DO NOT DO:**

```python
# BAD: Silently falls back to cheaper model without alerting user
if cost > budget:
    model = cheaper_fallback_model  # Silent downgrade
    route(request, model)
    # User doesn't know quality dropped; no alert fired
```

### Pattern: Loud, Deterministic Failures

**DO THIS:**

```python
# GOOD: Explicit failure with clear options
if cost > budget:
    log(f"Cost {cost} exceeds limit {limit}")
    raise BudgetExceededError(
        f"Cannot route {category} request. Options:\n"
        f"  1. Escalate to {next_category} (cost +${cost_delta})\n"
        f"  2. Queue for next month\n"
        f"  3. Reduce token count and retry\n"
        f"  4. Request manual approval"
    )
    # User sees explicit error; gets actionable options
```

### Guardrails

| Scenario                    | Behavior                               | Rationale                            |
| --------------------------- | -------------------------------------- | ------------------------------------ |
| Per-call cost exceeds limit | **REJECT** immediately with error      | Prevents runaway single requests     |
| Cumulative approaches 80%   | **WARN** ops team                      | Gives time to reallocate or escalate |
| Cumulative at 100%          | **BLOCK** all new requests in category | No overflow; hard stop               |
| All categories exhausted    | **QUEUE** request; alert manager       | Visible escalation queue             |
| Overflow detected           | **ALERT** + **LOG** all details        | Audit trail for post-mortem          |

---

## Manual Approval & Override Procedures

### When Manual Approval Is Required

| Scenario                                     | Trigger                            | Approver          | Process                                              |
| -------------------------------------------- | ---------------------------------- | ----------------- | ---------------------------------------------------- |
| Request exceeds per-call limit               | Cost > instantaneous limit         | Manager           | Review task justification; approve or deny           |
| Request would use last 10% of monthly budget | Cumulative > 90% of limit          | Operations        | Quick check; approve if legitimate                   |
| Multiple requests queue simultaneously       | Escalation queue size > 5          | Manager           | Prioritize queue; reallocate budget if possible      |
| Cross-month escalation                       | Task queued end-of-month           | Operations        | Decide: bump priority next month, de-scope, or defer |
| Budget reallocation                          | Need to shift $ between categories | Finance + Manager | Document rationale; update routing rules             |

### Approval Request Template

```
APPROVAL REQUEST: Cost Governance Override
ID: APR-2026-02-15-001
Requester: [system automated]
Date: 2026-02-15 14:30 UTC

Issue:
  Request estimated cost: $1.20
  Per-call limit: $0.85
  Category: HIGH_COMPLEX
  Reason: Token count 14K (multi-file code review)

Options:
  A. APPROVE: Route to Claude Opus 4.6 (pay the $1.20)
  B. DENY: Reject request; suggest de-scoping to 10K tokens or splitting into 2 requests
  C. DEFER: Queue for next month (if not time-critical)

Approver: [Manager name]
Decision: [A/B/C]
Rationale: [Brief explanation]
Signed: [Timestamp]
```

---

## Cost Monitoring Dashboard Spec

### KPIs to Track (Real-Time)

| Metric                        | Update Freq | Alert Threshold           | Audience     |
| ----------------------------- | ----------- | ------------------------- | ------------ |
| Cumulative cost by category   | Per request | 80%, 100%                 | Ops, Manager |
| Cost burn rate per category   | Hourly      | >10% ahead of linear pace | Ops          |
| Requests queued (escalation)  | Per event   | >0                        | Ops, Manager |
| Model mix by category (%)     | Daily       | Shift >10% vs. baseline   | Ops          |
| Error rate (cost-related)     | Per request | >1%                       | Ops          |
| Avg cost per call by category | Daily       | >10% variance             | Operations   |

### Dashboard Views (Mock)

**View 1: Budget Health**

```
╔════════════════════════════════════════════════════════════════╗
║ MONTHLY BUDGET HEALTH (as of 2026-02-15 16:00 UTC)             ║
╠════════════════════════════════════════════════════════════════╣
║ FAST           $47.32 / $50.00 ████████████░░░░░░░░░░░░░░░░░  94.6%  ✓ ║
║ NORMAL        $198.50 / $200.00 ██████████████████████████░░░░  99.3%  ⚠  ║
║ COMPLEX       $119.40 / $150.00 ███████████████░░░░░░░░░░░░░░░░  79.6%  ✓ ║
║ HIGH_COMPLEX   $31.20 / $50.00 ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░  62.4%  ✓ ║
║ ─────────────────────────────────────────────────────────────── ║
║ TOTAL         $396.42 / $450.00 ████████████████████░░░░░░░░░░░░  88.1%  ✓ ║
║                                                                   ║
║ Cumulative trend (linear pace): $435 by 2026-02-28             ║
║ Days remaining: 13                                               ║
║ Projected finish: $450 (ON BUDGET)                              ║
╚════════════════════════════════════════════════════════════════╝
```

**View 2: Routing Decisions (Last 24h)**

```
╔════════════════════════════════════════════════════════════════╗
║ ROUTING DECISIONS (Last 24 Hours)                               ║
╠════════════════════════════════════════════════════════════════╣
║ Time          | Category | Model              | Tokens | Cost    ║
╠════════════════════════════════════════════════════════════════╣
║ 14:00:23      | FAST     | Gemini Flash       | 320    | $0.0006 ║
║ 14:15:44      | NORMAL   | Haiku              | 1200   | $0.0420 ║
║ 14:32:15      | COMPLEX  | Sonnet             | 5100   | $0.0536 ║
║ 14:45:22      | NORMAL   | Gemini Flash ⚠     | 2800   | $0.0084 ║
║ 15:02:11      | HIGH_COMPLEX | Opus           | 10200  | $0.1785 ║
║ 15:18:33      | FAST     | Haiku              | 450    | $0.0016 ║
║ ...                                                               ║
║ ─────────────────────────────────────────────────────────────── ║
║ ⚠ = Fallback model (primary exhausted)                           ║
╚════════════════════════════════════════════════════════════════╝
```

**View 3: Alerts**

```
╔════════════════════════════════════════════════════════════════╗
║ ACTIVE ALERTS                                                   ║
╠════════════════════════════════════════════════════════════════╣
║ [⚠ WARNING] NORMAL category at 99.3% budget                    ║
║   Current: $198.50 / $200.00                                    ║
║   Last updated: 2026-02-15 14:45:22 UTC                         ║
║   Action: Switch new requests to Minimax or escalate            ║
║   Dismiss | View Details                                        ║
║                                                                   ║
║ [ℹ INFO] 3 requests queued for escalation                       ║
║   Category: NORMAL (awaiting COMPLEX availability)              ║
║   Oldest: 2026-02-15 13:22:10 UTC                               ║
║   View Queue                                                    ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Implementation Roadmap

| Phase       | Task                                            | Owner  | Timeline |
| ----------- | ----------------------------------------------- | ------ | -------- |
| **Phase 1** | Build cost ledger + real-time tracking          | Eng    | Week 1   |
| **Phase 2** | Implement per-call limit checks                 | Eng    | Week 1   |
| **Phase 3** | Implement cumulative limit checks + alerts      | Eng    | Week 2   |
| **Phase 4** | Build escalation paths + decision trees         | Eng    | Week 2   |
| **Phase 5** | Deploy monitoring dashboard                     | DevOps | Week 3   |
| **Phase 6** | Manual approval workflow                        | Ops    | Week 3   |
| **Phase 7** | Testing + shadow run (log only, no enforcement) | QA     | Week 3   |
| **Phase 8** | Go live with enforcement                        | Ops    | Week 4   |

---

## FAQ & Troubleshooting

**Q: A high-priority request just arrived. Can we override the cost limit?**
A: Yes, via manual approval. File an APPROVAL_REQUEST with manager sign-off. Document the rationale. Update ledger to reflect override.

**Q: The burn rate is 20% faster than expected. What do we do?**
A: Investigate: Are tasks larger than expected? Is routing choosing expensive models? Then:

1. Reduce scope (split large requests into smaller ones)
2. Shift expensive categories to cheaper models
3. Request budget reallocation (with VP approval)

**Q: Can we carry over unused budget to next month?**
A: No. Monthly budgets reset. If you under-spend one month, it does not roll forward. This encourages careful planning and prevents "save it for later" abuse.

**Q: What happens if actual cost exceeds estimate?**
A: Actual costs are recorded in ledger. If cumulative overflows, the hard block at 100% prevents new requests. Do not escalate already-routed requests retroactively.

**Q: Should we alert the user when we escalate their request to a more expensive model?**
A: Yes, always. Include cost note: "Your request was escalated from NORMAL to COMPLEX; estimated cost +$0.04. Proceed? Y/N"

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
