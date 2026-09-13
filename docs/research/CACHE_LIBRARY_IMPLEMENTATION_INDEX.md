<DONE>
# Caching Library Standardization — Quick Index

**Status**: Research Complete, Ready for Implementation
**Project**: thegent
**Last Updated**: 2026-02-18

---

## 📁 Documentation Map

### Core Research Package

| Document      | Location                                                        | Size  | Purpose                         |
| ------------- | --------------------------------------------------------------- | ----- | ------------------------------- |
| **Proposal**  | `docs/changes/research-library-cache/proposal.md`               | 70 L  | Problem + Goals + Rationale     |
| **Design**    | `docs/changes/research-library-cache/design.md`                 | 241 L | Architecture + Patterns + Files |
| **Tasks**     | `docs/changes/research-library-cache/tasks.md`                  | 245 L | Phased Breakdown + Criteria     |
| **README**    | `docs/changes/research-library-cache/README.md`                 | 380 L | Change Overview + Quick Start   |
| **Synthesis** | `docs/research/CONVERSATION_DUMP_2026-02-18-cache-synthesis.md` | 462 L | Executive Summary + Readiness   |

### Total: 1,398 lines of documentation

---

## 🎯 Quick Navigation

### I want to understand the change (15 min read)

1. Read: `proposal.md` (5 min) — What's the problem?
2. Skim: `design.md` sections (5 min) — How are we solving it?
3. Review: `tasks.md` summary table (5 min) — What's the work?

### I want to implement this (40 min execution)

1. Read all docs: proposal → design → tasks (20 min)
2. Execute: Follow `tasks.md` phases 1-6 (20 min)
3. Validate: Run tests & quality gates (5 min)
4. Handoff: Archive docs (5 min)

### I want to review this change

1. Checklist: Compare implementation to `design.md` sections
2. Acceptance criteria: Verify all `tasks.md` criteria met
3. Testing: Confirm `pytest` output and coverage
4. Success metrics: Check `README.md` checklist

---

## 📊 Change Summary

| Aspect     | Detail                                                                   |
| ---------- | ------------------------------------------------------------------------ |
| **What**   | Replace custom caching with `cachetools` v6.0.0                          |
| **Why**    | Reduce code duplication, improve safety, align with Library-First Policy |
| **Where**  | `src/lib/project_cache.py` (wrapper) + per-module replacements           |
| **Effort** | ~30-35 min (13-15 tasks, parallelizable)                                 |
| **Risk**   | 🟢 Low (isolated change, well-tested library)                            |
| **Value**  | >150 LOC reduction, zero breaking changes                                |

---

## ✅ Readiness Checklist

- ✅ Proposal: Complete, approved, clear success criteria
- ✅ Design: Complete, detailed architecture, wrapper API defined
- ✅ Tasks: Complete, 13-15 tasks with acceptance criteria
- ✅ Dependency: cachetools v≥5.3.3 already in pyproject.toml
- ✅ Risk Assessment: Low risk, clear mitigation
- ✅ Test Strategy: Unit + integration + regression defined
- ✅ Rollback Plan: Clear revert procedures documented
- 🟡 Discovery: Pending (Phase 3 will find custom caches)
- ⭕ Implementation: Ready to start

---

## 🚀 Implementation Phases

```
Phase 1: Setup (2 tasks, 2 min)
├─ Verify cachetools installed
└─ Verify test environment ready

Phase 2: Wrapper (2 tasks, 5 min)
├─ Create src/lib/project_cache.py (<50 LOC)
└─ Write tests + usage guide

Phase 3: Discovery (1 task, 3 min)
├─ Search for custom caches
└─ Create discovery map

Phase 4: Migration (3-5 tasks, 10-15 min) [Parallelizable]
├─ Per custom cache
├─ Identify → Baseline → Replace → Test → Delete
└─ Verify no import errors

Phase 5: Validation (3 tasks, 5 min)
├─ Full test suite
├─ Quality gates
└─ Code reduction measurement

Phase 6: Docs (2 tasks, 5 min)
├─ Update Library-First Audit
└─ Archive change documentation
```

**Critical Path**: Setup → Wrapper → Discovery → Migration → Validation → Docs
**Parallel Opportunities**: Discovery can run during Phase 2; Phase 4 tasks can run in parallel

---

## 🎨 Wrapper API Overview

### Location

`src/lib/project_cache.py` (~30 LOC)

### Functions

```python
# Factory functions
get_cache_ttl(maxsize: int, ttl: int) -> TTLCache
get_cache_lru(maxsize: int) -> LRUCache
get_cache_lfu(maxsize: int) -> LFUCache
```

### Usage Patterns

**Pattern 1: TTL Cache (function-level)**

```python
from src.lib.project_cache import get_cache_ttl
from cachetools import cached

_cache = get_cache_ttl(maxsize=100, ttl=300)


@cached(cache=_cache)
def get_data(item_id: str):
    return fetch_data(item_id)  # Cached 5 minutes
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

**Pattern 3: Thread-Safe**

```python
from src.lib.project_cache import get_cache_ttl
from cachetools import cached
from threading import RLock

_cache = get_cache_ttl(maxsize=100, ttl=300)
_lock = RLock()


@cached(cache=_cache, lock=_lock)
def get_data_safe(item_id: str):
    return fetch_data(item_id)
```

---

## 📋 Success Criteria

All must be met for change completion:

- [ ] All custom cache classes removed (100%)
- [ ] All cache usages replaced with cachetools
- [ ] Wrapper follows project conventions (<50 LOC)
- [ ] All existing tests pass (100% pass rate)
- [ ] Code reduction: >150 LOC
- [ ] Coverage maintained: 80%+
- [ ] Quality gates: 0 errors
- [ ] Zero new lint suppressions
- [ ] Documentation updated (audit + CLAUDE.md)
- [ ] Change archived (post-merge)

---

## ⚠️ Key Risks & Mitigation

| Risk                   | Mitigation                                      |
| ---------------------- | ----------------------------------------------- |
| Breaking change        | Thorough test coverage, baseline test per cache |
| Performance regression | Profile before/after, benchmark hot paths       |
| Memory overhead        | Monitor with profiler, review sizes             |
| Thread safety          | Use `lock` param in decorator when needed       |
| Missed call sites      | Grep verification, type checker confirmation    |

**Overall Assessment**: 🟢 Low Risk

---

## 🛠️ Command Reference

### Verify Setup

```bash
python -c "import cachetools; print(cachetools.__version__)"
pytest --co -q | head -5
```

### Create Wrapper

```bash
cat > src/lib/project_cache.py << 'EOF'
from cachetools import TTLCache, LRUCache, LFUCache

def get_cache_ttl(maxsize: int, ttl: int) -> TTLCache:
    """Return a TTL cache."""
    return TTLCache(maxsize=maxsize, ttl=ttl)

def get_cache_lru(maxsize: int) -> LRUCache:
    """Return an LRU cache."""
    return LRUCache(maxsize=maxsize)

def get_cache_lfu(maxsize: int) -> LFUCache:
    """Return an LFU cache."""
    return LFUCache(maxsize=maxsize)
EOF
```

### Find Custom Caches

```bash
grep -r "class.*Cache" src/
grep -r "dict.*timestamp\|dict.*ttl" src/
grep -r "LRU\|evict\|maxsize" src/
```

### Run Tests

```bash
pytest tests/test_project_cache.py -v
pytest tests/ --cov=src/ -q
pytest tests/ --cov=src/ --cov-fail-under=80
```

### Quality Gates

```bash
task quality
task lint
task test
ruff check src/
```

---

## 📈 Effort Breakdown

| Phase         | Tasks     | Time          | Parallelizable?             |
| ------------- | --------- | ------------- | --------------------------- |
| 1: Setup      | 2         | 2 min         | N/A                         |
| 2: Wrapper    | 2         | 5 min         | No                          |
| 3: Discovery  | 1         | 3 min         | **Yes** (run with 1-2)      |
| 4: Migration  | 3-5       | 10-15 min     | **Yes** (all per-cache)     |
| 5: Validation | 3         | 5 min         | No (aggregates)             |
| 6: Docs       | 2         | 5 min         | Yes                         |
| **Total**     | **13-15** | **30-35 min** | **20-25 min critical path** |

---

## 🔗 Related Resources

### Governance & Policy

- `docs/research/LIBRARY_FIRST_AUDIT_AND_PLAN.md` — Library-First Policy mandate
- `docs/guides/anti-patterns.md` — Custom implementations as anti-pattern
- `CLAUDE.md` — Project library preferences
- `docs/research/PROACTIVE_GOVERNANCE_EVOLUTION_PLAN.md` — Governance process

### Similar Changes

- `docs/changes/research-library-retry/` — Using tenacity for retries (reference)
- `docs/changes/research-library-watch/` — Using watchdog for file watching (reference)

### Implementation Support

- `Taskfile.yml` — Build automation (`task quality`, `task test`)
- `pyproject.toml` — Dependencies and tool config
- `.pre-commit-config.yaml` — Linting and security

---

## 🚦 Implementation Decision Points

**Should we proceed?**

- ✅ Proposal clear and complete
- ✅ Design detailed and implementable
- ✅ cachetools already a dependency
- ✅ Risk is low (isolated, well-tested)
- ✅ Alignment with Library-First Policy strong
- **Recommendation**: ✅ **Proceed immediately**

**What if discovery finds no custom caches?**

- Mark as WONTFIX
- Archive documentation
- Focus on preventing future custom implementations

**What if discovery finds >10 custom caches?**

- Still feasible (extend timeline to 45-60 min)
- Parallelize Phase 4 across multiple agents
- Reassess if additional resources needed

---

## 📞 Questions & Support

| Question               | Answer Location                             |
| ---------------------- | ------------------------------------------- |
| What's the problem?    | `proposal.md` — Problem Statement section   |
| How are we solving it? | `design.md` — Architecture Overview section |
| What are the tasks?    | `tasks.md` — Phased Work Breakdown section  |
| How do I start?        | `README.md` — Quick Start section           |
| What could go wrong?   | `design.md` — Risk Assessment section       |
| How do I validate?     | `synthesis.md` — Testing Strategy section   |
| How do I rollback?     | `design.md` — Rollback Plan section         |

---

## 📦 Deliverables

### Research Output (Complete)

- ✅ 5 markdown documents (1,398 lines total)
- ✅ Proposal with success criteria
- ✅ Detailed technical design
- ✅ Phased task breakdown (13-15 tasks)
- ✅ Executive summary and synthesis
- ✅ This quick index

### Implementation Output (Pending)

- ⭕ `src/lib/project_cache.py` wrapper (~30 LOC)
- ⭕ `tests/test_project_cache.py` tests
- ⭕ Per-module cache replacements (3-5 modules)
- ⭕ Updated tests for each module
- ⭕ Updated documentation (audit + CLAUDE.md)
- ⭕ Code reduction report (>150 LOC)

---

## 🎓 How to Use This Index

**For Quick Navigation**: Use the "📁 Documentation Map" table
**For Understanding**: Follow "I want to understand the change" (15 min)
**For Implementation**: Follow "I want to implement this" (40 min)
**For Review**: Use "I want to review this change" checklist
**For Questions**: See "📞 Questions & Support" table

---

**Version**: 1.0
**Status**: Ready for Implementation
**Audience**: Developers, Reviewers, Project Managers
**Last Verified**: 2026-02-18

🚀 **Ready to begin? Start with Phase 1 in `tasks.md`**
