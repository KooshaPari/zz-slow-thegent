<DONE>
# ChatGPT Pareto Router Deep Research — Part 2: Indices & Economics

**Source**: chatgpt3.md, chatgpt4.md
**Date**: 2026-02-18
**Scope**: Speed/Cost/Quality index formulas, shadow pricing, budget engine, plan types

---

## 1. Speed Index (Exact Formulas)

### 1.1 Speed ≠ Latency

For coding workloads, **speed = time to usable answer**, which includes:

- TTFT (time to first token)
- Total latency
- Output length (longer outputs = longer read + parse + post-process)
- Expected turns (agent workflows)

### 1.2 Raw Observables (Per Offer)

| Metric                   | Description         |
| ------------------------ | ------------------- |
| latency_p50, latency_p95 | Request latency     |
| ttft_p50                 | Time to first token |
| tokens_per_second        | Output throughput   |
| error_rate               | Failure rate        |

**Per role**:

- `expected_output_tokens(role, offer)`
- `expected_turns(role)`

### 1.3 Speed Formula

```
predicted_latency = latency_p95(offer)

predicted_generation_time = expected_output_tokens / tokens_per_second

session_time = predicted_latency
             + predicted_generation_time
             + gamma * expected_turns
```

Where `gamma` = penalty per turn (e.g., 300ms–1000ms depending on workflow).

### 1.4 Normalized Speed Score

```
speed_score = session_time / median_session_time_across_offers
```

**Lower is better.** This avoids overweighting raw milliseconds.

### 1.5 Why Not Just Latency?

- Claude Opus may be slow but **concise**
- Gemini Flash may be fast but **verbose**

If verbose models increase output tokens by 40%, they are slower in real usage. So speed must include verbosity.

---

## 2. Cost Index (Exact Formulas)

### 2.1 Base Marginal Cost

```
base_cost = (input_tokens * input_price_per_token)
          + (output_tokens * output_price_per_token)
```

### 2.2 Cache Adjustment

```
effective_input_tokens = input_tokens * (1 - cache_hit_rate)
effective_cost = recompute using adjusted tokens
```

### 2.3 Retry Risk Adjustment

If `error_rate = 5%`:

```
Expected retries = 1 / (1 - error_rate)
cost_adjusted = effective_cost * (1 / (1 - error_rate))
```

This penalizes flaky providers automatically.

### 2.4 Subscription Shadow Pricing (Critical)

If a plan has "included" usage, marginal cost is artificially low. To avoid front-loading:

```
remaining_ratio = remaining_quota / expected_remaining_quota_today
shadow_multiplier = 1 / max(remaining_ratio, ε)
shadow_cost = base_cost * shadow_multiplier
```

As quota depletes:

- remaining_ratio drops
- multiplier increases
- model becomes "more expensive"
- Router shifts away from draining quota

### 2.5 Final Cost Index

```
cost_score = shadow_cost / median_cost_across_offers
```

**Lower is better.**

---

## 3. Quality Index (Exact Formulas)

### 3.1 Requirements

Quality must be:

- Role-specific
- Dynamic
- Measured from your usage

### 3.2 External Baseline

```
normalized_benchmark = (model_score - min_score) / (max_score - min_score)
```

### 3.3 Online Performance Signals (Coding)

Per role track:

- test_pass_rate
- required_escalation_rate
- syntax_validity_rate
- tool_success_rate

Example composite:

```
quality_score = w1 * normalized_benchmark
              + w2 * test_pass_rate
              + w3 * (1 - escalation_rate)
              + w4 * format_adherence
```

All normalized 0–1.

### 3.4 Confidence Adjustment

If offer has low sample size:

```
quality_score_adjusted = quality_score * sqrt(sample_count / threshold)
```

Prevents new models from being overtrusted early.

---

## 4. Plan Types & Effective Unit Cost (EUC)

### 4.1 Plan Type Taxonomy

| Plan Type                  | Description                                     | EUC Calculation                                                               |
| -------------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------- |
| **payg_token**             | OpenRouter payg, direct APIs                    | EUC_in = price_in_per_token, EUC_out = price_out_per_token                    |
| **fixed_bucket_tokens**    | Claude Max, Codex "~11B tokens", GLM "3× usage" | EUC_blended = monthly_fee / expected_tokens_covered                           |
| **premium_request_bucket** | Copilot Pro/Pro+/Free (premium request caps)    | Convert requests→tokens via observed avg; EUC = fee / (requests × avg_tokens) |
| **prompt_rate_limited**    | Minimax "300 prompts / 5 hours"                 | prompts_month × avg_tokens; EUC = fee / expected_tokens                       |
| **volatile_free**          | Promo/preview models                            | EUC = very_small_floor + high volatility penalty                              |
| **daily_quota_bucket**     | Cerebras Code (tokens/day)                      | day_shadow = 1 / max(remaining_today / expected_remaining_today, ε)           |
| **weighted_unit_bucket**   | Copilot (multipliers + 0× models)               | units consumed = multiplier; implied_cost = 0.04 \* m                         |
| **compute_metered**        | NIM self-host                                   | $/token = ($/hour) / (measured_tokens_per_hour)                               |

### 4.2 Fixed Bucket Example (Claude Max / Codex)

```
Claude Max: $200/mo ≈ 3B tokens/mo
EUC = 200 / 3,000,000,000 = $0.0667/MTok

Codex: $200/mo ≈ 11B tokens/mo
EUC = 200 / 11,000,000,000 = $0.0182/MTok
```

Use as **priors**; logs converge to true EUC.

### 4.3 Minimax (Prompt Rate Limited)

```
P = 300 prompts per 5 hours
prompts/day = 300 * (24/5) = 1440
prompts/month ≈ 43,200 (30d)
expected_tokens_month = prompts_month * avgTok
EUC = monthly_fee / expected_tokens_month
```

### 4.4 "Unlimited" Plans (Copilot 0×)

Cannot price as $0 (would dominate every decision). Use:

- EUC = very_small_floor (e.g., $0.001/MTok)
- Add scarcity shadow to prevent degenerate always-pick
- Apply non-cost constraints: rate limits, quality thresholds

---

## 5. Shadow Pricing (Two Layers)

### 5.1 Layer 1: Monthly Budget Shadow

```
budget_remaining = 600 - spend_to_date
expected_remaining = 600 * (days_remaining / days_in_month)
ratio = budget_remaining / expected_remaining
budget_shadow = 1 / max(ratio, ε)
```

If you overspend early, budget_shadow rises → everything "more expensive."

### 5.2 Layer 2: Plan Quota Shadow

```
plan_ratio = remaining_tokens_est / expected_remaining_tokens_est
plan_shadow = 1 / max(plan_ratio, ε)

effective_cost = base_cost * budget_shadow * plan_shadow
```

### 5.3 Cursor / Claude Max / Codex: Robust Token Estimation

Usage is dynamic and includes caching. For each plan maintain:

- monthly_fee
- observed_spend_equivalent (if provider gives $ estimate)
- observed_tokens_total (from harness logs)
- effective_tokens_covered (latent variable)

Update daily with EWMA:

```
tokens_covered_est[today] =
  0.8 * tokens_covered_est[yesterday] +
  0.2 * observed_tokens_total_today * scale_factor
```

---

## 6. Budget Engine

### 6.1 Monthly Budget Model

```
Total monthly budget = $600
├── Fixed subscriptions: ~$200 (Claude Max, Codex, Cursor, etc.)
├── API pool: ~$300
└── Self-host infra: ~$100
```

### 6.2 Daily Burn Tracker

```
expected_daily_burn = remaining_budget / days_remaining
If actual_burn > expected:
  → increase global shadow multiplier
  → restrict premium roles
```

### 6.3 Role-Level Budget Allocation

| Role           | Allocation |
| -------------- | ---------- |
| code_complex   | 40%        |
| doc_writer     | 20%        |
| fast_chat      | 15%        |
| agent_workflow | 25%        |

Each role has `remaining_role_budget`. Shadow pricing also applied at role level.

### 6.4 Budget Rebalancing (Nightly)

- If some roles underspent → redistribute surplus proportionally
- If high-quality model underused → reduce its shadow slightly
- If model too popular → increase shadow

### 6.5 Degraded Mode

When budget burn crosses 85%:

- Disable premium offers
- Force cache-first behavior
- Prioritize self-host / low-cost API models
- User receives "degraded mode" metadata

---

## 7. Pareto Engine Interaction

Each offer has `(speed_score, cost_score, quality_score)`.

**Pareto** keeps all non-dominated offers. An offer A dominates B if:

- speed_A ≤ speed_B
- cost_A ≤ cost_B
- quality_A ≥ quality_B
- at least one strictly better

Pareto frontier typically ends up 2–5 offers.

---

## 8. Adding a New Model / Provider

### 8.1 Lifecycle

1. **Adapter adds offer** → State = "canary"
2. **Canary phase** → 5–10% traffic; collect telemetry
3. **Scoring initialization**:
   - cost: known
   - speed: estimated from first 100 calls
   - quality: benchmark-weighted baseline
4. **After enough data** → quality replaced by live metrics
5. **Confidence threshold met** → state → active; participates fully in Pareto

No hardcoded changes required.

---

## 9. How Everything Interacts (ASCII)

```
                ┌────────────────────┐
                │   Request + Role   │
                └─────────┬──────────┘
                          ▼
               ┌──────────────────────┐
               │ Load Snapshots       │
               │ Speed/Cost/Quality   │
               └─────────┬────────────┘
                         ▼
              Hard Constraint Filter
                         ▼
                 Compute Indices
                         ▼
                 Pareto Frontier
                         ▼
              Lexicographic Pick
                         ▼
                    Execute
                         ▼
                    Log Metrics
                         ▼
           Telemetry + Economics Update
```

---

## References

- chatgpt3.md, chatgpt4.md
- CHATGPT_PARETO_DEEP_01_FOUNDATIONS.md
- CHATGPT_PARETO_ROUTER_EXTENSION.md
