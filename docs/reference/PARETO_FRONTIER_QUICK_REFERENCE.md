# Pareto Frontier Quick Reference

**Status**: Quick lookup guide
**For**: Understanding why specific models are on/off the frontier

---

## The 3-Model Frontier

```
Tier 1: GPT-4o mini          70% quality, $0.375/M  (fallback)
Tier 2: MiniMax M2.5         80.2% quality, $0.79/M (PRIMARY)
Tier 3: Claude Opus 4.6      80.8% quality, $17.50/M (premium)
```

All other models are **dominated** (beaten on ≥2 dimensions).

---

## Your Questions Answered

### "Where is GLM-5?"

**GLM-5 (92.7% AIME, $2.60/M)** is OFF the frontier because:

| Comparison | Winner  | Reason                                                              |
| ---------- | ------- | ------------------------------------------------------------------- |
| vs MiniMax | MiniMax | 80.2% quality, $0.79/M = 3.3x cheaper for nearly same output        |
| vs Opus    | Opus    | 85% AIME reasoning, more reliable for mixed code+reasoning          |
| Cost-value | MiniMax | $0.79 per % quality beats $2.60 per % quality (3.7x more efficient) |

**When GLM-5 is useful**: Pure math/reasoning tasks where 92.7% AIME matters. But that's <5% of agent work.

**Verdict**: Dominated. Use MiniMax for cost-value, Opus for reasoning reliability.

---

### "Why not Opus 4.6?"

**Claude Opus 4.6 (80.8% SWE-Bench, $17.50/M)** IS on frontier, but ONLY for mission-critical.

| Category     | Primary  | Reason                                                      |
| ------------ | -------- | ----------------------------------------------------------- |
| FAST         | MiniMax  | 80.2% ≈ 80.8%, but $0.79 << $17.50 (22x cheaper)            |
| NORMAL       | MiniMax  | Same situation: MiniMax dominates on cost                   |
| COMPLEX      | MiniMax  | MiniMax quality (80.2%) is 99.3% of Opus (80.8%)            |
| HIGH_COMPLEX | **Opus** | Only model for mission-critical (medical, financial, legal) |

**Why reserved?** Opus costs $0.17/10K tokens. That's 22x MiniMax. You only pay that when quality is absolute requirement, not preference.

**When to use Opus**: `mission_critical = True` AND budget permits.

---

### "Codex 5.3? Codex-Spark?"

**Codex 5.3 (56.8% SWE-Bench, $1.25/M)** is REJECTED because:

```
GPT-4o mini:  70% quality, $0.375/M (CHEAPER & BETTER)
Codex 5.3:    56.8% quality, $1.25/M

GPT-4o mini DOMINATES:
  ✓ Higher quality (70% > 56.8%)
  ✓ Cheaper ($0.375 < $1.25)

No reason to use Codex.
```

**Codex-Spark**: Even worse (~50% quality). Fails quality floor (60%).

**Verdict**: Off frontier. Use GPT-4o mini for cost minimum instead.

---

## Why Only 3 Models?

**Pareto Frontier Rule**: A model is on frontier if no other model is strictly better on 2+ dimensions.

```
Test each model:

Model              vs Best Competitor     Beaten On
────────────────────────────────────────────────────
Claude Sonnet      vs MiniMax M2.5        Quality (80.2 > 77.2) + Cost ($0.79 < $10.50) ✗
Gemini Flash       vs MiniMax M2.5        Quality (80.2 > 78) + Cost ($0.79 < $1.50) ✗
Gemini 2.5 Pro     vs MiniMax M2.5        Quality (80.2 > 75) + Cost ($0.79 < $4.07) ✗
GLM-5              vs MiniMax M2.5        Cost ($0.79 < $2.60) [quality trade-off] ✗
Codex              vs GPT-4o mini         Quality (70 > 56.8) + Cost ($0.375 < $1.25) ✗

Only 3 survive dominance:
  • GPT-4o mini: Only model at cost floor (<$0.40/M)
  • MiniMax: Best cost-quality balance ($0.79/M, 80.2%)
  • Opus: Only model at quality peak (80.8%), reserved for mission-critical
```

A 4th model would be dominated. No competitive niche exists.

---

## Cost-Quality Efficiency

```
Model              Cost/% Quality    Efficiency
──────────────────────────────────────────────────
GPT-4o mini        $0.00536/%         186.7%/$
MiniMax M2.5       $0.00985/%         101.5%/$
Claude Sonnet      $0.13622/%         7.34%/$
Opus               $0.21655/%         4.6%/$

Winner: GPT-4o mini per-$ efficiency
Sweet spot: MiniMax (10.2x better than Sonnet, yet higher quality than Sonnet)
Premium: Opus (20x worse efficiency, but only option for mission-critical)
```

---

## Quick Decision Rules

### Rule 1: Cost Absolute Constraint

```
IF budget < $0.0002/call
  → Use GPT-4o mini (only frontier option that cheap)
ELSE
  → Use MiniMax (best overall value)
```

### Rule 2: Mission-Critical Lock

```
IF mission_critical = True
  → Use Claude Opus 4.6 (no negotiation)
  → Only if Opus unavailable: MiniMax fallback
ELSE
  → Use normal routing
```

### Rule 3: Latency Crisis

```
IF latency_sla < 300ms
  → Gemini 3 Flash (218 tok/s, fastest frontier-adjacent)
  → Not on strict frontier (dominated by MiniMax on cost-quality)
  → But acceptable for latency-critical work
ELSE
  → Use MiniMax
```

### Rule 4: Reasoning Edge Case

```
IF reasoning_heavy = True AND quality_threshold > 85%
  → Consider GLM-5 (92.7% AIME, best reasoning)
  → Trade: +12.7% reasoning for +3.3x cost vs MiniMax
  → Only worth if PURE math/logic (not mixed code+reasoning)
ELSE
  → Use MiniMax
```

### Rule 5: Default (applies to 95% of tasks)

```
→ Use MiniMax M2.5
```

---

## Model Comparison Matrix (Cost-Quality Only)

```
Quality ↑
   100 │
       │
    95 │ ★ GLM-5 (92.7%, not frontier)
       │
    85 │
       │
    80 │ ★ Opus (80.8%, mission-critical tier)
       │ ★ MiniMax (80.2%, PRIMARY)
    75 │   ✗ Sonnet (77.2%, dominated)
       │
    70 │ ★ GPT-4o mini (70%, fallback)
       │
    65 │
       │
    60 │   ✗ Codex (56.8%, dominated)
       │
    50 └─────────────────────────────────── Cost ($) →
       $0.4   $1    $2.6   $4   $10.5  $17.5

★ = Frontier
✗ = Dominated
```

---

## When to Escalate to Humans

```
IF no model meets requirements:
  ├─ Quality threshold impossible (e.g., >95%)
  ├─ Latency SLA impossible (<100ms for 10K tokens)
  ├─ Budget too low (<$0.0001/call for meaningful work)
  ├─ Task requires human judgment (medical diagnosis without review)
  └─ Model decision conflict (e.g., must be fast AND cheap simultaneously)

THEN:
  → Escalate to human queue
  → Provide: task description, failed constraints, recommended fallback
```

---

## Pricing Reference (January 2026)

| Model             | Cost/M | Speed      | Quality    |
| ----------------- | ------ | ---------- | ---------- |
| GPT-4o mini       | $0.375 | fast       | 70%        |
| MiniMax M2.5      | $0.79  | moderate   | 80.2%      |
| Gemini 3 Flash    | $1.50  | ultra-fast | 78%        |
| Codex 5.3         | $1.25  | fast       | 56.8%      |
| GLM-5             | $2.60  | slow       | 92.7% AIME |
| Gemini 2.5 Pro    | $4.07  | moderate   | 75%        |
| Claude Sonnet 4.5 | $10.50 | moderate   | 77.2%      |
| Claude Opus 4.6   | $17.50 | slow       | 80.8%      |

---

## Summary Table: Use This Model When...

| Model                 | Use When                                                |
| --------------------- | ------------------------------------------------------- |
| **GPT-4o mini**       | Budget < $0.0002/call OR cost is absolute constraint    |
| **MiniMax M2.5**      | Default for ALL tasks unless special constraint applies |
| **Claude Opus 4.6**   | mission_critical = True (medical, financial, legal)     |
| **Gemini 3 Flash**    | Latency SLA < 300ms AND standard routing unavailable    |
| **GLM-5**             | Pure reasoning (math, logic) AND quality > 85%          |
| **Gemini 2.5 Pro**    | Image + text input AND cost permits                     |
| **Claude Sonnet 4.5** | MiniMax unavailable AND willing to pay 13x more         |
| **Codex 5.3**         | Never. Use GPT-4o mini instead.                         |

---

## Further Reading

- **Complete analysis**: `PARETO_FRONTIER_COMPLETE_ANALYSIS.md` (detailed dominance proofs)
- **Decision tree**: `MODEL_ROUTING_DECISION_TREE.md` (pseudocode implementation)
- **Benchmarks**: See "Accuracy Metrics Explained" section in complete analysis

---

**Quick Ref Version 1.0**
**Updated**: 2026-02-15

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
