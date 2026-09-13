<DONE>
# Pareto Router + Auto Router Integration

**Date**: 2026-02-18
**Status**: Implemented (Full Plan)
**Purpose**: Full integration of Pareto router upgrades and auto router with Gemini Flash classifier

## Implementation Status (Full Spec)

| Phase | Item                              | Status                                                                                   |
| ----- | --------------------------------- | ---------------------------------------------------------------------------------------- |
| P0    | Canonical schemas (offers, plans) | `config/routing/offers.schema.yaml`, `plans.schema.yaml`                                 |
| P0    | Route trace output                | `RouteTrace`, `select_offer_with_trace()`, in `route_contract` when `--include-contract` |
| P1    | Shadow pricing                    | `_get_shadow_multiplier()` in pareto_router, applied to effective_cost                   |
| P1    | Economics integration             | cost_tracker + cost_budget_mtd for shadow                                                |
| P4    | Fallback by failure type          | `FAILURE_TYPE_FALLBACK_ORDER` (rate_limit, timeout, schema_tool)                         |
| P4    | LiteLLM Pareto                    | `policy=pareto` → cost-based; `get_pareto_preferred_model()`                             |

---

## 1. Pareto Router

### 1.1 Design

- **Hard constraints** → filter by min_quality, max_cost_weight
- **Pareto frontier** → non-dominated offers on (speed, cost, quality)
- **Lexicographic tie-break** → quality → cost → speed (default order)

### 1.2 Components

| File                                   | Purpose                                                                                |
| -------------------------------------- | -------------------------------------------------------------------------------------- |
| `src/thegent/routing/pareto_router.py` | Pareto selection logic, Offer model, `select_offer()`, `select_offer_with_fallbacks()` |

### 1.3 Usage

```python
from thegent.routing.pareto_router import select_offer, select_offer_with_fallbacks

# Single best offer
route = select_offer(complexity_tier="moderate", min_quality=0.6)
# Returns (provider, model_alias) or None

# Primary + fallback chain
chain = select_offer_with_fallbacks(complexity_tier="complex", k=3)
# Returns [(provider, model), ...]
```

### 1.4 Policy Integration

- **`resolve_route(model_id, policy="pareto")`** — Uses Pareto among routes for that model
- **`--routing pareto`** — CLI option for model-first routing

---

## 2. Auto Router

### 2.1 Design

1. **Classify** prompt via headless Gemini Flash (simple | moderate | complex)
2. **Select** (provider, model) from Pareto frontier based on complexity
3. **Return** resolved agent + model for run_impl

### 2.2 Components

| File                                 | Purpose                                                     |
| ------------------------------------ | ----------------------------------------------------------- |
| `src/thegent/routing/auto_router.py` | `auto_route()`, classifier system prompt, Gemini Flash call |

### 2.3 Usage

```bash
# Auto route: agent + model selected by classifier + Pareto
thegent run auto "Fix the typo in README"
thegent run -M auto "Refactor the auth module for OAuth2"

# Or via env
THGENT_AUTO_ROUTER_ENABLED=1 thegent run "Any prompt"
```

Agent or model `"auto"` triggers the auto router.

### 2.4 Config

| Env                                   | Default        | Description                                         |
| ------------------------------------- | -------------- | --------------------------------------------------- |
| `THGENT_AUTO_ROUTER_ENABLED`          | 1              | Enable auto router when agent/model is "auto"       |
| `THGENT_AUTO_ROUTER_CLASSIFIER_MODEL` | gemini-3-flash | Model for classification                            |
| `THGENT_AUTO_ROUTER_USE_CLASSIFIER`   | 1              | Use Gemini Flash to classify; if 0, assume moderate |
| `THGENT_AUTO_ROUTER_MIN_QUALITY`      | 0.0            | Min quality floor                                   |
| `THGENT_AUTO_ROUTER_MAX_COST_WEIGHT`  | 2.0            | Max cost weight                                     |

### 2.5 Classifier System Prompt

Robust role: classify into `simple` | `moderate` | `complex` with JSON output:

```json
{"complexity": "simple" | "moderate" | "complex", "reason": "brief one-line reason"}
```

- **simple**: trivial edits, one-liners, format changes
- **moderate**: multi-file, features, debugging, docs, tests
- **complex**: architecture, security-critical, multi-step reasoning

### 2.6 Fallback

If classifier or Pareto fails → `antigravity/gemini-3-flash`

---

## 3. Integration Points

| Location            | Change                                              |
| ------------------- | --------------------------------------------------- |
| `cli_impl.run_impl` | Auto router block when agent="auto" or model="auto" |
| `cli_impl.bg_impl`  | Same auto router block                              |
| `models/catalog.py` | `policy="pareto"` in `resolve_route()`              |
| `config.py`         | `auto_router_*` settings                            |
| `main.py`           | Help text for agent/model "auto"                    |

---

## 4. Quality Proxy

Rough quality tiers (0–1) per model in `pareto_router.QUALITY_PROXY`:

- claude-opus-4.6: 0.95
- claude-sonnet-4.6: 0.88
- gpt-5.3-codex-high: 0.92
- gemini-3-flash: 0.78
- glm-5: 0.78
- etc.

---

## 5. Canonical Schemas (Phase 0)

| File                                | Purpose                                                                   |
| ----------------------------------- | ------------------------------------------------------------------------- |
| `config/routing/offers.schema.yaml` | Offer definitions (offerId, modelId, provider, planId, pricing)           |
| `config/routing/plans.schema.yaml`  | Plan types (payg_token, fixed_bucket, prompt_rate_limited, volatile_free) |

## 6. Shadow Pricing (Phase 1)

- `_get_shadow_multiplier()`: 1 / max(remaining_ratio, ε)
- Uses cost_tracker.get_budget_remaining() and cost_budget_mtd
- effective_cost = cost_weight \* shadow_multiplier
- Applied in Pareto selection and dominance checks

## 7. Failure-Type Fallback (Phase 4)

| Failure     | Opt order              |
| ----------- | ---------------------- |
| rate_limit  | cost → speed → quality |
| timeout     | speed → cost → quality |
| schema_tool | quality → cost → speed |

## 8. Related Research

- [CHATGPT_PARETO_DEEP_01_FOUNDATIONS.md](./CHATGPT_PARETO_DEEP_01_FOUNDATIONS.md)
- [CHATGPT_PARETO_ROUTER_EXTENSION.md](./CHATGPT_PARETO_ROUTER_EXTENSION.md)
- [CHATGPT_PARETO_DEEP_06_HELIOS_UNIFIED_SPEC.md](./CHATGPT_PARETO_DEEP_06_HELIOS_UNIFIED_SPEC.md)
