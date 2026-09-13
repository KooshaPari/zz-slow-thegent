<DONE>
# ChatGPT Pareto Router Deep Research — Part 1: Foundations

**Source**: chatgpt3.md, chatgpt4.md (ChatGPT conversation transcripts)
**Date**: 2026-02-18
**Scope**: Core Pareto design, Offer abstraction, PRD/ALD foundations, design philosophy

---

## 1. Core Design: Pareto-First Router

### 1.1 Two Optimization Layers

The router operates at two distinct time scales:

| Layer         | Name                       | Frequency    | Responsibility                                                                                              |
| ------------- | -------------------------- | ------------ | ----------------------------------------------------------------------------------------------------------- |
| **Slow loop** | Monthly / Budget Allocator | Hourly/Daily | Decides enabled subscriptions/plans/providers/models; sets quotas + internal shadow prices                  |
| **Fast loop** | Per-Call Router            | Per request  | Chooses best offer from enabled pool using hard constraints first, then Pareto / lexicographic optimization |

**Key insight**: This separation is what makes subscriptions + scraping + seasonal bonuses manageable.

### 1.2 Optimization Axes (Three Pillars)

1. **Speed** — latency + "conciseness" proxy (expected output tokens, expected turns)
2. **Cost** — blended in/out, caching, effective $/MTok under subscriptions
3. **Quality** — task score index from benchmarks + internal evals

### 1.3 Selection Flow

```
Hard constraints (non-negotiable)
    ↓
Pareto frontier (non-dominated offers)
    ↓
Lexicographic tie-break (optimize in order)
    ↓
Execute + fallback chain
```

### 1.4 Hard Constraint Examples

- Must support tool calls / structured JSON
- Must handle context length
- Must meet p95_latency ≤ X (or at least predicted)
- Must meet cost ≤ Y (worst-case token cap)
- Must meet quality ≥ Qmin for role
- Compliance rules (if needed)

Anything failing gets removed before optimization.

### 1.5 Pareto Frontier

Compute objective vector for each remaining offer:

- **Speed objective**: (latency_pred_ms, output_tokens_pred, turns_pred)
  Collapse to: `session_time = latency + k*output_tokens + m*turns`
- **Cost objective**: effective_cost_pred (includes cache + subscription shadow price)
- **Quality objective**: -quality_pred (since we minimize)

**Pareto set** = non-dominated offers.
**A dominates B** iff: speed_A ≤ speed_B AND cost_A ≤ cost_B AND quality_A ≥ quality_B, with at least one strictly better.

### 1.6 Lexicographic Selection

Example order:

1. Maximize Quality (within ε)
2. Minimize Cost (within ε)
3. Minimize Speed

Implementation:

```
Take top-K by quality (or within epsilon of best)
Among those, take cheapest (or within epsilon)
Among those, take fastest
```

This is stable and easy to reason about. Alternative: weighted Tchebycheff or epsilon-constraint for "Pareto with preferences."

---

## 2. Offer-First Abstraction

### 2.1 Key Principle

**"Model" name is marketing.** The router operates on **offers**:

```
Offer = (provider endpoint, model id, region, plan/quota regime, pricing, constraints, telemetry)
```

Same "model" across:

- OpenRouter vs direct provider
- Different regions
- Different subscriptions/quotas

…is **not** the same offer.

### 2.2 Data Model: Offer Fields

| Category         | Fields                                                                               |
| ---------------- | ------------------------------------------------------------------------------------ |
| **Identity**     | offerId (unique), provider, modelName                                                |
| **Capabilities** | contextWindow, tool support (function calling, JSON mode, vision), max output tokens |
| **Pricing**      | in/out, cache read/write, batch discounts                                            |
| **Limits**       | RPM, TPM, concurrency                                                                |
| **Reliability**  | timeouts, error rate                                                                 |

### 2.3 Subscription / Plan Abstraction

Each plan is a **resource bucket**:

```
planId
provider
billingPeriod (monthly)
fixedCost ($/month)
includedUsage (by model or by family; sometimes separate in/out)
multipliers (seasonal 2x, weekends, etc.)
priorityRules (some providers throttle after threshold)
swapOptions (upgrade/downgrade rules + effective start date)
```

**Derived runtime object**:

- `effectiveUnitCost(model, tokensIn, tokensOut, cacheStats) → dollars`
- `remainingQuota(model) → tokens remaining (or "unlimited but throttled")`
- `shadowPrice(model) → internal $/token reflecting scarcity` ← **key**

Shadow price converts "subscription scarcity" into per-call routing.

### 2.4 Task + Role Schema

Per request:

- **role**: fast_chat, high_accuracy, doc_writer, code_review, e2e_test, etc.
- **hardConstraints**: must support tools? must be JSON? max latency? max cost?
- **softWeights** or priority order (lexicographic)
- **qualityTarget**: minimum quality score or "top tier only"

### 2.5 Why Offer-First Beats Model→Provider Two-Stage

| Two-Stage                                                     | Offer-First                              |
| ------------------------------------------------------------- | ---------------------------------------- |
| Select "claude-opus" without considering provider rate limits | Economics and limits baked in from start |
| Ignores subscription quotas                                   | Correct handling of quotas/outages       |
| Ignores region latency                                        | Consistent scoring                       |
| Must do offer-routing anyway as second step                   | Single routing decision                  |

**Recommendation**: Offer-first, always.

---

## 3. Quality Index (That Actually Works)

### 3.1 Normalized Score per Task Family

For each model, maintain benchmarks: MMLU, HumanEval, GSM8K, doc writing eval, tool use, etc.

Normalize each to 0–1:

```
norm = (score - min) / (max - min) across candidate set
```

### 3.2 Role → Benchmark Weights

Examples:

- **fast_chat**: 0.5 instruction following + 0.3 safety/refusal quality + 0.2 coherence
- **doc_writer**: 0.4 writing eval + 0.3 instruction following + 0.3 long-context
- **code_review**: 0.5 coding + 0.3 reasoning + 0.2 tool use
- **e2e_test_agent**: 0.6 tool use + 0.4 planning/robustness

```
quality_pred(role, model) = Σ w_i(role) * norm_benchmark_i(model)
```

### 3.3 "Your Reality" Correction

Benchmarks lie. Add:

- `online_success_rate(role, model)` from logs (pass/fail, user re-ask rate)
- `penalty_for_refusal_mismatch` (some models refuse too much)
- `format_adherence_rate` (JSON validity, schema conformance)

Fold in as multiplier or additive term.

---

## 4. Roles + Router Profiles

### 4.1 Example Profiles

```yaml
doc_writer:
  hard: context >= N, supports citations/tools? (if needed)
  hard: quality >= 0.78
  soft order: quality → cost → session_time
  output_tokens_pred multiplier: 1.8x baseline

fast_chat:
  hard: p95 latency <= 1500ms
  soft order: speed → cost → quality (or speed → quality → cost)

high_accuracy:
  hard: quality >= 0.9
  soft order: quality → speed → cost (or quality → cost → speed)
```

### 4.2 Design Note

You'll end up with ~8–20 roles, not 200. Keep it tight.

---

## 5. Implementation Skeleton

### 5.1 Components

| Component             | Responsibility                                                                      |
| --------------------- | ----------------------------------------------------------------------------------- |
| Catalog service       | Offers + capabilities + base pricing                                                |
| Plan service          | Scrapes usage, applies plan math, publishes effectiveUnitCost + quota + shadowPrice |
| Metrics service       | Latency/error stats by offer, updates predictors                                    |
| Quality index service | Benchmark table + online eval, publishes quality_pred per role                      |
| Router API (hot path) | chooseOffer(request, role, constraints) → offerId                                   |
| Execution layer       | Retries/fallbacks + circuit breaker                                                 |

### 5.2 Hot Path Algorithm

1. Parse request → role + constraints + estimate tokens
2. Candidate offers = enabled offers ∩ capability constraints
3. Filter by hard constraints (cost upper bound uses worst-case tokens cap)
4. For each candidate, compute (quality, cost, session_time)
5. Pareto prune
6. Lexicographic finalize
7. Execute with fallback policy:
   - Timeout/error → next best in Pareto set
   - Format invalid → retry once with same, then fallback to higher format-adherence model

### 5.3 Pareto MVP (Smallest Real Thing)

- Static catalog (JSON file) of offers + capabilities + raw pricing
- One plan adapter that turns subscription into effective cost (even if rough)
- Rolling metrics: p50/p95 latency + error rate by offer
- Quality index v0 from public benchmarks + manual role weights
- Router: hard filter + Pareto + lexicographic
- Fallback: timeout/error + format failure

---

## 6. Two Hard Problems (Don't Ignore)

### 6.1 Token Prediction

Cost and "conciseness" depend on output tokens. Start with heuristics per role, then upgrade to a learned predictor using prompt features + historical logs.

### 6.2 Subscription Arbitrage Correctness

If effective marginal cost math is wrong, routing becomes random. Shadow prices + conservative assumptions (worst-case) prevent nasty surprises.

---

## 7. Config Format (Drop into Repo)

- `roles.yaml` — constraints + objective order + weights
- `offers.yaml` — capabilities + base price
- `plans.yaml` — plan rules + seasonal multipliers
- `benchmarks.csv` — raw scores

---

## 8. Design Philosophy (From ChatGPT)

- **Models are commodities**
- **Offers are economic units**
- **Subscriptions are resource pools**
- **Routing is a constrained multi-objective optimization problem**
- **Pareto-first avoids premature scalar weighting mistakes**
- **Lexicographic tie-break gives stability**

---

## 9. ASCII Architecture (System Overview)

```
                   ┌─────────────────────┐
                   │   Client Request    │
                   │  (role + prompt)    │
                   └─────────┬───────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   Router API   │
                    │ (Hot Path)     │
                    └───────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
      Hard Constraint   Objective Calc   Fallback Logic
          Filter         (Speed/Cost/Quality)
                            │
                            ▼
                    Pareto Frontier
                            │
                            ▼
                    Lexicographic Select
                            │
                            ▼
                      Offer Execution
                            │
                            ▼
                    Telemetry Logging
```

### Control Plane vs Data Plane

```
                   ┌────────────────────────────┐
                   │        CONTROL PLANE       │
                   ├────────────────────────────┤
                   │ Offer Registry             │
                   │ Subscription Engine        │
                   │ Shadow Pricing Engine      │
                   │ Quality Index Engine       │
                   │ Telemetry Aggregator       │
                   │ Budget Allocator           │
                   └──────────────┬─────────────┘
                                  │
                                  ▼
                   ┌────────────────────────────┐
                   │         DATA PLANE         │
                   ├────────────────────────────┤
                   │ Router (hot path)          │
                   │ Provider Adapters          │
                   │ Execution Gateway          │
                   └────────────────────────────┘
```

---

## 10. Provider Adapter Interface

```python
interface ProviderAdapter:
    fetchModels()
    fetchPricing()
    fetchUsage()
    executeRequest()
    parseUsageFromResponse()
```

**Adapters**: OpenRouter, Vercel AI Gateway, Direct Provider, Self-host

---

## References

- chatgpt3.md, chatgpt4.md — Source transcripts
- CHATGPT_PARETO_ROUTER_EXTENSION.md — Project synthesis
- ULTRA_ADVANCED_ROUTER_RESEARCH.md — OpenRouter, LiteLLM, etc.
