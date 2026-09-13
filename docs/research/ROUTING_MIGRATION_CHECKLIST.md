<DONE>
# Routing Module Migration - Implementation Checklist

**Created:** 2026-02-23  
**Phase 1 Complete:** ✅ `cliproxy_router.py` + 5 compatibility shims created  
**Next:** Phase 3A/3B - Update 22 callers

## Quick Summary

- Total callers: 44 (across 22 unique files)
- Done: 6 files (cliproxy_router + 5 shims)
- Remaining: 38 changes across 22 files

## PHASE 2: COMPATIBILITY SHIMS ✅ (COMPLETE)

```
✅ src/thegent/utils/model_registry.py — wraps model_metadata
✅ src/thegent/utils/model_mapping.py — wraps harness_model_mapping
✅ src/thegent/utils/grounding.py — wraps grounding functions
✅ src/thegent/utils/provider_types.py — wraps provider utilities
✅ src/thegent/utils/ollama_provider.py — wraps ollama functions
✅ src/thegent/cliproxy_router.py — NEW routing wrapper
```

## PHASE 3A: UPDATE ROUTING CALLERS (12 files)

**Task:** Replace direct imports of `pareto_router`, `task_router`, `route_executor`, `auto_router` with `cliproxy_router` calls

### File 1: `src/thegent/cli/commands/impl.py`

**Line 692:** `from thegent.routing.pareto_router import QUALITY_PROXY, ParetoRouter, RouteCandidate`

**Action:**

1. Remove import
2. Add `from thegent.cliproxy_router import CLIProxyRouter, RoutingConstraints, RoutingSelection`
3. Find code that calls `ParetoRouter.select()` or `select_offer()`
4. Replace with:

```python
async with httpx.AsyncClient() as client:
    router = CLIProxyRouter(client=client)
    selection = await router.select_model(
        RoutingConstraints(task_complexity="high", max_cost_per_call=2.0, max_latency_ms=5000, min_quality_score=0.8)
    )
    model_id = selection.model_id
```

**Status:** [ ] TODO

---

### File 2: `src/thegent/cli/tui/pareto.py`

**Line 19:** `from thegent.routing.route_executor import (...)`  
**Line 112:** `from thegent.routing.route_executor import RoutingDecision`

**Action:**

1. Remove both imports
2. Add `from thegent.cliproxy_router import CLIProxyRouter, RoutingSelection, RoutingConstraints`
3. Replace `RoutingDecision` dataclass with local version or use `RoutingSelection`
4. Update TUI display code to use HTTP calls instead of direct routing logic

**Status:** [ ] TODO

---

### File 3: `src/thegent/models/catalog.py`

**Line 534:** `from thegent.routing.pareto_router import (QUALITY_PROXY, ParetoRouter, select_offer)`

**Action:**

1. Remove import
2. Add `from thegent.cliproxy_router import CLIProxyRouter, RoutingConstraints`
3. Find calls to `select_offer()` function
4. Replace with `await router.select_model(constraints)`

**Status:** [ ] TODO

---

### File 4: `src/thegent/planning/auto_launch.py`

**Line 45:** `from thegent.routing.task_router import TaskRouter`

**Action:**

1. Remove import
2. Analyze how TaskRouter is used (task classification)
3. Options:
   - Create local TaskClassifier based on constraints
   - Or extract task classifier from CLIProxy
   - Or manually classify by task complexity
4. Update code accordingly

**Status:** [ ] TODO

---

### File 5: `src/thegent/cli/commands/run_cmds.py`

**Line 516:** `from thegent.routing.task_router import TaskRouter`

**Action:** Same as File 4 above

**Status:** [ ] TODO

---

### File 6: `src/thegent/mcp/server/tools_terminal.py`

**Line 134:** `from thegent.routing.task_router import TaskRouter`

**Action:** Same as File 4 above

**Status:** [ ] TODO

---

### File 7: `src/thegent/orchestration/execution/engine.py`

**Line 12:** `from thegent.routing.route_executor import (RoutingDecision, RoutingStatus, ...)`

**Action:**

1. Remove import
2. Create local dataclass for RoutingDecision or use RoutingSelection from cliproxy_router
3. Update execution engine to call CLIProxy instead of direct routing logic
4. Update routing decision tracking

**Status:** [ ] TODO

---

### File 8: `src/thegent/cli/services/run_execution_core_helpers.py`

**Line 153, 1100:** `from thegent.routing.auto_router import auto_route`

**Action:**

1. Remove import
2. Add `from thegent.cliproxy_router import CLIProxyRouter, RoutingConstraints`
3. Find where `auto_route()` is called
4. Replace with direct call to `router.select_model()`
5. Extract task complexity from context if needed

**Status:** [ ] TODO

---

### File 9: `src/thegent/commands/router.py`

**Line 21, 56, 148, 210:** Multiple imports of `RouterStatus, read_routing_audit, AgentRoutingState`

**Action:**

1. Remove all routing imports
2. Create stub/mock versions of these classes for CLI output (these are for display only)
3. Or: Create local dataclasses that show routing history
4. Update router command to show CLIProxy-based routing info instead

**Status:** [ ] TODO

---

### File 10: `src/thegent/agents/maif_runner.py`

**Line 12:** `from thegent.routing.route_executor import RoutingDecision`

**Action:**

1. Remove import
2. Create local RoutingDecision dataclass or use RoutingSelection from cliproxy_router
3. Update agent execution to use CLIProxy routing

**Status:** [ ] TODO

---

### File 11: `src/thegent/agents/codex_proxy.py`

**Line 27:** `from thegent.routing.models import TaskMetadata`  
**Line 28:** `from thegent.routing.provider_types import ExecutionPath, get_execution_path`  
**Line 820:** `from thegent.routing.litellm_router import get_enhanced_router` ← TODO mark

**Action for lines 27-28:**

1. Remove both imports
2. Create local TaskMetadata dataclass or find alternative
3. Add `from thegent.utils.provider_types import ExecutionPath, get_execution_path`
4. Or define ExecutionPath locally if not in utils

**Action for line 820:**

1. Keep import
2. Add `# TODO(T1): migrate to CLIProxy` comment above it
3. No further action

**Status:** [ ] TODO

---

### File 12: `src/thegent/cli/commands/run_output_helpers.py`

**Line 7:** `from thegent.routing.grounding import normalize_grounding_source_url`

**Action:**

1. Replace with `from thegent.utils.grounding import normalize_grounding_source_url`
2. That's it - simple one-line change

**Status:** [ ] TODO

---

## PHASE 3B: UPDATE DATA/METADATA CALLERS (10 files)

**Task:** Replace `thegent.routing.*` imports with `thegent.utils.*`

### File 13: `src/thegent/cliproxy_adapter.py`

**Lines 53, 318, 628, 662:** Multiple imports of model_metadata, harness_model_mapping, cost_calculator

**Action:**

1. Line 53: `from thegent.routing.cost_calculator import ...` → Keep (no utils wrapper yet) or create wrapper
2. Line 628: `from thegent.routing.model_metadata import ...` → `from thegent.utils.model_registry import ...`
3. Line 662: `from thegent.routing.harness_model_mapping import ...` → `from thegent.utils.model_mapping import ...`
4. Update function calls if API changed (unlikely - it's just re-exports)

**Status:** [ ] TODO

---

### File 14: `src/thegent/cliproxy_models_transform.py`

**Line 114:** `from thegent.routing.model_metadata import get_model_metadata`

**Action:**

1. Replace with `from thegent.utils.model_registry import get_model_metadata`

**Status:** [ ] TODO

---

### File 15: `src/thegent/cliproxy_request_transform.py`

**Line 114:** `from thegent.routing.harness_model_mapping import resolve_model_for_backend`

**Action:**

1. Replace with `from thegent.utils.model_mapping import resolve_model_for_backend`

**Status:** [ ] TODO

---

### File 16: `src/thegent/cliproxy_stream_state.py`

**Line 219:** `from thegent.routing.cost_tracker import get_cost_tracker`

**Action:**

1. Keep as-is for now (cost_tracker is analytics; not migrated yet)
2. Or create `src/thegent/utils/cost_tracker.py` wrapper (optional)

**Status:** [ ] SKIP for now

---

### File 17: `src/thegent/cost/aggregator.py`

**Line 59:** `from thegent.routing.model_metadata import get_model_metadata`

**Action:**

1. Replace with `from thegent.utils.model_registry import get_model_metadata`

**Status:** [ ] TODO

---

### File 18: `src/thegent/tui/routing_dashboard.py`

**Line 10:** `from thegent.routing.cost_tracker import get_cost_tracker`

**Action:**

1. Keep as-is for now (analytics) or create wrapper

**Status:** [ ] SKIP for now

---

### File 19: `src/thegent/cli/apps/routing.py`

**Lines 17, 47, 56:** Multiple imports of cost_tracker, harvest

**Action:**

1. Keep as-is (these are routing command-specific; can stay in routing module)

**Status:** [ ] SKIP (internal routing module)

---

### File 20: `src/thegent/cli/services/run_input_helpers.py`

**Line 137:** `from thegent.routing.grounding import extract_grounding_sources, extract_grounding_sources_from_payload`

**Action:**

1. Replace with `from thegent.utils.grounding import extract_grounding_sources, extract_grounding_sources_from_payload`

**Status:** [ ] TODO

---

### File 21: `src/thegent/cli/services/run_model_helpers.py`

**Lines 49, 55:** `from thegent.routing.provider_types import ...` and `from thegent.routing.ollama_provider import ...`

**Action:**

1. Line 49: Replace with `from thegent.utils.provider_types import normalize_provider_name`
2. Line 55: Replace with `from thegent.utils.ollama_provider import is_ollama_available, get_available_models`

**Status:** [ ] TODO

---

### File 22: `src/thegent/models/catalog.py`

**Line 8:** `from thegent.routing.provider_types import normalize_provider_name`

**Action:**

1. Replace with `from thegent.utils.provider_types import normalize_provider_name`

**Status:** [ ] TODO

---

## PHASE 3C: MARK LITELLM CALLERS WITH TODO (8 files)

**Task:** Add `# TODO(T1): migrate to CLIProxy` comments to 8 callers of litellm_router/litellm_responses_handler

### These files need TODO comments:

1. **src/thegent/agents/codex_proxy.py:820** — `get_enhanced_router`
   - [ ] Add `# TODO(T1): migrate to CLIProxy` above import

2. **src/thegent/agents/droid.py:189,408** — `get_enhanced_router` (2 locations)
   - [ ] Add `# TODO(T1): migrate to CLIProxy` above each import

3. **src/thegent/agents/direct_agents.py:324** — `get_enhanced_router`
   - [ ] Add `# TODO(T1): migrate to CLIProxy` above import

4. **src/thegent/cliproxy_adapter.py:1026,1087** — `handle_responses_request`, `handle_responses_websocket`
   - [ ] Add `# TODO(T1): migrate to CLIProxy` above each import

5. **src/thegent/mcp/server_runtime_helpers.py:67** — `litellm_responses_handler`
   - [ ] Add `# TODO(T1): migrate to CLIProxy` above import

6. **src/thegent/mcp/server/lifecycle.py:189** — `close_http_client`
   - [ ] Add `# TODO(T1): migrate to CLIProxy` above import

7. **src/thegent/routing/donut_adapter.py:98,257** — internal routing module (skip for now)
   - Skip - internal to routing module

---

## PHASE 4: INTERNAL ROUTING WIRING (6 files)

**Task:** Update internal routing module imports to avoid circular deps

### Files that import from routing/:

1. **src/thegent/routing/auto_router.py** — imports pareto_router
   - [ ] Update to use cliproxy_router or stub

2. **src/thegent/routing/pareto.py** — imports pareto_router
   - [ ] Update or delete

3. **src/thegent/routing/cost_aware_router.py** — imports pareto_router
   - [ ] Update or delete

4. **src/thegent/routing/harvest.py** — imports cost_tracker
   - [ ] Keep as-is

5. **src/thegent/routing/litellm_router.py** — imports cost_tracker, circuit_breaker, etc.
   - [ ] Keep as-is (marked as TODO migration)

6. **src/thegent/routing/donut_adapter.py** — imports litellm_router, cost_tracker
   - [ ] Keep as-is (marked as TODO migration)

---

## PHASE 5: DELETE ROUTING MODULE

```bash
# Verify no external imports remain
grep -rn "from thegent.routing\|import thegent.routing" src/ --include="*.py" \
  | grep -v "__pycache__" | grep -v "^src/thegent/routing/" | wc -l
# Must return 0

# Delete
rm -rf src/thegent/routing/

# Run tests
pytest tests/test_pareto_router.py -v
pytest tests/test_race_orchestration.py -v

# Lint
tach check
ruff check src/
```

---

## PHASE 6: COMMIT & VERIFY

```bash
git status
git add -A
git commit -m "refactor(T1-cutover): migrate all routing callers to CLIProxy, delete thegent.routing"
git log --oneline -5
```

---

## Summary By File Type

### Simple Import Replacements (8 files)

- [ ] run_output_helpers.py (1 change)
- [ ] run_input_helpers.py (1 change)
- [ ] run_model_helpers.py (2 changes)
- [ ] cliproxy_models_transform.py (1 change)
- [ ] cliproxy_request_transform.py (1 change)
- [ ] cost/aggregator.py (1 change)
- [ ] models/catalog.py (1 change)
- [ ] cliproxy_adapter.py (2-3 changes)

### Complex Migrations (12 files)

- [ ] impl.py — ParetoRouter replacement
- [ ] pareto.py — RoutingDecision handling
- [ ] catalog.py — select_offer replacement
- [ ] auto_launch.py — TaskRouter replacement
- [ ] run_cmds.py — TaskRouter replacement
- [ ] tools_terminal.py — TaskRouter replacement
- [ ] execution/engine.py — RoutingDecision replacement
- [ ] run_execution_core_helpers.py — auto_route replacement
- [ ] router.py — RouterStatus replacement
- [ ] maif_runner.py — RoutingDecision replacement
- [ ] codex_proxy.py — TaskMetadata + ExecutionPath replacement
- [ ] direct_agents.py — TODO mark only

### TODO Comments (8 files)

- [ ] codex_proxy.py:820
- [ ] droid.py:189,408
- [ ] direct_agents.py:324
- [ ] cliproxy_adapter.py:1026,1087
- [ ] mcp/server_runtime_helpers.py:67
- [ ] mcp/server/lifecycle.py:189
- [ ] (skip: routing/donut_adapter.py)

### Keep As-Is (4 files)

- cliproxy_stream_state.py (cost_tracker - optional wrapper)
- tui/routing_dashboard.py (cost_tracker - optional wrapper)
- cli/apps/routing.py (internal routing commands)
- routing/harvest.py (internal routing module)

---

## Next Steps for Agent Team

1. **File-by-file:** Pick a file from "Simple Import Replacements" or "Complex Migrations"
2. **Check:** Look at actual code to understand how imports are used
3. **Update:** Replace with appropriate new imports or API calls
4. **Test:** Run `ruff check src/` and `tach check` to verify no breakage
5. **Commit:** After each file or in batches

**Recommended order:**

1. All simple import replacements first (quick wins)
2. Then TODO marks (trivial)
3. Then complex migrations (requires understanding actual usage)
4. Finally, delete and verify

---

## Tips for Implementation

### Async Pattern for CLIProxy Calls

```python
from thegent.cliproxy_router import CLIProxyRouter, RoutingConstraints


async def my_function():
    router = CLIProxyRouter()
    try:
        selection = await router.select_model(
            RoutingConstraints(
                task_complexity="medium",
                max_cost_per_call=1.0,
            )
        )
        return selection.model_id
    except RuntimeError as e:
        if "CLIProxy not available" in str(e):
            raise RuntimeError("CLIProxy required. Start with: thegent mcp start") from e
        raise
    finally:
        await router.close()
```

### Simple Import Replacement Pattern

```python
# Before:
from thegent.routing.grounding import extract_grounding_sources

# After:
from thegent.utils.grounding import extract_grounding_sources
# Rest of code stays same!
```

### TODO Mark Pattern

```python
# Before:
from thegent.routing.litellm_router import get_enhanced_router

# After:
# TODO(T1): migrate to CLIProxy (streaming/execution logic requires deeper refactor)
from thegent.routing.litellm_router import get_enhanced_router
```

---

## Estimated Time

- Simple replacements: 5-10 min each (8 files = 1-2 hours)
- TODO marks: 2-5 min each (8 files = 30 min)
- Complex migrations: 15-30 min each (12 files = 3-6 hours)
- Phases 4-6: 1-2 hours

**Total: 6-12 hours** (parallelizable)

---

## Questions?

Refer to:

- Migration plan: `docs/research/ROUTING_MODULE_CLIPPROXY_MIGRATION_PLAN.md`
- CLIProxy API: Line 10-67 of `cliproxyapi-plusplus/pkg/llmproxy/api/handlers/management/routing_select.go`
- Existing router: `src/thegent/cliproxy_router.py`
- Utils layer: `src/thegent/utils/*.py`
