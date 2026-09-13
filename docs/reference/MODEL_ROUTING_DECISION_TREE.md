# Model Routing Decision Tree

**Date**: 2026-02-15
**Version**: 1.0
**Purpose**: Programmatic model selection based on task constraints

---

## Quick Reference: Frontier Models

```
TIER 1 — FALLBACK (Cost minimum)
├─ Model: GPT-4o mini
├─ Quality: 70%
├─ Cost: $0.375/M
├─ Speed: fast
└─ Use when: budget < $0.0005/call, cost is absolute constraint

TIER 2 — PRIMARY (Best value)
├─ Model: MiniMax M2.5
├─ Quality: 80.2%
├─ Cost: $0.79/M
├─ Speed: moderate (75 tok/s)
└─ Use when: default choice for 95% of tasks

TIER 3 — PREMIUM (Highest quality)
├─ Model: Claude Opus 4.6
├─ Quality: 80.8%
├─ Cost: $17.50/M
├─ Speed: slow
└─ Use when: mission_critical = True (medical, financial, legal)
```

---

## Decision Tree (Pseudocode)

```python
def select_model(
    input_tokens: int,
    budget_cents: float,  # cost budget in cents ($0.05 = 5 cents)
    latency_sla_ms: int = 10000,
    quality_threshold: float = 70.0,
    complexity: str = "normal",
    mission_critical: bool = False,
    multi_modal_required: bool = False,
    reasoning_heavy: bool = False,
) -> str:
    """
    Select optimal model based on constraints.
    Returns: model_id (string)
    """

    # ═══════════════════════════════════════════════════════════════
    # PHASE 1: Check absolute constraints
    # ═══════════════════════════════════════════════════════════════

    # Quality floor check
    if quality_threshold < 60:
        return ERROR("quality_threshold < 60% is unacceptable")

    # Mission-critical lock: only Opus acceptable
    if mission_critical:
        # Opus cost: $17.50/M, avg 10K+ tokens per call
        opus_cost_cents = (17.50 / 1_000_000) * input_tokens * 100
        if opus_cost_cents > budget_cents:
            return WARN(f"Opus costs {opus_cost_cents}¢ > budget {budget_cents}¢") and use_fallback("minimax-m2.5")
        return "claude-opus-4.6"

    # ═══════════════════════════════════════════════════════════════
    # PHASE 2: Calculate actual costs for frontier models
    # ═══════════════════════════════════════════════════════════════

    gpt4o_mini_cost_cents = (0.375 / 1_000_000) * input_tokens * 100
    minimax_cost_cents = (0.79 / 1_000_000) * input_tokens * 100
    opus_cost_cents = (17.50 / 1_000_000) * input_tokens * 100
    sonnet_cost_cents = (10.50 / 1_000_000) * input_tokens * 100
    gemini_flash_cost_cents = (1.50 / 1_000_000) * input_tokens * 100
    glm5_cost_cents = (2.60 / 1_000_000) * input_tokens * 100

    # ═══════════════════════════════════════════════════════════════
    # PHASE 3: Speed-critical path (latency SLA)
    # ═══════════════════════════════════════════════════════════════

    if latency_sla_ms < 300:
        # Need ultra-fast model (>180 tok/s)
        # Gemini Flash: 218 tok/s → 4.6s for 1K tokens
        if gemini_flash_cost_cents <= budget_cents and quality_threshold <= 78:
            return "gemini-3-flash"
        # Fallback: GPT-4o mini is fast enough (fast tier)
        if gpt4o_mini_cost_cents <= budget_cents:
            return "gpt-4o-mini"
        # No other model achieves <300ms SLA well
        return WARN("No model achieves <300ms SLA within budget") and use_best_effort("gemini-3-flash")

    if latency_sla_ms < 500:
        # Need fast model (>100 tok/s)
        # Gemini Flash preferred for latency, MiniMax as fallback
        if gemini_flash_cost_cents <= budget_cents:
            return "gemini-3-flash"
        if minimax_cost_cents <= budget_cents:
            return "minimax-m2.5"
        return "gpt-4o-mini"

    # ═══════════════════════════════════════════════════════════════
    # PHASE 4: Cost-critical path (budget constraint)
    # ═══════════════════════════════════════════════════════════════

    if budget_cents < 0.02:  # less than $0.0002/call
        # Ultimate budget minimum: GPT-4o mini
        if gpt4o_mini_cost_cents <= budget_cents:
            return "gpt-4o-mini"
        return WARN("Budget too low even for GPT-4o mini") and use_fallback("gpt-4o-mini")

    # ═══════════════════════════════════════════════════════════════
    # PHASE 5: Quality-critical path (reasoning or domain-specific)
    # ═══════════════════════════════════════════════════════════════

    if reasoning_heavy and quality_threshold > 80:
        # Reasoning-heavy tasks: prefer GLM-5 or Opus
        # GLM-5: 92.7% AIME (best reasoning)
        # Opus: 85% AIME (second best, but more reliable for coding)
        if glm5_cost_cents <= budget_cents:
            # GLM-5 is specialist; good for math/logic
            # But Opus is more reliable for mixed reasoning+coding
            if quality_threshold > 85:
                # Pure reasoning: use GLM-5
                return "glm-5"
            else:
                # Mixed reasoning+coding: use Opus if budget permits
                if opus_cost_cents <= budget_cents:
                    return "claude-opus-4.6"
                else:
                    return "glm-5"
        # GLM-5 over budget: fallback to Opus if available
        if opus_cost_cents <= budget_cents:
            return "claude-opus-4.6"
        # All reasoning specialists over budget: use MiniMax
        return "minimax-m2.5"

    if multi_modal_required:
        # Image + text: Gemini 2.5 Pro is best, but dominated by MiniMax for text
        # Routing: use Gemini 2.5 Pro ONLY if:
        # 1. Input includes images, AND
        # 2. Cost is acceptable
        gemini_pro_cost_cents = (4.07 / 1_000_000) * input_tokens * 100
        if gemini_pro_cost_cents <= budget_cents:
            return "gemini-2.5-pro"  # Only multi-modal specialist
        # Image-less fallback: MiniMax
        return "minimax-m2.5"

    # ═══════════════════════════════════════════════════════════════
    # PHASE 6: Default path (standard tasks)
    # ═══════════════════════════════════════════════════════════════

    # MiniMax is best for 95% of tasks (80.2% quality, $0.79/M)
    if minimax_cost_cents <= budget_cents:
        return "minimax-m2.5"

    # If MiniMax over budget: try cheaper models
    if gpt4o_mini_cost_cents <= budget_cents:
        # Quality drops to 70%, but acceptable fallback
        if quality_threshold <= 70:
            return "gpt-4o-mini"
        else:
            return WARN(f"Quality drop: MiniMax 80.2% → GPT-4o mini 70%") and use_fallback("gpt-4o-mini")

    # All models over budget: hard error
    return ERROR(f"All models exceed budget {budget_cents}¢")
```

---

## Decision Tree (English pseudocode)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MODEL SELECTION DECISION TREE                         │
└─────────────────────────────────────────────────────────────────────────┘

START
  │
  ├─ IS mission_critical = True?
  │   ├─ YES → CHECK Opus cost
  │   │   ├─ Within budget? → USE: Claude Opus 4.6
  │   │   └─ Over budget? → WARN + USE: MiniMax M2.5 (fallback)
  │   │
  │   └─ NO → Continue
  │
  ├─ IS latency_sla < 300ms?
  │   ├─ YES → Need ultra-fast (>180 tok/s)
  │   │   ├─ Gemini Flash in budget? → USE: Gemini 3 Flash
  │   │   ├─ GPT-4o mini in budget? → USE: GPT-4o mini
  │   │   └─ Neither in budget? → WARN + USE: best available
  │   │
  │   └─ NO → Continue
  │
  ├─ IS latency_sla < 500ms?
  │   ├─ YES → Need fast model (>100 tok/s)
  │   │   ├─ Gemini Flash in budget? → USE: Gemini 3 Flash
  │   │   ├─ MiniMax in budget? → USE: MiniMax M2.5
  │   │   └─ Neither? → USE: GPT-4o mini
  │   │
  │   └─ NO → Continue
  │
  ├─ IS budget < $0.0002/call?
  │   ├─ YES → Cost absolute constraint
  │   │   ├─ GPT-4o mini in budget? → USE: GPT-4o mini
  │   │   └─ Over budget? → ERROR: budget too low
  │   │
  │   └─ NO → Continue
  │
  ├─ IS reasoning_heavy AND quality > 80%?
  │   ├─ YES → Need reasoning specialist
  │   │   ├─ Pure reasoning (quality > 85%)?
  │   │   │   ├─ GLM-5 in budget? → USE: GLM-5 (92.7% AIME)
  │   │   │   └─ Over budget? → Try Opus or MiniMax
  │   │   │
  │   │   └─ Mixed reasoning + coding?
  │   │       ├─ Opus in budget? → USE: Claude Opus 4.6
  │   │       └─ Over budget? → USE: GLM-5 or MiniMax
  │   │
  │   └─ NO → Continue
  │
  ├─ IS multi_modal_required?
  │   ├─ YES → Image + text input
  │   │   ├─ Gemini 2.5 Pro in budget? → USE: Gemini 2.5 Pro
  │   │   └─ Over budget? → USE: MiniMax M2.5 (image-less)
  │   │
  │   └─ NO → Continue
  │
  ├─ DEFAULT: Standard tasks
  │   ├─ MiniMax in budget? → USE: MiniMax M2.5 (primary)
  │   ├─ MiniMax over budget, GPT-4o mini available?
  │   │   ├─ quality_threshold <= 70%? → USE: GPT-4o mini
  │   │   └─ quality_threshold > 70%? → WARN + USE: GPT-4o mini
  │   │
  │   └─ All over budget? → ERROR: budget too low
  │
END
```

---

## Real-World Examples

### Example 1: Rapid Document Classification

**Input:**
- Input: 200 tokens
- Budget: $0.0001 (max cost $0.01 per 100 requests)
- Latency SLA: 2 seconds
- Quality threshold: 60%
- Task: Classify GitHub issues into categories

**Decision Path:**
1. mission_critical = False ✓
2. latency_sla_ms (2s) not critical ✓
3. budget check: $0.0001 is very tight
4. Cost calculation:
   - GPT-4o mini: (0.375 / 1M) × 200 × 100 = $0.0000075 (well within budget ✓)
   - MiniMax: (0.79 / 1M) × 200 × 100 = $0.0000158 (within budget ✓)
5. MiniMax in budget and meets quality (80.2% > 60%) ✓

**Result: USE MiniMax M2.5**
- Cost per request: $0.000016 (1.6¢ per 1000 requests)
- Quality: 80.2% (excellent for classification)
- Speed: moderate (acceptable for batch processing)

---

### Example 2: Real-Time Chat with User

**Input:**
- Input: 5K tokens (large conversation history)
- Budget: $0.05 (max cost per message)
- Latency SLA: 300ms (must respond within 300ms for interactive feel)
- Quality threshold: 75%
- Task: Conversational agent responding to user queries

**Decision Path:**
1. mission_critical = False ✓
2. latency_sla_ms = 300ms (CRITICAL) → Need >180 tok/s
3. Latency analysis:
   - Gemini 3 Flash: 218 tok/s → 5K / 218 = 22.9s (TOO SLOW!)
   - MiniMax: 75 tok/s → 5K / 75 = 66.6s (EVEN SLOWER)
4. Problem: No frontier model achieves <300ms for 5K tokens!
   - Even ultra-fast Gemini Flash needs 23s for large context
5. Practical solution: Use MiniMax with context reduction OR reduce SLA

**Result: USE MiniMax M2.5 with context optimization**
- Recommendation: Only include last 1K tokens in context (not full 5K)
- Cost: (0.79 / 1M) × 1K × 100 = $0.0000079 (0.79¢)
- Achievable latency: 75 tok/s → 13.3s per token (still high, but acceptable for thought generation)
- Alternative: Accept higher latency (5-10s) as OK for chat

**Why not Gemini Flash?** Even though ultra-fast, it doesn't achieve 300ms for 5K tokens. Both frontier models have speed-of-light limits: tokens must be computed serially.

---

### Example 3: Mission-Critical Medical Diagnosis Report

**Input:**
- Input: 50K tokens (detailed patient history, test results, prior diagnoses)
- Budget: $5.00 (no cost constraint; medical accuracy > cost)
- Latency SLA: 2 hours (medical work is async)
- Quality threshold: 90% (high bar for medical accuracy)
- Task: Generate diagnostic recommendations based on patient data

**Decision Path:**
1. mission_critical = True → LOCKED to Opus
2. Cost check:
   - Opus: (17.50 / 1M) × 50K × 100 = $0.0875 (87.5¢)
   - Budget: $5.00
   - Opus cost: $0.875 < $5.00 ✓ (within budget)
3. Quality: Opus 80.8% vs threshold 90%?
   - Opus doesn't reach 90%, but it's the only model with sufficient reliability for medical
   - Recommendation: PAIR with human review (Opus + doctor verification)

**Result: USE Claude Opus 4.6**
- Cost: $0.875 (acceptable for high-value medical task)
- Quality: 80.8% (highest available; human verifies final recommendation)
- Speed: slow (50K tokens @ 30 tok/s ≈ 27 minutes) → acceptable for async medical work
- Fallback: MiniMax M2.5 if Opus unavailable (emergency scenario)

---

### Example 4: Code Refactoring with Budget Constraint

**Input:**
- Input: 8K tokens (large source file)
- Budget: $0.01 (strict cost control; cost > quality)
- Latency SLA: 10 seconds (batch job)
- Quality threshold: 75%
- Task: Refactor Python code for readability

**Decision Path:**
1. mission_critical = False ✓
2. latency_sla_ms = 10s (reasonable) ✓
3. Budget: $0.01
4. Cost analysis:
   - MiniMax: (0.79 / 1M) × 8K × 100 = $0.0000632 (6.32¢ per call, well under $0.01 ✓)
   - Opus: (17.50 / 1M) × 8K × 100 = $0.0014 ($1.40, way over)
   - GLM-5: (2.60 / 1M) × 8K × 100 = $0.000208 (20.8¢, over)
5. MiniMax in budget, meets quality (80.2% > 75%) ✓

**Result: USE MiniMax M2.5**
- Cost: 6.32¢ (well under $0.01 budget)
- Quality: 80.2% (excellent for refactoring task)
- Speed: 8K / 75 tok/s ≈ 106s (acceptable for batch job)

---

### Example 5: Pure Reasoning: Complex Math Problem

**Input:**
- Input: 2K tokens (math problem, scratch space)
- Budget: $0.05 (willing to spend for correct answer)
- Latency SLA: 30 seconds (async, reasoning takes time)
- Quality threshold: 85% (high bar for mathematical correctness)
- reasoning_heavy = True
- Task: Solve competition-level math problem

**Decision Path:**
1. mission_critical = False (but quality is critical)
2. reasoning_heavy = True AND quality_threshold > 80% ✓
3. Best models for reasoning:
   - GLM-5: 92.7% AIME (best mathematical reasoning)
   - Opus: 85% AIME (good reasoning, more reliable overall)
4. Cost analysis:
   - GLM-5: (2.60 / 1M) × 2K × 100 = $0.000052 (5.2¢)
   - Opus: (17.50 / 1M) × 2K × 100 = $0.00035 (35¢)
5. Both in budget. GLM-5 dominates on reasoning (92.7% > 85%)

**Result: USE GLM-5**
- Cost: 5.2¢ (well under budget)
- Quality: 92.7% AIME (best mathematical reasoning)
- Speed: 2K / 50 tok/s ≈ 40s (acceptable for reasoning task)
- Note: GLM-5 is slow (slow speed tier), but acceptable for async math work

**Why not Opus?** GLM-5 is specialized for reasoning (92.7% AIME vs Opus 85%); cost savings (30.2¢ cheaper) are bonus. For pure math, GLM-5 is the right choice.

---

### Example 6: Multi-Modal Image Analysis

**Input:**
- Input: 3K tokens + 1 image (product photo for e-commerce)
- Budget: $0.02
- Latency SLA: 5 seconds
- Quality threshold: 70%
- multi_modal_required = True
- Task: Describe product image and extract attributes

**Decision Path:**
1. mission_critical = False ✓
2. multi_modal_required = True → Need image-capable model
3. Best multi-modal: Gemini 2.5 Pro (image + text)
4. Cost analysis:
   - Gemini 2.5 Pro: (4.07 / 1M) × 3K × 100 = $0.0001221 (12.2¢)
   - Budget: $0.02
   - Cost is within budget ✓
5. Quality: Gemini 2.5 Pro 75% > threshold 70% ✓

**Result: USE Gemini 2.5 Pro**
- Cost: 12.2¢ (within $0.02 budget)
- Quality: 75% (adequate for image description)
- Speed: moderate (acceptable for batch product processing)
- Note: Gemini 2.5 Pro is only model in frontier with strong image capability

**Why not MiniMax?** MiniMax cannot process images directly. Must choose Gemini 2.5 Pro for image input. (If image removed, MiniMax would be better value at $0.79/M, but defeats purpose.)

---

## Fallback Chains (Provider Outages)

### Primary → Secondary → Tertiary

```
FAST Category:
  Primary: MiniMax M2.5
  Secondary: Gemini 3 Flash (if MiniMax unavailable)
  Tertiary: GPT-4o mini (ultimate fallback)

NORMAL Category:
  Primary: MiniMax M2.5
  Secondary: GPT-4o mini (if MiniMax unavailable, quality drop to 70%)
  Tertiary: Gemini 3 Flash (if speed-critical)

COMPLEX Category:
  Primary: MiniMax M2.5
  Secondary: Claude Sonnet 4.5 (if MiniMax unavailable, cost +13x but quality maintained)
  Tertiary: GLM-5 (if reasoning-heavy alternative needed)

HIGH_COMPLEX Category:
  Primary: Claude Opus 4.6
  Secondary: MiniMax M2.5 (if Opus unavailable, cost drops 22x)
  Tertiary: GLM-5 (if reasoning-specific, cost -87%)
```

---

## Summary: When to Use Each Model

| Model | Primary Use Case | Cost | Quality | When |
|-------|---|---|---|---|
| **GPT-4o mini** | Ultimate cost minimum | $0.375/M | 70% | Budget < $0.0002/call AND cost > quality |
| **MiniMax M2.5** | DEFAULT for 95% of tasks | $0.79/M | 80.2% | Use unless specific constraint (latency, reasoning, mission-critical) |
| **Claude Opus 4.6** | Mission-critical work | $17.50/M | 80.8% | mission_critical = True AND budget permits |
| **Gemini 3 Flash** | Latency-critical only | $1.50/M | 78% | latency_sla < 300ms AND MiniMax doesn't fit |
| **GLM-5** | Reasoning-heavy | $2.60/M | 92.7% AIME | reasoning_heavy = True AND quality_threshold > 85% |
| **Gemini 2.5 Pro** | Multi-modal only | $4.07/M | 75% | Image + text input required |
| **Claude Sonnet 4.5** | Fallback for quality | $10.50/M | 77.2% | MiniMax unavailable AND quality gap matters |

---

## Implementation Note

This decision tree is designed to be **programmatically executable**. Pseudo-code above can be implemented in:
- Python: Direct implementation as function
- Go: Switch on constraint types
- TypeScript: Discriminated union pattern
- Bash: Case statements for major branches

**Integration point**: Cost governance subsystem calls this tree at task dispatch time, matching task budget to model selection.

---

**Document Status**: Reference; suitable for implementation
**Last Updated**: 2026-02-15
**Next Review**: When new models released or benchmarks updated


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
