# Task Routing Quick Reference Guide

**For:** Developers implementing task dispatch routing in thegent
**Read time:** 5 min
**Related:** `/docs/reference/TASK_ROUTING_DESIGN.md` (full specification)

---

## The 4 Categories at a Glance

```
FAST           NORMAL          COMPLEX         HIGH_COMPLEX
────────────────────────────────────────────────────────────────
< 1K tokens    < 5K tokens     < 15K tokens    > 15K tokens
70% quality    80% quality     90% quality     95% quality
< 1 sec        < 5 sec         < 20 sec        < 60 sec
$0.002         $0.03           $0.15           $0.85
Haiku/Gemini   Sonnet/Mini     Opus            Opus (locked)
```

---

## Which Category? (Decision Tree)

```
1. Does your task have > 5K input tokens OR > 15K output?
   → YES  → HIGH_COMPLEX (or COMPLEX if reasoning is deep)
   → NO   → go to 2

2. Does it need deep reasoning (architecture, debug, optimize)?
   → YES  → COMPLEX
   → NO   → go to 3

3. Is it under 500 input tokens and 1K output?
   → YES  → FAST
   → NO   → NORMAL
```

**Examples:**

- "Fix this typo in the README" → FAST
- "Implement a login handler" → NORMAL
- "Design the auth microservices architecture" → COMPLEX
- "Refactor entire auth stack: design + code + tests + docs" → HIGH_COMPLEX

---

## Provider Selection (Routing Policy)

### Default: `prefer_direct`

For **FAST**: Haiku → Gemini → Cursor Composer → Sonnet
For **NORMAL**: Sonnet → MiniMax → GLM → Haiku
For **COMPLEX**: Opus → Cursor Opus Thinking → Sonnet (last resort)
For **HIGH_COMPLEX**: Opus ONLY (no fallback)

### Alternative: `prefer_proxy` (cost optimization)

Use if budget is tight:

- FAST: (same)
- NORMAL: MiniMax/GLM → Sonnet
- COMPLEX: Cursor Opus Thinking → Opus
- HIGH_COMPLEX: Not allowed (Opus mandatory)

### Alternative: `cheapest`

Sort by cost_weight, pick lowest:

- Best for: repeated queries, high volume
- Tradeoff: quality may drop, latency may increase
- Safe for: FAST and NORMAL only

---

## Cost Budgets & Limits

**Monthly ($500 typical):**
| Category | Budget | Calls/Month | $/Call |
|----------|--------|-------------|--------|
| FAST | $50 | 25,000 | $0.002 |
| NORMAL | $300 | 10,000 | $0.03 |
| COMPLEX | $125 | 800 | $0.15 |
| HIGH_COMPLEX | $25 | 30 | $0.85 |

**Enforcement:** If MTD > budget → all new runs DENIED (escalate to human queue)

---

## Governance Gates

### FAST & NORMAL

No special gates. Check cost budget.

### COMPLEX

1. If `lane=critical` → require `confidence >= 0.9`
2. If `confidence < 0.85` → warn (suggest review)
3. Cost budget check (same as all)

### HIGH_COMPLEX

1. **MANDATORY:** cost budget approval (> $0.25)
2. **MANDATORY:** `lane=critical` requires `confidence >= 0.9`
3. **MANDATORY:** contract drift < 5%
4. **LOCKED PROVIDER:** Opus 4.6 only, no fallback
5. If all gates fail → escalate to `EscalationQueue` (30 min SLA)

---

## RunMeta: New Fields to Track

```python
task_category: str | None  # "FAST", "NORMAL", "COMPLEX", "HIGH_COMPLEX"
tokens_in_estimated: int | None  # estimated input tokens
tokens_out_estimated: int | None  # estimated output tokens
reasoning_depth: int | None  # 0=none, 1=light, 2=moderate, 3=deep
route_decision: str | None  # trace: "prefer_direct > opus"
fallback_count: int = 0  # how many times did we fallback?
```

---

## Typical Flows (Copy-Paste)

### FAST Query

```bash
thegent run claude "Find the retry decorator in utils.py"
# Automatically routes to: haiku-4.5 (direct)
# Cost: ~$0.001
# Latency: ~500ms
```

### NORMAL Implementation

```bash
thegent run claude \
  "Implement auth handler with error handling and tests" \
  --confidence 0.80
# Automatically routes to: sonnet-4.5 (direct)
# Cost: ~$0.03–$0.05
# Latency: ~2–5s
```

### COMPLEX Design (Requires Approval)

```bash
thegent run claude \
  "Design the microservices architecture for our data pipeline" \
  --lane critical \
  --confidence 0.92
# Governance checks:
#   - lane=critical → confidence must be >= 0.9 ✓ (0.92 >= 0.9)
#   - cost budget check ✓
# Automatically routes to: opus-4.6 (direct)
# Cost: ~$0.15–$0.25
# Latency: ~5–15s
```

### HIGH_COMPLEX Feature (Requires Escalation)

```bash
thegent run claude \
  "Full-stack feature: implement auth + tests + docs + CI setup" \
  --lane critical \
  --confidence 0.93 \
  --override "feature-review-scheduled"
# Governance checks:
#   - lane=critical ✓
#   - confidence 0.93 >= 0.9 ✓
#   - contract drift < 5% ✓
#   - cost budget $25 > $0.85 estimate ✓
#   - override provided ✓
# Automatically routes to: opus-4.6 (LOCKED, no fallback)
# Cost: ~$0.80–$1.50
# Latency: ~30–60s (async, acceptable)
```

---

## Fallback Rules

If your provider is exhausted:

| Category     | Fallback Sequence                                 |
| ------------ | ------------------------------------------------- |
| FAST         | Haiku → Gemini → Composer → Sonnet → ERROR        |
| NORMAL       | Sonnet → MiniMax → GLM → Haiku → ESCALATE         |
| COMPLEX      | Opus → Cursor Opus → Sonnet → ESCALATE            |
| HIGH_COMPLEX | Opus → Cursor Opus → ESCALATE (no lower fallback) |

**ESCALATE** = add to `EscalationQueue`, notify on-call, block dispatch until human approves.

---

## Monitoring (What to Watch)

**Daily check:**

```bash
thegent observe routing-summary
# Shows:
#   - Task distribution (% FAST, NORMAL, COMPLEX, HIGH_COMPLEX)
#   - Cost spend by category
#   - Fallback frequency
#   - Provider performance (latency, quality)
#   - Escalation queue length
```

**Cost alert threshold:** When MTD > 80% of budget
**Fallback alert:** When fallback rate > 10% in 1 hour
**Quality alert:** When average feedback < 0.80

---

## Config Env Vars

```bash
# Task routing
export THGENT_ROUTE_POLICY=prefer_direct
export THGENT_FAST_PROVIDER=claude
export THGENT_NORMAL_PROVIDER=claude
export THGENT_COMPLEX_PROVIDER=claude
export THGENT_HIGH_COMPLEX_PROVIDER=claude

# Cost gates
export THGENT_COST_TRACKING_ENABLED=1
export THGENT_COST_BUDGET_MTD=500

# Confidence & trust
export THGENT_CRITICAL_LANE_MIN_CONFIDENCE=0.9
export THGENT_PRODUCTION_TRUST_THRESHOLD=0.8

# Circuit breakers
export THGENT_CIRCUIT_BREAKER_ENABLED=1
export THGENT_CIRCUIT_BREAKER_THRESHOLD=5
export THGENT_CIRCUIT_BREAKER_WINDOW_S=300

# Escalation SLA
export THGENT_ESCALATION_SLA_MINUTES=30
```

---

## Common Mistakes (Don't!)

✗ **Mistake 1:** Submit HIGH_COMPLEX without `--confidence`

```
→ Denied: "Critical lane requires confidence >= 0.9"
→ Fix: Add `--confidence 0.91`
```

✗ **Mistake 2:** Use Sonnet for a COMPLEX task

```
thegent run claude "Design the architecture" --model sonnet-4.5
→ Warning: COMPLEX category prefers Opus, not Sonnet
→ Result: Lower quality (feedback ~0.75 instead of ~0.95)
```

✗ **Mistake 3:** Rely on fallback for HIGH_COMPLEX

```
→ HIGH_COMPLEX has NO fallback chain
→ If Opus exhausted → ESCALATE (hard stop)
→ Fix: Ensure Opus quota is sufficient, or pre-request more
```

✗ **Mistake 4:** Ignore calibration factors

```
Agent submits: confidence 0.90
But historical calibration: 0.85 (underconfident)
Adjusted: 0.90 × 0.85 = 0.765
Critical lane requires 0.9 → DENIED
→ Fix: Recognize your historical calibration, adjust confidence higher
```

---

## Implementing TaskRouter

**File:** `src/thegent/routing/classifier.py` (new)

**Core functions to implement:**

```python
def classify_task(input: TaskClassificationInput) -> TaskCategory:
    """Classify task into FAST, NORMAL, COMPLEX, or HIGH_COMPLEX."""


def resolve_provider(
    category: TaskCategory, provider_hint: str | None = None, policy: RoutePolicy = "prefer_direct"
) -> tuple[str, str]:
    """Resolve category to (provider, model_alias)."""


def estimate_tokens_input(prompt: str) -> int:
    """Quick estimate of input tokens (1 token ≈ 4 chars)."""


def infer_reasoning_depth(prompt: str) -> int:
    """Infer reasoning depth 0–3 from prompt keywords."""
```

**Integration points:**

1. `PolicyEngine.evaluate()` — add task classification check before dispatch
2. `RunRegistry.register_start()` — populate `task_category`, `tokens_in_estimated`, etc.
3. `RunRegistry.register_end()` — log actual cost vs. estimated
4. CLI (`cli_impl.py`) — extract classification signals from command args

---

## Next Steps

1. Read full spec: `/docs/reference/TASK_ROUTING_DESIGN.md`
2. Implement `TaskRouter` in new module
3. Add fields to `RunMeta`
4. Integrate into `PolicyEngine`
5. Create metrics dashboard query
6. Test with sample prompts (FAST, NORMAL, COMPLEX, HIGH_COMPLEX)
7. Monitor fallback rates for 1 week
8. Tune category thresholds based on real token distributions

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
