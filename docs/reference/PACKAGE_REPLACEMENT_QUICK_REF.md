# Package Replacement Quick Reference

> **Quick access guide** for implementing package replacements. See [PACKAGE_REPLACEMENT_IMPLEMENTATION_PLAN.md](../plans/PACKAGE_REPLACEMENT_IMPLEMENTATION_PLAN.md) for full details.

---

## Task Quick Reference

### Priority 1 (Critical) - Start Here

| Task                 | Files | Effort | Pattern                                              |
| -------------------- | ----- | ------ | ---------------------------------------------------- |
| **urllib→httpx**     | 7+    | 2-3h   | `httpx.get(url)` instead of `urllib.request.urlopen` |
| **retry→tenacity**   | 4     | 4-6h   | `@retry()` decorator instead of manual loops         |
| **polling→watchdog** | 1     | 2-4h   | `Observer` instead of `os.walk` polling              |

### Priority 2 (High Value)

| Task                          | Files | Effort | Pattern                                    |
| ----------------------------- | ----- | ------ | ------------------------------------------ |
| **cache→cachetools**          | 5+    | 2-3h   | `TTLCache()` instead of custom dict        |
| **circuit breaker→pybreaker** | 1     | 2-3h   | `CircuitBreaker()` instead of custom class |
| **PyYAML→ruamel.yaml**        | 15+   | 3-4h   | `YAML()` preserves comments/order          |
| **ANSI→rich**                 | 5     | 1h     | `strip_control_codes()` instead of regex   |
| **scrapers→diskcache**        | 1     | 1h     | `diskcache.Cache()` for file cache         |
| **monitoring→psutil**         | 2     | 2-3h   | `psutil.Process()` instead of subprocess   |

### Priority 3 (Quick Wins)

| Task                       | Files | Effort | Pattern                                      |
| -------------------------- | ----- | ------ | -------------------------------------------- |
| **md5→sha256**             | 1     | 0.5h   | `hashlib.sha256()` instead of `md5()`        |
| **os.environ→Settings**    | 15+   | 2-3h   | `settings.key` instead of `os.environ.get()` |
| **\_CWD_CACHE→cachetools** | 1     | 0.5h   | `TTLCache()` instead of dict                 |
| **Add tomlkit**            | deps  | 0.5h   | Add to `pyproject.toml`                      |

---

## Implementation Order

### Phase 1: Quick Wins (2 hours)

1. Add tomlkit (5 min)
2. md5→sha256 (5 min)
3. ANSI strip (1 hr)
4. \_CWD_CACHE (30 min)

### Phase 2: Critical (8-13 hours)

1. urllib→httpx (2-3 hrs)
2. retry→tenacity (4-6 hrs)
3. polling→watchdog (2-4 hrs)

### Phase 3: High Value (12-18 hours)

1. cachetools (2-3 hrs)
2. diskcache (1 hr)
3. psutil (2-3 hrs)
4. pybreaker (2-3 hrs)
5. ruamel.yaml (3-4 hrs)

### Phase 4: Enhancements (2-3 hours)

1. os.environ→Settings (2-3 hrs)

---

## Code Patterns

### HTTP Replacement

```python
# Before
import urllib.request

with urllib.request.urlopen(req) as resp:
    data = resp.read()

# After
import httpx

resp = httpx.get(url)
data = resp.content
```

### Retry Replacement

```python
# Before
for attempt in range(3):
    try:
        result = do_work()
        break
    except Exception:
        if attempt == 2:
            raise
        time.sleep(2**attempt)

# After
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential())
def do_work():
    pass
```

### Cache Replacement

```python
# Before
cache = {}
timestamps = {}
if key in cache and time.time() - timestamps[key] < ttl:
    return cache[key]

# After
from cachetools import TTLCache

cache = TTLCache(maxsize=1000, ttl=3600)
return cache.get(key)
```

### File Watching Replacement

```python
# Before
while True:
    for root, dirs, files in os.walk(directory):
        # Check mtime
    time.sleep(2)

# After
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

observer = Observer()
observer.schedule(Handler(), directory, recursive=True)
observer.start()
```

---

## Dependencies to Add

```toml
[project]
dependencies = [
    # ... existing
    "watchdog>=4.0.0",      # File watching
    "cachetools>=5.0.0",   # Caching
    "diskcache>=5.0.0",    # File cache
    "pybreaker>=1.0.0",    # Circuit breaker
    "ruamel.yaml>=0.18.0", # YAML (preserves comments)
    "psutil>=5.9.0",       # Resource monitoring
    "tomlkit>=0.12.0",     # TOML parsing
]
```

**Already in deps**: `httpx`, `tenacity`, `rich`

---

## Files Affected Summary

### HTTP (urllib → httpx)

- `models/scrapers.py`
- `agents/cliproxy_manager.py`
- `agents/cursor_api_runner.py`
- `execution.py`
- `mcp_manage.py`
- `clode_main.py`
- `routing/alerting.py`

### Retry (Manual → tenacity)

- `cli_impl.py`
- `agents/loop_controller.py`
- `agents/state_machine.py` (verify)

### File Watching (Polling → watchdog)

- `governance/triggers.py`

### Caching (Custom → cachetools)

- `models/speed_values.py`
- `models/quality_values.py`
- `models/catalog.py`
- `cli_impl.py` (\_CWD_CACHE)

### Circuit Breaker (Custom → pybreaker)

- `agents/resilience.py`

### YAML (PyYAML → ruamel.yaml)

- 15+ files using PyYAML

### ANSI Stripping (Custom → rich)

- `agents/codex_proxy.py`
- `agents/direct_agents.py`
- `agents/droid.py`
- `agents/cursor_api_runner.py`
- `parser.py`

---

## Testing Checklist

For each replacement:

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Error handling works
- [ ] Performance maintained or improved
- [ ] No regressions
- [ ] Documentation updated

---

## Success Metrics

- ✅ HTTP: Connection pooling, HTTP/2
- ✅ File watch: Real-time (<100ms vs 2s polling)
- ✅ Cache: Automatic TTL, LRU eviction
- ✅ Retry: Consistent behavior
- ✅ YAML: Comments preserved
- ✅ Code reduction: -500+ lines

---

## References

- **Full Plan**: [PACKAGE_REPLACEMENT_IMPLEMENTATION_PLAN.md](../plans/PACKAGE_REPLACEMENT_IMPLEMENTATION_PLAN.md)
- **Research Summary**: [PACKAGE_REPLACEMENT_RESEARCH_SUMMARY.md](../research/PACKAGE_REPLACEMENT_RESEARCH_SUMMARY.md)
- **Work Stream**: [WORK_STREAM.md](./WORK_STREAM.md) - All tasks in BACKLOG

---

**Last Updated**: 2026-02-18
