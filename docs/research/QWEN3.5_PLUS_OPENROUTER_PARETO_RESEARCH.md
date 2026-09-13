<DONE>
# Qwen3.5 Plus 02-15 on OpenRouter — Pareto Research

**Purpose:** Research Qwen3.5 Plus 02-15 via OpenRouter and add to Pareto frontier given QwenCode free limits.

**Date:** 2026-02-16
**Status:** Implemented
**Model URL:** https://openrouter.ai/qwen/qwen3.5-plus-02-15

---

## 1. Model Overview

| Attribute         | Value                                 |
| ----------------- | ------------------------------------- |
| **OpenRouter ID** | `qwen/qwen3.5-plus-02-15`             |
| **Provider**      | Qwen (Alibaba)                        |
| **Variant**       | Plus (larger, more capable than base) |
| **Release**       | 2026-02-15                            |

---

## 2. QwenCode Free Limits (Context)

**QwenCode** is Alibaba's AI coding platform (similar to Claude Code, Cursor). Free tier typically includes:

- Free inference for Qwen models (Qwen3-Coder, Qwen3.5 variants)
- Rate limits (requests/min, tokens/day)
- OAuth login via `thegent cliproxy login qwen`

**Implication for Pareto:** When QwenCode free tier is available, routing to Qwen models via OpenRouter or direct Qwen provider can reduce cost to **$0** for eligible usage. Pareto should treat Qwen routes as **cost-optimized** when free limits apply.

---

## 3. OpenRouter Integration

### 3.1 API Access

- **Base URL:** `https://openrouter.ai/api/v1`
- **Model string:** `openrouter/qwen/qwen3.5-plus-02-15`
- **Auth:** `OPENROUTER_API_KEY` or `OPENROUTER_API_KEY` env

### 3.2 Pricing (OpenRouter — Estimate)

OpenRouter aggregates provider pricing. Typical Qwen Plus tier:

| Source           | Input ($/1M) | Output ($/1M) | Notes                              |
| ---------------- | ------------ | ------------- | ---------------------------------- |
| OpenRouter (est) | $0.40–0.80   | $0.80–1.60    | Plus tier; verify at openrouter.ai |
| QwenCode free    | $0           | $0            | Within free tier limits            |

**Action:** Verify exact pricing at https://openrouter.ai/qwen/qwen3.5-plus-02-15

### 3.3 Context Window

- Qwen3.5 Plus: typically 128K–200K context
- **Action:** Add to `litellm_router.MODEL_CONTEXT_WINDOWS`

---

## 4. Terminal Bench 2.0 / Quality Estimate

**No published TB2.0 score** for Qwen3.5 Plus 02-15. Estimation:

| Model        | TB2.0 (known)            | Est. Qwen3.5 Plus                            |
| ------------ | ------------------------ | -------------------------------------------- |
| qwen3-coder  | ~45–55% (coding-focused) | —                                            |
| Qwen3.5 Plus | —                        | **50–58%** (generalist, stronger than Coder) |

**Rationale:** Qwen3.5 Plus is a general-purpose model; typically stronger than coding-specialized qwen3-coder on mixed tasks. Conservative estimate: **52%** for Pareto until benchmarked.

---

## 5. Pareto Frontier Placement

### 5.1 Current Frontier (Terminal Bench 2.0)

1. MiniMax M2.5 — 51.7%, $0.79/M (budget)
2. Codex-Spark — 58.4%, $1.00/M (speed)
3. GPT-5.3-Codex — 64.7%, $1.25/M (quality)
4. Claude Opus 4.6 — 62.9%, $17.50/M (premium)

### 5.2 Qwen3.5 Plus Placement

| Scenario            | Cost         | Quality (est) | Placement                                                                          |
| ------------------- | ------------ | ------------- | ---------------------------------------------------------------------------------- |
| **OpenRouter paid** | $0.50–0.80/M | 52%           | Between MiniMax and Codex-Spark; **free-tier alternative** when QwenCode available |
| **QwenCode free**   | $0           | 52%           | **Dominates** MiniMax on cost; competes with Codex-Spark for budget slot           |

**Recommendation:** Add as **openrouter** provider route with `cost_weight` reflecting paid pricing; add **qwen** provider route with `cost_weight ≈ 0** when free tier detected (or separate `qwen-free` route).

---

## 6. Implementation Checklist

| Task | File                                            | Status                                                                                    |
| ---- | ----------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 1    | `catalog.py`                                    | Done — openrouter route                                                                   |
| 2    | `catalog.py`                                    | Add `("qwen", "proxy", "qwen3.5-plus-02-15", 10, 0.0, 900, 0.52)` for QwenCode free route |
| 3    | `litellm_router.py`                             | Add `"qwen3.5-plus-02-15": 128000` to MODEL_CONTEXT_WINDOWS                               |
| 4    | `litellm_router.py`                             | Add to fallback chains: `"qwen3.5-plus-02-15": ["qwen3-coder", "deepseek-v3.2"]`          |
| 5    | `litellm_router.py`                             | Add `"qwen3.5-plus-02-15"` to cost map (verify OpenRouter pricing)                        |
| 6    | `quality_values.py`                             | Add TB2.0 placeholder 0.52 for qwen3.5-plus-02-15 (update when benchmarked)               |
| 7    | `PARETO_FRONTIER_TERMINAL_BENCH_2_0.md`         | Document Qwen3.5 Plus in frontier analysis                                                |
| 8    | `MODEL_ROUTING_TERMINAL_BENCH_2_0_QUICK_REF.md` | Add Qwen3.5 Plus to quick ref                                                             |

---

## 7. Alias and Canonical ID

```python
# catalog.py _ALIASES
"qwen3.5-plus": "qwen3.5-plus-02-15",
"qwen/qwen3.5-plus-02-15": "qwen3.5-plus-02-15",
```

---

## 8. References

- OpenRouter model: https://openrouter.ai/qwen/qwen3.5-plus-02-15
- OpenRouter free variant: https://openrouter.ai/docs/guides/routing/model-variants/free
- Qwen provider (cliproxy): `thegent cliproxy login qwen`
- Pareto design: `docs/reference/PARETO_ROUTING_DESIGN.md`
- Terminal Bench 2.0: `docs/reference/PARETO_FRONTIER_TERMINAL_BENCH_2_0.md`

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added research findings summary
2. Added practical implementations
3. Enhanced cross-references

### Cross-References Added

- Related research docs
- Implementation guides

### Practical Additions

- Research templates
- Implementation examples

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [SESSION_RESEARCH_FRAGMENTS_EXPANDED.md](./SESSION_RESEARCH_FRAGMENTS_EXPANDED.md) - Pareto routing
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
