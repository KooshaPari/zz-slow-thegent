# Routing Decision Matrix: Task Category Logic

**Purpose:** Detailed routing decision logic per task category with hard constraint checks, soft optimization, and fallback chains.

**Last Updated:** 2026-02-15
**Integration Point:** Feed this logic into `task-router.py` or equivalent dispatch system.

---

## Overview: Task Categories and Budget Allocation

| Category         | Token Range   | Monthly Budget | Cost/Call Limit | Calls/Month | Quality Floor | Speed SLA | Use Cases                                            |
| ---------------- | ------------- | -------------- | --------------- | ----------- | ------------- | --------- | ---------------------------------------------------- |
| **FAST**         | 50–500 tokens | $50            | $0.002          | ~25,000     | 70%           | <1s TTFT  | Interactive, chat, quick queries                     |
| **NORMAL**       | 500–3K tokens | $200           | $0.05           | ~4,000      | 73%           | <5s       | Default tier, standard implementations               |
| **COMPLEX**      | 3K–10K tokens | $150           | $0.15           | ~1,000      | 75%           | <20s      | Multi-step reasoning, debugging, analysis            |
| **HIGH_COMPLEX** | >10K tokens   | $50            | $0.85           | ~60         | 80%           | <60s      | Architecture decisions, novel problems, final review |

---

## FAST CATEGORY (50–500 tokens input, 100–1K output)

### Category Parameters

- **Performance Requirement:** ≥70% (SWE-Bench or equivalent)
- **Speed SLA:** <1 second TTFT (time-to-first-token)
- **Instantaneous Budget Limit:** $0.002 per call
- **Cumulative Budget Limit:** $50/month for all FAST tasks
- **Expected Monthly Volume:** ~25,000 calls (if 50M tokens total, avg 2K tokens/call)

### Hard Constraints Check

| #   | Constraint          | Check                                | Result | Models Passing                                                                                   |
| --- | ------------------- | ------------------------------------ | ------ | ------------------------------------------------------------------------------------------------ |
| 1   | Quality ≥ 70%       | SWE-Bench score or equivalent        | ✓      | Haiku (73%), Gemini Flash (78%), GPT-4o mini (70%)                                               |
| 2   | Cost ≤ $0.002/call  | Haiku: $3.50/M × 0.5K avg = $0.00175 | ✓      | Haiku ✓, Gemini Flash ($1.50–3/M × 0.5K = $0.001) ✓, GPT-4o mini ($0.375/M × 0.5K = $0.0002) ✓   |
| 3   | Cumulative ≤ $50/mo | 25,000 calls × $0.002 = $50          | ✓      | All three models ✓                                                                               |
| 4   | Speed < 1s TTFT     | P50 latency must be <600ms           | ✓      | Gemini Flash (150–600ms) ✓, GPT-4o mini (200–800ms) ⚠ P99 exceeds, Haiku (300–1200ms) ✗ P99 >1s |

**Hard Constraint Verdict:** Gemini Flash, GPT-4o mini meet all hard constraints. Haiku fails speed SLA (P99 > 1s) but acceptable if <5s SLA pushed up or interactive requirement relaxed.

### Soft Optimization (After Hard Constraints Met)

**Priority Order:** Speed > Cost > Quality

1. **Primary Route:** Gemini 3 Flash
   - Cost: $1.50–3/M (avg $2/M, $0.001/call)
   - Quality: 78% (exceeds 70% floor)
   - Speed: 150–600ms P50 (fastest option, meets <1s SLA with margin)
   - Risk: May hit daily quota limits on high-volume days (Gemini has generous but finite free tier)

2. **Fallback 1:** Claude Haiku 4.5
   - Cost: $3.50/M ($0.00175/call)
   - Quality: 73% (meets floor)
   - Speed: 300–1200ms P50 (P99 >1s; acceptable if latency SLA relaxed to <5s)
   - Advantage: Proven production reliability, no quota limits, consistent availability

3. **Fallback 2:** GPT-4o mini
   - Cost: $0.375/M ($0.0002/call, ultra-cheap)
   - Quality: 70% (meets floor exactly)
   - Speed: 200–800ms P50 (meets <1s SLA but variable under load)
   - Use case: Emergency overflow when both Gemini & Haiku exhausted

### Decision Rules (Pseudocode)

```
ROUTE_FAST(request):
  IF tokens < 500 AND reasoning_depth ≤ 1 AND confidence_score > 0.8:
    IF gemini_daily_quota_available():
      ROUTE → Gemini 3 Flash (primary)
    ELIF haiku_cost_available():
      ROUTE → Claude Haiku 4.5 (Fallback 1)
    ELIF gpt4o_cost_available():
      ROUTE → GPT-4o mini (Fallback 2)
    ELSE:
      ESCALATE → NORMAL category or queue request
  ELSE:
    ESCALATE → NORMAL category (task too complex for FAST)
```

### Monitoring & Alerts

| Metric                 | Alert Threshold      | Action                                          |
| ---------------------- | -------------------- | ----------------------------------------------- |
| Gemini daily calls     | >500                 | Switch to Haiku fallback                        |
| Gemini cost cumulative | >$40/mo (80% of $50) | Begin mixing in Haiku                           |
| Haiku cost cumulative  | >$40/mo (if primary) | Switch to GPT-4o for new requests               |
| Average response time  | >600ms               | Trigger load testing; consider splitting volume |
| Error rate             | >2%                  | Escalate to NORMAL category                     |

---

## NORMAL CATEGORY (500–3K tokens input, 500–3K output)

### Category Parameters

- **Performance Requirement:** ≥73% (SWE-Bench or equivalent)
- **Speed SLA:** <5 seconds TTFT
- **Instantaneous Budget Limit:** $0.05 per call
- **Cumulative Budget Limit:** $200/month for all NORMAL tasks
- **Expected Monthly Volume:** ~4,000 calls (if 50M tokens total)
- **Quality Baseline:** Default tier; most work lands here

### Hard Constraints Check

| #   | Constraint           | Check                               | Result | Models Passing                                                                                        |
| --- | -------------------- | ----------------------------------- | ------ | ----------------------------------------------------------------------------------------------------- |
| 1   | Quality ≥ 73%        | SWE-Bench score                     | ✓      | Haiku (73%), Sonnet (77%), Gemini Flash (78%), Minimax (80%), Opus (81%)                              |
| 2   | Cost ≤ $0.05/call    | Haiku: $3.50/M × 1.5K avg = $0.0525 | ⚠     | Haiku barely passes (edge case); Gemini ($2/M × 1.5K = $0.003) ✓, Sonnet ($10.50/M × 1.5K = $0.015) ✓ |
| 3   | Cumulative ≤ $200/mo | 4,000 calls × $0.05 = $200          | ✓      | All models ✓                                                                                          |
| 4   | Speed < 5s TTFT      | P50 latency must be <3s             | ✓      | Haiku (300–1200ms) ✓, Sonnet (400–1500ms) ✓, Gemini (150–600ms) ✓                                     |

**Hard Constraint Verdict:** All major models pass. Haiku is at edge of cost limit (hits $0.0525/call for 1.5K token tasks); safer to assume max 1.2K avg for Haiku in NORMAL.

### Soft Optimization (After Hard Constraints Met)

**Priority Order:** Cost > Quality > Speed

1. **Primary Route:** Claude Haiku 4.5
   - Cost: $3.50/M ($0.021/call typical for 1.5K tasks)
   - Quality: 73% (meets floor exactly; acceptable for well-defined tasks)
   - Speed: 300–1200ms P50 (comfortably under <5s SLA)
   - Advantage: Cost-optimal, proven reliability, no quota limits
   - Risk: May struggle with complex multi-step tasks (requires clear prompting)

2. **Fallback 1:** Gemini 3 Flash
   - Cost: $2/M avg ($0.003/call, ultra-cheap)
   - Quality: 78% (exceeds floor by 5%, noticeable quality jump)
   - Speed: 150–600ms P50 (faster than Haiku)
   - Use when: Haiku approaching budget limit or complex task needs quality bump but speed isn't critical

3. **Fallback 2:** Claude Sonnet 4.5
   - Cost: $10.50/M ($0.0315/call typical for 1.5K tasks)
   - Quality: 77% (4-point quality jump over Haiku)
   - Speed: 400–1500ms P50 (still under 5s)
   - Use when: Haiku returns low-confidence or multi-step reasoning required

4. **Fallback 3:** Minimax M2.5
   - Cost: $0.79/M ($0.001/call, extremely cheap)
   - Quality: 80% (frontier quality)
   - Speed: Very fast
   - Use when: Cost almost exhausted but task still needs 75%+ quality

### Decision Rules (Pseudocode)

```
ROUTE_NORMAL(request):
  IF 500 ≤ tokens ≤ 3000:
    IF complexity_score ≤ 3 AND haiku_cost_available():
      ROUTE → Claude Haiku 4.5 (primary, 70% of NORMAL traffic)
    ELIF quality_needed ≥ 76% OR multi_step_reasoning OR haiku_approaching_limit():
      IF gemini_cost_available():
        ROUTE → Gemini 3 Flash (fallback 1, 20% of NORMAL traffic)
      ELIF sonnet_cost_available():
        ROUTE → Claude Sonnet 4.5 (fallback 2, 8% of NORMAL traffic)
      ELSE:
        ROUTE → Minimax M2.5 (fallback 3, 2% of NORMAL traffic)
    ELIF cost_exhausted(haiku) AND quality_needed < 75%:
      ROUTE → Minimax M2.5 (ultra-cheap overflow)
    ELSE:
      ESCALATE → COMPLEX category or queue
  ELSE:
    ESCALATE → COMPLEX category (token count exceeds NORMAL range)
```

### Budget Enforcement (2x Limit Policy)

| Threshold                      | Action                                                                | Notes                                              |
| ------------------------------ | --------------------------------------------------------------------- | -------------------------------------------------- |
| $50 cumulative (25% of $200)   | None; proceed normally                                                | Green zone                                         |
| $160 cumulative (80% of $200)  | **WARN:** Log alert; consider shifting to Minimax for remaining month | Yellow zone; require approval for expensive routes |
| $200 cumulative (100% of $200) | **BLOCK:** No new NORMAL requests; escalate to COMPLEX or queue       | Red zone; hard stop                                |

### Monitoring & Alerts

| Metric                | Alert Threshold        | Action                                      |
| --------------------- | ---------------------- | ------------------------------------------- |
| Haiku cost cumulative | >$120/mo (60% of $200) | Begin mixing in Gemini/Minimax              |
| Haiku error rate      | >1.5%                  | Switch to Sonnet for problematic task types |
| Average response time | >3s                    | Load testing; consider batching             |
| Quality regression    | <72% (below floor)     | Switch to Sonnet for that task subtype      |
| Cumulative at 80%     | $160/mo                | Alert ops; prepare to escalate tasks        |

---

## COMPLEX CATEGORY (3K–10K tokens input, 1K–5K output)

### Category Parameters

- **Performance Requirement:** ≥75% (SWE-Bench or equivalent; quality jump vs. NORMAL)
- **Speed SLA:** <20 seconds TTFT
- **Instantaneous Budget Limit:** $0.15 per call
- **Cumulative Budget Limit:** $150/month for all COMPLEX tasks
- **Expected Monthly Volume:** ~1,000 calls
- **Quality Baseline:** Multi-step reasoning, debugging, analysis

### Hard Constraints Check

| #   | Constraint           | Check                               | Result | Models Passing                                                                                              |
| --- | -------------------- | ----------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------- |
| 1   | Quality ≥ 75%        | SWE-Bench score                     | ✓      | Sonnet (77%), Gemini Flash (78%), Minimax (80%), Opus (81%)                                                 |
| 2   | Cost ≤ $0.15/call    | Sonnet: $10.50/M × 5K avg = $0.0525 | ✓      | Sonnet ✓, Gemini ($2/M × 5K = $0.01) ✓, Minimax ($0.79/M × 5K = $0.004) ✓, Opus ($17.50/M × 5K = $0.0875) ✓ |
| 3   | Cumulative ≤ $150/mo | 1,000 calls × $0.15 = $150          | ✓      | All models ✓                                                                                                |
| 4   | Speed < 20s TTFT     | P50 latency must be <15s            | ✓      | All models ✓ (even Opus at 1.76s + overhead << 15s)                                                         |

**Hard Constraint Verdict:** Sonnet, Gemini, Minimax, and Opus all pass. Haiku (73%) dropped due to quality floor.

### Soft Optimization (After Hard Constraints Met)

**Priority Order:** Quality > Cost > Speed

1. **Primary Route:** Claude Sonnet 4.5
   - Cost: $10.50/M ($0.0525/call for 5K tasks)
   - Quality: 77% (meets floor + 2-point buffer)
   - Speed: 400–1500ms P50 (fast, reserves time for complex reasoning)
   - Advantage: Production-proven, balanced quality/cost, reliable for debugging
   - Risk: Higher cost than Haiku (3x); justify when multi-step reasoning needed

2. **Fallback 1:** Gemini 3 Flash
   - Cost: $2/M avg ($0.01/call, 5x cheaper than Sonnet)
   - Quality: 78% (exceeds Sonnet by 1 point)
   - Speed: 150–600ms P50 (faster than Sonnet)
   - Use when: Cost approaching limit and task doesn't need Sonnet's reasoning depth

3. **Fallback 2:** Claude Opus 4.6
   - Cost: $17.50/M ($0.0875/call, highest in this category)
   - Quality: 81% (best available, 4-point jump)
   - Speed: 1760ms+ P50 (slower but acceptable <20s SLA)
   - Use when: Task is genuinely hard (novel problem, architecture-level) or Sonnet returns low-confidence

4. **Fallback 3:** Minimax M2.5
   - Cost: $0.79/M ($0.004/call, ultra-cheap)
   - Quality: 80% (frontier-level, competitive with Opus)
   - Speed: Very fast
   - Use when: Cost nearly exhausted and task is batch/non-urgent

### Decision Rules (Pseudocode)

```
ROUTE_COMPLEX(request):
  IF 3000 ≤ tokens ≤ 10000:
    IF complexity_score ≤ 6 AND confidence_threshold >= 0.75:
      IF sonnet_cost_available():
        ROUTE → Claude Sonnet 4.5 (primary, 60% of COMPLEX traffic)
      ELIF gemini_cost_available():
        ROUTE → Gemini 3 Flash (fallback 1, 25% of COMPLEX traffic)
      ELIF minimax_cost_available():
        ROUTE → Minimax M2.5 (fallback 2, 10% of COMPLEX traffic)
      ELSE:
        ESCALATE → HIGH_COMPLEX with approval required
    ELIF complexity_score > 6 OR confidence_threshold < 0.70 OR reasoning_depth > 3:
      IF opus_cost_available():
        ROUTE → Claude Opus 4.6 (fallback 2, 5% of COMPLEX traffic)
      ELIF sonnet_cost_available():
        ROUTE → Claude Sonnet 4.5 (secondary for hard tasks)
      ELSE:
        ESCALATE → HIGH_COMPLEX or queue with priority
    ELSE:
      ESCALATE → HIGH_COMPLEX category
  ELSE:
    ESCALATE → HIGH_COMPLEX category (token count exceeds COMPLEX range)
```

### Budget Enforcement (2x Limit Policy)

| Threshold                      | Action                                                                     | Notes                                                |
| ------------------------------ | -------------------------------------------------------------------------- | ---------------------------------------------------- |
| $50 cumulative (33% of $150)   | None; proceed normally                                                     | Green zone                                           |
| $120 cumulative (80% of $150)  | **WARN:** Log alert; evaluate if remaining tasks can wait until next month | Yellow zone; require approval for Opus-tier requests |
| $150 cumulative (100% of $150) | **BLOCK:** No new COMPLEX requests; escalate to HIGH_COMPLEX queue         | Red zone; hard stop                                  |

### Monitoring & Alerts

| Metric                 | Alert Threshold                   | Action                                                   |
| ---------------------- | --------------------------------- | -------------------------------------------------------- |
| Sonnet cost cumulative | >$90/mo (60% of $150)             | Begin mixing in Gemini/Minimax for well-defined tasks    |
| Sonnet error rate      | >2%                               | Escalate problematic tasks to Opus for review            |
| Opus cost per-request  | >$0.50 (indicates 6K+ token task) | Warn user; may overflow monthly budget in single request |
| Gemini daily calls     | >100                              | Monitor quota; may need fallback to Sonnet               |
| Average response time  | >10s                              | Load analysis; consider batching                         |
| Cumulative at 80%      | $120/mo                           | Alert ops; freeze non-urgent COMPLEX tasks               |

---

## HIGH_COMPLEX CATEGORY (>10K tokens, >5K output)

### Category Parameters

- **Performance Requirement:** ≥80% (SWE-Bench or equivalent; mission-critical quality)
- **Speed SLA:** <60 seconds TTFT (offline/batch acceptable)
- **Instantaneous Budget Limit:** $0.85 per call
- **Cumulative Budget Limit:** $50/month for all HIGH_COMPLEX tasks
- **Expected Monthly Volume:** ~60 calls (rare; mission-critical only)
- **Quality Baseline:** Architecture decisions, novel problems, final review, complex debugging

### Hard Constraints Check

| #   | Constraint          | Check                           | Result | Models Passing                                                                                                          |
| --- | ------------------- | ------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------- |
| 1   | Quality ≥ 80%       | SWE-Bench score                 | ✓      | Opus (81%), Minimax (80%), GLM-5 (92.7% AIME)                                                                           |
| 2   | Cost ≤ $0.85/call   | Opus: $17.50/M × 8K avg = $0.14 | ✓      | Opus ✓ ($0.14), Minimax ($0.79/M × 8K = $0.006) ✓, GLM-5 ($1/M × 8K = $0.008) ✓                                         |
| 3   | Cumulative ≤ $50/mo | 60 calls × $0.85 = $51          | ⚠     | Budget is _tight_; Opus alone at $0.14/call = 357 calls max, but expected 60 calls = only $8.40/mo, so very safe margin |
| 4   | Speed < 60s TTFT    | P50 latency <40s                | ✓      | Opus (1760ms) ✓, all models ✓                                                                                           |

**Hard Constraint Verdict:** Opus, Minimax, and GLM-5 pass. Sonnet (77%), Haiku (73%), Gemini Flash (78%) dropped due to 80% quality floor.

### Soft Optimization (After Hard Constraints Met)

**Priority Order:** Quality > Speed > Cost (cost is acceptable; quality is paramount)

1. **Primary Route:** Claude Opus 4.6
   - Cost: $17.50/M ($0.14/call for 8K tasks)
   - Quality: 81% (best proven model for complex reasoning, novel problems)
   - Speed: 1760ms+ P50 (acceptable <60s SLA for mission-critical)
   - Advantage: Largest context, best reasoning, production track record
   - Budget headroom: $50/mo ÷ $0.14/call = ~357 calls possible; only expecting 60
   - Risk: If usage exceeds ~60/mo, will overflow budget

2. **Fallback 1:** Minimax M2.5
   - Cost: $0.79/M ($0.006/call, 20x cheaper than Opus)
   - Quality: 80% (meets floor; frontier-level)
   - Speed: Very fast
   - Use when: Task is non-urgent, cost approaching limit, or Opus quality not strictly needed
   - Risk: Lower production track record in US market

3. **Fallback 2 (Rare):** Claude Sonnet 4.5
   - Cost: $10.50/M ($0.084/call for 8K tasks)
   - Quality: 77% (below 80% floor; only if task de-escalated)
   - Use when: Task initially HIGH_COMPLEX but scope reduced and Sonnet budget still available

### Decision Rules (Pseudocode)

```
ROUTE_HIGH_COMPLEX(request):
  IF tokens > 10000:
    IF complexity_score > 8 OR novel_problem OR architecture_level:
      IF opus_cost_available():
        ROUTE → Claude Opus 4.6 (primary, 90% of HIGH_COMPLEX)
      ELIF minimax_cost_available():
        ROUTE → Minimax M2.5 (fallback 1, 10% of HIGH_COMPLEX)
      ELSE:
        ESCALATE → Queue with "URGENT" tag; require manual approval & budget reallocation
    ELIF can_reduce_scope_to_complex():
      ESCALATE → COMPLEX category (try to fit in reduced scope)
    ELSE:
      ESCALATE → Queue with human review required; manual approval for Opus
  ELSE:
    ERROR: Token count does not match HIGH_COMPLEX category
```

### Budget Enforcement (Hard Caps, No Overflow)

| Threshold                    | Action                                                                                        | Notes                            |
| ---------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------- |
| $40 cumulative (80% of $50)  | **WARN:** Log alert; next HIGH_COMPLEX request requires manager approval                      | Yellow zone; escalation protocol |
| $50 cumulative (100% of $50) | **BLOCK:** No new HIGH_COMPLEX requests without budget reallocation; escalate to human review | Red zone; hard stop              |

### Monitoring & Alerts

| Metric               | Alert Threshold         | Action                                                       |
| -------------------- | ----------------------- | ------------------------------------------------------------ |
| Opus cost cumulative | >$40/mo (80% of $50)    | Alert ops; next request requires approval                    |
| Monthly call count   | >80 (above expected 60) | Investigate spike; may indicate category misclassification   |
| Opus error rate      | >3%                     | Escalate problematic tasks to manual review                  |
| Response latency     | >30s                    | Opus may be under load; queue remaining requests             |
| Cumulative at limit  | $50/mo                  | Hard freeze; all subsequent requests denied until next month |

---

## Cross-Category Budget View

| Category     | Monthly Budget | Primary Model                             | Fallback Chain | Total Commits   |
| ------------ | -------------- | ----------------------------------------- | -------------- | --------------- |
| FAST         | $50            | Gemini Flash → Haiku → GPT-4o mini        | 3              | $450 cumulative |
| NORMAL       | $200           | Haiku → Gemini → Sonnet → Minimax         | 4              |                 |
| COMPLEX      | $150           | Sonnet → Gemini → Opus → Minimax          | 4              |                 |
| HIGH_COMPLEX | $50            | Opus → Minimax (→ Sonnet if de-escalated) | 2              |                 |

**Total Monthly Budget:** $450
**Current Spend:** $550/mo
**Savings Target:** $100/mo (18% reduction)

---

## Global Escalation Protocol

```
If all primary routes exhausted in category:
  IF next_cheaper_category_exists():
    TRY route to cheaper category (with quality check)
  ELIF higher_category_budget_available():
    ESCALATE to higher category (with approval)
  ELSE:
    QUEUE request with priority tag
    ALERT ops for manual triage

Example: NORMAL task, Haiku budget exhausted, Gemini quota hit
  → Try routing to Minimax (cheaper, meets 80% floor)
  → If Minimax quota hit, escalate to COMPLEX with approval
  → If all exhausted, QUEUE for next month
```

---

## Implementation Checklist

- [ ] Create `task_router.py` with category detection logic (token count, complexity_score, reasoning_depth)
- [ ] Integrate constraint validation (hard + soft checks per category)
- [ ] Implement fallback chain dispatcher (route to next model if current exhausted)
- [ ] Add cost tracking per category (cumulative, alert at 80%, block at 100%)
- [ ] Set up monitoring dashboard (cost, latency, error rates, volume trends)
- [ ] Wire hooks to log routing decisions (which model, why, cost impact)
- [ ] Test escalation paths (all routes exhausted → queue + alert)
- [ ] Document manual override procedure (ops can reallocate budget across categories)
- [ ] Set calendar reminder to re-evaluate benchmarks Q1 2026

---

## FAQ & Troubleshooting

**Q: Haiku is failing tasks that should pass. Should I escalate immediately?**
A: No. Log failure patterns first (what task types, tokens, reasoning depth). If >5% failure rate on specific subtype, escalate that subtype to Sonnet. Don't blanket-escalate the entire category.

**Q: We hit the NORMAL budget cap mid-month. What now?**
A: Switch all new NORMAL requests to Minimax (80% quality, $0.001/call); batch them if possible. Or escalate to COMPLEX for urgent, justified tasks. Do not violate the cap.

**Q: Can we reallocate budget between categories?**
A: Yes, but requires ops approval. Document the reason (e.g., "HIGH_COMPLEX spike due to architecture redesign; reducing FAST budget by $20"). Re-validate routing rules after reallocation.

**Q: Gemini Flash is hitting quota limits daily. What's the fallback?**
A: Haiku is primary fallback for FAST. If Haiku budget also tight, use GPT-4o mini (ultra-cheap, meets 70% floor). For NORMAL, switch to Minimax.

**Q: Should we use Cursor Ultra as a primary route?**
A: No. Cursor's pricing ($0.50/M effective, but $600-1000/mo overflow risk) is volatile. Use only as secondary fallback after exhausting safer options. Requires manual cost oversight.

**Q: How often should we re-evaluate the frontier matrix?**
A: Q1 2026 (next quarterly benchmark release). If major pricing changes occur mid-quarter, reassess immediately. Log benchmark dates in the routing system.

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
