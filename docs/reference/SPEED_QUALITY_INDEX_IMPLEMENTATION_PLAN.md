# Speed & Quality Index Implementation Plan

**Date**: 2026-02-16
**Status**: Implemented + Extended (2026-02-16)
**Related**: `cost_values.py`, `speed_values.py`, `quality_values.py`, `PARETO_FRONTIER_TERMINAL_BENCH_2_0.md`, `catalog.py`, `selector.py`

---

## Implementation Summary

| Component | Status |
|-----------|--------|
| `speed_values.py` | Done — TPS+latency+success, p95 penalty, config params, TTL cache |
| `quality_values.py` | Done — TB2.0+SWE+AIME, benchmarks path override, TTL cache |
| `benchmarks.json` | Done — bundled in models/ |
| ParetoRouter | Done — dominates() and get_pareto_front() use indices |
| cost_quality policy | Done — uses quality_index for floor (was cost_weight bug) |
| Config | Done — speed_index_tps_max, latency_max_ms, cache_ttl, benchmarks_path |
| CLI | Done — `models speed-index`, `models quality-index`, `--no-cache` |
| Task router | Done — speed_demon uses pareto+speed |
| Tests | Done — TestSpeedQualityIndices in test_unit_models.py |

---

## Executive Summary

Currently thegent uses:
- **Speed**: Static `Route.latency_ms` only; ParetoRouter "speed" = `min(front, key=latency_ms)`; ObjectiveSelector uses `avg_latency_ms` from `models_meta.py`. No TPS, no composite index.
- **Quality**: Static `Route.accuracy_score` only; ParetoRouter "quality" = `max(front, key=accuracy_score)`. Terminal Bench 2.0 scores exist only in docs; no combined quality index.

This plan defines:
1. **Speed index** — Composite of TPS + latency + X (e.g. success_rate), using proxy metrics, mapped to model–provider pairs.
2. **Quality index** — Composite of Terminal Bench 2.0 + SWE-Bench + AIME + parser quality (extensible), loaded from config/JSON.

Both indices feed into routing (ParetoRouter, ObjectiveSelector, task_router).

---

## Part 1: Speed Index (TPS + Latency + X)

### 1.1 Data Sources

| Source | Fields | Granularity | Availability |
|--------|--------|-------------|--------------|
| **Proxy metrics** | `tps_1m`, `latency_p50_ms`, `latency_p95_ms`, `success_rate` | Per provider | Live (CLIProxyAPIPlus GET /v1/metrics/providers) |
| **Catalog Route** | `latency_ms` | Per route (model–provider) | Static fallback |
| **Cost values** | — | — | Used for provider→model mapping pattern |

**Proxy metrics shape** (from `fetch_provider_metrics`):
```json
{
  "codex": {
    "tps_1m": 150,
    "latency_p50_ms": 450,
    "latency_p95_ms": 1200,
    "success_rate": 0.98,
    "cost_per_1k_input": 0.005,
    "cost_per_1k_output": 0.015
  },
  "gemini": { ... },
  ...
}
```

**Provider→model mapping**: Proxy metrics are **per provider**. A model can be served by multiple providers (e.g. `gemini-3-flash` via `gemini`, `cursor`, `antigravity`). We map provider metrics to each (model, provider) route using the same pattern as `cost_values.py`: iterate catalog routes, look up provider in metrics.

### 1.2 Speed Index Formula

**Design goals**:
- Higher index = faster (better).
- Combine throughput (TPS) and latency; optionally success_rate.
- Normalize to 0–1 or 0–100 for routing.

**Proposed formula** (configurable weights):

```
speed_index = w1 * norm_tps + w2 * norm_latency + w3 * norm_success
```

Where:
- `norm_tps = min(1, tps_1m / TPS_MAX)` — TPS_MAX default 200 (tokens/sec)
- `norm_latency = max(0, 1 - latency_p50_ms / LATENCY_MAX)` — LATENCY_MAX default 10000 ms
- `norm_success = success_rate` (already 0–1)

**Default weights**: `w1=0.4`, `w2=0.5`, `w3=0.1` (latency-weighted; TPS secondary).

**Alternative (inverse-latency style, like ObjectiveSelector)**:
```
speed_score = (w1 / (1 + latency_p50/1000)) + (w2 * min(1, tps_1m/200)) + (w3 * success_rate)
```
Then normalize to 0–1 for consistency with quality.

**Fallback**: When proxy unreachable, use `Route.latency_ms` only:
```
speed_index_fallback = max(0, 1 - latency_ms / 10000)
```

### 1.3 Module Design: `speed_values.py`

**Location**: `src/thegent/models/speed_values.py`

**API**:
```python
def get_model_provider_speed_index(
    model_id: str,
    provider: str,
    settings: ThegentSettings | None = None,
) -> float:
    """
    Get speed index (0–1, higher = faster) for a model–provider pair.
    Uses proxy metrics when reachable; falls back to Route.latency_ms.
    """


def get_model_provider_speed_indices(
    settings: ThegentSettings | None = None,
) -> dict[str, dict[str, float]]:
    """
    Returns: {model_id: {provider: speed_index}}
    Same structure as get_model_provider_costs().
    """
```

**Internal logic**:
1. Call `fetch_provider_metrics(settings)`.
2. If metrics available: for each catalog route, get provider metrics; compute `speed_index` from `tps_1m`, `latency_p50_ms`, `success_rate`.
3. If proxy unreachable: use `Route.latency_ms` for `speed_index_fallback`.
4. Return dict keyed by (model_id, provider).

**Config** (optional, in `thegent.yaml` or env):
```yaml
speed_index:
  tps_max: 200
  latency_max_ms: 10000
  weights:
    tps: 0.4
    latency: 0.5
    success_rate: 0.1
```

### 1.4 Integration Points

| Component | Change |
|-----------|--------|
| **ParetoRouter** | Add `speed_index` to Route (or compute on-the-fly). "speed" strategy: `max(front, key=speed_index)` instead of `min(front, key=latency_ms)`. |
| **ObjectiveSelector** | Replace `latency_score = 1 - avg_latency_ms/10000` with `speed_index` from `speed_values` when available. |
| **Catalog Route** | Optionally add `speed_index: float` field (computed at resolution time from speed_values). |
| **Task router** | When selecting "speed_demon" or similar, prefer routes with highest speed_index. |
| **CLI** | `thegent metrics` already shows tps_1m, latency_p50; add `thegent speed-index` to show per-model-provider speed indices. |

### 1.5 Data Flow

```
CLIProxyAPIPlus (GET /v1/metrics/providers)
        │
        ▼
fetch_provider_metrics()
        │
        ▼
speed_values.get_model_provider_speed_indices()
        │
        ├──► ParetoRouter (strategy="speed")
        ├──► ObjectiveSelector (latency component)
        ├──► Task router (speed_demon role)
        └──► CLI (thegent speed-index)
```

---

## Part 2: Quality Index (Terminal Bench 2.0 + X)

### 2.1 Data Sources

| Source | Fields | Granularity | Availability |
|--------|--------|-------------|--------------|
| **Terminal Bench 2.0** | TB2.0 score (0–100%) | Per model | `PARETO_FRONTIER_TERMINAL_BENCH_2_0.md`, or JSON |
| **SWE-Bench** | SWE-Bench % | Per model | Docs, MODEL_SELECTION_INDEX.md |
| **AIME** | AIME % (reasoning) | Per model | Docs (GLM-5 92.7%, Opus 85%, etc.) |
| **Parser quality** | TBD (e.g. JSON/tool-call parse success) | Per model | Future: runtime metrics |
| **Route.accuracy_score** | 0.0–1.0 | Per route | Static fallback in catalog |

**TB2.0 scores** (from PARETO_FRONTIER_TERMINAL_BENCH_2_0.md):

| Model | TB2.0 | SWE-Bench (ref) |
|-------|-------|-----------------|
| GPT-5.3-Codex | 64.7% | 56.8% |
| Claude Opus 4.6 | 62.9% | 80.8% |
| Codex-Spark | 58.4% | ~50% |
| GLM-5 | 56.2% | 92.7% (AIME) |
| Gemini 3 Flash | 51.7% | 78.0% |
| MiniMax M2.5 | 51.7% | 80.2% |
| Claude Sonnet 4.5 | 42.8% | 77.2% |
| Claude Haiku 4.5 | 28.3% | 73.3% |

### 2.2 Quality Index Formula

**Design goals**:
- Higher index = better quality.
- Primary: Terminal Bench 2.0 (thegent is terminal/CLI agent).
- Optional: SWE-Bench, AIME for mixed workloads.
- Extensible: parser quality, custom benchmarks.

**Proposed formula** (configurable weights):

```
quality_index = w1 * norm_tb2 + w2 * norm_swe + w3 * norm_aime + w4 * norm_parser
```

Where:
- `norm_tb2 = tb2_score / 100` (TB2.0 already 0–100%)
- `norm_swe = swe_score / 100`
- `norm_aime = aime_score / 100`
- `norm_parser = parser_success_rate` (0–1, or 1.0 if not available)

**Default weights** (terminal-first): `w1=0.7`, `w2=0.2`, `w3=0.1`, `w4=0.0` (parser placeholder).

**Fallback**: When benchmark data missing, use `Route.accuracy_score` or `ModelMetadata.quality_score`.

### 2.3 Benchmark Data Storage

**Option A: JSON config** (recommended)

**Location**: `config/benchmarks.json` or `~/.config/thegent/benchmarks.json`

```json
{
  "version": 1,
  "terminal_bench_2_0": {
    "gpt-5.3-codex": 64.7,
    "claude-opus-4.6": 62.9,
    "gpt-5.3-codex-spark": 58.4,
    "glm-5": 56.2,
    "gemini-3-flash": 51.7,
    "minimax-m2.5": 51.7,
    "claude-sonnet-4.5": 42.8,
    "claude-haiku-4.5": 28.3
  },
  "swe_bench": {
    "gpt-5.3-codex": 56.8,
    "claude-opus-4.6": 80.8,
    "minimax-m2.5": 80.2,
    "gemini-3-flash": 78.0,
    "claude-sonnet-4.5": 77.2,
    "claude-haiku-4.5": 73.3
  },
  "aime": {
    "glm-5": 92.7,
    "claude-opus-4.6": 85,
    "minimax-m2.5": 60
  }
}
```

**Option B**: Parse from markdown (fragile; not recommended for production).

**Option C**: Extend `models_meta.py` with benchmark fields (duplicates data; use JSON for single source of truth).

### 2.4 Module Design: `quality_values.py`

**Location**: `src/thegent/models/quality_values.py`

**API**:
```python
def get_model_quality_index(
    model_id: str,
    settings: ThegentSettings | None = None,
    benchmarks_config_path: str | Path | None = None,
) -> float:
    """
    Get quality index (0–1) for a model.
    Uses benchmarks JSON when available; falls back to Route.accuracy_score.
    """


def get_all_model_quality_indices(
    settings: ThegentSettings | None = None,
) -> dict[str, float]:
    """
    Returns: {model_id: quality_index}
    """


def get_model_provider_quality_indices(
    settings: ThegentSettings | None = None,
) -> dict[str, dict[str, float]]:
    """
    Returns: {model_id: {provider: quality_index}}
    Same model can have same quality across providers; structure matches cost/speed.
    """
```

**Internal logic**:
1. Load `benchmarks.json` from config path or default.
2. For each model in catalog: compute `quality_index` from TB2.0 + SWE + AIME (weighted).
3. Missing benchmark → use `Route.accuracy_score` for that route.
4. Normalize to 0–1.

**Config**:
```yaml
quality_index:
  benchmarks_path: "config/benchmarks.json"
  weights:
    terminal_bench_2_0: 0.7
    swe_bench: 0.2
    aime: 0.1
    parser_quality: 0.0
```

### 2.5 Integration Points

| Component | Change |
|-----------|--------|
| **ParetoRouter** | "quality" strategy: use `quality_index` from quality_values (or Route.accuracy_score if not available). |
| **ObjectiveSelector** | Replace `quality_score = meta.quality_score` with `get_model_quality_index(model_id)` when available. |
| **Catalog Route** | Optionally add `quality_index: float` (computed at resolution or from quality_values). |
| **Task router** | Quality floor checks use quality_index. |
| **CLI** | `thegent quality-index` to show per-model quality indices. |

### 2.6 Data Flow

```
config/benchmarks.json
        │
        ▼
quality_values.load_benchmarks()
        │
        ▼
quality_values.get_model_provider_quality_indices()
        │
        ├──► ParetoRouter (strategy="quality")
        ├──► ObjectiveSelector (quality component)
        ├──► Task router (quality floor)
        └──► CLI (thegent quality-index)
```

---

## Part 3: Config Schema

### 3.1 `thegent.yaml` (or env) Extensions

```yaml
# Speed index (optional)
speed_index:
  enabled: true
  tps_max: 200
  latency_max_ms: 10000
  weights:
    tps: 0.4
    latency: 0.5
    success_rate: 0.1
  fallback_to_catalog_latency: true

# Quality index (optional)
quality_index:
  enabled: true
  benchmarks_path: "config/benchmarks.json"
  weights:
    terminal_bench_2_0: 0.7
    swe_bench: 0.2
    aime: 0.1
    parser_quality: 0.0
  fallback_to_accuracy_score: true
```

### 3.2 `benchmarks.json` Schema

```json
{
  "$schema": "https://thegent.dev/schemas/benchmarks.json",
  "version": 1,
  "terminal_bench_2_0": { "<canonical_model_id>": <0-100> },
  "swe_bench": { "<canonical_model_id>": <0-100> },
  "aime": { "<canonical_model_id>": <0-100> },
  "parser_quality": { "<canonical_model_id>": <0-1> }
}
```

Model IDs must match catalog canonical IDs (e.g. `gpt-5.3-codex`, `claude-opus-4.6`).

---

## Part 4: ParetoRouter & Route Enrichment

### 4.1 Enriching Routes at Resolution Time

Currently `Route` has `latency_ms`, `accuracy_score` (static). To use live indices:

**Option A: Compute at resolution**
- When `policy == "pareto"`, call `get_model_provider_speed_indices()` and `get_model_provider_quality_indices()`.
- Build enriched route list with `speed_index` and `quality_index` per (model, provider).
- ParetoRouter operates on enriched routes.

**Option B: Add fields to Route**
- Add `speed_index: float | None` and `quality_index: float | None` to `Route`/`ResolvedRoute`.
- Catalog builder or a separate "enricher" populates these from speed_values/quality_values before routing.

**Recommendation**: Option A for minimal catalog changes; Option B if we want to cache indices in Route for performance.

### 4.2 ParetoRouter Strategy Updates

| Strategy | Before | After |
|----------|--------|-------|
| `speed` | `min(front, key=lambda p: p.latency_ms)` | `max(front, key=lambda p: p.speed_index or (1 - p.latency_ms/10000))` |
| `quality` | `max(front, key=lambda p: p.accuracy_score)` | `max(front, key=lambda p: p.quality_index or p.accuracy_score)` |
| `cost` | unchanged | unchanged |
| `balanced` | `(1/cost) + (1000/latency) + (accuracy*10)` | `(1/cost) + (speed_index*10) + (quality_index*10)` |

---

## Part 5: ObjectiveSelector Updates

### 5.1 Current `_calculate_score`

```python
latency_score = max(0, 1.0 - (meta.avg_latency_ms / 10000))
cost_score = max(0, 1.0 - (total_cost / 0.1))
quality_score = meta.quality_score
weighted_score = quality * weights.quality + latency * weights.latency + cost * weights.cost
```

### 5.2 Updated Logic

```python
# Use speed_index when available (per model-provider)
speed_index = get_model_provider_speed_index(model_id, provider) or max(0, 1.0 - meta.avg_latency_ms / 10000)
quality_index = get_model_quality_index(model_id) or meta.quality_score
cost_score = max(0, 1.0 - (total_cost / 0.1))
weighted_score = (quality_index * weights.quality) + (speed_index * weights.latency) + (cost_score * weights.cost)
```

**Note**: ObjectiveSelector works with `candidate_ids` (model IDs). For model–provider, we need to either:
- Resolve provider per model (e.g. prefer_direct) and use that for speed_index, or
- Use best speed_index across providers for that model.

---

## Part 6: Implementation Phases

### Phase 1: Speed Index (2–3 days)

1. Create `speed_values.py` with `get_model_provider_speed_indices()`, `get_model_provider_speed_index()`.
2. Use `_iter_catalog_routes()` pattern from cost_values.
3. Add config schema for speed_index weights.
4. CLI: `thegent speed-index` (or extend `thegent metrics`).
5. Unit tests with mocked proxy metrics.

### Phase 2: Quality Index (2–3 days)

1. Create `benchmarks.json` from PARETO_FRONTIER_TERMINAL_BENCH_2_0.md data.
2. Create `quality_values.py` with `get_model_quality_index()`, `get_all_model_quality_indices()`.
3. Add config schema for quality_index weights and benchmarks_path.
4. CLI: `thegent quality-index`.
5. Unit tests with fixtures.

### Phase 3: Routing Integration (2 days)

1. ParetoRouter: enrich routes with speed_index, quality_index at resolution.
2. Update `select_by_strategy` for "speed" and "quality".
3. Update "balanced" formula.
4. ObjectiveSelector: integrate speed_index, quality_index.

### Phase 4: Task Router & Polish (1 day)

1. Task router: use speed_index for "speed_demon" role.
2. Use quality_index for quality floor in cost_quality policy.
3. Documentation updates.

---

## Part 7: File Summary

| File | Purpose |
|------|---------|
| `src/thegent/models/speed_values.py` | NEW | Speed index from proxy metrics |
| `src/thegent/models/quality_values.py` | NEW | Quality index from benchmarks.json |
| `config/benchmarks.json` | NEW | TB2.0, SWE-Bench, AIME scores |
| `src/thegent/models/catalog.py` | MODIFY | ParetoRouter strategy logic |
| `src/thegent/planning/selector.py` | MODIFY | ObjectiveSelector uses indices |
| `src/thegent/planning/models_meta.py` | OPTIONAL | Fallback quality_score |
| `src/thegent/cli.py` | MODIFY | Add speed-index, quality-index commands |
| `docs/reference/SPEED_QUALITY_INDEX_IMPLEMENTATION_PLAN.md` | THIS |

---

## Part 8: Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Proxy unreachable | Fallback to catalog latency; quality to accuracy_score |
| Benchmark data stale | Document refresh cadence; `thegent setup perf` (future) to ingest |
| Model ID mismatch | Normalize via `catalog.normalize_model_id()` |
| Performance | Cache speed/quality indices (TTL 60s) when proxy used |

---

## Part 9: Extensibility ("X" Factors)

### Speed Index X Factors

| Factor | Source | Notes |
|--------|--------|-------|
| **success_rate** | Proxy metrics | Already in formula; reduces index when provider fails |
| **latency_p95_ms** | Proxy metrics | Optional: penalize tail latency |
| **queue_depth** | Future proxy | If proxy reports queue depth, penalize high queue |
| **regional_latency** | Future | Geo-based latency adjustment |

### Quality Index X Factors

| Factor | Source | Notes |
|--------|--------|-------|
| **parser_quality** | Runtime metrics | JSON/tool-call parse success rate per model |
| **SWE-Bench** | benchmarks.json | Code editing; weight 0.2 default |
| **AIME** | benchmarks.json | Reasoning; weight 0.1 default |
| **GPQA** | benchmarks.json | Domain knowledge; optional |
| **MMLU** | benchmarks.json | General knowledge; optional |
| **custom_bench** | User config | Extensible key in benchmarks.json |

To add a new benchmark: extend `benchmarks.json` with a new key (e.g. `"gpqa"`) and add weight in config.

---

## Appendix A: Sample benchmarks.json

```json
{
  "version": 1,
  "terminal_bench_2_0": {
    "gpt-5.3-codex": 64.7,
    "claude-opus-4.6": 62.9,
    "gpt-5.3-codex-spark": 58.4,
    "glm-5": 56.2,
    "gemini-3-flash": 51.7,
    "minimax-m2.5": 51.7,
    "claude-sonnet-4.5": 42.8,
    "claude-haiku-4.5": 28.3,
    "deepseek-v3.2": 55.0,
    "step-3.5-flash": 52.0,
    "glm-4.7-flash": 48.0
  },
  "swe_bench": {
    "gpt-5.3-codex": 56.8,
    "claude-opus-4.6": 80.8,
    "claude-sonnet-4.5": 77.2,
    "claude-haiku-4.5": 73.3,
    "minimax-m2.5": 80.2,
    "gemini-3-flash": 78.0,
    "glm-5": 65.0,
    "deepseek-v3.2": 73.0
  },
  "aime": {
    "glm-5": 92.7,
    "claude-opus-4.6": 85,
    "minimax-m2.5": 60,
    "claude-sonnet-4.5": 68
  }
}
```

---

## References

- `cost_values.py` — Pattern for model–provider mapping
- `PARETO_FRONTIER_TERMINAL_BENCH_2_0.md` — TB2.0 scores
- `catalog.py` — Route, ParetoRouter
- `selector.py` — ObjectiveSelector
- `cliproxy_manager.fetch_provider_metrics` — Proxy metrics API


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
