# Hook Optimization Strategy

## Current State Analysis

The hooks already implement several optimizations:

1. **Git-aware caching** - Cache results keyed on git state
2. **Cross-hook shared results** - Changed files computed once
3. **Circuit breaker** - Fast-fail for broken tools
4. **Smart skip** - Only run if relevant files changed
5. **Async test runner** - Run affected tests after edits

## Implementation Status

| Priority | Optimization                         | Status | Location                                                                      |
| -------- | ------------------------------------ | ------ | ----------------------------------------------------------------------------- |
| P0       | Fix timeout issue                    | Done   | hook-config.yaml `timeout_overrides`                                          |
| P1       | Affected test selection              | Done   | common.sh `affected_tests_for_file`, `get_affected_tests`                     |
| P2       | Pre-warm caches                      | Done   | common.sh `hook_prewarm_all`, qa-preflight.sh                                 |
| P3       | Parallel pipeline                    | Done   | quality-gate.sh staged execution                                              |
| P4       | Speculative execution                | Done   | async-test-runner uses `get_affected_tests`, speculative-stop-prewarmer       |
| P5       | Learning-based skip                  | Done   | quality-gate.sh + common.sh                                                   |
| P7       | Coverage/import-based test selection | Done   | common.sh `affected_tests_from_coverage_index`, `affected_tests_from_imports` |
| P6       | Incremental analysis                 | Done   | common.sh + hooks/lib/incremental_parser.py                                   |
| P8       | Background daemon mode               | Done   | hooks/hook-watcher.sh, qa-preflight, thegent govern hook-watcher              |

## Remaining Optimizations (Future)

### 1. Incremental Analysis (P6) — DONE

- Only re-analyze changed functions, not entire files
- For Python: use ast parse to find changed functions
- For TypeScript: use ts-morph or similar
- **Effort:** High | **Impact:** Medium

### 2. Coverage-Based Test Selection (P7) — DONE

- **Flow:** Run `task coverage:map` (or `task coverage-index`) to build `coverage_affected_map.json` from `.coverage`.
- **Config:** `pyproject.toml` has `dynamic_context = "test_function"`; use `pytest --cov=src --cov-context=test`.
- **Hooks:** When `coverage_based_selection: true`, `get_affected_tests` merges file-pattern + coverage-index + import-based for Python.
- **Map location:** `HOOK_CACHE_DIR/coverage_affected_map.json` (or `coverage-index.json` in project root as fallback).

### 3. Background Daemon Mode (P8) — DONE

- `hooks/hook-watcher.sh` polls every 5s, invalidates cache and pre-warms on change
- Started by qa-preflight when `daemon_mode: true`, or `thegent govern hook-watcher`

### 4. Wire Learning-Based Skip (P5 completion) — DONE

- Integrated `hook_learning_record` / `hook_learning_should_skip` into quality-gate
- Set `learning_skip: true` in hook-config to enable

## Configuration

Current hook-config.yaml settings:

```yaml
settings:
  cache_ttl: 600
  smart_skip: true
  prewarm_on_session_start: true
  parallel_stages: true
  speculative: true
  learning_skip: false # opt-in
  timeout_overrides:
    quality-gate: 300
    task-completion: 300
    security-pipeline: 600
```

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

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
