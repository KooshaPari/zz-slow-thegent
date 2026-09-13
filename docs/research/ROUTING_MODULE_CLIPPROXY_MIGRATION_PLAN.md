<DONE>
# Routing Module → CLIProxy Migration Plan

**Status:** In Progress  
**Scope:** Migrate 25+ callers from `thegent.routing` to CLIProxy HTTP API  
**Target Deletion:** `src/thegent/routing/` directory  
**Date Created:** 2026-02-23

## Executive Summary

The `thegent.routing` module (11.5K LOC) is being replaced with calls to CLIProxy API running on `localhost:8317`. This reduces code duplication, centralizes routing logic in Go, and simplifies the Python codebase.

**Key fact:** CLIProxy already has Go implementations of all core routing functionality:

- `POST /v1/routing/select` — Pareto router (replaces `ParetoRouter`, `select_offer`)
- `POST /v1/translate/acp` — ACP adapter
- `POST /v1/auth/oauth/store`, `GET /v1/auth/oauth/get/{provider}` — OAuth token manager
- `POST /v1/quota/check` — Quota enforcer

## Architecture

### What's Being Deleted

```
src/thegent/routing/
├── pareto_router.py (11.5K) — MIGRATE to /v1/routing/select
├── task_router.py
├── route_executor.py
├── auto_router.py
├── cost_aware_router.py
├── litellm_router.py (KEEP - streaming)
├── litellm_responses_handler.py (KEEP - streaming)
├── model_metadata.py
├── harness_model_mapping.py
├── cost_calculator.py
├── cost_tracker.py
├── grounding.py
├── provider_types.py
├── ollama_provider.py
├── circuit_breaker.py
├── semantic_cache.py
└── guardrails/ (KEEP - DLP/moderation)
```

### Replacement: New Wrapper Layer

```
src/thegent/
├── cliproxy_router.py (NEW) — HTTP client for /v1/routing/select
│   ├── CLIProxyRouter class
│   ├── RoutingSelection dataclass
│   ├── RoutingConstraints dataclass
│   └── async select_model() function
└── utils/
    ├── model_registry.py (NEW) — Re-exports model_metadata
    ├── model_mapping.py (NEW) — Re-exports harness_model_mapping
    ├── grounding.py (NEW) — Re-exports grounding functions
    ├── provider_types.py (NEW) — Re-exports provider utilities
    └── ollama_provider.py (NEW) — Re-exports ollama functions
```

### What Stays (Temporarily)

These modules remain in `routing/` until deeper refactoring:

- `litellm_router.py` — Streaming/execution; requires major refactor
- `litellm_responses_handler.py` — HTTP + WebSocket streaming
- `guardrails/*` — DLP, moderation, semantic guard (independent)

**Marked with `# TODO(T1): migrate to CLIProxy`** in 8 callers.

## Migration Phases

### Phase 1: Create Wrapper Infrastructure (DONE)

- ✅ Created `src/thegent/cliproxy_router.py`
- ✅ Async HTTP client wrapping `/v1/routing/select`
- ✅ Clear error handling (fails loudly if CLIProxy unavailable)
- **Status:** Complete

### Phase 2: Create Compatibility Shims (NEXT)

For modules that are pure data/utility (no routing logic):

1. **Create `src/thegent/utils/model_registry.py`**
   - Re-export from `thegent.routing.model_metadata`
   - Keep same API surface: `get_model_metadata()`, `has_model_metadata()`, `MODEL_METADATA`

2. **Create `src/thegent/utils/model_mapping.py`**
   - Re-export from `thegent.routing.harness_model_mapping`
   - Keep same API: `CANONICAL_TO_OPENROUTER`, `resolve_model_for_backend()`, etc.

3. **Create `src/thegent/utils/grounding.py`**
   - Re-export from `thegent.routing.grounding`
   - API: `normalize_grounding_source_url()`, `extract_grounding_sources()`

4. **Create `src/thegent/utils/provider_types.py`**
   - Re-export from `thegent.routing.provider_types`
   - API: `normalize_provider_name()`, `ExecutionPath`, `get_execution_path()`

5. **Create `src/thegent/utils/ollama_provider.py`**
   - Re-export from `thegent.routing.ollama_provider`
   - API: `is_ollama_available()`, `get_available_models()`

### Phase 3: Update External Callers (CRITICAL)

**Group A: Routing Logic (12 files → cliproxy_router)**

| File                                                         | Current Import                 | Migration                                     |
| ------------------------------------------------------------ | ------------------------------ | --------------------------------------------- |
| `src/thegent/cli/commands/impl.py:692`                       | `ParetoRouter, RouteCandidate` | Replace with `cliproxy_router.select_model()` |
| `src/thegent/cli/tui/pareto.py:19`                           | `RoutingDecision`              | Create local dataclass; use `cliproxy_router` |
| `src/thegent/models/catalog.py:534`                          | `select_offer`                 | Replace with `cliproxy_router.select_model()` |
| `src/thegent/planning/auto_launch.py:45`                     | `TaskRouter`                   | Use task classifier from utils or remove      |
| `src/thegent/cli/commands/run_cmds.py:516`                   | `TaskRouter`                   | Use task classifier from utils or remove      |
| `src/thegent/mcp/server/tools_terminal.py:134`               | `TaskRouter`                   | Use task classifier from utils or remove      |
| `src/thegent/orchestration/execution/engine.py:12`           | `RoutingDecision`              | Create local dataclass                        |
| `src/thegent/cli/services/run_execution_core_helpers.py:153` | `auto_router.auto_route`       | Direct `cliproxy_router.select_model()` call  |
| `src/thegent/commands/router.py:21`                          | `RouterStatus, routing_audit`  | Create mock/stub for CLI status               |
| `src/thegent/agents/maif_runner.py:12`                       | `RoutingDecision`              | Create local dataclass                        |
| `src/thegent/agents/codex_proxy.py:27`                       | `TaskMetadata, ExecutionPath`  | Move to utils/                                |

**Group B: Data/Metadata (10 files → utils/)**

| File                                                | Current Import                                           | Target                                                          |
| --------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------- |
| `src/thegent/cliproxy_adapter.py:53`                | `model_metadata, harness_model_mapping, cost_calculator` | `thegent.utils.model_*`                                         |
| `src/thegent/cliproxy_models_transform.py:114`      | `model_metadata`                                         | `thegent.utils.model_registry`                                  |
| `src/thegent/cliproxy_request_transform.py:114`     | `harness_model_mapping`                                  | `thegent.utils.model_mapping`                                   |
| `src/thegent/cliproxy_stream_state.py:219`          | `cost_tracker`                                           | Keep in routing/ or create utils/cost_tracker                   |
| `src/thegent/cost/aggregator.py:59`                 | `model_metadata`                                         | `thegent.utils.model_registry`                                  |
| `src/thegent/tui/routing_dashboard.py:10`           | `cost_tracker`                                           | Keep in routing/ or create utils/cost_tracker                   |
| `src/thegent/cli/apps/routing.py:17`                | `cost_tracker, harvest`                                  | Keep in routing/ or create utils/                               |
| `src/thegent/cli/commands/run_output_helpers.py:7`  | `grounding`                                              | `thegent.utils.grounding`                                       |
| `src/thegent/cli/services/run_input_helpers.py:137` | `grounding`                                              | `thegent.utils.grounding`                                       |
| `src/thegent/cli/services/run_model_helpers.py:49`  | `provider_types, ollama`                                 | `thegent.utils.provider_types`, `thegent.utils.ollama_provider` |

**Group C: Keep with TODO (8 files → mark for T2)**

These use streaming/execution logic that's harder to migrate. Mark with TODO:

| File                                           | Import                      | Reason              |
| ---------------------------------------------- | --------------------------- | ------------------- |
| `src/thegent/agents/codex_proxy.py:820`        | `litellm_router`            | Streaming execution |
| `src/thegent/agents/droid.py:189,408`          | `litellm_router`            | Streaming execution |
| `src/thegent/agents/direct_agents.py:324`      | `litellm_router`            | Streaming execution |
| `src/thegent/cliproxy_adapter.py:1026`         | `litellm_responses_handler` | WebSocket handler   |
| `src/thegent/mcp/server_runtime_helpers.py:67` | `litellm_responses_handler` | Response handling   |
| `src/thegent/mcp/server/lifecycle.py:189`      | `litellm_responses_handler` | HTTP client close   |
| `src/thegent/routing/donut_adapter.py:98`      | `litellm_router`            | Internal routing    |

### Phase 4: Update Internal Routing Module (Self-References)

Files within `routing/` that import from routing/:

- `auto_router.py` — imports `pareto_router` → Switch to `cliproxy_router`
- `pareto.py` — imports `pareto_router` → Delete or stub
- `cost_aware_router.py` — imports `pareto_router` → Delete or stub
- `harvest.py` — imports `cost_tracker` → Keep
- `litellm_router.py` — imports `cost_tracker, circuit_breaker, etc.` → Keep as-is (TODO mark)
- `donut_adapter.py` — imports `litellm_router, cost_tracker` → Keep as-is (TODO mark)
- `cost_calculator.py` — imports `model_metadata` → Keep as-is initially

### Phase 5: Delete Routing Module

Once all external imports are removed:

```bash
rm -rf src/thegent/routing/
grep -rn "from thegent.routing\|import thegent.routing" src/ --include="*.py" \
  | grep -v "__pycache__" | wc -l  # Must be 0
```

### Phase 6: Verify & Commit

```bash
# Run tests
python -m pytest tests/test_pareto_router.py tests/test_race_orchestration.py \
  tests/test_wl221_connector_quota.py tests/test_wl241_auth_expiry.py \
  -q --tb=short -p no:tach

# Lint
tach check
ruff check src/

# Commit
git commit -m "refactor(T1-cutover): migrate all routing callers to CLIProxy, delete thegent.routing"
```

## Implementation Details

### CLIProxy Router API

**Endpoint:** `POST /v1/routing/select`

**Request:**

```json
{
  "taskComplexity": "medium",
  "maxCostPerCall": 1.5,
  "maxLatencyMs": 5000,
  "minQualityScore": 0.8
}
```

**Response:**

```json
{
  "model_id": "gpt-4o",
  "provider": "openai",
  "estimated_cost": 0.5,
  "estimated_latency_ms": 1200,
  "quality_score": 0.95
}
```

### Error Handling

**CLIProxy Unavailable:**

```python
try:
    selection = await cliproxy_router.select_model(constraints)
except RuntimeError as e:
    if "CLIProxy not available" in str(e):
        raise RuntimeError("CLIProxy required for routing. Start with: thegent mcp start") from e
    raise
```

**NO FALLBACKS:** If CLIProxy is required, it's required. Fail fast and loudly.

## Circular Dependencies

**Risk:** Moving modules creates circular imports between routing/ and models/.

**Solution:** Use compatibility shim pattern:

1. Keep original modules in `routing/`
2. Create re-export wrappers in `utils/`
3. Update external imports to use `utils/`
4. Once external imports done, delete `routing/`
5. Internal references within `routing/` can stay

This avoids refactoring internal routing module wiring.

## Testing Strategy

### Keep Existing Tests

- `tests/routing/` — All parity tests stay
- `tests/adapters/` — All adapter tests stay
- `tests/auth/` — All auth tests stay
- `tests/quota/` — All quota tests stay

### No New Tests Needed

- Existing test suite verifies routing parity
- CLIProxy tests are in cliproxyapi-plusplus repo

### Run Before Commit

```bash
pytest tests/test_pareto_router.py -v  # Verify parity
pytest tests/test_race_orchestration.py -v
pytest tests/e2e/ -k routing -v
```

## Estimated Effort

| Phase                      | Files  | Effort    | Notes                          |
| -------------------------- | ------ | --------- | ------------------------------ |
| Phase 1 (Wrapper)          | 1      | ✅ Done   | `cliproxy_router.py` complete  |
| Phase 2 (Shims)            | 5      | 1-2h      | Simple re-exports              |
| Phase 3A (Routing callers) | 12     | 2-4h      | Replace with HTTP calls        |
| Phase 3B (Data callers)    | 10     | 1-2h      | Update imports                 |
| Phase 3C (TODO marks)      | 8      | 30min     | Add comments                   |
| Phase 4 (Self-references)  | 6      | 1-2h      | Update internal routing wiring |
| Phase 5 (Delete)           | 1      | 10min     | `rm -rf`                       |
| Phase 6 (Verify)           | 1      | 30min     | Tests, lint, commit            |
| **Total**                  | **44** | **6-12h** | Parallelizable                 |

## Blockers & Risks

### Risk 1: Circular Imports (Model/Routing)

- **Mitigation:** Use compatibility shims in `utils/`; don't move, re-export

### Risk 2: CLIProxy Not Running

- **Mitigation:** Clear error message + startup instructions
- **Code:** `if "CLIProxy not available" in str(e): raise RuntimeError("Start CLIProxy: ...")`

### Risk 3: LiteLLM Streaming Logic

- **Mitigation:** Keep in `routing/` with TODO marks; migrate in T2
- **Files:** `litellm_router.py`, `litellm_responses_handler.py`

### Risk 4: Guardrails (DLP, Moderation)

- **Status:** Independent; can stay in `routing/` or be extracted later
- **Action:** Don't block deletion on these

## Rollback Plan

If issues arise:

1. Revert `src/thegent/` changes
2. Keep `src/thegent/routing/` intact
3. Revert `src/thegent/utils/` wrappers
4. Cherry-pick individual migrations once issues fixed

## Success Criteria

- [ ] All external imports migrated (0 `from thegent.routing` outside `routing/`)
- [ ] All LiteLLM callers marked with `# TODO(T1): migrate`
- [ ] All data callers using `thegent.utils.*` instead of `thegent.routing`
- [ ] Test suite passes (100% parity)
- [ ] `tach check` passes
- [ ] `src/thegent/routing/` deleted
- [ ] Single commit: `refactor(T1-cutover): migrate all routing callers to CLIProxy`

## Timeline

- **Phase 1:** ✅ 2026-02-23 (Done)
- **Phase 2:** 2026-02-23 1-2h
- **Phase 3A:** 2026-02-23 2-4h
- **Phase 3B:** 2026-02-23 1-2h
- **Phase 3C:** 2026-02-23 30min
- **Phase 4:** 2026-02-24 1-2h
- **Phase 5-6:** 2026-02-24 1h

**Estimated Completion:** 2026-02-24 (2 days)

## Next Actions

1. Create compatibility shims in `src/thegent/utils/` (Phase 2)
2. Update Group A callers to use `cliproxy_router` (Phase 3A)
3. Update Group B callers to use `thegent.utils` (Phase 3B)
4. Mark Group C with TODO comments (Phase 3C)
5. Update internal routing wiring (Phase 4)
6. Run test suite & verify (Phase 5-6)
7. Delete `src/thegent/routing/` directory

## References

- **CLIProxy routing handler:** `cliproxyapi-plusplus/pkg/llmproxy/api/handlers/management/routing_select.go`
- **Current routing module:** `src/thegent/routing/` (11.5K LOC)
- **Git commits:**
  - Deletion attempt: `0cb9997e1`
  - Revert: `6cb252936` (due to 25+ callers still importing)
- **Tracking issue:** T1-cutover
