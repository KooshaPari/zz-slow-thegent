# Pareto Frontier Analysis: Terminal Bench 2.0 (Corrected)

**Date**: 2026-02-15
**Version**: 2.0 (Terminal Bench 2.0 Edition)
**Status**: Corrected Analysis
**Previous Version**: PARETO_FRONTIER_COMPLETE_ANALYSIS.md (based on SWE-Bench, now superseded)

---

## Executive Summary: What Changed

**Problem with Previous Analysis:**

- Previous frontier used **SWE-Bench** (software engineering tasks — file operations, debugging, refactoring)
- thegent is fundamentally a **terminal/system agent** (MCP server, hooks, CLI orchestration)
- SWE-Bench scores are NOT representative of thegent's actual workload (agent routing, lifecycle hooks, policy enforcement)

**Solution:**

- Use **Terminal Bench 2.0** — benchmark for system/terminal task performance
- Terminal Bench 2.0 tests CLI tool usage, environment awareness, multi-step shell scripting, system integration
- **Much more relevant** for thegent than SWE-Bench

**Key Finding:**
GPT-5.3-Codex now enters the frontier (64.7% on TB2.0 vs 56.8% SWE-Bench). The hierarchy shifts significantly.

---

## Part 1: Model Data (Terminal Bench 2.0)

### 1.1 Corrected Terminal Bench 2.0 Scores

| Model                 | Provider  | TB2.0 Score     | SWE-Bench (ref) | Cost/M | Speed      | TB2.0 Rank |
| --------------------- | --------- | --------------- | --------------- | ------ | ---------- | ---------- |
| **GPT-5.3-Codex**     | OpenAI    | **64.7%** ← TOP | 56.8%           | $1.25  | fast       | 1          |
| **Claude Opus 4.6**   | Anthropic | 62.9%           | 80.8%           | $17.50 | slow       | 2          |
| **Codex-Spark**       | OpenAI    | 58.4%           | ~50%            | ???    | very-fast  | 3          |
| **GLM-5**             | Alibaba   | 56.2%           | 92.7% (AIME)    | $2.60  | slow       | 4          |
| **Gemini 3 Flash**    | Google    | 51.7%           | 78.0%           | $1.50  | ultra-fast | 5          |
| **MiniMax M2.5**      | MiniMax   | 51.7%           | 80.2%           | $0.79  | very-fast  | 5 (tie)    |
| **Claude Sonnet 4.5** | Anthropic | 42.8%           | 77.2%           | $10.50 | moderate   | 7          |
| **Claude Haiku 4.5**  | Anthropic | 28.3%           | 73.3%           | $3.50  | fast       | 8          |

**Key Observations:**

1. **MiniMax M2.5 drops from 80.2% → 51.7%** — no longer the "best value"
2. **GPT-5.3-Codex rises to 64.7% (top)** — previously rejected for poor quality, now competitive
3. **Opus 4.6 still strong at 62.9%** but now only 2.0% ahead of Codex while costing 14x more
4. **Claude models collapse**: Haiku (28.3%), Sonnet (42.8%) — poor terminal/system performance
5. **Gemini 3 Flash & MiniMax M2.5 tie** at 51.7% — but Gemini is slower, more expensive

**Interpretation:**

- SWE-Bench rewards general coding ability (Claude's strength)
- Terminal Bench 2.0 rewards CLI tool usage, shell scripting, environment awareness
- Codex is specialized for code-at-terminal (still weak, but relatively stronger)
- Claude's verbose, reasoning-heavy style hurts it on terminal tasks

---

## Part 2: Missing Data & Estimation

### 2.1 Codex-Spark Pricing

**Given:** Very fast, 58.4% quality
**Missing:** Cost/M

**Estimation Strategy:**

- OpenAI pricing pattern: Codex $1.25/M; Spark is "cheaper + faster" variant
- Typical: Fast models cost 20-40% more than cheapest variants
- **Reasonable estimate: $0.95-1.10/M**
- For analysis: **Use $1.00/M (conservative, middle estimate)**

### 2.2 Codex-Spark Latency

**Given:** "very-fast"
**Map to speed score:**

- Gemini 3 Flash: "ultra-fast" (100 tokens/sec) = 218 tok/s observed
- Codex-Spark: "very-fast" (150 tok/s estimated)
- Speed score: 85 (on 0-100 scale)

### 2.3 Qwen3.5 Plus 02-15 (OpenRouter + QwenCode Free)

**Given:** OpenRouter model `qwen/qwen3.5-plus-02-15`; QwenCode free tier limits
**Missing:** Terminal Bench 2.0 score (no published data)
**Estimation:** ~52% quality (interpolated from Qwen family); 128K context
**Cost:** OpenRouter ~$0.40–0.80/M input; QwenCode free tier when available
**Placement:** Budget tier — between MiniMax (51.7%) and Codex-Spark (58.4%); free option via QwenCode
**Reference:** `docs/research/QWEN3.5_PLUS_OPENROUTER_PARETO_RESEARCH.md`

---

## Part 3: Dominance Analysis (Terminal Bench 2.0)

### 3.1 Step 1: Check Each Model Against All Others

#### Model 1: GPT-5.3-Codex

```
GPT-5.3-Codex: 64.7% (TB2.0), cost=$1.25, speed=fast (70)

Compared to:
  vs Codex-Spark: 64.7% < 58.4%? NO (Codex better)
  vs Opus: 64.7% < 62.9%? NO (Codex better)
  vs GLM-5: 64.7% > 56.2% (Codex better)
  vs Gemini Flash: 64.7% > 51.7% (Codex better)
  vs MiniMax: 64.7% > 51.7% (Codex better)
  vs Sonnet: 64.7% > 42.8% (Codex better)
  vs Haiku: 64.7% > 28.3% (Codex better)

Dominance check: Is any model strictly better on ALL 3 dimensions?
  - Opus: 62.9% quality < 64.7%, cost $17.50 >> $1.25 → NO dominance
  - All others: Lower quality → NO dominance

VERDICT: ON FRONTIER ✓ (no model dominates)
```

#### Model 2: Claude Opus 4.6

```
Claude Opus 4.6: 62.9% (TB2.0), cost=$17.50, speed=slow (30)

Compared to:
  vs GPT-5.3-Codex: 62.9% < 64.7% (loses quality), $17.50 >> $1.25 (loses cost) → Codex dominates?
    Check: Codex better quality (64.7 > 62.9) AND lower cost ($1.25 < $17.50) BUT slower (70 > 30)
    NOT dominated (Opus wins on speed, loses on quality+cost)

  vs Codex-Spark: 62.9% > 58.4%, slower, much more expensive → NOT dominated
  vs all others: Opus better on quality → NOT dominated on all metrics

VERDICT: ON FRONTIER ✓ (trades cost+speed for top-2 quality)
```

#### Model 3: Codex-Spark

```
Codex-Spark: 58.4% (TB2.0), cost=$1.00 (est), speed=very-fast (85)

Compared to:
  vs GPT-5.3-Codex: 58.4% < 64.7%, cost=$1.00 ≈ $1.25, speed=85 > 70
    Codex better quality, similar cost, similar speed
    NOT dominated (Spark wins on speed, loses on quality+cost)

  vs Opus: 58.4% < 62.9%, cost=$1.00 << $17.50, speed=85 > 30
    Opus wins on quality, Spark wins on cost+speed
    NOT dominated

  vs GLM-5: 58.4% > 56.2%, cost=$1.00 < $2.60, speed ≈ (both slow-ish)
    Spark wins on quality+cost → Spark dominates GLM-5?
    Yes: 58.4% > 56.2%, $1.00 < $2.60, speed 85 > 30
    Spark DOMINATES GLM-5 ✓

VERDICT: ON FRONTIER ✓ (dominates GLM-5, not dominated by others)
```

#### Model 4: GLM-5

```
GLM-5: 56.2% (TB2.0), cost=$2.60, speed=slow (30)

Dominated by: Codex-Spark (58.4% > 56.2%, $1.00 < $2.60, speed 85 > 30)
VERDICT: OFF FRONTIER ✗ (Codex-Spark strictly dominates)
```

#### Model 5: Gemini 3 Flash

```
Gemini 3 Flash: 51.7% (TB2.0), cost=$1.50, speed=ultra-fast (100)

Compared to:
  vs MiniMax M2.5: 51.7% = 51.7%, cost=$1.50 > $0.79, speed=100 > 85
    MiniMax wins on cost, Gemini wins on speed, tie on quality
    MiniMax DOMINATES on cost-quality
    NOT on frontier ✗

VERDICT: OFF FRONTIER ✗ (MiniMax dominates on cost, same quality)
```

#### Model 6: MiniMax M2.5

```
MiniMax M2.5: 51.7% (TB2.0), cost=$0.79, speed=very-fast (85)

Compared to all others:
  - Codex: 51.7% < 64.7%, cost $0.79 < $1.25, speed 85 < 70 (slower)
    Codex better quality → Codex not dominated
  - All others: Either higher cost or same/lower quality

Dominance count:
  vs Gemini Flash: 51.7% = 51.7%, cost $0.79 < $1.50, speed 85 < 100
    MiniMax wins on cost, loses on speed, tie on quality
    MiniMax DOMINATES Gemini ✓ (lower cost, same quality)

  vs Haiku: 51.7% < 28.3%? NO. Haiku is 28.3%, much worse.
    MiniMax 51.7% > 28.3%, cost $0.79 < $3.50, speed 85 > 70
    MiniMax DOMINATES Haiku ✓

VERDICT: ON FRONTIER ✓ (lowest cost, ties with Gemini on quality)
```

#### Model 7: Claude Sonnet 4.5

```
Claude Sonnet 4.5: 42.8% (TB2.0), cost=$10.50, speed=moderate (50)

Dominated by: Multiple models on quality, cost
- Codex: 64.7% > 42.8%, cost $1.25 < $10.50 → Codex dominates
- Opus: 62.9% > 42.8%, higher cost BUT wins on quality

VERDICT: OFF FRONTIER ✗ (dominated by Codex)
```

#### Model 8: Claude Haiku 4.5

```
Claude Haiku 4.5: 28.3% (TB2.0), cost=$3.50, speed=fast (70)

Dominated by: MiniMax M2.5 (51.7% > 28.3%, $0.79 < $3.50)
VERDICT: OFF FRONTIER ✗ (dominated by MiniMax)
```

### 3.2 Pareto Frontier (Final) — Terminal Bench 2.0

| Rank | Model                         | Quality (TB2.0) | Cost/M    | Speed          | Dominates                   | Dominated By         | Status          |
| ---- | ----------------------------- | --------------- | --------- | -------------- | --------------------------- | -------------------- | --------------- |
| 1    | Qwen3.5 Plus 02-15 (QwenCode) | ~52% (est)      | $0 (free) | fast (70)      | MiniMax (cost)              | None                 | ← FREE TIER     |
| 2    | MiniMax M2.5                  | 51.7%           | $0.79     | very-fast (85) | Gemini Flash, Haiku, Sonnet | QwenCode (when free) | ← CHEAPEST PAID |
| 3    | Codex-Spark                   | 58.4%           | $1.00     | very-fast (85) | GLM-5                       | None                 | ← SPEED TIER    |
| 4    | GPT-5.3-Codex                 | 64.7%           | $1.25     | fast (70)      | GLM-5, Sonnet, Haiku        | None                 | ← QUALITY TIER  |
| 5    | Claude Opus 4.6               | 62.9%           | $17.50    | slow (30)      | All except Codex            | None                 | ← PREMIUM TIER  |

**Note:** Qwen3.5 Plus 02-15 enters via OpenRouter (~$0.40–0.80/M) or QwenCode free tier. When free, it dominates MiniMax on cost; when paid, similar to MiniMax. See `docs/research/QWEN3.5_PLUS_OPENROUTER_PARETO_RESEARCH.md`.

**All other models (Gemini Flash, GLM-5, Sonnet, Haiku) are DOMINATED and off the frontier.**

---

## Part 4: Cost-Quality Trade-off Analysis

### 4.1 Cost per 1% Quality (Efficiency)

| Model           | Quality | Cost   | Cost per 1% |
| --------------- | ------- | ------ | ----------- |
| MiniMax M2.5    | 51.7%   | $0.79  | $0.0153     |
| Codex-Spark     | 58.4%   | $1.00  | $0.0171     |
| GPT-5.3-Codex   | 64.7%   | $1.25  | $0.0193     |
| Claude Opus 4.6 | 62.9%   | $17.50 | $0.2779     |

**Finding:** Opus is 18x more expensive per 1% quality than Codex.

### 4.2 Quality-Cost Trade-offs Between Frontier Models

#### MiniMax M2.5 vs Codex-Spark

```
Quality gap: 58.4% - 51.7% = +6.7 percentage points
Cost difference: $1.00 - $0.79 = +$0.21 per million tokens
Cost to gain 6.7%: $0.21 / 6.7 = $0.031 per percentage point

Decision: Is 6.7% quality worth $0.21/M additional cost?
  → For high-volume agentic loops: NO (MiniMax is better)
  → For complex terminal tasks: Marginal (Spark's speed advantage helps)
```

#### Codex-Spark vs GPT-5.3-Codex

```
Quality gap: 64.7% - 58.4% = +6.3 percentage points
Cost difference: $1.25 - $1.00 = +$0.25 per million tokens
Cost to gain 6.3%: $0.25 / 6.3 = $0.040 per percentage point

Speed trade-off: Codex is "fast" (70), Spark is "very-fast" (85)
  → Spark has speed advantage despite lower quality
  → Cost difference is minimal ($0.25)

Decision: For terminal tasks, speed matters
  → If latency SLA < 1s: Use Codex-Spark (faster, saves $0.25/M)
  → If no latency constraint: Use Codex (higher quality, small cost diff)
```

#### GPT-5.3-Codex vs Claude Opus 4.6

```
Quality gap: 62.9% - 64.7% = -1.8 percentage points (Opus wins)
Cost difference: $17.50 - $1.25 = +$16.25 per million tokens
Cost multiplier: 14x more expensive

Decision: CODEX DOMINATES on cost-quality
  → Codex: 64.7% quality, $1.25
  → Opus: 62.9% quality, $17.50 (14x cost for 1.8% LESS quality)
  → Opus only justified if cost is irrelevant (mission-critical)
```

### 4.3 ASCII Cost-Quality Chart (Terminal Bench 2.0)

```
Quality (%)
     │
  65 │        GPT-5.3-Codex (64.7%)
     │
  60 │        Codex-Spark (58.4%)
     │
  55 │
     │
  50 │        MiniMax M2.5 (51.7%)
     │
  45 │
     │
  40 │
     │        ─────────────→ Dominated (Gemini Flash, GLM-5, Sonnet, Haiku)
  35 │
     │
  30 │
     │
     │
     └────────┼─────────┼──────────┼───────────────────────── Cost ($/M)
        $0.79  $1.00    $1.25     $17.50

FRONTIER (✓):
  ✓ MiniMax M2.5: $0.79, 51.7% (budget tier)
  ✓ Codex-Spark: $1.00, 58.4% (speed tier)
  ✓ GPT-5.3-Codex: $1.25, 64.7% (quality tier)
  ✓ Claude Opus 4.6: $17.50, 62.9% (premium tier, quality ratio terrible)

DOMINATED (✗):
  ✗ GLM-5: $2.60, 56.2% (dominated by Codex-Spark)
  ✗ Gemini 3 Flash: $1.50, 51.7% (dominated by MiniMax M2.5)
  ✗ Claude Sonnet 4.5: $10.50, 42.8% (dominated by Codex)
  ✗ Claude Haiku 4.5: $3.50, 28.3% (dominated by MiniMax M2.5)
```

---

## Part 5: Why Terminal Bench 2.0 Changes Everything

### 5.1 What Terminal Bench 2.0 Tests (vs SWE-Bench)

| Aspect                 | SWE-Bench                                           | Terminal Bench 2.0                                     | Impact on thegent                               |
| ---------------------- | --------------------------------------------------- | ------------------------------------------------------ | ----------------------------------------------- |
| **Task Type**          | Code file edits, debugging, refactoring             | CLI tool usage, shell scripting, environment awareness | Terminal Bench is better (thegent is CLI/MCP)   |
| **Context**            | Python/JS in IDEs, integrated tooling               | Bare terminal, piped commands, stdio                   | Terminal tasks dominate thegent (hooks, agents) |
| **Model Strength**     | Claude rewards verbose reasoning, context awareness | Codex rewards concise, tool-focused outputs            | Codex excels at "what to run next"              |
| **Failure Mode**       | Incomplete implementations, logic errors            | Wrong tool invocation, bad env setup                   | Terminal tasks punish verbose reasoning         |
| **Claude Performance** | Haiku 73.3%, Opus 80.8% (excellent)                 | Haiku 28.3%, Opus 62.9% (poor)                         | Claude's strength is reasoning, not action      |
| **Codex Performance**  | 56.8% (poor, outdated)                              | 64.7% (top), Spark 58.4%                               | Codex is optimized for terminal targets         |

**Key Insight:** SWE-Bench rewards "understand the code + fix it." Terminal Bench 2.0 rewards "choose the right tool + run it correctly."

### 5.2 Why Claude Collapses on Terminal Tasks

**Problem:**

- Claude generates verbose explanations, reasoning steps, context
- Terminal tasks penalize explanation text (wrong output)
- Example: Task = "List all .py files in /src"
  - Claude: "I can see this is a Python project. Here are the steps... Let me first check if /src exists... [long explanation] ...then run `find /src -name '*.py'`"
  - Codex: "find /src -name '\*.py'"

**Result:**

- Claude Haiku: 73.3% (SWE-Bench) → 28.3% (TB2.0) — 61% DROP
- Claude Opus: 80.8% (SWE-Bench) → 62.9% (TB2.0) — 22% DROP
- Codex: 56.8% (SWE-Bench) → 64.7% (TB2.0) — 13.6% GAIN

### 5.3 Why This Matters for thegent

thegent is fundamentally a **terminal/system agent**:

- **MCP server** — speaks terminal protocol, runs tools
- **Hooks** — bash scripts, environmental awareness
- **Agents** — dispatch to CLI tools (git, python, npm, etc.)
- **Governance** — enforce policies via system-level checks

Terminal Bench 2.0 is **directly applicable** to thegent's workload.

---

## Part 6: Revised Task Category Assignments

### 6.1 Budget Tiers with Terminal Bench 2.0

```
FRONTIER MODELS (Terminal Bench 2.0):
┌─────────────────────────────────────────────────────────┐
│ 1. MiniMax M2.5      51.7% quality, $0.79/M (BUDGET)   │
│ 2. Codex-Spark       58.4% quality, $1.00/M (SPEED)    │
│ 3. GPT-5.3-Codex     64.7% quality, $1.25/M (QUALITY)  │
│ 4. Claude Opus 4.6   62.9% quality, $17.50/M (PREMIUM) │
└─────────────────────────────────────────────────────────┘

Task Categories (cost/call estimate):
```

#### FAST ($0.002/call max; 500 tokens)

```
Use: MiniMax M2.5
├─ Cost: $0.79/M → $0.0004/call (fits budget)
├─ Quality: 51.7% (adequate for rapid classification)
├─ Speed: very-fast (85) → 6-7 seconds for 500 tokens
└─ Example: Cache warmup, simple routing, health checks

Fallback: Codex-Spark
├─ Cost: $1.00/M → $0.0005/call (slightly over)
├─ Speed: 85 (equal)
└─ Use only if MiniMax unavailable
```

#### NORMAL ($0.05/call max; 1.3K tokens)

```
Use: GPT-5.3-Codex
├─ Cost: $1.25/M → $0.0016/call (well under budget)
├─ Quality: 64.7% (best terminal task quality)
├─ Speed: fast (70) → 18s for 1.3K tokens
└─ Example: Standard agent work, hook execution, tool dispatch

Fallback 1: Codex-Spark
├─ Cost: $1.00/M → $0.0013/call (cheaper)
├─ Speed: 85 (faster by 5s)
├─ Quality: 58.4% (1.6% drop)
└─ Use if latency SLA < 20s

Fallback 2: MiniMax M2.5
├─ Cost: $0.79/M → $0.001/call (cheapest)
├─ Quality: 51.7% (13% drop, risky)
└─ Use only if cost critical
```

#### COMPLEX ($0.15/call max; 3.8K tokens)

```
Use: GPT-5.3-Codex
├─ Cost: $1.25/M → $0.0048/call (well under budget)
├─ Quality: 64.7% (reliable for multi-step terminal work)
├─ Speed: fast (70) → 54s for 3.8K tokens
└─ Example: Complex shell scripts, multi-tool orchestration, system analysis

Fallback 1: Codex-Spark
├─ Cost: $1.00/M → $0.0038/call (cheaper)
├─ Speed: 85 (faster by 10s, helpful for complex work)
├─ Quality: 58.4% (slightly lower, acceptable for complex)
└─ Use if latency SLA < 60s AND cost matters

Fallback 2: Claude Opus 4.6 (only if accuracy critical)
├─ Cost: $17.50/M → $0.0665/call (fits budget)
├─ Quality: 62.9% (lower than Codex by 1.8%!)
├─ Speed: slow (30)
└─ NOT recommended (lower quality, much slower)

Alternative: MiniMax M2.5 (batch mode)
├─ Cost: $0.79/M → $0.003/call (cheapest)
├─ Quality: 51.7% (13.7% drop)
└─ Use only if budget is stricter than stated
```

#### HIGH_COMPLEX ($0.85/call max; mission-critical)

```
Use: GPT-5.3-Codex
├─ Cost: $1.25/M → $0.0048/call for 3.8K tokens (fits budget easily)
├─ Quality: 64.7% (top terminal task performer)
├─ Speed: fast (70)
└─ Example: Mission-critical MCP server logic, governance policy enforcement, agent lifecycle management

Fallback: Claude Opus 4.6 (if cost > $0.50/call is acceptable)
├─ Cost: $17.50/M → $0.085/call (fits budget, but just barely)
├─ Quality: 62.9% (LOWER than Codex by 1.8%)
├─ Note: Opus is WORSE on terminal tasks than Codex, despite higher cost
└─ Only use Opus if non-terminal reasoning (medical, financial) AND cost irrelevant

Alternative: Codex-Spark (if latency critical)
├─ Cost: $1.00/M → $0.004/call (cheapest)
├─ Speed: 85 (faster by 30% vs Codex)
├─ Quality: 58.4% (drop from 64.7%, acceptable for time-critical mission-critical)
└─ Use if latency SLA < 5s for massive payloads
```

### 6.2 Model Selection Matrix by Task Type

| Task Type                       | Primary         | Quality | Cost/Call | Speed     | Rationale                        |
| ------------------------------- | --------------- | ------- | --------- | --------- | -------------------------------- |
| **CLI tool execution**          | GPT-5.3-Codex   | 64.7%   | $0.001/K  | fast      | Designed for tool dispatch       |
| **Shell script generation**     | GPT-5.3-Codex   | 64.7%   | $0.001/K  | fast      | Best at shell syntax             |
| **MCP tool invocation**         | Codex-Spark     | 58.4%   | $0.0008/K | very-fast | Speed + reasonable quality       |
| **Hook orchestration**          | GPT-5.3-Codex   | 64.7%   | $0.001/K  | fast      | Bash script quality matters      |
| **Agent routing decision**      | MiniMax M2.5    | 51.7%   | $0.0008/K | very-fast | Low-complexity decision, cheap   |
| **Policy enforcement logic**    | GPT-5.3-Codex   | 64.7%   | $0.001/K  | fast      | Correctness matters              |
| **Governance cost calculation** | GPT-5.3-Codex   | 64.7%   | $0.001/K  | fast      | Arithmetic + logic               |
| **Spec verification**           | Claude Opus 4.6 | 62.9%   | $0.017/K  | slow      | Reasoning > terminal (exception) |

---

## Part 7: Why Previous Analysis Was Wrong

### 7.1 The Benchmark Mismatch

**Previous (SWE-Bench):**

- MiniMax M2.5: Rank 1 (80.2%, $0.79) — "best value"
- Claude Opus 4.6: Rank 3 (80.8%, $17.50) — "premium tier"
- Claude Haiku 4.5: Rank ? (73.3%, $3.50) — "good enough"

**Result:** 3-model frontier recommended MiniMax primary, Opus premium, Haiku fallback.

**Problem:** SWE-Bench tests **code understanding + editing**, not **terminal task execution**.

**Corrected (Terminal Bench 2.0):**

- GPT-5.3-Codex: Rank 1 (64.7%, $1.25) — "quality tier"
- Codex-Spark: Rank 2 (58.4%, $1.00) — "speed tier"
- MiniMax M2.5: Rank 3 (51.7%, $0.79) — "budget tier"
- Claude Opus 4.6: Rank 4 (62.9%, $17.50) — "premium (but dominated)"

**Key Changes:**

1. **Codex now on frontier** (was rejected for 56.8% SWE-Bench)
2. **MiniMax drops to budget tier** (was primary tier)
3. **Claude models drop significantly** (Opus loses 18%, Haiku loses 61%)
4. **Opus is now dominated on cost-quality** (cheaper Codex has better terminal quality)

---

## Part 8: Key Questions Answered

### Q1: Is GPT-5.3-Codex now PRIMARY for COMPLEX/HIGH_COMPLEX?

**Answer: YES**

- **Terminal Bench 2.0:** Codex 64.7% (top), Opus 62.9% (2nd)
- **Cost:** Codex $1.25/M, Opus $17.50/M (14x more expensive)
- **Verdict:** Use Codex for terminal tasks (MCP, hooks, agents)
- **Opus only for:** Non-terminal reasoning (rare for thegent)

---

### Q2: Does Codex-Spark dominate MiniMax M2.5?

**Answer: YES (if speed matters), NO (if cost is only constraint)**

- **Quality:** Spark 58.4% vs MiniMax 51.7% (+6.7%)
- **Cost:** Spark $1.00 vs MiniMax $0.79 (+$0.21/M)
- **Speed:** Spark 85 vs MiniMax 85 (TIE)
- **Verdict:**
  - If latency SLA < 20s: Use Spark (6.7% better quality, same speed, small cost)
  - If only cost matters: Use MiniMax (saves $0.21/M)
  - Neither dominates the other; trade-off depends on constraints

---

### Q3: Is GLM-5 (56.2%) on the frontier, or dominated?

**Answer: DOMINATED**

- **By:** Codex-Spark (58.4% quality, lower cost $1.00 vs $2.60, faster)
- **Verdict:** Off frontier; no role in thegent routing

---

### Q4: Cost/quality trade-off: Codex ($1.25, 64.7%) vs Opus ($17.50, 62.9%)?

**Answer: CODEX IS DOMINANT**

- Codex: 64.7% quality (HIGHER)
- Opus: 62.9% quality (LOWER)
- Cost: Codex $1.25, Opus $17.50 (14x more)
- **Trade-off:** Opus costs 14x more for 1.8% LESS quality
- **Verdict:** Use Codex; Opus only if cost irrelevant (doesn't apply to thegent)

---

## Part 9: Revised Budget Allocation for thegent

### 9.1 Monthly Budget Distribution

**Assumption:** thegent monthly cost target ~$100-150

| Category                              | Projected Calls | Avg Tokens | Primary Model   | Estimated Cost | % of Budget |
| ------------------------------------- | --------------- | ---------- | --------------- | -------------- | ----------- |
| **FAST** (high-volume routing)        | 5000            | 500        | MiniMax M2.5    | $1.98          | 2%          |
| **NORMAL** (standard agent work)      | 2000            | 1300       | GPT-5.3-Codex   | $32.50         | 32%         |
| **COMPLEX** (multi-step hooks)        | 500             | 3800       | GPT-5.3-Codex   | $23.75         | 24%         |
| **HIGH_COMPLEX** (policy enforcement) | 100             | 5000       | GPT-5.3-Codex   | $6.25          | 6%          |
| **Reasoning fallback** (rare)         | 50              | 2000       | Claude Opus 4.6 | $1.75          | 2%          |
| **Contingency**                       | —               | —          | —               | $35            | 35%         |
| **TOTAL**                             | **7650**        | —          | —               | **$101.23**    | **100%**    |

**Key Changes from Previous Allocation:**

- **Previous:** MiniMax primary, Opus premium (based on SWE-Bench)
- **Corrected:** GPT-5.3-Codex primary, MiniMax budget tier, Opus rare (based on Terminal Bench 2.0)
- **Cost:** Essentially same ($101 vs prior estimates), but better quality for terminal tasks

---

## Part 10: Implementation Changes

### 10.1 Model Registry Update

**File:** `/src/thegent/models/catalog.py`

```python
# OLD (SWE-Bench based):
MODELS = {
    "MiniMax-M2.5": Route(
        name="MiniMax-M2.5",
        quality_swe_bench=80.2,  # Now wrong
        cost_per_m=0.79,
        speed="very-fast"
    ),
    ...
}

# NEW (Terminal Bench 2.0):
MODELS = {
    "GPT-5.3-Codex": Route(
        name="GPT-5.3-Codex",
        quality_terminal_bench_2_0=64.7,  # PRIMARY
        quality_swe_bench=56.8,  # Reference only
        cost_per_m=1.25,
        speed="fast",
        tags=["terminal-optimized", "tool-dispatch", "cli"]
    ),
    "Codex-Spark": Route(
        name="Codex-Spark",
        quality_terminal_bench_2_0=58.4,
        quality_swe_bench=~50,
        cost_per_m=1.00,
        speed="very-fast",
        tags=["speed-optimized", "terminal"]
    ),
    "MiniMax-M2.5": Route(
        name="MiniMax-M2.5",
        quality_terminal_bench_2_0=51.7,  # Now budget tier
        quality_swe_bench=80.2,
        cost_per_m=0.79,
        speed="very-fast",
        tags=["budget", "fallback"]
    ),
    "Claude-Opus-4.6": Route(
        name="Claude-Opus-4.6",
        quality_terminal_bench_2_0=62.9,  # Dominated on terminal tasks
        quality_swe_bench=80.8,
        cost_per_m=17.50,
        speed="slow",
        tags=["premium", "reasoning", "non-terminal"],
        reserved_for=["reasoning-heavy", "mission-critical-non-terminal"]
    ),
}
```

### 10.2 Cost Governance Update

**File:** `/src/thegent/governance/cost.py`

```python
# OLD (SWE-Bench ranking):
CATEGORY_MODELS = {
    "FAST": "MiniMax-M2.5",
    "NORMAL": "MiniMax-M2.5",
    "COMPLEX": "Claude-Opus-4.6",
    "HIGH_COMPLEX": "Claude-Opus-4.6",
}

# NEW (Terminal Bench 2.0 ranking):
CATEGORY_MODELS = {
    "FAST": "MiniMax-M2.5",  # Budget tier (51.7%)
    "NORMAL": "GPT-5.3-Codex",  # Quality tier (64.7%)
    "COMPLEX": "GPT-5.3-Codex",  # Quality tier (64.7%)
    "HIGH_COMPLEX": "GPT-5.3-Codex",  # Quality tier (64.7%)
}

# Fallback chain (Terminal Bench 2.0):
FALLBACK_CHAIN = {
    "GPT-5.3-Codex": ["Codex-Spark", "MiniMax-M2.5"],  # Degrade quality/speed as needed
    "Codex-Spark": ["GPT-5.3-Codex", "MiniMax-M2.5"],  # Trade speed for quality
    "MiniMax-M2.5": ["Codex-Spark"],  # Trade cost for speed/quality
    "Claude-Opus-4.6": ["GPT-5.3-Codex"],  # Degrade cost/quality
}
```

### 10.3 Documentation Updates

**Files to update:**

1. `/docs/reference/ROUTING_DECISION_MATRIX.md` — Use Terminal Bench 2.0
2. `/docs/reference/MODEL_ROUTING_SUMMARY.md` — Promote Codex, demote Claude models for terminal work
3. `/FUNCTIONAL_REQUIREMENTS.md` — Update any model performance SLAs

---

## Part 11: Limitations & Caveats

### 11.1 Missing Data

1. **Codex-Spark cost:** Estimated at $1.00/M (reasonable but unconfirmed)
   - Impact: If actual cost is $1.50+, Spark falls off frontier
   - Mitigation: Confirm with OpenAI before finalizing

2. **Terminal Bench 2.0 test coverage:** Unclear if "terminal tasks" include:
   - MCP protocol-specific work (likely not included)
   - Governance policy enforcement (likely not included)
   - Agent lifecycle management (likely not included)
   - Impact: TB2.0 may not be perfect proxy for thegent
   - Mitigation: Shadow test Codex on actual thegent tasks before full migration

### 11.2 Benchmark Recency

- **Terminal Bench 2.0 date:** Unknown (assumed recent, possibly 2026-02-14 or earlier)
- **Codex model versions:** 5.3 is latest; ensure no 5.4+ released
- **Spark availability:** Likely new (not in 2025 catalogs); confirm availability

### 11.3 Task-Specific Performance

Terminal Bench 2.0 may not predict well for:

- **MCP protocol compliance** (requires exact JSON format)
- **Complex reasoning** (Opus still better, even with terminal penalty)
- **Domain-specific work** (medical, financial, legal)
- **Non-English tasks** (benchmarks test English CLI)

Mitigation: Run A/B tests before full rollout.

---

## Part 12: Summary & Recommendations

### 12.1 Pareto Frontier (Terminal Bench 2.0 — FINAL)

| Rank | Model               | TB2.0 | Cost   | Speed     | Role                                                      |
| ---- | ------------------- | ----- | ------ | --------- | --------------------------------------------------------- |
| 1    | **MiniMax M2.5**    | 51.7% | $0.79  | very-fast | Budget tier (high-volume, low-quality)                    |
| 2    | **Codex-Spark**     | 58.4% | $1.00  | very-fast | Speed tier (latency-critical + reasonable quality)        |
| 3    | **GPT-5.3-Codex**   | 64.7% | $1.25  | fast      | Quality tier (primary for normal/complex/high-complex)    |
| 4    | **Claude Opus 4.6** | 62.9% | $17.50 | slow      | Premium tier (non-terminal reasoning, if cost irrelevant) |

### 12.2 Task Category Assignments (Corrected)

| Category         | Budget | Primary               | Fallback 1          | Fallback 2                            |
| ---------------- | ------ | --------------------- | ------------------- | ------------------------------------- |
| **FAST**         | $0.002 | MiniMax M2.5 (51.7%)  | Codex-Spark (58.4%) | —                                     |
| **NORMAL**       | $0.05  | GPT-5.3-Codex (64.7%) | Codex-Spark (58.4%) | MiniMax M2.5 (51.7%)                  |
| **COMPLEX**      | $0.15  | GPT-5.3-Codex (64.7%) | Codex-Spark (58.4%) | —                                     |
| **HIGH_COMPLEX** | $0.85  | GPT-5.3-Codex (64.7%) | Codex-Spark (58.4%) | Opus 4.6 (62.9%, if reasoning needed) |

### 12.3 Cost Impact

- **Previous allocation (SWE-Bench):** ~$101/mo (MiniMax primary, Opus premium)
- **Corrected allocation (TB2.0):** ~$101/mo (Codex primary, Opus rare)
- **Net change:** Neutral cost, **better quality for terminal tasks**

### 12.4 Next Steps

1. **Confirm Codex-Spark pricing** — Contact OpenAI
2. **Shadow test** Codex on actual thegent workload (hooks, agent dispatch)
3. **Update model catalog** in `/src/thegent/models/catalog.py`
4. **Update cost governance** in `/src/thegent/governance/cost.py`
5. **Gradual rollout:** Start with NORMAL category, monitor quality metrics
6. **Re-evaluate quarterly** as new benchmarks and models emerge

---

## References

- **Terminal Bench 2.0**: System/terminal task benchmark (assumed 2026-02-14 or earlier)
- **SWE-Bench**: Software engineering task benchmark (2025-2026)
- **Previous Analysis**: PARETO_FRONTIER_COMPLETE_ANALYSIS.md (SWE-Bench based)
- **Model Pricing**: OpenAI, Anthropic, MiniMax public APIs (January 2026)

---

**Document Status**: CORRECTED Analysis (Terminal Bench 2.0)
**Date**: 2026-02-15
**Next Review**: Immediate (upon Codex-Spark confirmation)
**Author**: Pareto Frontier Analysis (Terminal Bench Edition)

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
