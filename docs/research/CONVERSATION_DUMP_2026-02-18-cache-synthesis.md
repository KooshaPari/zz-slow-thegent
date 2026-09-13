<DONE>
# Caching Library Standardization: Synthesis & Implementation Readiness

**Date**: 2026-02-18
**Project**: thegent
**Change**: research-library-cache
**Status**: Ready for Implementation

---

## Executive Summary

A complete research & design package exists for standardizing caching across thegent using the `cachetools` library (v6.0.0). The proposal, design, and task breakdown are mature and ready for immediate execution. This document synthesizes findings and confirms readiness.

### Key Documents

| Document     | Location                                          | Purpose                                    | Status      |
| ------------ | ------------------------------------------------- | ------------------------------------------ | ----------- |
| **Proposal** | `docs/changes/research-library-cache/proposal.md` | Problem statement, goals, success criteria | ✅ Complete |
| **Design**   | `docs/changes/research-library-cache/design.md`   | Architecture, wrapper API, patterns, files | ✅ Complete |
| **Tasks**    | `docs/changes/research-library-cache/tasks.md`    | Phased work breakdown, acceptance criteria | ✅ Complete |

---

## Change Rationale

### Problem Statement

- **Code duplication**: Multiple custom cache implementations across codebase
- **Maintenance burden**: Custom cache logic scattered, difficult to audit
- **Missing features**: No eviction policies, thread-safe decorators, statistics
- **Inconsistency**: Different behaviors per implementation
- **Governance gap**: Custom caching violates Library-First Policy

### Library Choice: cachetools v6.0.0

| Criteria                   | Evaluation                                    |
| -------------------------- | --------------------------------------------- |
| **Maturity**               | ✅ 10+ years, widely used (100M+ downloads)   |
| **Dependencies**           | ✅ Zero external deps (stdlib only)           |
| **Performance**            | ✅ Hand-optimized C code in CPython           |
| **Policies**               | ✅ TTL, LRU, LFU, custom eviction             |
| **Safety**                 | ✅ Thread-safe decorators available           |
| **Alternative considered** | ❌ diskcache (overkill for in-memory caching) |

---

## Implementation Plan

### Phased Execution (6 phases, ~13-15 tasks)

```
Phase 1: Dependency & Setup (2 tasks)
  ↓
Phase 2: Wrapper Design (2 tasks)
  ↓
Phase 3: Discovery & Mapping (1 task)
  ├─ (Parallel)
Phase 4: Per-Cache Migration (3-5 tasks)
  ↓
Phase 5: Integration & Validation (3 tasks)
  ↓
Phase 6: Documentation & Cleanup (2 tasks)
```

### Success Criteria Checklist

- [ ] All custom cache classes removed
- [ ] All cache usages replaced with cachetools
- [ ] Wrapper follows project conventions (<50 LOC)
- [ ] All existing tests pass
- [ ] Code reduction: >150 LOC
- [ ] Library-first audit updated
- [ ] Zero new warnings from quality gates

### Effort Estimate

| Phase      | Time          | Blocker        |
| ---------- | ------------- | -------------- |
| Setup      | 2 min         | None           |
| Wrapper    | 5 min         | Phase 1        |
| Discovery  | 3 min         | None           |
| Migration  | 10-15 min     | Phase 2, 3     |
| Validation | 5 min         | Phase 4        |
| Docs       | 5 min         | Phase 5        |
| **Total**  | **30-35 min** | Parallelizable |

---

## Architecture: Wrapper Design

### Thin Wrapper Pattern

**File**: `src/lib/project_cache.py` (<50 LOC)

```python
from cachetools import TTLCache, LRUCache, LFUCache, cached


def get_cache_ttl(maxsize: int, ttl: int) -> TTLCache:
    """Return a TTL cache. Use with @cached decorator."""
    return TTLCache(maxsize=maxsize, ttl=ttl)


def get_cache_lru(maxsize: int) -> LRUCache:
    """Return an LRU cache. Use with @cached decorator."""
    return LRUCache(maxsize=maxsize)


def get_cache_lfu(maxsize: int) -> LFUCache:
    """Return an LFU cache. Use with @cached decorator."""
    return LFUCache(maxsize=maxsize)
```

### Usage Patterns

**Pattern 1: TTL Cache**

```python
from src.lib.project_cache import get_cache_ttl
from cachetools import cached

_cache = get_cache_ttl(maxsize=100, ttl=300)


@cached(cache=_cache)
def get_data(item_id: str) -> dict:
    return fetch_data(item_id)  # Cached 5 min
```

**Pattern 2: LRU Cache (Class Method)**

```python
from src.lib.project_cache import get_cache_lru
from cachetools import cached


class DataManager:
    _cache = get_cache_lru(maxsize=50)

    @cached(cache=_cache)
    def get_item(self, item_id: str):
        return self._fetch_item(item_id)
```

**Pattern 3: Thread-Safe Caching**

```python
from src.lib.project_cache import get_cache_ttl
from cachetools import cached
from threading import RLock

_cache = get_cache_ttl(maxsize=100, ttl=300)
_lock = RLock()


@cached(cache=_cache, lock=_lock)
def get_data_threadsafe(item_id: str):
    return fetch_data(item_id)
```

---

## Dependency Addition

### Current State

**pyproject.toml already includes**:

```toml
cachetools>=5.3.3
diskcache>=5.0.0
```

✅ **cachetools is already a dependency!** No need to add.

### Action Required

- Verify version is sufficient (>=5.3.3; proposal suggests pinning to 6.0.0 for consistency)
- Consider: Keep at `>=5.3.3` or pin to `==6.0.0`?
  - **Recommendation**: Pin to `==6.0.0` for stability and to align with design document

---

## Phase-by-Phase Breakdown

### Phase 1: Setup (2 tasks, 2 min)

1. **Verify dependency**: `uv pip show cachetools` → confirm >=5.3.3 installed
2. **Verify test environment**: `pytest --co` → ensure test discovery works

### Phase 2: Wrapper (2 tasks, 5 min)

1. **Create `src/lib/project_cache.py`** (~30 LOC)
   - Factory functions: `get_cache_ttl()`, `get_cache_lru()`, `get_cache_lfu()`
   - Type hints on all functions
   - Docstrings with examples

2. **Create `tests/test_project_cache.py`**
   - Test cache instantiation
   - Test decorator usage
   - Test eviction behavior

### Phase 3: Discovery (1 task, 3 min)

**Search for custom caches**:

```bash
grep -r "class.*Cache" src/         # Find cache classes
grep -r "dict.*timestamp\|ttl" src/ # Find TTL patterns
grep -r "LRU\|evict\|maxsize" src/  # Find eviction logic
```

**Output**: `docs/reference/CACHE_DISCOVERY_MAP.md`

### Phase 4: Migration (3-5 tasks, 10-15 min)

For each discovered custom cache:

1. Identify call sites (grep + type checking)
2. Write baseline unit test
3. Replace with cachetools equivalent
4. Run module tests
5. Delete custom cache class
6. Verify no import errors

### Phase 5: Validation (3 tasks, 5 min)

1. **Full test suite**: `pytest` → all green
2. **Quality gates**: `task quality` → 0 errors
3. **Coverage verification**: `pytest --cov` → 80%+ maintained

### Phase 6: Documentation (2 tasks, 5 min)

1. **Update `LIBRARY_FIRST_AUDIT_AND_PLAN.md`**
   - Add cachetools to governed libraries table
   - Link to usage guide
   - Document LOC reduction

2. **Update project `CLAUDE.md`**
   - Add caching to library preferences
   - Link to patterns guide

3. **Archive change docs** (post-merge)

---

## Key Design Decisions

| Decision               | Rationale                        | Alternative             | Status       |
| ---------------------- | -------------------------------- | ----------------------- | ------------ |
| **Use cachetools**     | Mature, zero deps, battle-tested | Custom/diskcache        | ✅ Approved  |
| **Thin wrapper**       | Consistency, project conventions | Direct cachetools usage | ✅ Approved  |
| **Location: src/lib/** | Standard library location        | Other                   | ✅ Approved  |
| **Thread-safe lock**   | Conditional (only if needed)     | Always include          | ✅ On-demand |
| **TTL + LRU combo**    | Separate caches (composition)    | Single cache            | ✅ Simple    |

---

## Risk Assessment & Mitigation

| Risk                               | Probability | Impact | Mitigation                       |
| ---------------------------------- | ----------- | ------ | -------------------------------- |
| Breaking change to cache interface | Low         | Medium | Thorough test coverage           |
| Performance regression             | Very Low    | Medium | Benchmark before/after           |
| Memory overhead                    | Very Low    | Low    | Monitor with profiler            |
| Thread safety issues               | Low         | High   | Use `lock` param in decorator    |
| Missed call sites                  | Low         | High   | grep + type checker verification |

**Overall Risk**: 🟢 Low (isolated, well-tested library, comprehensive test coverage)

---

## Testing Strategy

### Unit Tests (Per Module)

- Cache hits/misses work
- Eviction (size and TTL)
- Thread safety (if applicable)
- No functional regressions

### Integration Tests

- Cache behavior across modules
- Concurrent access patterns
- Cache invalidation

### Regression Tests

- All existing tests pass
- Coverage threshold maintained (80%+)

### Coverage Target

- Current: 80%+
- After migration: 80%+ (maintained, not reduced)

---

## Rollback Plan

| Scenario               | Action                                                   |
| ---------------------- | -------------------------------------------------------- |
| Tests fail             | Revert `src/lib/project_cache.py`, restore cache classes |
| Performance regression | Profile with `py-spy`, optimize wrapper                  |
| Production issues      | `git revert` commit                                      |

---

## Files Affected

| File                                            | Change                 | Type   | Priority |
| ----------------------------------------------- | ---------------------- | ------ | -------- |
| `src/lib/project_cache.py`                      | Create wrapper         | new    | P0       |
| `tests/test_project_cache.py`                   | Test wrapper           | new    | P0       |
| Per-module cache files                          | Replace caches         | modify | P1       |
| Per-module tests                                | Update imports         | modify | P1       |
| `docs/reference/CACHE_DISCOVERY_MAP.md`         | Discovery results      | new    | P2       |
| `docs/guides/CACHE_PATTERNS.md`                 | Usage guide            | new    | P2       |
| `docs/research/LIBRARY_FIRST_AUDIT_AND_PLAN.md` | Mark governed          | modify | P2       |
| `CLAUDE.md`                                     | Add library preference | modify | P2       |

---

## Next Steps for Implementation

### Immediate (Ready Now)

1. **Phase 1 (Setup)**
   - Verify cachetools installed: `python -c "import cachetools; print(cachetools.__version__)"`
   - Confirm test environment: `pytest --co -q | head -10`

2. **Phase 2 (Wrapper)**
   - Create `src/lib/project_cache.py` using design.md as reference
   - Write `tests/test_project_cache.py`
   - Run: `pytest tests/test_project_cache.py -v`

3. **Phase 3 (Discovery)**
   - Execute discovery searches
   - Create `docs/reference/CACHE_DISCOVERY_MAP.md`
   - Prioritize findings by LOC and impact

### Conditional (After Discovery)

4. **Phase 4 (Migration)**
   - Per each custom cache: 1 task per cache
   - Parallel execution allowed
   - Expected 3-5 tasks based on design estimate

5. **Phase 5 (Validation)**
   - Run full suite: `pytest`
   - Quality gates: `task quality`
   - Coverage check: `pytest --cov=src/`

6. **Phase 6 (Docs & Cleanup)**
   - Update audit documentation
   - Archive change documentation
   - Verify links and references

---

## Decision Points

### Should we proceed?

**Criteria**:

- ✅ Proposal is clear and complete
- ✅ Design is detailed and implementable
- ✅ Tasks are well-defined with acceptance criteria
- ✅ cachetools is already a dependency
- ✅ Risk is low (isolated, well-tested)
- ✅ Alignment with Library-First Policy strong

**Recommendation**: ✅ **Proceed immediately**

### What if we find >10 custom caches?

- Extend timeline, but still feasible (10-15 tasks = 30-45 min)
- Consider parallelizing Phase 4 across 2-3 agents

### What if discovery finds no custom caches?

- Mark as WONTFIX (noop change)
- Archive documentation
- Focus on ensuring future caches use cachetools

---

## Documentation References

### Governance & Standards

- `docs/research/LIBRARY_FIRST_AUDIT_AND_PLAN.md` — Library-First Policy
- `docs/guides/anti-patterns.md` — Custom cache as anti-pattern
- `CLAUDE.md` — Project library preferences
- `docs/research/PROACTIVE_GOVERNANCE_EVOLUTION_PLAN.md` — Governance mandate

### Cachetools Resources

- Official docs: https://cachetools.readthedocs.io/
- GitHub: https://github.com/tkem/cachetools/
- PyPI: https://pypi.org/project/cachetools/

### Related Changes

- `docs/changes/research-library-retry/` — Similar pattern (tenacity)
- `docs/reference/LIBRARY_FIRST_AUDIT_AND_PLAN.md` — Other governed libraries

---

## Appendix: Quick Reference

### Command Cheatsheet

```bash
# Verify cachetools
python -c "import cachetools; print(cachetools.__version__)"

# Run tests
pytest tests/test_project_cache.py -v
pytest tests/ --cov=src/ -q

# Quality gates
task quality
task lint
task test

# Search for custom caches
grep -r "class.*Cache" src/
grep -r "TTLCache\|LRUCache" src/

# Verify wrapper works
python -c "from src.lib.project_cache import get_cache_ttl, get_cache_lru; print('OK')"
```

### Key APIs

```python
# Import
from cachetools import cached, TTLCache, LRUCache, LFUCache
from src.lib.project_cache import get_cache_ttl, get_cache_lru, get_cache_lfu

# Create cache
cache = get_cache_ttl(maxsize=100, ttl=300)


# Decorate function
@cached(cache=cache)
def my_func(arg1, arg2):
    return expensive_operation(arg1, arg2)


# Thread-safe decoration
@cached(cache=cache, lock=RLock())
def thread_safe_func(arg):
    return operation(arg)


# Custom key function
def key_func(arg1, arg2, **kwargs):
    return (arg1, arg2)


@cached(cache=cache, key=key_func)
def custom_key_func(arg1, arg2, **kwargs):
    return result
```

---

## Conclusion

The caching library standardization is a **low-risk, high-value** change that:

- Aligns with Library-First Policy
- Reduces code duplication (>150 LOC savings)
- Improves maintainability and safety
- Leverages mature, battle-tested library
- Has clear, phased implementation plan

**Status**: Ready for immediate implementation by any team member following the task breakdown in `tasks.md`.

---

**Document Version**: 1.0
**Last Updated**: 2026-02-18
**Owner**: Claude Code Agent
**Tags**: #library-first #caching #cachetools #standardization
