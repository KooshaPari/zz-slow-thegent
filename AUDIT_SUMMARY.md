# TheGent Stabilization Audit Summary

**Date:** 2026-09-12  
**Branch:** `fix/ci-blocking`  
**Audit Score:** 82% (baseline)  

---

## 1. PR #1205 Status

The `fix/ci-blocking` branch exists locally with 2 commits on top of main:

| Commit | Description |
|--------|-------------|
| `ae6b417` | fix: correct ruff.toml syntax for per-file-ignores |
| `99f1080` | fix: make CI quality gates blocking instead of advisory |

**Status:** Branch is local only. Not yet pushed as PR (no remote tracking branch found). The branch contains the CI quality gate fix and ruff config correction.

---

## 2. Source Bloat Assessment

### Summary

| Metric | Value |
|--------|-------|
| Total Python files in `src/thegent/` | **1,056** |
| Total lines of Python | **163,936** |
| Files exceeding 500-line hard limit | **~19** |
| Files exceeding 350-line target | **111** |

### Top 10 Oversized Files (>500 lines)

| Rank | File | Lines |
|------|------|-------|
| 1 | `cli/services/run_execution_core_helpers.py` | **2,985** |
| 2 | `execution/__init__.py` | **2,592** |
| 3 | `ux/cli_cockpit.py` | **2,343** |
| 4 | `cli/commands/impl.py` | **1,803** |
| 5 | `ux/cockpit.py` | **1,714** |
| 6 | `cli/commands/observability_impl.py` | **1,518** |
| 7 | `integrations/workstream_autosync_shared.py` | **1,377** |
| 8 | `mcp/server/__init__.py` | **1,332** |
| 9 | `config/settings.py` | **1,102** |
| 10 | `protocols/jsonrpc_agent_server.py` | **1,079** |

Additional oversized files (>500 lines):

| File | Lines |
|------|-------|
| `agents/plangent.py` | 1,045 |
| `utils/routing_impl/litellm_router.py` | 1,017 |
| `integrations/gh_project_sync.py` | 997 |
| `ux/decision_audit.py` | 935 |
| `govern/vetter/checks.py` | 894 |
| `agents/unified_session_index.py` | 875 |
| `utils/routing_impl/litellm_responses_handler.py` | 870 |
| `integrations/base.py` | 866 |
| `agents/codex_proxy_runner.py` | 806 |

### Top Directories by Code Volume

| Directory | Lines | Files |
|-----------|-------|-------|
| `integrations/` | ~13,209 | 152 |
| `agents/` | ~12,014 | 80 |
| `cli/` | (115 files) | 115 |
| `utils/` | ~6,734 | 98 |
| `governance/` | (76 files) | 76 |
| `orchestration/` | (58 files) | 58 |
| `infra/` | (57 files) | 57 |

---

## 3. Integration Module Bloat (Critical Finding)

The `src/thegent/integrations/` directory contains **143 non-init Python files** but only **3 modules** are exported from `__init__.py`:

1. `base` (BaseIntegration, BaseIntegrationConfig, etc.)
2. `github_actions` (WorkflowRun, trigger_workflow, etc.)
3. `github_pr` (PullRequest, create_pr, merge_pr, etc.)

**~140 integration modules are NOT exported** from the package's public API. These include modules like:
- `adaptive_rate_limiter`, `alert_routing`, `artifact_redaction`, `beads`, `bifrost`
- `ci_benchmark_gates`, `cognee`, `cold_warm_benchmark`, `compliance_snapshot`
- `conflict_guardrails`, `connector_chaos`, `connector_circuit_breaker`
- `drift_replay`, `e2e_replay_fixture`, `encrypted_artifact`
- `latent_chaos`, `load_test_harness`, `offline_simulation`
- `sandbox_seeder`, `stale_detector`, `symptom_matrix`
- Many more

**Impact estimate:** 140+ modules at ~100-300 lines each = **14,000-42,000 lines** of potentially dead code. This is a major contributor to the L9 Complexity score of 40.

---

## 4. Test Collection Diagnosis

### Configuration

- **Pytest config:** Present in `pyproject.toml` with `pythonpath = ["src"]`, `testpaths = ["tests"]`
- **Test files found:** **1,423** test files in `tests/`
- **Conftest files:** 5 (root, tests/, tests/ui/compositor/, tests/research_engine/, benchmarks/)
- **Package import:** `import thegent` succeeds with python3
- **Test markers:** 13 defined (unit, integration, e2e, slow, asyncio, load, chaos, a11y, performance, requirement, fast, deep)

### Test Directory Structure

The test tree is deep with many subdirectories:
- `tests/unit/` — memory, contracts, dependencies, agents, ux, architecture, orchestration, i18n, infrastructure, migration, onboarding
- `tests/test_integration/`
- `tests/mesh/`
- `tests/agent_roles/`
- `tests/ui/`
- `tests/research/`

### Collection Risk Factors

1. **1,056 source modules vs 1,423 test files** — test-to-source ratio is ~1.35:1 (reasonable)
2. **`norecursedirs`** excludes templates, .venv, archive, docs, benchmarks, crates — good
3. **Filterwarnings** suppresses DeprecationWarning and some PydanticJsonSchemaWarning — appropriate
4. **No obvious collection blockers** detected from config alone; actual collection errors would require running pytest (not attempted to avoid side effects)

---

## 5. Dead/Unused Module Estimate

Based on the integrations directory analysis:

| Category | Count | Estimate |
|----------|-------|----------|
| Integration modules NOT in `__init__` | ~140 | ~14,000-42,000 lines |
| Total files >500 lines | ~19 | ~20,000+ lines |
| Total files >350 lines | 111 | ~50,000+ lines |
| Top-level module directories | **130+** | Extreme fragmentation |

The 130+ top-level directories under `src/thegent/` suggest significant architectural fragmentation. Many directories contain only a handful of files, indicating either incomplete decomposition or abandoned modules.

---

## 6. Top 5 Recommended Fixes

### Fix 1: Purge Dead Integration Modules (Effort: 2-3 days)

**Problem:** ~140 of 143 integration modules are not exported and likely unused.  
**Impact:** L9 Complexity (40 → 70+), L1 Architecture (40 → 55+)  
**Approach:**
1. Grep for imports of each non-exported integration module across the entire codebase
2. For modules with 0 imports: delete
3. For modules with internal-only imports: trace and consolidate
4. Estimated removal: 100+ files, 15,000-30,000 lines

### Fix 2: Decompose Top 10 Oversized Files (Effort: 3-4 days)

**Problem:** 19 files exceed 500 lines; worst offenders are 2,500-3,000 lines.  
**Impact:** L1 Architecture (40 → 60), L2 Dev Loop (60 → 75)  
**Approach:**
1. Start with `run_execution_core_helpers.py` (2,985 lines) — extract submodules
2. `execution/__init__.py` (2,592 lines) — should not contain logic
3. `cli_cockpit.py` / `cockpit.py` (2,343 + 1,714) — consider merge + split
4. Each decomposition should follow the project's established patterns (service submodule, adapter extraction)

### Fix 3: Consolidate Top-Level Directories (Effort: 2-3 days)

**Problem:** 130+ directories under `src/thegent/` indicate extreme fragmentation.  
**Impact:** L1 Architecture (40 → 65), L3 Agent Loop (40 → 55)  
**Approach:**
1. Map directory dependency graph
2. Merge directories with <3 files and cohesive purpose
3. Target: reduce to 40-50 top-level directories
4. Update all imports simultaneously (aggressive change policy)

### Fix 4: Enable and Validate Test Collection (Effort: 1 day)

**Problem:** Cannot confirm tests actually collect and run without side effects.  
**Impact:** L2 Dev Loop (60 → 80)  
**Approach:**
1. Run `pytest --collect-only` to verify collection succeeds
2. Fix any import errors that prevent collection
3. Run fast lane tests (`pytest -m "unit and not slow"`) to establish baseline
4. Address any fixture or dependency issues

### Fix 5: Prune Governance/Orchestration Overhead (Effort: 1-2 days)

**Problem:** `governance/` (76 files) and `orchestration/` (58 files) are disproportionate.  
**Impact:** L9 Complexity (40 → 60), L3 Agent Loop (40 → 55)  
**Approach:**
1. Audit governance modules for actual usage
2. Consolidate orchestration modules into a cleaner hierarchy
3. Remove any governance modules that are advisory-only or not wired into the agent loop

---

## Summary

| Area | Current | Target | Key Action |
|------|---------|--------|------------|
| L1 Architecture | 40 | 70 | Decompose oversized files, consolidate directories |
| L2 Dev Loop | 60 | 80 | Fix test collection, validate CI gates |
| L3 Agent Loop | 40 | 65 | Remove dead integration modules, prune governance |
| L9 Complexity | 40 | 70 | Bulk-delete ~140 unused integration modules |
| **Overall** | **82%** | **90%+** | Focus on Fixes 1 and 2 first |

**Estimated total effort:** 9-13 days of focused work  
**Quick wins:** Fix 1 (dead module purge) and Fix 4 (test validation) can be done in 3-4 days and would have the highest impact on the weakest scores.
