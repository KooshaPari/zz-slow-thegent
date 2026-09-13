# Model Routing Quick Card (Pocket Reference)

Print this page. Post on your desk. Reference when routing tasks.

---

## THE DECISION MATRIX (30 seconds)

```
INPUT: Task request with token estimate

├─ ≤500 tokens?
│  └─ FAST CATEGORY ($0.002/call, $50/mo)
│     PRIMARY:  Gemini Flash (fastest, 78% quality)
│     FALLBACK: Haiku → GPT-4o mini
│
├─ 500–3K tokens?
│  └─ NORMAL CATEGORY ($0.05/call, $200/mo)
│     PRIMARY:  Claude Haiku (affordable, 73% quality)
│     FALLBACK: Gemini Flash → Sonnet → Minimax
│
├─ 3K–10K tokens?
│  └─ COMPLEX CATEGORY ($0.15/call, $150/mo)
│     PRIMARY:  Claude Sonnet (balanced, 77% quality)
│     FALLBACK: Gemini Flash → Opus → Minimax
│
└─ >10K tokens?
   └─ HIGH_COMPLEX CATEGORY ($0.85/call, $50/mo)
      PRIMARY:  Claude Opus (best, 81% quality)
      FALLBACK: Minimax M2.5
```

---

## THE SIX MODELS (Ranked by Cost-Quality Ratio)

```
RANK | MODEL              | COST/M | QUALITY | SPEED      | WHEN TO USE
═════╪════════════════════╪════════╪═════════╪════════════╪═════════════════════════
🥇  | Haiku 4.5          | $3.50  | 73%     | 300-1200ms | Default tier; 70% of work
🥈  | Gemini 3 Flash     | $2.00  | 78%     | 150-600ms  | Interactive; latency SLA
🥉  | Sonnet 4.5         | $10.50 | 77%     | 400-1500ms | Complex reasoning
4   | Opus 4.6           | $17.50 | 81%     | 1760ms+    | Architecture decisions
5   | Minimax M2.5       | $0.79  | 80%     | Very fast  | Ultra-high-volume loops
6   | GPT-4o mini        | $0.38  | 70%     | 200-800ms  | Emergency fallback only
```

---

## COST GUARDRAILS (Hard Stops, No Exceptions)

```
Per-Call Limits (Instantaneous):
  FAST:        $0.002 per call
  NORMAL:      $0.05 per call
  COMPLEX:     $0.15 per call
  HIGH_COMPLEX: $0.85 per call

If estimated cost > limit: ESCALATE or REJECT

Monthly Cumulative Limits:
  FAST:        $50
  NORMAL:      $200
  COMPLEX:     $150
  HIGH_COMPLEX: $50
  ─────────────────
  TOTAL:       $450

Alert at 80% → WARN OPS
Block at 100% → NO NEW REQUESTS
```

---

## FALLBACK CHAINS (If Primary Unavailable)

```
FAST:
  1. Gemini Flash (78% quality, <600ms)
  2. Claude Haiku (73% quality, <1.2s)
  3. GPT-4o mini (70% quality, <800ms)
  4. QUEUE if all exhausted

NORMAL:
  1. Claude Haiku (73% quality, $0.02/call)
  2. Gemini Flash (78% quality, $0.001/call)
  3. Claude Sonnet (77% quality, $0.03/call)
  4. Minimax M2.5 (80% quality, $0.001/call)
  5. QUEUE if all exhausted

COMPLEX:
  1. Claude Sonnet (77% quality, $0.05/call)
  2. Gemini Flash (78% quality, $0.01/call)
  3. Claude Opus (81% quality, $0.09/call)
  4. Minimax M2.5 (80% quality, $0.004/call)
  5. QUEUE if all exhausted

HIGH_COMPLEX:
  1. Claude Opus (81% quality, $0.14/call)
  2. Minimax M2.5 (80% quality, $0.006/call)
  3. QUEUE if all exhausted (requires approval)
```

---

## WHAT TO LOG (Per Request)

```json
{
  "timestamp": "2026-02-15T14:23:45Z",
  "category": "NORMAL",
  "tokens": 1200,
  "cost_estimate": 0.0042,
  "model_routed": "Claude Haiku 4.5",
  "fallback_reason": null,
  "cumulative_cost_this_month": 47.32,
  "cumulative_limit": 200,
  "pct_budget_used": 23.7,
  "alert_level": "NONE",
  "status": "ROUTED"
}
```

---

## WHEN TO ALERT

```
🟢 <80% budget used      → No action; proceed normally
🟡 80–100% budget used   → ALERT OPS; prepare alternatives
🔴 ≥100% budget used     → BLOCK new requests; QUEUE or escalate
🔥 Estimate > per-call   → REJECT; escalate or split request
```

---

## ESCAPE HATCHES (Rare Situations)

```
Budget exhausted this month?
  → Queue request for next month (add priority flag)
  → Ask manager to reallocate budget across categories

Single request too expensive?
  → Split into smaller requests
  → Escalate to higher category
  → Request manual approval (manager signature required)

Model underperforming?
  → Switch to next fallback in chain
  → Log quality regression; notify ops

Estimate wrong?
  → Use actual cost for future estimation
  → Update your cost model (input:output ratio)
```

---

## GOLDEN RULES

1. **No per-call overages.** Hard limit per call; don't exceed.
2. **No monthly overages.** Hard limit per category; don't exceed.
3. **No silent downgrades.** Always escalate explicitly or log fallback.
4. **No graceful degradation.** Fail loud and clear; give options.
5. **Alert at 80%.** Give ops time to react before limit hit.
6. **Block at 100%.** Deterministic hard stop; no exceptions without approval.

---

## QUICK EXAMPLES

### Example 1: 750-token implementation task

```
Tokens: 750 → NORMAL category
Check constraints:
  Quality ≥73%? → Haiku is 73%, ✓
  Cost ≤$0.05? → $3.50/M × 1K = $0.0035, ✓
  Speed <5s? → Haiku P50 = 300–1200ms, ✓
  Budget available? → Check cumulative...

Action: ROUTE to Claude Haiku 4.5
Log: cost_estimate=$0.0035, status=ROUTED
```

### Example 2: 8K-token debugging task (complex)

```
Tokens: 8000 → COMPLEX category
Check constraints:
  Quality ≥75%? → Sonnet is 77%, ✓
  Cost ≤$0.15? → $10.50/M × 8K = $0.084, ✓
  Speed <20s? → Sonnet P50 = 400–1500ms, ✓
  Budget available? → Check cumulative ($150 limit)...

If cumulative <80%: ROUTE to Claude Sonnet 4.5
If cumulative ≥80%: Try Gemini Flash (78% quality, $0.01/call) instead
If all exhausted: QUEUE with priority="debugging"
```

### Example 3: 100-token quick query (FAST)

```
Tokens: 100 → FAST category
Check constraints:
  Quality ≥70%? → Gemini Flash is 78%, ✓
  Cost ≤$0.002? → $2/M × 0.1K = $0.0002, ✓
  Speed <1s? → Gemini P50 = 150–600ms, ✓
  Budget available? → Check cumulative ($50 limit)...

Action: ROUTE to Gemini 3 Flash
Log: cost_estimate=$0.0002, status=ROUTED
```

### Example 4: 12K-token architecture task (HIGH_COMPLEX)

```
Tokens: 12000 → HIGH_COMPLEX category
Check constraints:
  Quality ≥80%? → Opus is 81%, ✓
  Cost ≤$0.85? → $17.50/M × 12K = $0.21, ✓
  Speed <60s? → Opus P50 = 1760ms, ✓ (within SLA)
  Budget available? → Check cumulative ($50 limit)...

If cumulative <$40: ROUTE to Claude Opus 4.6
If cumulative $40–50: REQUEST APPROVAL (cost=$0.21)
If cumulative ≥$50: QUEUE with priority="architecture"
```

---

## BUDGET SNAPSHOT (Current Month)

Print and update weekly. Post on team channel.

```
                    SPENT    LIMIT    %      STATUS
FAST              [$_____] / $50     [__]%   [🟢/🟡/🔴]
NORMAL            [$_____] / $200    [__]%   [🟢/🟡/🔴]
COMPLEX           [$_____] / $150    [__]%   [🟢/🟡/🔴]
HIGH_COMPLEX      [$_____] / $50     [__]%   [🟢/🟡/🔴]
──────────────────────────────────────────────────────
TOTAL             [$_____] / $450    [__]%   [🟢/🟡/🔴]

Last updated: _____________
```

---

## ONE-LINERS (Copy-Paste Validation)

```python
# Category check
category = "FAST" if tokens <= 500 else "NORMAL" if tokens <= 3000 else "COMPLEX" if tokens <= 10000 else "HIGH_COMPLEX"

# Cost estimate
cost = (tokens / 1_000_000) * MODEL_COSTS[model]

# Per-call validation
assert cost <= PER_CALL_LIMITS[category], f"Cost ${cost} exceeds {category} limit ${PER_CALL_LIMITS[category]}"

# Cumulative validation
assert cumulative_cost + cost <= MONTHLY_LIMITS[category], f"Would exceed {category} monthly limit"

# Alert threshold
if (cumulative_cost + cost) / MONTHLY_LIMITS[category] >= 0.8:
    alert(f"WARNING: {category} at 80% of monthly budget")

# Block threshold
if (cumulative_cost + cost) >= MONTHLY_LIMITS[category]:
    raise BudgetExhaustedError(f"Cannot route new {category} requests")
```

---

## CONTACT (Questions, Escalations)

```
Model selection → Ask team lead or check PARETO_FRONTIER_MATRIX.md
Routing logic → Check ROUTING_DECISION_MATRIX.md for your category
Cost/budget → Ask ops or check COST_ENFORCEMENT_POLICY.md
Implementation → See MODEL_ROUTING_SUMMARY.md checklist
Navigation → Use MODEL_ROUTING_INDEX.md as guide
```

---

**Print & Post. Reference Daily. Questions? Check the full docs in /docs/reference/**

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
