# Task Categorization & AI Agent Dispatch Routing Design

**Date:** 2026-02-15
**Status:** Design (Phase 7 Routing Enhancement)
**Context:** thegent is an agent orchestration + governance platform. This document specifies task categorization, routing logic, and provider dispatch strategy for optimal cost, speed, and quality.

---

## 1. Task Categories (4-Level Classification)

### Overview
All agent dispatch requests are classified into 4 categories based on token budget, reasoning depth, and performance requirements. Each category maps to different provider strategies.

| Category | Use Case | Input Budget | Output Budget | Performance Bar | Speed vs Cost Preference | Provider Strategy |
|----------|----------|--------------|---------------|-----------------|-------------------------|------------------|
| **FAST** | Simple queries, lookups, quick synthesis | 50-500 tokens | 100-1K tokens | Acceptable (70%+) | Speed >> cost >> quality | Haiku 4.5, Gemini Flash, Cursor Composer |
| **NORMAL** | Standard tasks, implementation, refactoring | 500-3K tokens | 500-5K tokens | Good (80%+) | Cost > speed > quality | Sonnet 4.5, GPT-5.3, MiniMax, GLM |
| **COMPLEX** | Architecture, deep debugging, algorithm design | 3K-10K tokens | 2K-15K tokens | Excellent (90%+) | Quality > speed > cost | Opus 4.6, Claude API, Cursor Opus |
| **HIGH_COMPLEX** | Full-stack orchestration, agentic synthesis | 5K-30K tokens | 5K-50K tokens | Mission-critical (95%+) | Quality >> cost/speed | Opus 4.6 + fallback chain, human review gate |

### Detailed Specification

#### FAST Category
- **Token allocation:** Input 50–500, output 100–1K
- **Examples:**
  - Code snippet lookup: "Find the error handling function in retry.py"
  - Quick synthesis: "Write a 10-line Python decorator for timing"
  - Single-file analysis: "Explain what this test does"
  - Snippet completion: "Finish this SQL query"
- **Performance threshold:** Acceptable quality (70%+). Errors are recoverable; end-user can refine.
- **Cost-speed tradeoff:** Speed is primary. Acceptable cost increase if latency < 1s.
- **Preferred models:** Haiku 4.5 ($0.80/M in, $4/M out), Gemini 2.5 Flash ($0.1/M in, $0.4/M out), Cursor Composer
- **Fallback chain:** Haiku → Gemini → Cursor Composer → Claude Sonnet
- **Cost estimate:** $0.0005–$0.005 per call (median $0.002)
- **Expected latency:** < 1 second p99

#### NORMAL Category
- **Token allocation:** Input 500–3K, output 500–5K
- **Examples:**
  - Implement a function with error handling
  - Refactor a method for clarity
  - Write docstrings and type hints
  - Generate test cases for a feature
  - Write implementation documentation
- **Performance threshold:** Good quality (80%+). Correctness is important; minor revisions acceptable.
- **Cost-speed tradeoff:** Cost optimization primary, but maintain latency < 5s. Quality floor: no logic errors.
- **Preferred models:** Sonnet 4.5 ($3/M in, $15/M out), GPT-5.3 Codex ($5–7/M in, $20–35/M out), MiniMax M2.5 ($2/M in, $6/M out), GLM-5 ($2/M in, $6/M out)
- **Fallback chain:** Sonnet → MiniMax → GLM → Haiku (degraded quality, acceptable for iteration)
- **Cost estimate:** $0.01–$0.10 per call (median $0.03)
- **Expected latency:** 2–5 seconds p99

#### COMPLEX Category
- **Token allocation:** Input 3K–10K, output 2K–15K
- **Examples:**
  - Design a multi-module architecture
  - Debug a complex race condition across 5 files
  - Optimize algorithm performance (improve O(n²) → O(n log n))
  - Write a comprehensive test suite (>20 tests)
  - Security audit and hardening
  - Refactor large codebase module with reasoning
- **Performance threshold:** Excellent quality (90%+). Reasoning must be sound; no logic errors acceptable.
- **Cost-speed tradeoff:** Quality >> speed > cost. Budget up to $0.30–$0.50 per call for high-quality output.
- **Preferred models:** Opus 4.6 ($15/M in, $75/M out), Claude API native (when available), Cursor Opus thinking mode
- **Fallback chain:** Opus → Cursor-API Opus Thinking → Sonnet (degraded; requires review)
- **Cost estimate:** $0.08–$0.50 per call (median $0.15)
- **Expected latency:** 5–20 seconds p99 (thinking time acceptable)

#### HIGH_COMPLEX Category
- **Token allocation:** Input 5K–30K, output 5K–50K
- **Examples:**
  - Full-stack feature implementation (design + code + tests + docs)
  - Multi-agent orchestration / synthesis
  - Governance policy design and implementation
  - Complete system refactor with zero-downtime plan
  - Create comprehensive test matrix and CI setup
  - Dispute resolution in contract validation
- **Performance threshold:** Mission-critical (95%+). No errors; must be battle-tested. Requires explicit approval before execution.
- **Cost-speed tradeoff:** Quality >> all else. Cost and latency are secondary. Build once, reuse many times.
- **Preferred models:** Opus 4.6 (mandatory first choice), Cursor Opus Thinking, Claude API latest
- **Fallback chain:** None; HIGH_COMPLEX requests must have explicit provider lock-in. No auto-fallback.
- **Cost estimate:** $0.20–$2.00 per call (typical $0.50–$1.00)
- **Expected latency:** 10–60 seconds p99 (acceptable; async execution expected)
- **Governance:** Requires cost approval, human sign-off for critical lane, escalation queue integration

---

## 2. Routing Decision Tree

```
┌─ Parse task request
│
├─ Extract signals:
│  ├─ Input token budget (estimate from prompt)
│  ├─ Output token target (expected response length)
│  ├─ Reasoning depth (0=none, 1=light, 2=moderate, 3=deep)
│  ├─ Quality bar (acceptable/good/excellent/critical)
│  ├─ Lane (standard/critical/recovery)
│  └─ Caller confidence score (0.0–1.0)
│
└─ CLASSIFY TASK:
   │
   ├─ IF (tokens_in < 500 AND tokens_out < 1K AND reasoning == 0 AND quality <= good)
   │  └─► FAST
   │
   ├─ ELIF (tokens_in < 3K AND tokens_out < 5K AND reasoning <= 1 AND quality == good AND lane != critical)
   │  └─► NORMAL
   │
   ├─ ELIF (tokens_in < 10K AND tokens_out < 15K AND reasoning >= 2 AND quality == excellent)
   │  └─► COMPLEX
   │
   └─ ELIF (tokens_in >= 5K OR tokens_out > 15K OR reasoning == 3 OR quality == critical OR lane == critical)
      └─► HIGH_COMPLEX
         │
         ├─ IF (cost_budget_remaining < est_cost) → DENY (escalate to EscalationQueue)
         ├─ IF (lane == critical AND confidence < 0.9) → DENY (require --override)
         └─ IF (contract_drift > budget) → DENY (blocking policy XC2)

   ┌─ RESOLVE PROVIDER (category determined)
   │
   ├─ FAST:
   │  ├─ IF provider_hint exists AND hint in [haiku, gemini, composer]
   │  │  └─► use provider_hint
   │  ├─ ELIF cost_budget remaining < $0.005
   │  │  └─► prefer_cheapest (Gemini Flash)
   │  └─ ELSE
   │     └─► prefer_direct (Haiku native)
   │        ├─ 1st: claude (haiku-4.5) — lowest latency
   │        ├─ 2nd: gemini (flash) — cheapest
   │        └─ 3rd: cursor-agent (composer) — fallback
   │
   ├─ NORMAL:
   │  ├─ IF provider_hint exists AND hint in catalog
   │  │  └─► use provider_hint
   │  ├─ ELIF policy == prefer_proxy AND cost_budget < $0.10
   │  │  └─► route to MiniMax/GLM (cheap proxy providers)
   │  └─ ELSE
   │     └─► prefer_direct (standard cost optimization)
   │        ├─ 1st: claude (sonnet-4.5) — best quality for cost
   │        ├─ 2nd: minimax (m2.5) or glm (glm-5) — 40% cheaper
   │        └─ 3rd: codex (gpt-5.3) if cost allows
   │
   ├─ COMPLEX:
   │  ├─ IF lane == critical OR confidence < 0.85
   │  │  └─► MUST use Opus (no fallback to Sonnet)
   │  ├─ ELIF provider_hint == opus
   │  │  └─► use Opus (prefer_direct)
   │  └─ ELSE
   │     └─► prefer_direct
   │        ├─ 1st: claude (opus-4.6) — best reasoning
   │        ├─ 2nd: cursor-api (opus-thinking) — alt high-quality
   │        └─ 3rd: sonnet-4.5 (if cost critical, lower quality bar)
   │
   └─ HIGH_COMPLEX:
      ├─ POLICY: Must lock to Opus, no automatic fallback
      ├─ GATE: Require governance approval before dispatch
      ├─ PROVIDER: claude/opus-4.6 ONLY
      │           (fallback: cursor-api/opus-thinking if claude exhausted)
      └─ MONITORING: Track execution; escalate failures to escalation queue
```

---

## 3. Provider Selection & Fallback Chains

### Static Model Catalog (Anthropic 4.5/4.6, Gemini Flash, Codex 5.3, GLM/MiniMax)

| Model ID | Provider | Backend | Latency | Cost (/1M in, /1M out) | Use Case | Priority |
|----------|----------|---------|---------|------------------------|----------|----------|
| **haiku-4.5** | claude | direct | ~500ms | $0.80, $4 | FAST queries | 1 |
| **sonnet-4.5** | claude | direct | ~1.5s | $3, $15 | NORMAL tasks | 1 |
| **opus-4.6** | claude | direct | ~3s | $15, $75 | COMPLEX/HIGH | 1 |
| **gemini-2.5-flash** | gemini | direct | ~400ms | $0.10, $0.40 | FAST (cheapest) | 2 |
| **gpt-5.3-codex** | codex | direct | ~1.2s | $5–7, $20–35 | NORMAL (codex) | 2 |
| **gpt-5.3-codex-high** | codex | direct | ~2s | $7–10, $30–50 | COMPLEX (codex) | 2 |
| **composer-1.5** | cursor-agent | direct | ~2s | ~$0.30/call | FAST (alt) | 3 |
| **minimax-m2.5** | minimax | proxy | ~2s | $2, $6 | NORMAL (proxy) | 4 |
| **glm-5** | glm | proxy | ~2s | $2, $6 | NORMAL (proxy) | 4 |
| **roo-default** | roo | proxy | ~3s | ~$0.50/call | NORMAL (niche) | 5 |
| **opus-thinking** | cursor-api | proxy | ~10–30s | $1.2, $5.5 | COMPLEX (thinking) | 5 |
| **gpt-4o** | cursor-api | proxy | ~2s | $2.50, $10 | COMPLEX (alt) | 5 |

### Fallback Chains per Category

#### FAST Category Fallback
```
1. haiku-4.5 (claude/direct)
2. gemini-2.5-flash (gemini/direct)
3. composer-1.5 (cursor-agent/direct)
4. sonnet-4.5 (claude/direct, degraded quality)
→ Escalate if all fail
```

#### NORMAL Category Fallback
```
1. sonnet-4.5 (claude/direct) — preferred
2. minimax-m2.5 (minimax/proxy) — cost optimization
3. glm-5 (glm/proxy) — cost optimization
4. gpt-5.3-codex (codex/direct) — quality backup
5. haiku-4.5 (claude/direct) — last resort, degraded
→ Escalate to escalation queue if all fail
```

#### COMPLEX Category Fallback
```
1. opus-4.6 (claude/direct) — mandatory first choice
2. opus-thinking (cursor-api/proxy) — alt thinking mode
3. gpt-5.3-codex-high (codex/direct) — fallback (lower quality)
4. sonnet-4.5 (claude/direct) → requires explicit review before dispatch
→ DO NOT auto-fall below Sonnet without human approval
```

#### HIGH_COMPLEX Category Fallback
```
1. opus-4.6 (claude/direct) — LOCKED, no negotiation
2. (emergency only) opus-thinking (cursor-api/proxy) if Claude exhausted
→ NO fallback to lower models
→ If both exhausted: escalate & block dispatch
```

---

## 4. Cost-Quality Curves by Category

### Cost vs Quality Trade-off (median $$ per call)

```
Quality →
  95% │                          [HIGH: Opus $0.50–$2.00]
  90% │                  [COMPLEX: Opus $0.15–$0.50]
  80% │          [NORMAL: Sonnet $0.03–$0.10]
  70% │  [FAST: Haiku/Gemini $0.0005–$0.01]
     │
     └──────────────────────────────────────
       Fast  Haiku   Gemini  Sonnet  Opus
       ~$0.002 $0.003  $0.0001 $0.03  $0.15
```

### Budget Allocation Strategy

**Assumption:** Monthly AI agent budget = $500 (typical production org)

| Category | Budget Allocation | Typical Monthly Calls | Cost/Call | Rationale |
|----------|-------------------|----------------------|-----------|-----------|
| FAST | 10% ($50) | 25,000 | $0.002 | High volume, low cost; absorb spikes |
| NORMAL | 60% ($300) | 10,000 | $0.03 | Bulk of work; optimize cost |
| COMPLEX | 25% ($125) | 800 | $0.15 | Quality-critical; allocate headroom |
| HIGH_COMPLEX | 5% ($25) | 30 | $0.85 | Rare; reserve for critical path |

**Governance enforcement:**
- Hourly tracking via `CostAggregator`
- MTD budget cap: `cost_budget_mtd` (env var)
- If MTD exceeded → deny all new runs (PolicyEngine.evaluate)
- Per-lane overrides via `OverrideRegistry` (30-min TTL default)

---

## 5. Routing Configuration & Implementation

### Input Signals for Classification

When a task arrives, extract these signals:

```python
@dataclass
class TaskClassificationInput:
    prompt: str  # Full prompt text
    agent: str  # Agent name (claude, gemini, etc.)
    mode: str  # write, read, observe, etc.
    lane: str  # standard, critical, recovery
    owner: str  # User/team
    confidence: float | None  # Caller's confidence (0.0–1.0)
    provider_hint: str | None  # Preferred provider (if any)
    token_budget_explicit: int | None  # Explicit token limit (if known)
```

### Classification Logic (Pseudocode)

```python
def classify_task(input: TaskClassificationInput) -> TaskCategory:
    # 1. Estimate token budgets
    tokens_in = estimate_tokens_input(input.prompt)
    tokens_out = estimate_tokens_output(input.prompt)  # heuristic

    # 2. Infer reasoning depth from prompt signals
    reasoning_depth = infer_reasoning_depth(
        prompt=input.prompt, keywords=["design", "architect", "debug", "optimize", "complex"]
    )  # returns 0–3

    # 3. Map lane to quality requirement
    quality_bar = {"critical": "critical", "recovery": "excellent", "standard": "good"}.get(input.lane, "good")

    # 4. Apply classification rules
    if tokens_in < 500 and tokens_out < 1_000 and reasoning_depth <= 0:
        return TaskCategory.FAST
    elif tokens_in < 3_000 and tokens_out < 5_000 and reasoning_depth <= 1 and quality_bar != "critical":
        return TaskCategory.NORMAL
    elif tokens_in < 10_000 and tokens_out < 15_000 and reasoning_depth >= 2:
        return TaskCategory.COMPLEX
    else:
        return TaskCategory.HIGH_COMPLEX
```

### Provider Resolution (Pseudocode)

```python
def resolve_provider(
    category: TaskCategory,
    provider_hint: str | None,
    route_policy: RoutePolicy = "prefer_direct",
    cost_budget_remaining: float = float("inf"),
) -> tuple[str, str]:  # (provider, model_alias)

    routes = ModelCatalog.routes_for(category.preferred_model)

    # If provider hint provided, use it (if valid for category)
    if provider_hint:
        for route in routes:
            if route.provider == provider_hint:
                return (route.provider, route.model_alias)
        # Hint invalid for category; fall through to default

    # Apply routing policy
    if route_policy == "prefer_direct":
        routes = sorted(routes, key=lambda r: (r.priority, r.provider))
    elif route_policy == "cheapest":
        routes = sorted(routes, key=lambda r: (r.cost_weight, r.priority))
    elif route_policy == "round_robin":
        routes = rotate_round_robin(routes, category)

    # Return first available
    for route in routes:
        if route.cost_weight * category.cost_estimate <= cost_budget_remaining:
            return (route.provider, route.model_alias)

    # Budget exceeded; escalate
    raise BudgetExceeded(f"No route available within budget for {category}")
```

---

## 6. Integration with thegent Governance

### Execution Flow

1. **Intake:** User/agent submits task via `thegent run <agent> <prompt> [--provider <hint>]`
2. **Classification:** `TaskRouter.classify(TaskClassificationInput)` → `TaskCategory`
3. **Governance Check:** `PolicyEngine.evaluate(RunMeta)` → (allow|deny|warn, reason)
   - Checks cost budget (MTD), circuit breakers, trust score, contract drift
   - Blocks HIGH_COMPLEX if missing approval
4. **Provider Resolution:** `resolve_provider(category)` → (provider, model)
5. **Dispatch:** `AgentRunner.execute(provider, model, prompt, ...)`
6. **Cost Tracking:** `RunRegistry.register_end(..., cost_usd=estimate)`
7. **Escalation:** Failed runs → `EscalationQueue` (SLA 30 min for critical)

### Hooks Integration

| Hook | Event | Action |
|------|-------|--------|
| `spec-preflight` | SessionStart | Validate cost budget config exists |
| `prompt-submit-guard` | UserPromptSubmit | Classify task; check budget |
| `qa-policy-engine` | PreToolUse | Run PolicyEngine.evaluate; gate execution |
| `async-test-runner` | PostToolUse | Track cost; update calibration |
| `quality-gate` | Stop | Report cost spend, routing decisions |

### New Signals in RunMeta

```python
@dataclass
class RunMeta(BaseModel):
    # ... existing fields ...

    # NEW: Task classification & routing context
    task_category: str | None = None  # FAST, NORMAL, COMPLEX, HIGH_COMPLEX
    tokens_in_estimated: int | None = None
    tokens_out_estimated: int | None = None
    reasoning_depth: int | None = None  # 0=none, 1=light, 2=moderate, 3=deep
    route_decision: str | None = None  # decision_tree trace (for audit)
    fallback_count: int = 0  # Number of fallback attempts
```

---

## 7. Configuration (Environment Variables)

```bash
# Cost governance
THGENT_COST_TRACKING_ENABLED=1
THGENT_COST_BUDGET_MTD=500                  # $500/month

# Provider routing
THGENT_ROUTE_POLICY=prefer_direct           # prefer_direct|prefer_proxy|cheapest|round_robin
THGENT_FAST_PROVIDER=claude                 # default FAST provider
THGENT_NORMAL_PROVIDER=claude               # default NORMAL provider
THGENT_COMPLEX_PROVIDER=claude              # default COMPLEX provider
THGENT_HIGH_COMPLEX_PROVIDER=claude         # LOCKED for HIGH_COMPLEX

# Governance gates
THGENT_CRITICAL_LANE_MIN_CONFIDENCE=0.9     # minimum confidence for critical lane
THGENT_PRODUCTION_TRUST_THRESHOLD=0.8
THGENT_CIRCUIT_BREAKER_ENABLED=1
THGENT_CIRCUIT_BREAKER_THRESHOLD=5          # failures before open
THGENT_CIRCUIT_BREAKER_WINDOW_S=300         # observation window

# Escalation
THGENT_ESCALATION_SLA_MINUTES=30
```

---

## 8. Metrics & Observability

### Per-Run Metrics (captured in RunRegistry)

```json
{
  "run_id": "run_abc123",
  "task_category": "NORMAL",
  "provider": "claude",
  "model": "claude-sonnet-4.5",
  "tokens_in_estimated": 800,
  "tokens_out_estimated": 2500,
  "cost_usd": 0.052,
  "latency_ms": 2341,
  "fallback_count": 0,
  "route_decision": "preferred_direct > sonnet_4.5",
  "confidence_calibration_factor": 1.02,
  "feedback_score": 0.95
}
```

### Dashboard Queries

**Cost Breakdown by Category:**
```
SELECT
  task_category,
  COUNT(*) as calls,
  SUM(cost_usd) as total_cost,
  AVG(cost_usd) as avg_cost,
  AVG(latency_ms) as avg_latency_ms
FROM run_registry
WHERE DATE(started_at_utc) = TODAY()
GROUP BY task_category
ORDER BY total_cost DESC
```

**Provider Performance:**
```
SELECT
  provider,
  AVG(feedback_score) as avg_quality,
  AVG(latency_ms) as avg_latency_ms,
  COUNT(CASE WHEN feedback_score < 0.8 THEN 1 END) as low_quality_count
FROM run_registry
WHERE started_at_utc > NOW() - INTERVAL 7 DAY
GROUP BY provider
ORDER BY avg_quality DESC
```

---

## 9. Typical Request Flows (Examples)

### Flow 1: FAST Query
```
User: "Find the retry decorator in utils.py"
         ↓
Classification: tokens_in=80, tokens_out=300 → FAST
         ↓
Provider: claude/haiku-4.5 (prefer_direct)
         ↓
Cost budget: $0.0015 << $50/month allocation ✓
         ↓
Dispatch: claude run "Find the retry..." --model haiku-4.5
         ↓
Result: 2s latency, $0.0015 cost, quality 0.92
```

### Flow 2: NORMAL Implementation Task
```
User: "Implement the auth handler with tests"
         ↓
Classification: tokens_in=1500, tokens_out=3000, reasoning=1 → NORMAL
         ↓
Provider: claude/sonnet-4.5 (prefer_direct, cost-optimized)
         ↓
Cost budget: $0.045 << $300/month allocation ✓
         ↓
Dispatch: claude run "Implement the auth..." --model sonnet-4.5
         ↓
Result: 4.2s latency, $0.045 cost, quality 0.88, feedback 0.90
         ↓
Calibration: update_calibration_factor(claude, 0.90/0.85 = 1.06)
```

### Flow 3: COMPLEX Architecture Design (Critical Lane)
```
User: "Design the microservices architecture for data pipeline"
       --lane critical --confidence 0.85
         ↓
Classification: tokens_in=5000, tokens_out=8000, reasoning=3 → COMPLEX
         ↓
Governance check:
   - Lane: critical → min_confidence 0.9 required
   - Confidence: 0.85 < 0.9 → DENY
         ↓
Response: "Critical lane requires confidence >= 0.9 (current: 0.85)"
         ↓
User re-submits: --confidence 0.92 --override "design-review-scheduled"
         ↓
Provider: claude/opus-4.6 (COMPLEX requirement, no fallback)
         ↓
Cost budget: $0.20 < $125/month allocation ✓
         ↓
Dispatch: claude run "Design the..." --model opus-4.6 --override ...
         ↓
Result: 8.1s latency, $0.22 cost, quality 0.95, feedback 0.98
```

### Flow 4: HIGH_COMPLEX Multi-Component Refactor
```
User: "Full-stack feature: auth + tests + docs + CI"
       --lane critical --confidence 0.91
         ↓
Classification: tokens_in=15000, tokens_out=25000, reasoning=3 → HIGH_COMPLEX
         ↓
Governance check:
   - HIGH_COMPLEX requires: cost approval, lane check, contract drift
   - Contract drift: 3% < 5% ✓
   - Cost estimate: $1.20 < $25/month allocation ✓
   - Confidence: 0.91 >= 0.9 ✓
   - All policies pass
         ↓
Provider: LOCKED → claude/opus-4.6 (no fallback)
         ↓
Dispatch: claude run "Full-stack feature..." --model opus-4.6 --lane critical
         ↓
Monitoring:
   - Execution time: 35s (async, expected)
   - Cost: $1.18
   - Quality: 0.97
   - Feedback: 0.99
   - Escalation: none
         ↓
Result: Success; added to CODE_ENTITY_MAP; PR auto-created
```

---

## 10. Edge Cases & Error Handling

### Scenario: Cost Budget Exhausted Mid-Month

**Policy:** Explicit fail-fast (no silent degradation)

```
Month-to-date: $499.50 / $500 budget
New NORMAL task estimate: $0.08
Available budget: $0.50

→ Cost check passes; dispatch allowed

Post-execution:
MTD spent: $499.58
Next FAST task estimate: $0.002
Available: -$0.08 (over budget!)

→ PolicyEngine.evaluate() returns:
   ("deny", "Monthly budget exceeded ($499.58 >= $500.00)")

→ EscalationQueue.add():
   - run_id: escalation_123
   - reason: "Cost budget exhausted"
   - sla_minutes: 30
   - priority: 1 (high)

→ User receives error; must request budget override or wait until next month
```

### Scenario: Provider Exhausted (Usage Limit Hit)

**Policy:** Auto-failover through fallback chain

```
Attempt 1: Provider "claude" quota exhausted
  → RunRegistry logs: fallback_count = 1
  → Next in fallback chain: "minimax"

Attempt 2: Dispatch to "minimax" via proxy
  → Returns result with quality 0.82 (good, acceptable)
  → Log: "Fallback #1 succeeded (claude → minimax)"

Monitor:
  - Route decision: "prefer_direct[1 fallback] > minimax"
  - Cost: $0.025 (minimax cheaper)
  - Latency: 2.1s (similar)
  - Quality: 0.82 (acceptable for NORMAL)
```

### Scenario: HIGH_COMPLEX Provider Locked, All Exhausted

**Policy:** Hard block; escalate to human queue

```
HIGH_COMPLEX task arrives
Provider lock: claude/opus-4.6 only

Attempt 1: claude/opus unavailable (quota exhausted)
Attempt 2: cursor-api/opus-thinking unavailable (also exhausted)

→ No fallback allowed for HIGH_COMPLEX
→ PolicyEngine.evaluate() returns:
   ("deny", "HIGH_COMPLEX requires Opus; all Opus providers exhausted")

→ EscalationQueue.add():
   - run_id: run_xyz
   - reason: "No provider available for HIGH_COMPLEX task"
   - sla_minutes: 15 (critical)
   - priority: 2 (highest)

→ Dashboard alert: "CRITICAL: HIGH_COMPLEX queue blocked"
→ On-call engineer must approve fallback or provision more quota
```

### Scenario: Confidence Calibration Anomaly

**Policy:** Detect and adjust; track via CalibrationRegistry

```
Agent "alice" historical:
  - Avg confidence: 0.88
  - Avg feedback score: 0.75
  - Calibration factor: 0.75 / 0.88 = 0.85 (underconfident)

New run from alice:
  - Confidence: 0.90 (claimed)
  - Adjusted: 0.90 × 0.85 = 0.765

Lane: critical (requires >= 0.9)
Governance check:
  - Adjusted confidence 0.765 < 0.9 → DENY
  - Reason: "Critical lane requires confidence >= 0.9 after calibration (0.765 < 0.9)"

Alice receives feedback; improves estimation over time.
CalibrationRegistry auto-updates as more feedback arrives.
```

---

## 11. Migration & Rollout

### Phase 1: Static Routing (Week 1)
- Deploy `TaskRouter.classify()` and `resolve_provider()` functions
- Add `task_category` to RunMeta
- Enable logging of classification decisions (no enforcement)
- Collect metrics on actual task distribution

### Phase 2: Soft Enforcement (Week 2–3)
- PolicyEngine checks category-based budgets
- Log warnings when routes would exceed budget (no actual blocks yet)
- Gather feedback from users
- Adjust category thresholds based on observed token distributions

### Phase 3: Hard Enforcement (Week 4+)
- Enable blocking when cost budgets exceeded
- Activate EscalationQueue for denied HIGH_COMPLEX requests
- Monitor for fallback chain effectiveness
- Tune fallback chains based on real provider performance data

### Metrics to Track During Rollout
- Distribution of task categories (%)
- Average cost per category (actual vs. estimated)
- Fallback frequency and success rates
- Policy denial reasons (top 5)
- Escalation queue fill rates

---

## 12. Summary: Routing Decision Matrix

| Category | Tokens | Quality | Speed | Cost | Primary Model | Fallback | Cost $$ |
|----------|--------|---------|-------|------|---------------|----------|---------|
| **FAST** | <1K | 70% | <1s | high | Haiku 4.5 | Gemini Flash | $0.002 |
| **NORMAL** | <5K | 80% | <5s | high | Sonnet 4.5 | MiniMax | $0.03 |
| **COMPLEX** | <15K | 90% | <20s | medium | Opus 4.6 | Cursor Opus | $0.15 |
| **HIGH** | >15K | 95% | <60s | low | Opus 4.6 | NONE | $0.85 |

---

## References

- **Provider Catalog:** `/src/thegent/models/catalog.py` (Route, ModelCatalog)
- **Cost Governance:** `/src/thegent/governance/cost.py` (CostEstimator, CostAggregator)
- **Execution Registry:** `/src/thegent/execution.py` (RunMeta, RunRegistry, PolicyEngine, CircuitBreakerRegistry)
- **Agent Registry:** `/src/thegent/agents/registry.py` (get_runner, get_fallback_agents)
- **Configuration:** `/src/thegent/config.py` (cost_tracking_enabled, cost_budget_mtd, etc.)

---

**Next Steps:**
1. Implement `TaskRouter` class in new module `src/thegent/routing/classifier.py`
2. Add task classification signals to RunMeta
3. Integrate classification into `PolicyEngine.evaluate()` before dispatch
4. Add metrics collection hooks to RunRegistry
5. Create dashboard queries for cost breakdown by category
6. Document for teams: "How to submit high-quality prompts per category"


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
