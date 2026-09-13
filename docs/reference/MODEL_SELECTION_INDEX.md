# Model Selection Documentation Index

**Purpose**: Central index for all model selection, Pareto frontier, and routing documentation

**Status**: Complete reference set
**Last Updated**: 2026-02-15

---

## Quick Answer to "Where is [Model]?"

### GLM-5 (92.7% AIME, $2.60/M)

**Status**: OFF frontier
**Why**: Dominated by MiniMax on cost-value (3.3x more expensive) for general tasks, and by Opus on reasoning reliability (Opus 85% AIME vs GLM-5 92.7%, but Opus more reliable for mixed code+reasoning)

**Location**: See `/docs/reference/PARETO_FRONTIER_COMPLETE_ANALYSIS.md` → "GLM-5 (92.7% AIME) — Why Not Selected?"

---

### Claude Opus 4.6 (80.8% SWE-Bench, $17.50/M)

**Status**: ON frontier, but RESERVED for mission-critical only
**Why**: Best quality (80.8%), but costs 22x more than MiniMax for only 0.6% improvement. Reserved for HIGH_COMPLEX tier when quality is absolute requirement (not preference)

**Location**: See `/docs/reference/PARETO_FRONTIER_COMPLETE_ANALYSIS.md` → "Claude Opus 4.6 — Why Reserved for Premium Only?"

**When to use**: `mission_critical = True` (medical, financial, legal diagnosis)

---

### Claude Sonnet 4.5 (77.2% SWE-Bench, $10.50/M)

**Status**: OFF frontier
**Why**: Dominated by MiniMax on both quality (80.2% > 77.2%) and cost ($0.79 < $10.50). MiniMax is 13.3x cheaper for higher quality.

**Location**: See `/docs/reference/PARETO_FRONTIER_COMPLETE_ANALYSIS.md` → "Claude Sonnet 4.5 — Why Dominated?"

---

### Gemini 3 Flash (78% SWE-Bench, 218 tok/s, $1.50/M)

**Status**: OFF frontier (quality-cost), but available as speed fallback
**Why**: Dominated by MiniMax on cost-quality (80.2% > 78%, $0.79 < $1.50). But ultra-fast (218 tok/s) makes it acceptable fallback for <300ms latency SLA.

**Location**: See `/docs/reference/PARETO_FRONTIER_COMPLETE_ANALYSIS.md` → "Gemini 3 Flash — Why Off Frontier Despite Speed?"

**When to use**: `latency_sla < 300ms` AND MiniMax doesn't fit

---

### GPT-5.3-Codex (56.8% SWE-Bench, $1.25/M) & Codex-Spark (~50%, ~$1.00/M)

**Status**: REJECTED
**Why**: Both fail quality floor (60% minimum). Also dominated by GPT-4o mini: 70% quality, $0.375/M beats Codex on BOTH quality and cost.

**Location**: See `/docs/reference/PARETO_FRONTIER_COMPLETE_ANALYSIS.md` → "GPT-5.3-Codex & GPT-5.3-Codex-Spark — Why Rejected?"

**Verdict**: Never use. GPT-4o mini is cheaper and higher quality.

---

### Gemini 2.5 Pro (75% SWE-Bench, $4.07/M, multi-modal)

**Status**: OFF frontier (quality-cost), but available for image tasks
**Why**: Dominated by MiniMax on cost-quality (80.2% > 75%, $0.79 < $4.07). But multi-modal capability makes it acceptable for image+text input.

**Location**: See `/docs/reference/PARETO_FRONTIER_COMPLETE_ANALYSIS.md` → "Gemini 2.5 Pro — Why Dominated?"

**When to use**: `multi_modal_required = True` AND cost permits

---

## Documentation Organization

### Document 1: Complete Pareto Frontier Analysis

**File**: `PARETO_FRONTIER_COMPLETE_ANALYSIS.md`
**Length**: ~1500 lines
**Audience**: Detailed explanation seekers

**Contents**:

- Full 14-model comparison table
- Dominance relationships (ASCII chart)
- Per-model detailed explanations (GLM-5, Opus, Sonnet, Gemini Flash, Codex, Gemini Pro)
- Category assignment justification with budget tier analysis
- Accuracy metrics explained (SWE-Bench, AIME, GPQA, MMLU)
- Cost-quality trade-off chart
- Summary decision matrix

**Start here if**: You want to understand WHY each model is on/off frontier with full context

---

### Document 2: Model Routing Decision Tree

**File**: `MODEL_ROUTING_DECISION_TREE.md`
**Length**: ~1000 lines
**Audience**: Implementers, programmatic selection

**Contents**:

- Quick reference (3-model frontier summary)
- Pseudocode decision tree (Python-like)
- English-language decision tree (flowchart)
- 6 real-world examples:
  1. Rapid document classification (FAST tier)
  2. Real-time chat with latency SLA (speed-critical)
  3. Mission-critical medical diagnosis (HIGH_COMPLEX)
  4. Code refactoring with budget constraint (COMPLEX)
  5. Pure reasoning math problem (reasoning-heavy)
  6. Multi-modal image analysis (image-specific)
- Fallback chains (provider outage scenarios)
- Summary table: when to use each model

**Start here if**: You're building the router logic or need to implement decision tree

---

### Document 3: Pareto Frontier Quick Reference

**File**: `PARETO_FRONTIER_QUICK_REFERENCE.md`
**Length**: ~400 lines
**Audience**: Quick lookup, managers, decision makers

**Contents**:

- The 3-model frontier (TL;DR)
- Your questions answered (GLM-5, Opus, Codex, etc.)
- Why only 3 models?
- Cost-quality efficiency table
- Quick decision rules (5 basic rules)
- Model comparison matrix (ASCII)
- When to escalate to humans
- Summary table: when to use each model
- Further reading references

**Start here if**: You want a 5-minute overview without details

---

### Document 4: Dominance Proof Reference

**File**: `DOMINANCE_PROOF_REFERENCE.md`
**Length**: ~600 lines
**Audience**: Verification, quality assurance, academic rigor

**Contents**:

- Dominance definition (mathematical)
- 7 detailed dominance proofs:
  1. MiniMax dominates Sonnet (quality + cost)
  2. GPT-4o mini dominates Codex (quality + cost)
  3. MiniMax dominates Gemini Flash (quality + cost)
  4. MiniMax dominates Gemini Pro (quality + cost)
  5. GLM-5 niche analysis (specialized reasoning)
  6. Opus niche analysis (mission-critical quality)
  7. Codex-Spark floor check (quality rejection)
- Dominance summary table
- Quality floor analysis by category
- Efficiency analysis (cost per quality %)
- Conclusion (why only 3 models)

**Start here if**: You need to verify the selection logic with mathematical rigor

---

### Document 5: This Index

**File**: `MODEL_SELECTION_INDEX.md`

**Contents**:

- Quick answers to common questions
- Document organization guide
- Which document to read based on need
- Usage scenarios

---

## How to Use This Documentation

### Scenario 1: "Why is [model] not selected?"

→ Read `/docs/reference/PARETO_FRONTIER_QUICK_REFERENCE.md` (section "Your Questions Answered")

### Scenario 2: "I need to implement the router"

→ Read `/docs/reference/MODEL_ROUTING_DECISION_TREE.md` (Python pseudocode + examples)

### Scenario 3: "I want to understand the full analysis"

→ Read `/docs/reference/PARETO_FRONTIER_COMPLETE_ANALYSIS.md` (comprehensive, 1500 lines)

### Scenario 4: "I need to verify the logic is correct"

→ Read `/docs/reference/DOMINANCE_PROOF_REFERENCE.md` (mathematical proofs)

### Scenario 5: "I'm explaining this to non-technical stakeholder"

→ Show `/docs/reference/PARETO_FRONTIER_QUICK_REFERENCE.md` (visual, simple rules)

### Scenario 6: "What should I do in situation X?"

→ Use `/docs/reference/MODEL_ROUTING_DECISION_TREE.md` (find matching example or trace through tree)

---

## Key Concepts (Glossary)

### Pareto Frontier

Set of solutions where no solution dominates another on all dimensions. A model is ON the frontier if no other model beats it on 2+ dimensions simultaneously.

**Example**:

- MiniMax (80.2% quality, $0.79/M) is on frontier
- Sonnet (77.2% quality, $10.50/M) is OFF frontier (MiniMax beats it on quality AND cost)

### Dominance

Model A dominates Model B if A is ≥ B on all dimensions and strictly better on ≥2 dimensions.

**Example**: MiniMax dominates Sonnet

- Quality: 80.2% > 77.2% ✓ (strictly better)
- Cost: $0.79 < $10.50 ✓ (strictly better)
- Speed: moderate = moderate (tie)
  → MiniMax is strictly better on 2 dimensions → dominates

### Quality Floor

Minimum acceptable quality for a given category. Models below floor are REJECTED.

**Example**: Quality floor for NORMAL tasks = 70%

- GPT-4o mini: 70% ✓ (meets floor)
- Codex: 56.8% ✗ (below floor, rejected)

### Cost Per Quality Point

Cost divided by quality percentage. Measure of efficiency.

**Example**:

- GPT-4o mini: $0.375 / 70% = $0.00536 per % (most efficient)
- MiniMax: $0.79 / 80.2% = $0.00985 per % (good balance)
- Opus: $17.50 / 80.8% = $0.21655 per % (least efficient)

### Frontier Tier

Category within the Pareto frontier based on use case

**Tiers**:

1. **Tier 1 (Fallback)**: GPT-4o mini — cost minimum
2. **Tier 2 (Primary)**: MiniMax M2.5 — cost-quality sweet spot
3. **Tier 3 (Premium)**: Claude Opus 4.6 — mission-critical quality

### Budget Tier

Cost allocation category for task routing

**Tiers**:

1. **FAST**: <$0.0005/call (short inputs, <500 tokens)
2. **NORMAL**: $0.001-$0.05/call (standard, 1-3K tokens)
3. **COMPLEX**: $0.05-$0.15/call (advanced, 3-8K tokens)
4. **HIGH_COMPLEX**: >$0.85/call (mission-critical, 10K+ tokens)

---

## Model Quick Reference

| Model           | Tier | Status    | Quality    | Cost     | When To Use                    |
| --------------- | ---- | --------- | ---------- | -------- | ------------------------------ |
| GPT-4o mini     | 1    | FRONTIER  | 70%        | $0.375/M | Cost absolute minimum          |
| MiniMax M2.5    | 2    | PRIMARY   | 80.2%      | $0.79/M  | DEFAULT (95% of tasks)         |
| Claude Opus 4.6 | 3    | PREMIUM   | 80.8%      | $17.50/M | mission_critical = True        |
| Gemini Flash    | -    | FALLBACK  | 78%        | $1.50/M  | latency < 300ms                |
| GLM-5           | -    | NICHE     | 92.7% AIME | $2.60/M  | Pure reasoning only            |
| Gemini 2.5 Pro  | -    | FALLBACK  | 75%        | $4.07/M  | Image + text required          |
| Sonnet 4.5      | -    | DOMINATED | 77.2%      | $10.50/M | MiniMax unavailable (fallback) |
| Codex 5.3       | -    | REJECTED  | 56.8%      | $1.25/M  | NEVER (use GPT-4o mini)        |
| Codex-Spark     | -    | REJECTED  | ~50%       | ~$1.00/M | NEVER (use GPT-4o mini)        |

---

## Decision Tree Summary

```
START
  ├─ mission_critical = True?
  │   ├─ YES → Use Claude Opus 4.6
  │   └─ NO  → Continue
  ├─ latency_sla < 300ms?
  │   ├─ YES → Use Gemini 3 Flash (if in budget), else MiniMax
  │   └─ NO  → Continue
  ├─ reasoning_heavy AND quality > 85%?
  │   ├─ YES → Use GLM-5 or Opus (if budget permits)
  │   └─ NO  → Continue
  ├─ multi_modal_required?
  │   ├─ YES → Use Gemini 2.5 Pro (if in budget), else MiniMax
  │   └─ NO  → Continue
  └─ DEFAULT
      └─ Use MiniMax M2.5 (universal fallback)
```

---

## Integration Points

### Cost Governance System

The model router integrates with cost governance to enforce budget constraints:

- Task budget (in cents per call) is checked against model cost
- If budget < model cost: try fallback
- If all models exceed budget: escalate to human queue

### Quality Assurance

Models selected must meet category quality floor:

- FAST: ≥ 60% quality
- NORMAL: ≥ 70% quality
- COMPLEX: ≥ 75% quality
- HIGH_COMPLEX: ≥ 80% quality

### SLA Monitoring

Latency SLA compliance:

- If SLA < 300ms: switch to Gemini 3 Flash (218 tok/s) or error
- If SLA < 500ms: MiniMax or Gemini as tradeoff
- If SLA > 500ms: standard MiniMax routing

---

## Future Updates

### When Benchmarks Change

- Update quality % in all documents
- Recalculate dominance relationships
- Verify frontier remains 3-model
- Note: date of benchmark update in header

### When Pricing Changes

- Update $/M in all tables
- Recalculate cost per quality %
- Verify MiniMax remains optimal
- If price changes >10%: recompute frontier

### When New Models Released

- Add row to comparison table
- Run dominance check against 3-frontier models
- If dominated: mark as fallback/niche
- If on frontier: update tier assignments

---

## References

- **Pareto Optimality**: https://en.wikipedia.org/wiki/Pareto_efficiency
- **Cost-Quality Trade-offs**: See "Accuracy Metrics Explained" in PARETO_FRONTIER_COMPLETE_ANALYSIS.md
- **SWE-Bench**: https://www.swe-bench.com/ (software engineering benchmarks)
- **Pricing**: January 2026 public API rates (see PARETO_FRONTIER_COMPLETE_ANALYSIS.md for sources)

---

## Document Versions

| Document                             | Version | Date       | Status    |
| ------------------------------------ | ------- | ---------- | --------- |
| PARETO_FRONTIER_COMPLETE_ANALYSIS.md | 1.0     | 2026-02-15 | Reference |
| MODEL_ROUTING_DECISION_TREE.md       | 1.0     | 2026-02-15 | Reference |
| PARETO_FRONTIER_QUICK_REFERENCE.md   | 1.0     | 2026-02-15 | Reference |
| DOMINANCE_PROOF_REFERENCE.md         | 1.0     | 2026-02-15 | Reference |
| MODEL_SELECTION_INDEX.md (this)      | 1.0     | 2026-02-15 | Reference |

---

**Questions?** Refer to the appropriate document above. For implementation, start with `MODEL_ROUTING_DECISION_TREE.md`. For understanding, start with `PARETO_FRONTIER_QUICK_REFERENCE.md`.

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
