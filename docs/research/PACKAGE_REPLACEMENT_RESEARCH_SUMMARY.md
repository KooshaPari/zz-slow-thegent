<DONE>
# Package Replacement Research Summary

> **Date**: 2026-02-18
> **Status**: Research Complete, Implementation Plan Ready
> **Purpose**: Summary of latest package replacement research and implementation plan

---

## Research Documents Reviewed

1. **LIBRARY_REPLACEMENT_COMPLETE.md** (890 lines)
   - Comprehensive audit covering all replacement categories
   - File-level analysis with migration patterns
   - Complete breadth and depth

2. **LIBRARY_REPLACEMENT_CONSOLIDATED.md** (604 lines)
   - Unified migration strategy
   - Priority classifications
   - Migration phases

3. **LIBRARY_REPLACEMENT_PHASE_DWBS.md** (238 lines)
   - Detailed task breakdowns for each phase
   - File-by-file migration instructions
   - Execution order recommendations

**Total Research**: ~1,700+ lines consolidated

---

## Implementation Plan Created

**New Document**: `docs/plans/PACKAGE_REPLACEMENT_IMPLEMENTATION_PLAN.md`

### Key Features

1. **Complete Task Inventory**
   - 13 tasks total (9 replacements + 4 enhancements)
   - Prioritized (P1: 3, P2: 6, P3: 4)
   - Effort estimates: 0.5-6 hours per task

2. **Detailed Task Breakdowns**
   - Files affected
   - Migration patterns (before/after code)
   - Exception mapping
   - Acceptance criteria
   - Testing requirements

3. **Implementation Phases**
   - Phase 1: Quick Wins (1-2 hours)
   - Phase 2: Critical Replacements (8-13 hours)
   - Phase 3: High Value Replacements (12-18 hours)
   - Phase 4: Enhancements (2-3 hours)

4. **Risk Mitigation**
   - Technical risks and mitigations
   - Migration risks and mitigations
   - Testing strategy
   - Success metrics

---

## Tasks Identified

### Priority 1 (Critical) - 3 Tasks

| Task ID | Title | Files | Effort |
|---------|-------|-------|--------|
| IMPL-LIB-001 | Replace urllib with httpx | 7+ | 2-3 hrs |
| IMPL-LIB-002 | Migrate retry to tenacity | 4 | 4-6 hrs |
| IMPL-LIB-003 | Replace polling with watchdog | 1 | 2-4 hrs |

### Priority 2 (High Value) - 6 Tasks

| Task ID | Title | Files | Effort |
|---------|-------|-------|--------|
| IMPL-LIB-101 | Replace custom caching with cachetools | 5+ | 2-3 hrs |
| IMPL-LIB-102 | Replace circuit breaker with pybreaker | 1 | 2-3 hrs |
| IMPL-LIB-103 | Replace PyYAML with ruamel.yaml | 15+ | 3-4 hrs |
| IMPL-LIB-104 | Replace ANSI stripping with rich | 5 | 1 hr |
| IMPL-LIB-105 | Replace scrapers cache with diskcache | 1 | 1 hr |
| IMPL-LIB-106 | Add psutil for resource monitoring | 2 | 2-3 hrs |

### Priority 3 (Quick Wins) - 4 Tasks

| Task ID | Title | Files | Effort |
|---------|-------|-------|--------|
| IMPL-LIB-201 | Replace md5 with sha256 | 1 | 0.5 hr |
| IMPL-LIB-202 | Consolidate os.environ → ThegentSettings | 15+ | 2-3 hrs |
| IMPL-LIB-203 | Replace _CWD_CACHE with cachetools | 1 | 0.5 hr |
| IMPL-LIB-204 | Add tomlkit to dependencies | 1 | 0.5 hr |

**Total Effort**: ~23-36 hours

---

## WORK_STREAM.md Updates

### Tasks Added to BACKLOG

Added missing tasks to `docs/reference/WORK_STREAM.md`:

- `research-library-http` - Replace urllib with httpx (P1)
- `research-library-watchdog` - Replace polling with watchdog (P1)
- `research-library-diskcache` - Replace scrapers cache with diskcache (P2)
- `research-library-psutil` - Add psutil for resource monitoring (P2)
- `research-library-md5-sha256` - Replace md5 with sha256 (P3)
- `research-library-env-settings` - Consolidate os.environ → ThegentSettings (P3)
- `research-library-tomlkit` - Add tomlkit to dependencies (P3)

### Tasks Already in BACKLOG

- `research-library-retry` - Migrate retry to tenacity (P1) ✅
- `research-library-cache` - Replace custom caching with cachetools (P2) ✅
- `research-library-circuit-breaker` - Replace circuit breaker with pybreaker (P2) ✅
- `research-library-yaml` - Replace PyYAML with ruamel.yaml (P2) ✅
- `research-library-ansi` - Replace ANSI stripping with rich (P2) ✅

---

## Implementation Recommendations

### Start with Phase 1 (Quick Wins)

1. **IMPL-LIB-204** - Add tomlkit (5 min) - No code changes
2. **IMPL-LIB-201** - md5→sha256 (5 min) - Simple replacement
3. **IMPL-LIB-104** - ANSI strip (1 hr) - Straightforward
4. **IMPL-LIB-203** - _CWD_CACHE (30 min) - Quick win

**Total**: ~2 hours for 4 tasks

### Then Phase 2 (Critical)

1. **IMPL-LIB-001** - urllib→httpx (2-3 hrs) - High impact
2. **IMPL-LIB-002** - retry→tenacity (4-6 hrs) - Consistency
3. **IMPL-LIB-003** - polling→watchdog (2-4 hrs) - Performance

**Total**: ~8-13 hours for 3 tasks

### Continue with Phase 3 (High Value)

All P2 tasks can be done in parallel or sequentially based on dependencies.

---

## Key Migration Patterns

### HTTP (urllib → httpx)
```python
# Before
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as resp:
    data = resp.read()

# After
resp = httpx.get(url)
data = resp.content
```

### Retry (Manual → tenacity)
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
@retry(stop=stop_after_attempt(3), wait=wait_exponential())
def do_work():
    pass
```

### File Watching (Polling → watchdog)
```python
# Before
while True:
    for root, dirs, files in os.walk(directory):
        # Check mtime
    time.sleep(2)

# After
observer = Observer()
observer.schedule(Handler(), directory, recursive=True)
observer.start()
```

---

## Next Steps

1. ✅ **Research Complete** - All documents reviewed
2. ✅ **Implementation Plan Created** - `PACKAGE_REPLACEMENT_IMPLEMENTATION_PLAN.md`
3. ✅ **WORK_STREAM Updated** - Missing tasks added
4. ⏳ **Ready for Implementation** - Start with Phase 1 (Quick Wins)

---

## References

- [PACKAGE_REPLACEMENT_IMPLEMENTATION_PLAN.md](../plans/PACKAGE_REPLACEMENT_IMPLEMENTATION_PLAN.md) - Complete implementation guide
- [LIBRARY_REPLACEMENT_COMPLETE.md](./LIBRARY_REPLACEMENT_COMPLETE.md) - Comprehensive audit
- [LIBRARY_REPLACEMENT_CONSOLIDATED.md](./LIBRARY_REPLACEMENT_CONSOLIDATED.md) - Consolidated plan
- [LIBRARY_REPLACEMENT_PHASE_DWBS.md](./LIBRARY_REPLACEMENT_PHASE_DWBS.md) - Detailed task breakdowns
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream

---

**Status**: Research complete, implementation plan ready
**Last Updated**: 2026-02-18
