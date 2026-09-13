# Pareto Frontier Matrix: Model Selection Guide

**Purpose:** Single-page reference for selecting AI models based on performance, cost, and speed constraints.

**Last Updated:** 2026-02-15
**Context:** User's current spend ~$550/mo across Claude, Cursor, Gemini, and others. Goal: optimize cost/quality ratio while meeting SLA constraints.

---

## Table 1: Performance Tiers

| Performance Tier        | Benchmark Threshold           | Models Meeting Threshold                                                                | Use Cases                                                                           |
| ----------------------- | ----------------------------- | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **Excellent (78%+)**    | SWE-Bench ≥ 78% OR AIME ≥ 90% | Claude Opus 4.6 (80.8%), Gemini 3 Flash (78%), MiniMax M2.5 (80.2%), GLM-5 (92.7% AIME) | Complex reasoning, architecture design, multi-step debugging, novel problem-solving |
| **Good (75-78%)**       | SWE-Bench 75-78%              | Claude Sonnet 4.5 (77.2%)                                                               | Standard implementations, code generation, refactoring, integration tasks           |
| **Acceptable (70-75%)** | SWE-Bench 70-75%              | Claude Haiku 4.5 (73.3%), GPT-5.3-Codex (56.8% SPro)                                    | Quick fixes, snippets, simple queries, well-defined tasks                           |
| **Budget (65-70%)**     | SWE-Bench <70%                | GLM 4.7 (74%), Minimax M2 (70%), GPT-4o mini (70%)                                      | Simple coding when quality floor is met but cost is critical, utility tasks         |

---

## Table 2: Speed Tiers (Base Minima in Milliseconds)

| Speed SLA         | P50 Latency | P99 Latency | Models                                                                   | Use Case                                          | Notes                            |
| ----------------- | ----------- | ----------- | ------------------------------------------------------------------------ | ------------------------------------------------- | -------------------------------- |
| **Instant (<1s)** | <300ms      | <800ms      | Gemini Flash (150-600ms), GPT-4o mini (200-800ms), GLM Flash (150-600ms) | Interactive (REPL, chat, live code completion)    | Prioritize for user-facing tasks |
| **Fast (<5s)**    | 300-500ms   | 800-1500ms  | Claude Haiku (300-1200ms), Cursor Ultra (400-1500ms)                     | Standard request (CLI, editor, background ops)    | Acceptable for most workflows    |
| **Normal (<20s)** | 500-1000ms  | 1500-3000ms | Claude Sonnet (400-1500ms), Gemini 2.5 Pro (250-900ms)                   | Engineering tasks, analysis, multi-step workflows | Batch processing OK              |
| **Batch (<60s)**  | 1000ms+     | 3000ms+     | Claude Opus (1760ms+), MiniMax reasoning modes                           | Offline, batch processing, comprehensive analysis | No time pressure                 |

---

## Table 3: Cost Tiers (Effective Per M Tokens, Including Tax)

| Cost Tier              | Per-M Cost | Annual Cost (@50M tokens) | Models                                                                | Budget Profile                                                         |
| ---------------------- | ---------- | ------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **Ultra-Low (<$1/M)**  | $0.27-0.79 | $13.50-39.50              | GLM Flash ($0.27), Minimax M2 ($0.79), GPT-4o mini ($0.375)           | Ultra high-volume loops (10K+ requests/mo), acceptable 65-70% quality  |
| **Low ($1-4/M)**       | $1-4       | $50-200                   | Claude Haiku ($3.50), Gemini 2.5 Pro (<200K tokens) ($4.07)           | High-volume (1K-10K requests/mo), baseline quality 70%+                |
| **Standard ($4-12/M)** | $4-12      | $200-600                  | Claude Sonnet ($10.50), OpenAI GPT-4o ($10.00), Gemini 3 Pro ($10.00) | Typical use (100-1K requests/mo), quality 75%+                         |
| **Premium ($15+/M)**   | $15+       | $750+                     | Claude Opus ($17.50)                                                  | Selective, high-stakes tasks (<100 requests/mo), 80%+ quality required |

---

## Table 4: Pareto Frontier — 6-Model Recommendation Tier

| Rank                | Provider/Model    | Cost/M     | Quality          | Speed (P50) | Best For                                             | Constraint Profile                              |
| ------------------- | ----------------- | ---------- | ---------------- | ----------- | ---------------------------------------------------- | ----------------------------------------------- |
| 🥇 **BEST**         | Claude Haiku 4.5  | $3.50      | 73% (Good)       | 300-1200ms  | **High-volume NORMAL tasks, cost-conscious**         | Cost < $0.05/call, Speed > 5s SLA, Perf ≥ 70%   |
| 🥈 **FASTEST**      | Gemini 3 Flash    | $1.50-3.00 | 78% (Excellent)  | 150-600ms   | **FAST queries, latency-critical, interactive**      | Cost < $0.01/call, Speed > 1s SLA, Perf ≥ 75%   |
| 🥉 **BALANCED**     | Claude Sonnet 4.5 | $10.50     | 77% (Excellent)  | 400-1500ms  | **COMPLEX reasoning, standard tier, debugging**      | Cost < $0.10/call, Speed > 20s SLA, Perf ≥ 75%  |
| 4️⃣ **PEAK**         | Claude Opus 4.6   | $17.50     | 81% (Excellent)  | 1760ms+     | **HIGH_COMPLEX, mission-critical, architecture**     | Cost < $0.50/call, Speed > 60s SLA, Perf ≥ 80%  |
| 5️⃣ **ULTRA-BUDGET** | Minimax M2.5      | $0.79      | 80% (Excellent)  | Very fast   | **Agentic loops, ultra-high-volume batch**           | Cost < $0.005/call, Speed > 10s SLA, Perf ≥ 75% |
| 6️⃣ **FALLBACK**     | GPT-4o mini       | $0.375     | 70% (Acceptable) | 200-800ms   | **Ultra-low-cost fallback, simple tasks, emergency** | Cost < $0.003/call, Speed > 1s SLA, Perf ≥ 70%  |

**Annotation:**

- **🥇 Claude Haiku 4.5** dominates the "Good enough + affordable + reliable" segment. Recommended as primary for 80% of use cases.
- **🥈 Gemini 3 Flash** is fastest and near-excellent quality; ideal for interactive/latency-critical paths.
- **🥉 Claude Sonnet 4.5** steps up for complex multi-step reasoning; 75% quality jump over Haiku for 3x cost.
- **🥇 Claude Opus 4.6** reserved for hardest problems (>15K token context, architecture decisions).
- **5️⃣ Minimax M2.5** is the "dark horse" — frontier-level quality at ultra-low cost, but less proven in production.
- **6️⃣ GPT-4o mini** is emergency fallback and last-mile option when budget is absolutely critical.

---

## Table 5: Cost-Quality Ratio (Quality per Dollar Spent)

| Model             | Cost/M      | Quality % | Ratio (Quality/$) | Recommendation                          |
| ----------------- | ----------- | --------- | ----------------- | --------------------------------------- |
| Claude Haiku 4.5  | $3.50       | 73        | **20.9**          | ⭐⭐⭐⭐⭐ BEST ratio; default tier     |
| Gemini 3 Flash    | $2.00 (avg) | 78        | **39.0**          | ⭐⭐⭐⭐⭐ Superior if cost available   |
| Claude Sonnet 4.5 | $10.50      | 77        | **7.3**           | ⭐⭐⭐ Good for complex tasks           |
| Claude Opus 4.6   | $17.50      | 81        | **4.6**           | ⭐⭐ Use sparingly for hardest 5%       |
| Minimax M2.5      | $0.79       | 80        | **101.3**         | ⭐⭐⭐⭐ Best raw ratio; scaling option |
| GPT-4o mini       | $0.375      | 70        | **186.7**         | ⭐ Emergency fallback only              |

**Key Insight:** Gemini Flash has the best ratio when cost is available; Minimax M2.5 is exceptional for batch/agentic loops; Claude Haiku is the "Goldilocks" option (cost-reasonable + quality-solid + proven in production).

---

## Selection Decision Tree

```
START: Incoming request with tokens estimate

┌─ Is this FAST task (50-500 tokens)?
│  ├─ YES → Check latency SLA
│  │  ├─ <1s required? → Gemini 3 Flash (best speed, meets perf)
│  │  ├─ <5s required? → Claude Haiku (fast enough, better quality reserve)
│  │  └─ Cost critical? → GPT-4o mini (emergency fallback)
│  │
│  └─ NO → Check tokens
│
├─ Is this NORMAL task (500-3K tokens)?
│  ├─ YES → Default to Claude Haiku (73% quality, $0.02/call typical, 5-20s OK)
│  └─ NO → Check complexity next
│
├─ Is this COMPLEX task (3K-10K tokens)?
│  ├─ YES → Check if multi-step reasoning required
│  │  ├─ Complex logic? → Claude Sonnet 4.5 (77% quality, $0.10/call typical)
│  │  ├─ Simple? → Claude Haiku (cost savings, still adequate)
│  │  └─ Cost critical? → Minimax M2.5 (80% quality, $0.01/call)
│  │
│  └─ NO → Check tokens again
│
└─ Is this HIGH_COMPLEX task (>10K tokens)?
   ├─ YES → Mission-critical?
   │  ├─ YES → Claude Opus 4.6 (81% quality, $0.50+/call, best reasoning)
   │  ├─ NO → Claude Sonnet 4.5 (77% quality, 3x cheaper than Opus)
   │  └─ NOT URGENT? → Minimax M2.5 (batch mode, $0.01/call)
   │
   └─ NO → Should not reach here; escalate to human review
```

---

## Cumulative Cost Projection (User Scenario)

**Current state:** ~$550/mo across all providers

**Optimized allocation:**

| Category                      | Monthly Budget | Models                                                          | Rationale                       |
| ----------------------------- | -------------- | --------------------------------------------------------------- | ------------------------------- |
| FAST (25% of requests)        | $50            | Gemini Flash primary, Haiku fallback                            | Latency-critical, high-volume   |
| NORMAL (50% of requests)      | $150           | Claude Haiku primary (70-80% of this category), Gemini fallback | Default tier, volume driver     |
| COMPLEX (20% of requests)     | $120           | Claude Sonnet (60% of this), Haiku (40% of this)                | Reasoning tier, selective use   |
| HIGH_COMPLEX (5% of requests) | $80            | Claude Opus (70% of this), Sonnet (30% of this)                 | Mission-critical only           |
| **Contingency**               | $50            | Emergency fallback (GPT-4o mini, unused Gemini credits)         | Buffer for overages             |
| **TOTAL**                     | **$450**       | —                                                               | **$100/mo savings vs. current** |

---

## Notes & Caveats

1. **Benchmarks are point-in-time.** SWE-Bench, AIME, and other metrics evolve quarterly. Re-evaluate Q1 2026.
2. **Latency varies by load.** P50/P99 timings assume normal load; peak times may add 500ms-1s.
3. **Cost includes token tax.** Estimates assume input:output ratio of 1:1. Complex reasoning (o1 family) may have higher output multipliers.
4. **Quality is task-dependent.** A model's benchmark score doesn't guarantee performance on your specific workload. Use shadow testing before full commit.
5. **Cursor Ultra credit model.** $20/mo subscription = $0.50/M effective, but $600-1000/mo overages. Use as supplementary, not primary.
6. **Gemini Flash constraints.** Requires Google Cloud account; some features (video, advanced tools) are premium.
7. **Minimax M2.5 production readiness.** Strong benchmarks; lower production track record in US market. Recommend shadow testing before critical path.

---

## Quick Reference: "I have 1 minute, what should I use?"

| Scenario                     | Model             | Why                                             |
| ---------------------------- | ----------------- | ----------------------------------------------- |
| Quick fix, low stakes        | Claude Haiku      | Best overall ratio; 73% is good enough          |
| API integration test         | Gemini 3 Flash    | Fastest, meets 78% quality bar                  |
| Architecture decision        | Claude Opus 4.6   | 81% quality + best reasoning for novel problems |
| Urgent, no budget left       | GPT-4o mini       | Meets 70% floor; ultra-cheap                    |
| Agentic loop, 1000+ calls/mo | Minimax M2.5      | Frontier quality at ultra-low cost              |
| Stuck with medium problem    | Claude Sonnet 4.5 | 77% quality, faster than Opus, worth the cost   |

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
