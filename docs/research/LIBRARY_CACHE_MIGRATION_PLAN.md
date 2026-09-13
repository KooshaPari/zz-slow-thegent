<DONE>
# Library Cache Migration Plan

**ID**: research-library-cache
**Priority**: P2
**Status**: In Progress
**Files**: 5

## Overview

Replace custom caching implementations with `cachetools` library per LIBRARY_FIRST_POLICY.md.

## Custom Cache Implementations Found

### 1. `cli_impl.py` - Simple Dict Cache

**Location**: `src/thegent/cli_impl.py`
**Pattern**: Global `_CWD_CACHE` dict

```python
_CWD_CACHE: dict[str, tuple[str, float]] = {}
```

**Usage**: CWD-based cache with no TTL
**Migration**: Replace with `TTLCache(maxsize=100, ttl=3600)`

---

### 2. `infra/fast_json_schema.py` - Global Dict Cache

**Location**: `src/thegent/infra/fast_json_schema.py`
**Pattern**: Global `_schema_cache` dict

```python
_schema_cache: dict[str, FastJSONSchemaValidator] = {}
```

**Usage**: Schema validator caching (no expiration)
**Migration**: Replace with `LRUCache(maxsize=50)`

---

### 3. `infra/fast_process_monitor.py` - Class Attribute Cache with TTL

**Location**: `src/thegent/infra/fast_process_monitor.py`
**Pattern**: Instance attribute `self._cache` dict with manual TTL

```python
self._cache: dict[int, ProcessInfo] = {}
self._cache_time: float = 0
self._cache_ttl: float = 1.0  # Cache for 1 second
```

**Usage**: Process info caching with 1s TTL
**Migration**: Replace with `TTLCache(maxsize=100, ttl=1.0)`

---

### 4. `tools/cache.py` - Full JSONCache Implementation

**Location**: `src/thegent/tools/cache.py`
**Pattern**: Complete custom `JSONCache` class

```python
class JSONCache:
    def __init__(self, ttl_seconds: int = 300): ...
    def get(self, key: str): ...  # Checks time.time() - timestamp > ttl
    def set(self, key: str, payload: Any): ...
```

**Features**:

- File-based persistence (JSON)
- TTL expiration (manual time.time() checks)
- ETag hashing for change detection
- Global cache via `__call__`

**Usage**: Shared tool cache across sessions

**Migration**:

- Replace in-memory cache with `TTLCache`
- Keep file persistence as separate layer (decorator pattern)
- Remove manual TTL checks (handled by cachetools)

---

### 5. `infra/fast_cache.py` - Full FastCache Implementation

**Location**: `src/thegent/infra/fast_cache.py`
**Pattern**: Complete custom `FastCache` class with L1/L2 levels

```python
class FastCache:
    def __init__(self, l1_size: int = 10, l2_size: int = 100, ttl: int = 60): ...
    def get(self, key: str): ...  # Checks L1, then L2, with time.time() expiry
    def set(self, key: str, value: Any): ...  # LRU eviction from L2
```

**Features**:

- Two-level caching (L1 + L2)
- TTL expiration (manual time.time() checks)
- LRU eviction from L2
- Thread-safe (basic)

**Usage**: High-performance multi-level caching

**Migration**:

- Replace with `TTLCache` (single level, faster than custom)
- Remove manual L1/L2 logic (simpler, less code)
- Remove manual time.time() checks (handled by cachetools)
- Consider `LRUCache` for L2 if needed (but TTLCache is usually sufficient)

---

## Migration Plan

### Phase 1: Simple Dict Caches (2 files)

1. **cli_impl.py**
   - Replace `_CWD_CACHE: dict[str, tuple[str, float]]`
   - With `TTLCache(maxsize=100, ttl=3600)`
   - Tests: Verify cache eviction works

2. **infra/fast_json_schema.py**
   - Replace `_schema_cache: dict[str, FastJSONSchemaValidator]`
   - With `LRUCache(maxsize=50)`
   - Tests: Verify schema caching works

**Estimated**: 2 tool calls, 2-3 min

---

### Phase 2: Class Attribute Cache (1 file)

3. **infra/fast_process_monitor.py**
   - Replace `self._cache: dict[int, ProcessInfo]`
   - With `TTLCache(maxsize=100, ttl=1.0)`
   - Remove `self._cache_time` and `self._cache_ttl`
   - Tests: Verify 1s TTL works

**Estimated**: 3-4 tool calls, 2-3 min

---

### Phase 3: Full Implementations (2 files)

4. **tools/cache.py** (Most Complex)
   - Replace `JSONCache.__init__` cache with `TTLCache(maxsize=100, ttl=300)`
   - Keep file persistence (separate concern)
   - Remove `time.time()` checks from `get()` and `set()`
   - Update `__call__` to use new cache
   - Tests: Verify TTL, persistence, ETag still work

5. **infra/fast_cache.py** (Most Complex)
   - Replace entire `FastCache` class
   - With simple `TTLCache(maxsize=100, ttl=60)`
   - Remove L1/L2 logic (simpler, faster)
   - Remove manual eviction logic
   - Tests: Verify cache performance, TTL work

**Estimated**: 6-8 tool calls each, 5-8 min total

---

## Benefits of Cachetools

1. **Battle-tested**: 25M+ downloads, widely used
2. **Correctness**: No off-by-one errors in TTL calculations
3. **Performance**: Optimized C implementation where possible
4. **Features**: TTL, LRU, LFU, max size all built-in
5. **Type hints**: Full type annotation support
6. **Thread-safety**: Built-in `Lock` support via `@cached` decorator

---

## Test Coverage

Each migration must include:

- Unit test for cache behavior (get/set/expire)
- Integration test for actual usage pattern
- Performance regression test (should not be slower)

---

## Anti-Patterns to Avoid

1. **Do NOT** create wrapper classes around cachetools (thin wrapper only if needed)
2. **Do NOT** keep manual `time.time()` checks (let cachetools handle it)
3. **Do NOT** reinvent TTL math (use built-in)
4. **Do NOT** add custom LRU logic (use built-in)

---

## Migration Checklist

- [ ] Install cachetools: `uv add cachetools`
- [ ] Migrate cli_impl.py
- [ ] Migrate infra/fast_json_schema.py
- [ ] Migrate infra/fast_process_monitor.py
- [ ] Migrate tools/cache.py
- [ ] Migrate infra/fast_cache.py
- [ ] Add tests for each migration
- [ ] Update documentation
- [ ] Run `task quality` to verify

---

## Status

**Phase 1**: Not Started
**Phase 2**: Not Started
**Phase 3**: Not Started
