# Design: Replace Custom Caching with cachetools

## Architecture Overview

```
Calling Code
    ↓
    v
Thin Wrapper Layer (project_cache.py)  [<50 LOC]
    ├── get_cache_ttl(maxsize, ttl)
    ├── get_cache_lru(maxsize)
    ├── get_cache_lfu(maxsize)
    └── cached_method(key_func, ttl=None, policy='lru')
    ↓
    v
cachetools Library
    ├── cachetools.TTLCache(maxsize, ttl)
    ├── cachetools.LRUCache(maxsize)
    ├── cachetools.LFUCache(maxsize)
    └── cachetools.cached(cache, key=_key_func)
```

### Wrapper Location

**File**: `src/lib/project_cache.py` (new, thin wrapper)

### Wrapper API

```python
from functools import wraps
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


def cached_method(cache_or_factory, key=None, ttl=None, policy="lru"):
    """
    Decorator for caching method results.

    Args:
        cache_or_factory: Cache instance or factory function
        key: Key function (default: use all args/kwargs)
        ttl: TTL in seconds (only if cache supports it)
        policy: Cache policy ('lru', 'lfu', 'ttl')

    Returns: Decorated function with caching
    """
    # Thin layer over @cachetools.cached
    if callable(cache_or_factory):
        cache = cache_or_factory()
    else:
        cache = cache_or_factory

    return cached(cache=cache, key=key)
```

### Usage Patterns

**Pattern 1: TTL Cache (function-level)**
```python
from src.lib.project_cache import get_cache_ttl
from cachetools import cached

_cache = get_cache_ttl(maxsize=100, ttl=300)


@cached(cache=_cache)
def get_data(item_id: str) -> dict:
    # Cached for 5 minutes
    return fetch_data(item_id)
```

**Pattern 2: LRU Cache (class method)**
```python
from src.lib.project_cache import get_cache_lru
from cachetools import cached


class DataManager:
    _cache = get_cache_lru(maxsize=50)

    @cached(cache=_cache)
    def get_item(self, item_id: str):
        return self._fetch_item(item_id)
```

**Pattern 3: TTL + Thread Safety**
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

## Affected Modules

### Discovery Phase

Search for custom cache implementations:
- `grep -r "class.*Cache" src/` - Find custom cache classes
- `grep -r "def.*cache" src/` - Find cache-related functions
- `grep -r "TTL\|LRU\|evict\|maxsize" src/` - Find manual cache logic
- `grep -r "dict.*timestamp\|dict.*created" src/` - Find dict-based TTL caches

### Expected Custom Caches (Placeholder)

| Module | Pattern | Type | LOC | Replacement |
|--------|---------|------|-----|-------------|
| `src/services/provider_cache.py` | Dict-based TTL | TTL | 40 | `cachetools.TTLCache` |
| `src/lib/memo.py` | Manual LRU impl | LRU | 35 | `cachetools.LRUCache` |
| `src/api/response_cache.py` | Custom eviction | Mixed | 30 | `cachetools.LFUCache` |

*(Exact modules TBD after discovery)*

## Migration Strategy

### Phase 1: Add Dependency
- Add `cachetools==6.0.0` to `pyproject.toml`
- Run `uv sync`
- Verify no conflicts

### Phase 2: Create Wrapper
- Create `src/lib/project_cache.py` (~30 LOC)
- Add docstrings and examples
- Add to type checking

### Phase 3: Replace Caches (per module)
For each custom cache:

1. **Identify**: Locate custom class, understand interface
2. **Isolate**: Locate all call sites (grep, type checking)
3. **Replace**: Use cachetools equivalent + wrapper if needed
4. **Test**: Run unit tests for that module
5. **Remove**: Delete custom cache class (verify no usage remains)

### Phase 4: Integration Testing
- Run full test suite: `pytest`
- Run quality gates: `task quality`
- Verify coverage: `pytest --cov`

### Phase 5: Documentation
- Update `docs/research/LIBRARY_FIRST_AUDIT_AND_PLAN.md` - mark caching as governed
- Update project `CLAUDE.md` with caching pattern reference
- Create `docs/guides/CACHE_PATTERNS.md` with best practices

## Compatibility

**Breaking Changes**: None (wrapper is transparent)

**Deprecations**: Custom cache classes will be removed (old code will fail to import)

**Migration Path**:
```python
# Old
from src.lib.old_cache import LRUCache

cache = LRUCache(maxsize=100)

# New
from src.lib.project_cache import get_cache_lru
from cachetools import cached

cache = get_cache_lru(100)


@cached(cache=cache)
def my_func():
    pass
```

## Performance Impact

**Expected**: Negligible (cachetools is hand-optimized C code in CPython)

- **TTL Cache**: ~1-2% faster (C implementation vs. Python dict)
- **LRU Cache**: ~5-10% faster (linked-list eviction vs. manual)
- **Memory**: Same (dict-based storage)

**Benchmarking**: Simple before/after timing on hot cache paths (optional, post-merge)

## Testing Strategy

### Unit Tests (Per Module)
- Verify cache hits/misses work
- Verify eviction (size and TTL)
- Verify thread safety (if using locks)
- Verify no functional changes to cached functions

### Integration Tests
- Cache behavior across module boundaries
- Concurrent access (multi-threaded tests)
- Cache invalidation patterns

### Regression Tests
- All existing tests must pass
- Coverage threshold maintained (80%+)

## Rollback Plan

- **If tests fail**: Revert `pyproject.toml` and `src/lib/project_cache.py`, restore original cache classes
- **If performance regression**: Profile with `py-spy`, optimize wrapper or cache policy
- **If issues in production**: Use `git revert` to undo the commit

---

## Files to Modify

| File | Change | Type |
|------|--------|------|
| `pyproject.toml` | Add `cachetools==6.0.0` | dependency |
| `src/lib/project_cache.py` | Create new wrapper | new file |
| `src/services/provider_cache.py` | Replace custom cache | replace |
| `src/lib/memo.py` | Replace custom cache | replace |
| `src/api/response_cache.py` | Replace custom cache | replace |
| Tests for above modules | Update imports, verify behavior | update |
| `docs/research/LIBRARY_FIRST_AUDIT_AND_PLAN.md` | Mark caching as governed | update |
| `CLAUDE.md` | Add caching to library preferences | update |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Breaking change to cache interface | Low | Medium | Thorough test coverage |
| Performance regression | Very Low | Medium | Benchmark before/after |
| Memory overhead | Very Low | Low | Monitor with profiler |
| Thread safety issues | Low | High | Use `lock` param in decorator |

**Overall Risk**: Low (isolated change, well-tested library, good test coverage)
