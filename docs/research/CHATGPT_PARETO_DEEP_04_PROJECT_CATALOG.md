<DONE>
# ChatGPT Pareto Router Deep Research — Part 4: Project Catalog & Ground Truths

**Source**: chatgpt3.md, chatgpt4.md
**Date**: 2026-02-18
**Scope**: Project-specific subscriptions, Copilot schema, catalog examples, worked routing examples

---

## 1. Ground Truth Subscriptions (From User)

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

### Copilot Tiers (Clarified)

| Tier              | Premium Requests | Overage       | Notes                    |
| ----------------- | ---------------- | ------------- | ------------------------ |
| **Free**          | 50 premium/mo    | —             | 2,000 inline suggestions |
| **Pro** (Student) | 300 premium/mo   | $0.04/request | Unlimited completions    |
| **Pro+**          | 1,500 premium/mo | $0.04/request | Full model access        |

**Key**: Premium requests are **weighted by model**. Some models (GPT-4.1, GPT-5 mini) are **0×** — don't count against usage.

---

## 2. Copilot Weighted Unit Model

### 2.1 Unit Multipliers (Examples)

| Model             | Multiplier |
| ----------------- | ---------- |
| Claude Sonnet 4.6 | 1.0×       |
| Claude Opus 4.6   | 2.0×       |
| Claude Haiku 4.5  | 0.33×      |
| Gemini 3 Pro      | 0.1×       |
| Gemini 3 Flash    | 0.1×       |
| GPT-4.1           | 0×         |
| GPT-5 mini        | 0×         |

### 2.2 Plan Schema (Copilot Pro Student)

```json
{
  "planId": "copilot-pro-student",
  "type": "weighted_unit_bucket",
  "monthlyFeeUsd": 0,
  "resetsAt": "2026-03-01T00:00:00Z",
  "entitlements": {
    "premiumUnitsIncluded": 300,
    "premiumUnitOverageUsd": 0.04,
    "unlimitedCompletions": true
  },
  "unitMultipliers": {
    "claude-sonnet-4.6": 1.0,
    "claude-opus-4.6": 2.0,
    "claude-haiku-4.5": 0.33,
    "gemini-3-pro": 0.1,
    "gemini-3-flash": 0.1,
    "gpt-4.1": 0.0,
    "gpt-5-mini": 0.0
  },
  "observed": {
    "premiumUnitsUsed": 37.2,
    "avgTokensInByModel": {},
    "avgTokensOutByModel": {}
  }
}
```

### 2.3 Copilot Effective Cost (0× Models)

For m = 0 (GPT-4.1, GPT-5 mini):

- Monetary cost = 0
- Add: floor_cost + volatility_penalty + opportunity_penalty
- Floor cost tiny (e.g., $0.002 equivalent) to prevent degenerate "always pick free" during tie-breaks

### 2.4 Copilot Effective Cost (Non-0×)

```
units consumed per request = multiplier(model)
implied_cost = unit_overage_usd * units_consumed
unit_shadow = 1 / max(remaining_units / expected_remaining_units, ε)
effective_cost = implied_cost * unit_shadow * budget_shadow
```

---

## 3. Offer ID Examples (Project Context)

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

---

## 4. Models (Project Context)

- Gemini 3 Pro, 3 Flash
- GLM-5, 5-code
- Claude 4.6 Sonnet, Opus, 4.5 Haiku
- GPT 5.3 Codex (med+), 5.3 Codex Spark (med+)
- MiniMax M2.5
- Kimi K2.5
- DeepSeek V3.2
- Qwen 3.5 variants
- GPT 4.1, GPT 5 mini (0× via Copilot — true unlimited)

---

## 5. Catalog Schema Examples

### 5.1 models.yaml (Capabilities)

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
      maxOutputTokens: 8192

  - modelId: qwen-coder-32b
    family: qwen
    capabilities:
      tools: false
      jsonMode: false
      vision: false
      maxContextTokens: 65536
      maxOutputTokens: 8192
```

### 5.2 plans.yaml

```yaml
plans:
  - planId: openrouter-payg
    type: payg
    provider: openrouter
    monthlyFeeUsd: 0
    includedTokens: null
    throttle: none

  - planId: google-vertex-sub
    type: subscription
    provider: google
    monthlyFeeUsd: 200
    included:
      gemini-flash:
        inputTokens: 200000000
        outputTokens: 50000000
    seasonalMultipliers:
      - name: winter_promo
        starts: 2026-02-01
        ends: 2026-02-28
        multiplier: 2.0

  - planId: codex-sub
    type: fixed_bucket_tokens
    provider: openai
    monthlyFeeUsd: 200
    priorTokPerMonth: 11000000000

  - planId: copilot-pro-student
    type: weighted_unit_bucket
    premiumUnitsIncluded: 300
    unitOverageUsd: 0.04
```

### 5.3 offers.yaml (Routable Units)

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
      cacheReadPerMTokUsd: 0.50
      cacheWritePerMTokUsd: 6.00
    limits:
      rpm: 600
      tpm: 600000
      concurrency: 50

  - offerId: copilot:gpt-5-mini:chat
    modelId: gpt-5-mini
    provider: copilot
    planId: copilot-pro-student
    pricingHint: { type: "copilot_units", unitMultiplier: 0.0 }
    capabilities:
      tools: true
      json: true
      maxContextTokens: 128000

  - offerId: codex:sub:gpt-5.3-codex-medplus
    modelId: gpt-5.3-codex-medplus
    provider: openai
    planId: codex-sub
    pricing:
      type: fixed_bucket_tokens
      feeUsd: 200
      priorTokPerMonth: 11000000000
```

---

## 6. Snapshot Schemas (Hot Path)

### EconomicsSnapshot

```json
{
  "asOf": "2026-02-18T07:00:00Z",
  "global": { "budgetRemainingUsd": 412.3, "budgetShadow": 1.15 },
  "plans": {
    "copilot-pro": {
      "shadow": 1.02,
      "effectiveUnitCost": { "inPerMTokUsd": 0.09, "outPerMTokUsd": 0.09 },
      "premiumRequestsRemaining": 263
    },
    "codex-sub": {
      "shadow": 1.3,
      "effectiveUnitCost": { "inPerMTokUsd": 0.02, "outPerMTokUsd": 0.02 }
    }
  }
}
```

### TelemetrySnapshot

```json
{
  "offers": {
    "copilot:gpt-5-mini:chat": {
      "p95ms": 1100,
      "tps": 110,
      "errRate": 0.02,
      "jsonAdherence": 0.98
    },
    "codex:gpt-5.3-codex-medplus": {
      "p95ms": 1500,
      "tps": 90,
      "errRate": 0.01,
      "jsonAdherence": 0.995
    }
  }
}
```

### QualitySnapshot

```json
{
  "offers": {
    "copilot:gpt-5-mini:chat": { "code_complex": 0.78, "code_simple": 0.84 },
    "codex:gpt-5.3-codex-medplus": { "code_complex": 0.88, "code_simple": 0.9 }
  },
  "confidence": {
    "copilot:gpt-5-mini:chat": { "code_complex": 0.55 },
    "codex:gpt-5.3-codex-medplus": { "code_complex": 0.82 }
  }
}
```

---

## 7. Worked Example: Routing to an Offer

**Request**: code_complex, inTok=12,000, outTok=2,500

**Candidates**: codex-sub, copilot:gpt-5-mini, openrouter:deepseek-v3.2

### Cost per Offer

**A) Codex sub (fixed bucket)**

```
EUC ~ $0.0182/MTok × shadow 1.3
Total tokens = 14,500
base = 14500 * (0.0182 / 1e6) = $0.000264
effective = base * 1.3 = $0.000343
```

**B) Copilot chat (premium requests)**

```
avg total tokens per premium request = 20,000
Implied EUC = 0.04/20000 = $2/MTok
shadow = 1.1
base = 14500 * (2 / 1e6) = $0.029
effective = 0.029 * 1.1 = $0.032
```

**C) OpenRouter payg**

```
base = 12000*(0.5/1e6) + 2500*(1/1e6) = $0.0085
effective = base * budget_shadow(1.15) = $0.0098
```

**Insight**: Copilot chat may not be cheapest despite "free student" — premium requests are scarce and have implicit replacement cost.

---

## 8. Plan Mapping (Ground Truths → Schema)

| User Plan          | Schema Type                                                |
| ------------------ | ---------------------------------------------------------- |
| Claude Max $200    | fixed_bucket_tokens, prior 3B tok/mo                       |
| Codex $200         | fixed_bucket_tokens, prior 11B tok/mo                      |
| Cursor $200        | subsidized_payg (3× value prior) + learn from logs         |
| Minimax $40        | prompt_rate_limited                                        |
| Copilot student    | weighted_unit_bucket, 300 units, 0× for GPT-4.1/GPT-5 mini |
| GLM Max $80        | fixed_bucket or prompt-limited; learn EUC from logs        |
| Gemini premium $20 | fixed_bucket / unlimited depending on limits               |
| Promo harnesses    | volatile_free, high volatility penalty                     |

---

## References

- chatgpt3.md, chatgpt4.md
- CHATGPT_PARETO_DEEP_01_FOUNDATIONS.md
- CHATGPT_PARETO_DEEP_02_INDICES_ECONOMICS.md
- CHATGPT_PARETO_ROUTER_EXTENSION.md
