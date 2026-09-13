# Tasks: Replace Custom Caching with cachetools

## Phased Work Breakdown

### Phase 1: Dependency & Setup (2 tasks)

#### Task 1.1: Add cachetools Dependency

- **Status**: Pending
- **Owner**: TBD
- **Description**: Add `cachetools==6.0.0` to `pyproject.toml` and sync dependencies
- **Acceptance Criteria**:
  - [ ] `cachetools` pinned in `pyproject.toml` to version 6.0.0
  - [ ] `uv sync` completes without errors
  - [ ] `uv pip show cachetools` confirms installation
  - [ ] No version conflicts reported by pip audit
- **Blockers**: None
- **Depends On**: None

#### Task 1.2: Verify Test Environment

- **Status**: Pending
- **Owner**: TBD
- **Description**: Confirm test infrastructure ready (pytest, coverage, type checking)
- **Acceptance Criteria**:
  - [ ] `pytest --co` lists all tests without errors
  - [ ] `pytest --cov=src/` runs and produces baseline coverage
  - [ ] Type checking (`pyright` or `mypy`) passes on existing code
- **Blockers**: Task 1.1
- **Depends On**: Task 1.1

---

### Phase 2: Wrapper Design & Implementation (2 tasks)

#### Task 2.1: Create project_cache.py Wrapper

- **Status**: Pending
- **Owner**: TBD
- **Description**: Implement thin wrapper module `src/lib/project_cache.py` with standard cache factory functions
- **Acceptance Criteria**:
  - [ ] `src/lib/project_cache.py` created with <50 LOC
  - [ ] Functions: `get_cache_ttl()`, `get_cache_lru()`, `get_cache_lfu()`
  - [ ] Each function documented with docstrings + examples
  - [ ] Type hints on all functions (return types: TTLCache, LRUCache, LFUCache)
  - [ ] No external imports except `cachetools` and stdlib
  - [ ] Module is importable: `from src.lib.project_cache import get_cache_ttl`
- **Test**:
  - [ ] Unit test: `tests/test_project_cache.py` with basic instantiation tests
- **Blockers**: Task 1.2
- **Depends On**: Task 1.2

#### Task 2.2: Document Wrapper Usage Patterns

- **Status**: Pending
- **Owner**: TBD
- **Description**: Add usage documentation to wrapper and create reference guide
- **Acceptance Criteria**:
  - [ ] Inline docstrings in wrapper show 3+ usage patterns
  - [ ] `docs/guides/CACHE_PATTERNS.md` created with:
    - [ ] Pattern 1: TTL cache (function-level)
    - [ ] Pattern 2: LRU cache (class method)
    - [ ] Pattern 3: TTL + thread safety
    - [ ] When to use each policy (TTL vs LRU vs LFU)
    - [ ] Common pitfalls (cache key conflicts, eviction tuning)
  - [ ] Examples are runnable (copy-paste to REPL)
- **Blockers**: Task 2.1
- **Depends On**: Task 2.1

---

### Phase 3: Discovery & Mapping (1 task)

#### Task 3.1: Discover Custom Caches

- **Status**: Pending
- **Owner**: TBD
- **Description**: Search codebase for all custom cache implementations
- **Acceptance Criteria**:
  - [ ] Run searches:
    - [ ] `grep -r "class.*Cache" src/` → list all cache classes
    - [ ] `grep -r "dict.*timestamp\|dict.*ttl" src/` → list TTL dict patterns
    - [ ] `grep -r "LRU\|evict\|maxsize" src/` → list eviction logic
  - [ ] Create `docs/reference/CACHE_DISCOVERY_MAP.md` with:
    - [ ] Table: Module | Cache Class | Type (TTL/LRU/LFU) | LOC | Call Sites
    - [ ] Total custom cache LOC (estimated)
    - [ ] List of all call sites per cache
  - [ ] Identify any caches not in source (config-driven, factory patterns)
- **Notes**: If <3 custom caches found, scope is minimal (1-2 hour work)
- **Blockers**: None
- **Depends On**: None

---

### Phase 4: Migration (per custom cache)

#### Task 4.X: Replace Custom Cache in Module X

- **Status**: Pending (one task per discovered cache)
- **Owner**: TBD
- **Description**: Replace custom cache in module X with cachetools equivalent
- **Template Acceptance Criteria**:
  - [ ] Identify custom cache class in module X
  - [ ] Grep for all call sites (should be isolated to module or few callers)
  - [ ] Create unit test that reproduces current behavior (baseline)
  - [ ] Replace cache implementation:
    - [ ] Remove custom cache class
    - [ ] Update callers to use wrapper factory function
    - [ ] Add @cached decorator where appropriate
    - [ ] Preserve cache policy (TTL, LRU, etc.)
  - [ ] Run module tests: `pytest tests/test_X.py -v`
  - [ ] Verify coverage maintained: `pytest tests/test_X.py --cov=src/module_X`
  - [ ] Delete custom cache class (verify no import errors remain)
  - [ ] Code reduction: Log removed LOC (target: >20 LOC per cache)
- **Blockers**: Task 2.1, Task 3.1
- **Depends On**: Task 2.1, Task 3.1

**Example for provider_cache.py** (if discovered):

```
Task 4.1: Replace src/services/provider_cache.py custom TTL cache
- [ ] Remove class ProviderCache (35 LOC)
- [ ] Import get_cache_ttl wrapper
- [ ] Create _cache = get_cache_ttl(100, ttl=300)
- [ ] Add @cached(cache=_cache) to get_provider_data()
- [ ] Tests pass: pytest tests/test_provider_cache.py -v
- [ ] Coverage: 85%+ maintained
```

---

### Phase 5: Integration & Validation (3 tasks)

#### Task 5.1: Run Full Test Suite

- **Status**: Pending
- **Owner**: TBD
- **Description**: Execute complete test suite after all replacements
- **Acceptance Criteria**:
  - [ ] `pytest` (all tests) completes with 0 failures
  - [ ] Coverage maintained at 80%+ (or threshold in `pyproject.toml`)
  - [ ] No deprecation warnings related to removed cache classes
  - [ ] No import errors in test discovery
- **Blockers**: All Phase 4 tasks
- **Depends On**: All Phase 4 tasks

#### Task 5.2: Run Quality Gates

- **Status**: Pending
- **Owner**: TBD
- **Description**: Run project quality checks (linters, type checking, security)
- **Acceptance Criteria**:
  - [ ] `task quality` (or `task lint test security`) completes with 0 errors
  - [ ] Ruff check: 0 issues
  - [ ] Mypy / Pyright: 0 type errors on modified files
  - [ ] No new lint suppressions introduced
  - [ ] Coverage gate: 80%+ maintained
- **Blockers**: Task 5.1
- **Depends On**: Task 5.1

#### Task 5.3: Verify Code Reduction

- **Status**: Pending
- **Owner**: TBD
- **Description**: Measure and document LOC reduction
- **Acceptance Criteria**:
  - [ ] Count removed LOC from custom cache classes (target: >150 LOC total)
  - [ ] Count added LOC in wrapper + new imports (expected: <50 LOC)
  - [ ] Net reduction: >100 LOC
  - [ ] Document in `docs/reference/LIBRARY_FIRST_AUDIT_AND_PLAN.md`:
    - [ ] Before: N custom caches, M total LOC
    - [ ] After: 0 custom caches, N total LOC (M - X reduction)
    - [ ] Wrapper overhead: <50 LOC
- **Blockers**: Task 5.2
- **Depends On**: Task 5.2

---

### Phase 6: Documentation & Cleanup (2 tasks)

#### Task 6.1: Update Library-First Audit

- **Status**: Pending
- **Owner**: TBD
- **Description**: Update governance documentation to reflect cachetools adoption
- **Acceptance Criteria**:
  - [ ] Update `docs/research/LIBRARY_FIRST_AUDIT_AND_PLAN.md`:
    - [ ] Add entry to "Governed Libraries" table: `caching | cachetools | v6.0.0 | TTL, LRU, LFU policies`
    - [ ] Link to `docs/guides/CACHE_PATTERNS.md`
    - [ ] Remove entry from "Custom Implementations" (if present)
  - [ ] Update project `CLAUDE.md`:
    - [ ] Add to library preferences table:
      ```
      | Caching | cachetools | No custom TTL/LRU logic; use get_cache_ttl(), get_cache_lru() |
      ```
  - [ ] Verify links are valid (no 404s)
- **Blockers**: Task 5.3
- **Depends On**: Task 5.3

#### Task 6.2: Archive Change Documentation

- **Status**: Pending
- **Owner**: TBD
- **Description**: Move this change doc to archive after merge
- **Acceptance Criteria**:
  - [ ] After PR merge: move `docs/changes/research-library-cache/` to `docs/changes/archive/`
  - [ ] Update `docs/changes/archive/README.md` to list this change
  - [ ] Link back to merge commit / PR
- **Blockers**: Task 6.1
- **Depends On**: Task 6.1

---

## Summary

| Phase         | Tasks     | LOC Changed | Est. Time     |
| ------------- | --------- | ----------- | ------------- |
| 1: Setup      | 2         | 0           | 2 min         |
| 2: Wrapper    | 2         | ~50         | 5 min         |
| 3: Discovery  | 1         | 0           | 3 min         |
| 4: Migration  | 3-5       | -150+       | 10-15 min     |
| 5: Validation | 3         | 0           | 5 min         |
| 6: Docs       | 2         | ~100        | 5 min         |
| **Total**     | **13-15** | **~0 net**  | **30-35 min** |

---

## Checklist for Implementer

- [ ] Read proposal.md and design.md
- [ ] Understand wrapper API (cachetools.cached, decorators, key functions)
- [ ] Understand test baseline (run existing tests before touching code)
- [ ] Complete tasks in order (dependencies matter)
- [ ] Commit per phase (not per task) to keep history clean
- [ ] Run `task quality` after each phase
- [ ] Verify no import errors: `python -c "from src.lib.project_cache import *"`
- [ ] Document discovered custom caches in Task 3.1 output
- [ ] Ask for clarification if Task 3.1 discovers >5 custom caches or unusual patterns

---

## Notes

- **Parallelization**: Tasks 2.1 & 2.2 are sequential (2.2 depends on 2.1). All Phase 4 tasks (per cache) can run in parallel after Task 3.1 completes.
- **Testing**: Each Phase 4 task must include unit tests for that module. Phase 5 runs the aggregate suite.
- **Discovery**: If Task 3.1 finds no custom caches, this entire effort is a NOOP (mark as WONTFIX). If >10 custom caches, may need to extend timeline.
- **Rollback**: If at any point tests fail during Phase 4-5, revert the change and re-assess. Cachetools is a mature library; failure likely indicates missed call site or edge case in current logic.

---

## Related Documentation

- `proposal.md` — Problem, goals, rationale
- `design.md` — Architecture, API, patterns, file changes
- `docs/guides/CACHE_PATTERNS.md` — Usage guide (created by Task 2.2)
- `docs/research/LIBRARY_FIRST_AUDIT_AND_PLAN.md` — Updated by Task 6.1
- `CLAUDE.md` — Project library preferences (updated by Task 6.1)
