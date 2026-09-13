# Code Bloat Audit & Refactoring Opportunities

**Date:** February 23, 2026  
**Purpose:** Identify code reduction and optimization opportunities

---

## Executive Summary

| Metric     | Current | Target   | Opportunity         |
| ---------- | ------- | -------- | ------------------- |
| Python LOC | 258,446 | <200,000 | 58K+ reduction      |
| Rust LOC   | 168,545 | >200,000 | +31K migration      |
| Python %   | 60.5%   | <50%     | Shift to Rust       |
| Files      | 1,408   | 800      | 600+ can be reduced |

---

## Code Bloat Areas

### 1. Largest Files (>1500 LOC) - Candidates for Splitting

| File                     | LOC   | Recommendation                |
| ------------------------ | ----- | ----------------------------- |
| `execution.py`           | 2,823 | Split into modules by concern |
| `workstream_autosync.py` | 2,217 | Extract to separate package   |
| `doctor.py`              | 2,020 | Split CLI from lib            |
| `project.py`             | 2,012 | Split into focused modules    |
| `install.py`             | 1,784 | Extract install strategies    |
| `sync.py`                | 1,745 | Split by sync type            |

### 2. Duplicate Patterns - Refactor to Shared Utils

| Pattern        | Count | Recommendation            |
| -------------- | ----- | ------------------------- |
| `to_dict`      | 67    | Use Pydantic models       |
| `_load_config` | 27    | Centralize config loading |
| `is_enabled`   | 28    | Use FeatureFlag class     |
| `register`     | 40    | Centralize registry       |
| `compose`      | 30    | Extract to composables    |

---

## Code That Can Move to Rust

### High Priority (Python doing system work)

| Module                         | LOC  | Rust Replacement            |
| ------------------------------ | ---- | --------------------------- |
| `subprocess` calls (80+ files) | ~15K | Use `thegent-shims` crate   |
| `shell` operations             | ~8K  | Use `thegent-shims` crate   |
| `git` operations               | ~5K  | Use `thegent-git` crate     |
| File watching                  | ~2K  | Use `thegent-watcher` crate |
| JSON parsing                   | ~3K  | Use `thegent-jsonl` crate   |

### Candidates for External Libraries

| Custom Code    | LOC   | Better Alternative            |
| -------------- | ----- | ----------------------------- |
| Custom logging | 500+  | Use `loguru`                  |
| Custom caching | 300+  | Use `cachetools`              |
| Custom CLI     | 1000+ | Use `typer` more consistently |

---

## Code Ownership Issues

### Belongs in CLIProxyAPI (not thegent)

| Code                      | LOC | Reason                |
| ------------------------- | --- | --------------------- |
| Provider-specific routing | ~3K | CLIProxy owns routing |
| Model-specific logic      | ~2K | Provider concern      |
| API client wrappers       | ~5K | Belongs in API layer  |

### Belongs in Separate Packages

| Code                | LOC  | New Package          |
| ------------------- | ---- | -------------------- |
| Workstream autosync | 4K+  | `thegent-workstream` |
| Install logic       | 1.8K | `thegent-installer`  |
| Doctor/diagnosis    | 2K   | `thegent-doctor`     |
| Project scaffolding | 2K   | `thegent-scaffold`   |

---

## Refactoring Opportunities

### Immediate (Quick Wins)

1. **Use Pydantic everywhere** - Replace `to_dict`/`from_dict` with Pydantic models
   - Impact: Remove 40+ custom serializers
   - LOC: -500

2. **Centralize config loading** - Single `_load_config` pattern
   - Impact: Remove 27 duplicate implementations
   - LOC: -300

3. **Feature flags as class** - Replace 28 `is_enabled` patterns
   - LOC: -200

4. **Extract install strategies** - Strategy pattern for install backends
   - LOC: -400

### Medium Term (1-2 Sprints)

1. **Split execution.py** - Separate concerns
   - Process management → `thegent-executor`
   - State management → `thegent-state`
   - LOC: -1,500

2. **Split workstream_autosync** - Separate sync types
   - GitHub sync → `thegent-sync-github`
   - Linear sync → `thegent-sync-linear`
   - LOC: -2,000

3. **Rust migration** - Move hot paths to Rust
   - Subprocess handling
   - File operations
   - JSON parsing
   - LOC: -20,000 Python, +20,000 Rust

### Long Term (Architecture)

1. **Plugin system** - Make integrations truly pluggable
2. **Microservices** - Extract workstream to separate service
3. **Core + Extensions** - thegent-core with extension packages

---

## Recommendations Summary

| Priority  | Action                     | LOC Impact |
| --------- | -------------------------- | ---------- |
| 🔴 High   | Move subprocess to Rust    | -15K       |
| 🔴 High   | Split execution.py         | -1.5K      |
| 🟡 Medium | Pydantic everywhere        | -500       |
| 🟡 Medium | Split workstream_autosync  | -2K        |
| 🟢 Low    | Extract install to package | -400       |
| 🟢 Low    | Centralize config          | -300       |

---

## Implementation Plan

### Sprint 1: Quick Wins

- [ ] Centralize config loading
- [ ] Standardize is_enabled patterns
- [ ] Add Pydantic models for remaining dict-serializable classes

### Sprint 2: Medium Refactors

- [ ] Split execution.py into modules
- [ ] Extract workstream_autosync types
- [ ] Create thegent-installer package

### Sprint 3: Rust Migration

- [ ] Move subprocess handling to Rust
- [ ] Move file operations to Rust
- [ ] Expand thegent-shims crate

---

## Success Metrics

| Metric        | Current | Post-Refactor |
| ------------- | ------- | ------------- |
| Python LOC    | 258,446 | <200,000      |
| Rust LOC      | 168,545 | >200,000      |
| Files         | 1,408   | <1,000        |
| Avg file size | 183 LOC | <150 LOC      |

---

## Additional Findings (Feb 23, 2026)

### Empty Stub Files (21 total) - Can Be Removed

| Path                                                  | Module        | Action |
| ----------------------------------------------------- | ------------- | ------ |
| src/docs_engine/export/**init**.py                    | docs_engine   | Remove |
| src/docs_engine/git/**init**.py                       | docs_engine   | Remove |
| src/docs_engine/hub/**init**.py                       | docs_engine   | Remove |
| src/docs_engine/mcp/**init**.py                       | docs_engine   | Remove |
| src/docs_engine/semantic/**init**.py                  | docs_engine   | Remove |
| src/docs_engine/sidebar/**init**.py                   | docs_engine   | Remove |
| src/thegent/cli/apps/**init**.py                      | cli           | Remove |
| src/thegent/evals/**init**.py                         | evals         | Remove |
| src/thegent/mcp/tools/**init**.py                     | mcp           | Remove |
| src/thegent/observability/**init**.py                 | observability | Remove |
| src/thegent/offload/**init**.py                       | offload       | Remove |
| src/thegent/orchestration/consensus/**init**.py       | orchestration | Review |
| src/thegent/orchestration/pruning/**init**.py         | orchestration | Review |
| src/thegent/orchestration/resilience/**init**.py      | orchestration | Review |
| src/thegent/orchestration/resource/**init**.py        | orchestration | Review |
| src/thegent/orchestration/state/**init**.py           | orchestration | Review |
| src/thegent/orchestration/strategies/**init**.py      | orchestration | Review |
| src/thegent/prompts/**init**.py                       | prompts       | Remove |
| src/thegent/protocols/**init**.py                     | protocols     | Remove |
| src/thegent/tools/**init**.py                         | tools         | Remove |
| src/thegent/utils/routing_impl/guardrails/**init**.py | utils         | Review |

### Files with TODO/FIXME (16 files)

All TODOs/FIXMEs are intentional - regex patterns, constants, test code.

### Lint Status

- Core modules: ✅ Clean
- Broken files: Excluded (Python 3.14 G-GP-05 issue)

---

## Action Plan

### Split: workstream_autosync.py (2217 LOC)

- Extract to `thegent-sync-workstream` package
- Split by: adapters (GH/Linear), core (runner, config)

### Split: project.py (2012 LOC)

- Split by: scaffold, install, update commands

### Rust Migration: Subprocess

- 80+ files using subprocess
- Already exists: `thegent-shims` crate
- Opportunity: Add more shim functions

---

## Migration Progress

### Shim Subprocess Migration (Feb 23, 2026) ✅ COMPLETE

- Created: `thegent/infra/shim_subprocess.py` - shim-aware subprocess runner
- **Updated 91 files to use shims** - Full migration complete!

All subprocess.run calls now use shim_run for automatic Rust shim acceleration.
