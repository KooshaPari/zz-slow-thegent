<DONE>
# Routing Module → CLIProxy Migration Status

**Date:** 2026-02-23  
**Status:** Phase 2 Complete - Infrastructure Ready  
**Completion:** ~50% (Infrastructure done, Implementation pending)

## Summary

Infrastructure phase complete. New wrapper layer in place. Ready for implementation phase.

**Files Created:** 8  
**Lines Added:** ~400 (mostly documentation)  
**Next:** Phase 3A-3C implementation (22 files, 6-12 hours)

## What's Done

### Phase 1 & 2: Complete ✅

- [x] `src/thegent/cliproxy_router.py` — HTTP client wrapper for `/v1/routing/select`
- [x] `src/thegent/utils/model_registry.py` — re-exports model_metadata
- [x] `src/thegent/utils/model_mapping.py` — re-exports harness_model_mapping
- [x] `src/thegent/utils/grounding.py` — re-exports grounding functions
- [x] `src/thegent/utils/provider_types.py` — re-exports provider utilities
- [x] `src/thegent/utils/ollama_provider.py` — re-exports ollama functions
- [x] `docs/research/ROUTING_MODULE_CLIPPROXY_MIGRATION_PLAN.md` — Main plan (600+ lines)
- [x] `docs/research/ROUTING_MIGRATION_CHECKLIST.md` — File-by-file checklist (400+ lines)

## What's Next

### Phase 3: Update Callers (6-8 hours)

**3A: Routing Logic Callers (12 files, 2-4 hours)**

- [ ] cli/commands/impl.py — ParetoRouter replacement
- [ ] cli/tui/pareto.py — RoutingDecision handling
- [ ] models/catalog.py — select_offer replacement
- [ ] planning/auto_launch.py — TaskRouter replacement
- [ ] cli/commands/run_cmds.py — TaskRouter replacement
- [ ] mcp/server/tools_terminal.py — TaskRouter replacement
- [ ] orchestration/execution/engine.py — RoutingDecision replacement
- [ ] cli/services/run_execution_core_helpers.py — auto_route replacement
- [ ] commands/router.py — RouterStatus replacement
- [ ] agents/maif_runner.py — RoutingDecision replacement
- [ ] agents/codex_proxy.py — TaskMetadata/ExecutionPath replacement
- [ ] cli/commands/run_output_helpers.py — grounding import update

**3B: Data/Metadata Callers (10 files, 1-2 hours)**

- [ ] cliproxy_adapter.py (2-3 lines)
- [ ] cliproxy_models_transform.py (1 line)
- [ ] cliproxy_request_transform.py (1 line)
- [ ] cost/aggregator.py (1 line)
- [ ] cli/services/run_input_helpers.py (1 line)
- [ ] cli/services/run_model_helpers.py (2 lines)
- [ ] models/catalog.py (1 line)

**3C: TODO Marks for LiteLLM (8 files, 30 min)**

- [ ] agents/codex_proxy.py — add TODO comment above litellm_router import
- [ ] agents/droid.py — add TODO comments (2 places)
- [ ] agents/direct_agents.py — add TODO comment
- [ ] cliproxy_adapter.py — add TODO comments (2 places)
- [ ] mcp/server_runtime_helpers.py — add TODO comment
- [ ] mcp/server/lifecycle.py — add TODO comment

### Phase 4: Internal Routing Wiring (1-2 hours)

- [ ] auto_router.py — update pareto_router usage
- [ ] pareto.py — update pareto_router usage
- [ ] cost_aware_router.py — update pareto_router usage

### Phase 5: Delete Module (10 min)

- [ ] Remove src/thegent/routing/
- [ ] Verify no imports remain
- [ ] Run tests

### Phase 6: Verify & Commit (30 min)

- [ ] tach check
- [ ] ruff check src/
- [ ] pytest tests/test_pareto_router.py tests/test_race_orchestration.py
- [ ] git commit

## Documentation

See:

- **Main Plan:** `docs/research/ROUTING_MODULE_CLIPPROXY_MIGRATION_PLAN.md`
- **Checklist:** `docs/research/ROUTING_MIGRATION_CHECKLIST.md`

Both are comprehensive with code examples, patterns, and detailed instructions per file.

## Key Stats

- Total imports to migrate: 72 (across 22 files)
- Complexity ranges: Simple 1-liners to complex logic replacements
- Estimated effort: 6-12 hours (parallelizable)
- Risk level: Low (shim layer avoids circular deps, LiteLLM marked TODO)

## Next Reviewer/Agent Actions

1. Read `ROUTING_MODULE_CLIPPROXY_MIGRATION_PLAN.md` (5 min) for context
2. Pick a file from checklist (preferably simple imports first)
3. Follow file-specific instructions in `ROUTING_MIGRATION_CHECKLIST.md`
4. Update imports and test locally
5. Commit changes
6. Repeat until all phases complete
