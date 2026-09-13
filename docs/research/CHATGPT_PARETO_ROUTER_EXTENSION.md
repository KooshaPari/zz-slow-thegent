<DONE>
# ChatGPT Pareto Router Research Extension - Maximum Depth Synthesis

**Date**: 2026-02-18
**Status**: Research Complete - Project-Adapted
**Sources**: chatgpt3.md, chatgpt4.md (ChatGPT conversation transcripts)
**Purpose**: Synthesize Pareto-first router design, Offer abstraction, shadow pricing, and subscription economics into project-ready form; extend ULTRA_ADVANCED_ROUTER_RESEARCH.md with project-specific adaptation

---

## Executive Summary

This document synthesizes **extreme-depth research** from ChatGPT conversations (chatgpt3.md, chatgpt4.md) with the project's existing ULTRA_ADVANCED_ROUTER_RESEARCH.md. It provides:

1. **Pareto-first router architecture** (Helios Router design) - 3 pillars: Speed, Cost, Quality
2. **Offer-first abstraction** - provider+model+region+plan as routable unit (not model name)
3. **Subscription economics** - shadow pricing, effective cost, blended $/MTok
4. **Project-specific adaptation** - Codex CLI, harnesses, LiteLLM, Responses API
5. **Concrete catalog schemas** - models.yaml, offers.yaml, plans.yaml
6. **Index calculation formulas** - Speed, Cost, Quality with exact math
7. **Mapping to LiteLLM** - How Helios concepts map to LiteLLM Router

**Key Design Philosophy** (from ChatGPT research):

- Models are commodities
- Offers are economic units
- Subscriptions are resource pools
- Routing is constrained multi-objective optimization
- Pareto-first avoids premature scalar weighting
- Lexicographic tie-break gives stability

---

## Table of Contents

1. [Pareto-First Router Design](#1-pareto-first-router-design)
2. [Offer-First Abstraction](#2-offer-first-abstraction)
3. [Three Pillars: Speed, Cost, Quality](#3-three-pillars-speed-cost-quality)
4. [Subscription Economics & Shadow Pricing](#4-subscription-economics--shadow-pricing)
5. [Budget Engine & $600/Month Control](#5-budget-engine--600month-control)
6. [Quality Index with Spotty Benchmarks](#6-quality-index-with-spotty-benchmarks)
7. [Project-Specific Catalog (Ground Truths)](#7-project-specific-catalog-ground-truths)
8. [Ingestion Pipelines](#8-ingestion-pipelines)
9. [API Processes & User Journeys](#9-api-processes--user-journeys)
10. [Mapping to LiteLLM & Project Architecture](#10-mapping-to-litellm--project-architecture)
11. [Implementation Roadmap](#11-implementation-roadmap)

---

## 1. Pareto-First Router Design

### 1.1 Two Optimization Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SLOW LOOP (Monthly/Budget Allocator)                  │
│  - Decides enabled subscriptions/plans/providers/models                  │
│  - Sets quotas + internal shadow prices                                 │
│  - Runs hourly/daily                                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FAST LOOP (Per-Call Router)                           │
│  - Given request + role + constraints                                   │
│  - Chooses best offer from enabled pool                                 │
│  - Hard constraints first → Pareto → Lexicographic                      │
│  - < 5ms p95 latency                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Selection Algorithm

```
Step 1 — Filter by hard constraints (non-negotiable)
  - Capability requirements (tools, JSON, vision)
  - Context length
  - Maximum cost threshold
  - Latency threshold (optional)
  - Minimum quality threshold
  - Compliance rules

Step 2 — Compute objective vector per offer
  O = (minimize speed_score, minimize effective_cost, maximize quality_score)

Step 3 — Compute Pareto frontier (non-dominated offers)
  A dominates B iff:
    speed_A <= speed_B AND cost_A <= cost_B AND quality_A >= quality_B
    AND at least one strictly better

Step 4 — Lexicographic tie-break (example order)
  1. Highest quality (within ε)
  2. Lowest cost (within ε)
  3. Lowest speed score

Step 5 — Generate fallback chain
  Primary → Secondary (Pareto set) → Tertiary (high-adherence) → Quaternary (cheapest self-host)
```

### 1.3 Fallback Strategy by Failure Type

| Failure Type        | Fallback Action                       |
| ------------------- | ------------------------------------- |
| Rate limit / 429    | Switch provider/offer immediately     |
| Timeout             | Switch to fastest offer on Pareto set |
| Schema/tool failure | Switch to highest adherence offer     |
| Bad output quality  | Escalate to higher quality tier       |

---

## 2. Offer-First Abstraction

### 2.1 Key Principle: Offer = Routable Unit

**Model name is marketing.** The router operates on **offers**:

```
Offer = (provider endpoint, modelId, region, plan/quota regime, pricing, constraints, telemetry)
```

Same "model" across:

- OpenRouter vs direct provider
- Different regions
- Different subscriptions/quotas

…is **not** the same offer.

### 2.2 Why Offer-First Beats Model→Provider Two-Stage

| Two-Stage (model → provider)                                  | Offer-First                              |
| ------------------------------------------------------------- | ---------------------------------------- |
| Select "claude-opus" without considering provider rate limits | Economics and limits baked in from start |
| Ignores subscription quotas                                   | Correct handling of quotas/outages       |
| Ignores region latency                                        | Consistent scoring                       |
| Must do offer-routing anyway as second step                   | Single routing decision                  |

**Recommendation**: Offer-first, always.

### 2.3 Canonical Schema Layers

**A) Identity & Capabilities** (mostly static)

- provider, offerId, modelId
- context window, max output, tool support, JSON mode, vision

**B) Commercials & Limits** (changes often)

- list prices (in/out, cache read/write)
- rate limits / concurrency
- plan entitlements / included usage / throttling rules

**C) Observed Telemetry** (changes constantly)

- p50/p95 latency, error rate, timeout rate
- format adherence rate (JSON validity, tool-call success)
- per-role success metrics

---

## 3. Three Pillars: Speed, Cost, Quality

### 3.1 Speed Index (Exact Formula)

Speed = time to usable answer (not just latency). Includes:

- TTFT (time to first token)
- Total latency
- Output length (longer outputs = longer read + parse)
- Expected turns (agent workflows)

```
predicted_latency = latency_p95(offer)
predicted_generation_time = expected_output_tokens / tokens_per_second
session_time = predicted_latency + predicted_generation_time + gamma * expected_turns

speed_score = session_time / median_session_time_across_offers   # Lower is better
```

**Why not just latency?** Claude Opus may be slow but concise. Gemini Flash may be fast but verbose. Verbose models increase output tokens by 40% → slower in real usage.

### 3.2 Cost Index (Exact Formula)

```
base_cost = (input_tokens * input_price) + (output_tokens * output_price)

# Cache adjustment
effective_input_tokens = input_tokens * (1 - cache_hit_rate)

# Retry risk (flaky providers)
cost_adjusted = effective_cost * (1 / (1 - error_rate))

# Shadow pricing (subscription scarcity)
remaining_ratio = remaining_quota / expected_remaining_quota_today
shadow_multiplier = 1 / max(remaining_ratio, ε)
shadow_cost = base_cost * shadow_multiplier

cost_score = shadow_cost / median_cost_across_offers   # Lower is better
```

### 3.3 Quality Index (See Section 6)

Role-specific, dynamic, measured from usage + benchmarks.

---

## 4. Subscription Economics & Shadow Pricing

### 4.1 Effective Unit Cost (EUC) by Plan Type

| Plan Type                  | EUC Calculation                                                                   |
| -------------------------- | --------------------------------------------------------------------------------- |
| **payg_token**             | EUC_in = price_in_per_token, EUC_out = price_out_per_token                        |
| **fixed_bucket_tokens**    | EUC_blended = monthly_fee / expected_tokens_covered                               |
| **premium_request_bucket** | Convert requests→tokens via observed avg; EUC = fee / (requests × avg_tokens)     |
| **prompt_rate_limited**    | Minimax: 300 prompts/5h → prompts_month × avg_tokens; EUC = fee / expected_tokens |
| **volatile_free**          | EUC = very_small_floor + high volatility penalty                                  |

### 4.2 Shadow Pricing (Two Layers)

**Layer 1: Monthly Budget Shadow**

```
budget_remaining = 600 - spend_to_date
expected_remaining = 600 * (days_remaining / days_in_month)
ratio = budget_remaining / expected_remaining
budget_shadow = 1 / max(ratio, ε)
```

**Layer 2: Plan Quota Shadow**

```
plan_ratio = remaining_tokens_est / expected_remaining_tokens_est
plan_shadow = 1 / max(plan_ratio, ε)

effective_cost = base_cost * budget_shadow * plan_shadow
```

As quota depletes → shadow spikes → router shifts away from that offer.

### 4.3 "Unlimited" Plans (Copilot)

Cannot price as $0 (would dominate every decision). Use:

- EUC = very_small_floor (e.g., $0.001/MTok)
- Add scarcity shadow to prevent degenerate always-pick
- Apply non-cost constraints: rate limits, quality thresholds

---

## 5. Budget Engine & $600/Month Control

### 5.1 Monthly Allocation

```
Total: $600/month
├── Fixed subscriptions: ~$200 (Claude Max, Codex, Cursor, etc.)
├── API pool: ~$300
└── Self-host infra: ~$100
```

### 5.2 Role-Level Budget Allocation (Example)

| Role           | Allocation |
| -------------- | ---------- |
| code_complex   | 40%        |
| doc_writer     | 20%        |
| fast_chat      | 15%        |
| agent_workflow | 25%        |

### 5.3 Degraded Mode

When budget burn crosses 85%:

- Disable premium offers
- Force cache-first behavior
- Prioritize self-host / low-cost API models
- User receives "degraded mode" metadata in response

### 5.4 Daily Burn Tracker

```
expected_daily_burn = remaining_budget / days_remaining
If actual_burn > expected → increase global shadow multiplier, restrict premium roles
```

---

## 6. Quality Index with Spotty Benchmarks

### 6.1 Problem

Benchmarks are sparse: Model A has 5/8, Model B has 6/8, but missing sets differ. Naive averaging produces garbage rankings.

### 6.2 Solution: Two-Part Quality System

**Offline Quality (from benchmark table)**

1. Normalize per benchmark: z = (score - mean_b) / std_b
2. Impute missing via shrinkage to family mean:
   ```
   imputed_z(offer,b) = λ * mean_z(family,b) + (1-λ) * mean_z_global(b)
   ```
3. Role weights + missingness penalty:
   ```
   coverage = (# real benchmarks present) / (total in role-set)
   offline_quality_adj = offline_quality * (0.6 + 0.4 * coverage)
   ```

**Online Quality (from your reality)**

- test_pass_rate, lint/build success
- "needed escalation" rate
- tool/schema adherence

**Final Blend**

```
q = sigmoid(offline_quality_adj) * (1 - ρ(n)) + online_quality * ρ(n)
ρ(n) = n / (n + k)   # n = eval'd tasks for offer+role
```

Early on: benchmarks guide. Later: your data wins.

---

## 7. Project-Specific Catalog (Ground Truths)

### 7.1 Subscription Plans (From User)

| Plan                                    | Monthly | Notes                                                  |
| --------------------------------------- | ------- | ------------------------------------------------------ |
| Claude Max                              | $200    | ~3B tok/mo (dynamic, across 3 models, includes cached) |
| Codex                                   | $200    | ~11B tok/mo                                            |
| Cursor                                  | $200    | ~$600 usage equivalent                                 |
| Minimax                                 | $40     | 300 prompts / 5 hours                                  |
| Copilot Student Pro                     | Free    | Unlimited completions; 300 premium requests/mo (Pro)   |
| GLM Max                                 | $80     | 3× usage vs Claude (on paper)                          |
| Gemini/Antigravity                      | $20     | Free plans via Google AI Premium                       |
| Promo (Kilo, Roo, Opencode, Kimi, Qwen) | Varies  | Rotating free/cheap models                             |

### 7.2 Offer ID Examples (Project Context)

```
claude-ui:max:sonnet-4.6
claude-ui:max:opus-4.6
openai:codex-sub:gpt-5.3-codex-medplus
openai:codex-sub:gpt-5.3-codex-spark-medplus
cursor:sub:blended
copilot:student:gpt-5-mini
copilot:student:gpt-4.1
glm:max:glm-5-code
google:premium:gemini-3-pro
google:premium:gemini-3-flash
minimax:sub:m2.5
openrouter:payg:deepseek-v3.2
promo:harness:kilo|roo|opencode:<rotating>
```

### 7.3 Models (Project Context)

- Gemini 3 Pro, 3 Flash
- GLM-5, 5-code
- Claude 4.6 Sonnet, Opus, 4.5 Haiku
- GPT 5.3 Codex (med+), 5.3 Codex Spark (med+)
- MiniMax M2.5
- Kimi K2.5
- DeepSeek V3.2
- Qwen 3.5 variants
- GPT 4.1, GPT 5 mini (0× via Copilot - true unlimited)

---

## 8. Ingestion Pipelines

### 8.1 Pipeline 1: Offer & Metadata

```
[Provider APIs]     [Docs/HTML]     [Self-host Fleet]
      |                 |                |
      +-------> [Adapters / Scrapers] <---+
                       |
                       v
              [Normalizer + Validator]
                       |
                       v
               [Offer Registry (db)]
                       |
                       v
             [Offer Snapshot (immutable)]
```

**Sources**:

- OpenRouter Models API
- Vercel AI Gateway model mappings
- Direct provider docs/APIs
- Self-host registry (inference fleet)
- LiteLLM Proxy (unified API, cost tracking)

### 8.2 Pipeline 2: Telemetry

```
[Router Calls]
       |
       v
[Event Log / Queue] ---> [Stream Aggregator] ---> [Telemetry DB]
                                 |
                                 v
                       [Telemetry Snapshot]
                                 |
                                 v
                           (Hot Path)
```

**Per-request metrics**: latency, tokens in/out, cache hit/miss, errors, output schema validity

### 8.3 Pipeline 3: Economics

```
[Sub Dashboards] [Billing APIs] [Your Metering]
       |              |             |
       +-------> [Plan Adapters / Scrapers]
                      |
                      v
           [Commercial Engine]
   (quota, multipliers, throttle, shadow)
                      |
                      v
        [Effective Cost Table + Budgets]
                      |
                      v
                 (Hot Path)
```

---

## 9. API Processes & User Journeys

### 9.1 Router API (Hot Path)

**POST /v1/route** — Route + execute (one stop)

```json
// Request
{
  "role": "code_complex",
  "messages": [...],
  "hard": {
    "maxCostUsd": 0.12,
    "maxLatencyMsP95": 2500,
    "minQuality": 0.78,
    "needsTools": true,
    "needsJson": false,
    "minContextTokens": 32000
  },
  "soft": {
    "optOrder": ["quality", "cost", "speed"],
    "epsilon": { "quality": 0.02, "cost": 0.10, "speed": 0.15 }
  }
}

// Response
{
  "response": {...},
  "routeTrace": {
    "selectedOfferId": "openrouter:anthropic:claude-opus:us-east",
    "paretoSet": ["...", "..."],
    "fallbackChain": ["...", "..."],
    "fallbackUsed": false,
    "scores": {
      "speedScore": 1880,
      "costUsd": 0.083,
      "qualityScore": 0.84
    }
  },
  "usage": { "promptTokens": 12450, "completionTokens": 2800 }
}
```

**POST /v1/plan** — Dry-run (route decision only, no execution)

### 9.2 Hot Path Data Model

Router runs off **snapshots** (fast, deterministic):

- OfferSnapshot (capabilities + base pricing)
- TelemetrySnapshot (latency/errors/adherence)
- EconomicsSnapshot (effective cost + shadow price + budget state)
- QualitySnapshot (per-role quality indices)

---

## 10. Mapping to LiteLLM & Project Architecture

### 10.1 Concept Mapping

| Helios / Pareto Concept | LiteLLM Equivalent                     | Project Component                                 |
| ----------------------- | -------------------------------------- | ------------------------------------------------- |
| Offer                   | Deployment (model + provider + config) | `harness_model_mapping`, `model_indices.json`     |
| Offer Registry          | Router model_list                      | `litellm_router.py`, `catalog.py`                 |
| Commercial Engine       | Cost tracking, budget                  | `cost_tracker.py`, custom                         |
| Shadow Pricing          | Not built-in                           | **Extend** cost_tracker                           |
| Pareto Selection        | simple-shuffle, cost-based-routing     | **Extend** routing strategies                     |
| Responses API           | Chat Completions                       | `cliproxy_adapter.py`, Responses→Chat translation |
| Data Plane              | LiteLLM Proxy                          | `litellm_router.py`                               |
| Control Plane           | Config + custom services               | Offer Registry, Economics, Quality                |

### 10.2 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Codex CLI / Claude Code / Droid                    │
│                     (Responses API or Chat Completions)                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    cliproxy_adapter.py (Responses API Handler)            │
│  - Translates Responses API ↔ Chat Completions                           │
│  - THGENT_USE_LITELLM_ROUTER=1 → route via LiteLLM                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LiteLLM Router (Data Plane)                            │
│  - 100+ providers                                                       │
│  - simple-shuffle, cost-based, latency-based                             │
│  - Fallbacks, caching, retries                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            OpenRouter      Vercel AI Gateway    Direct Providers
            (300+ models)   (BYOK)              (Anthropic, etc.)
```

### 10.3 Gaps to Fill (Pareto → LiteLLM)

| Gap               | Solution                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------- |
| Shadow pricing    | Custom callback / middleware in LiteLLM; or pre-filter deployments by effective cost          |
| Pareto frontier   | Custom routing strategy plugin; or pre-compute ranked list, pass to LiteLLM as fallback chain |
| Offer abstraction | Map offers → LiteLLM deployments; one deployment per offer                                    |
| Quality index     | Pre-filter by min quality; or weight deployments by quality in custom strategy                |
| Budget engine     | Integrate with cost_tracker; enforce caps before routing                                      |

### 10.4 Recommended Phased Approach

**Phase 1**: LiteLLM Router + Responses API adapter (existing plan)

- Single translation layer
- Basic routing (model selection, fallbacks)
- Cost tracking

**Phase 2**: Offer Registry + Economics Snapshot

- Canonical offers.yaml, plans.yaml
- Shadow pricing engine (background job)
- Effective cost in routing decision

**Phase 3**: Pareto + Lexicographic Router

- Custom routing strategy or wrapper
- Hard constraints → Pareto → Lexi
- Full fallback chain generation

**Phase 4**: Quality Index + Budget Engine

- Benchmark ingestion + imputation
- Online quality from harness logs
- Role budgets, degraded mode

---

## 11. Implementation Roadmap

### 11.1 Immediate (Align with CODEX_LITELLM_INTEGRATION_PLAN)

1. LiteLLM Router Responses API handler
2. cliproxy_adapter.py → LiteLLM when THGENT_USE_LITELLM_ROUTER=1
3. Model mapping from harness_model_mapping

### 11.2 Short-Term (Pareto Foundation)

1. Canonical schemas: offers.yaml, plans.yaml, models.yaml
2. Adapters: OpenRouter Models API, Vercel usage, LiteLLM spend
3. Telemetry pipeline: log per-request metrics
4. Hard constraint filter + basic cost-based routing

### 11.3 Medium-Term (Full Pareto)

1. Shadow pricing engine
2. Pareto frontier computation
3. Lexicographic selection
4. Fallback chain by failure type

### 11.4 Long-Term (Quality + Budget)

1. Quality index (benchmarks + online)
2. Budget allocator ($600/month)
3. Degraded mode
4. Learned routing (RouteLLM-style) — optional V2

---

## Appendix A: Catalog Schema Snippets

### models.yaml (capabilities)

```yaml
models:
  - modelId: claude-opus
    family: claude
    capabilities:
      tools: true
      jsonMode: true
      vision: false
      maxContextTokens: 1000000
      maxOutputTokens: 8192
  - modelId: gemini-flash
    family: gemini
    capabilities:
      tools: true
      jsonMode: true
      vision: true
      maxContextTokens: 1048576
```

### offers.yaml (routable units)

```yaml
offers:
  - offerId: openrouter:claude-opus:us-east
    modelId: claude-opus
    provider: openrouter
    endpoint: https://openrouter.ai/api/v1/chat/completions
    region: us-east
    planId: openrouter-payg
    pricing:
      inputPerMTokUsd: 5.00
      outputPerMTokUsd: 25.00
    limits:
      rpm: 600
      tpm: 600000
  - offerId: copilot:student:gpt-5-mini
    modelId: gpt-5-mini
    provider: copilot
    planId: copilot-pro
    pricing:
      type: premium_request_bucket
      eucPerMTokUsd: 0.001
```

### plans.yaml (subscriptions)

```yaml
plans:
  - planId: codex-sub
    type: fixed_bucket_tokens
    provider: openai
    monthlyFeeUsd: 200
    priorTokPerMonth: 11000000000
  - planId: copilot-pro
    type: premium_request_bucket
    monthlyFeeUsd: 0
    entitlements:
      premiumRequestsIncluded: 300
      unlimitedCompletions: true
```

---

## Appendix B: References

- **chatgpt3.md**, **chatgpt4.md** — Source ChatGPT conversations
- **ULTRA_ADVANCED_ROUTER_RESEARCH.md** — OpenRouter, LiteLLM, Portkey, Helicone, Semantic Router
- **CODEX_LITELLM_INTEGRATION_PLAN.md** — Codex + LiteLLM integration
- **LITELLM_HARNESS_MASTER_PLAN.md** — Harness unification
- **COMPLETE_PLAN_AND_RESEARCH.md** — Master index

---

**Document complete. Ready for implementation planning.**
