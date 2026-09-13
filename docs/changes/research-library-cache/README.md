# Research: Standardized Caching Library (cachetools)

**Status**: Research Complete, Ready for Implementation
**Change**: research-library-cache
**Date**: 2026-02-18

## Overview

This directory contains a complete research and design package for standardizing caching across the thegent project using the `cachetools` library (v6.0.0). The package includes a detailed proposal, technical design, and phased task breakdown for implementation.

## Documents

### 1. Proposal (`proposal.md`) — 70 lines

**Purpose**: Define the problem, goals, and rationale.

**Covers**:

- **Problem**: Code duplication, custom cache implementations, inconsistency
- **Goals**: Replace all custom caches, reduce code by >150 LOC, improve safety
- **Success Criteria**: 7 measurable checkpoints
- **Rationale**: Why cachetools (mature, zero deps, battle-tested)
- **Timeline**: ~12-17 tool calls (~20-25 min)

**Key Finding**: cachetools is already a dependency in `pyproject.toml` (v≥5.3.3).

---

### 2. Design (`design.md`) — 241 lines

**Purpose**: Technical architecture, wrapper API, and implementation patterns.

**Covers**:

- **Architecture**: Thin wrapper pattern (<50 LOC) in `src/lib/project_cache.py`
- **Wrapper API**:
  - `get_cache_ttl(maxsize, ttl)` → TTLCache
  - `get_cache_lru(maxsize)` → LRUCache
  - `get_cache_lfu(maxsize)` → LFUCache
- **Usage Patterns**: 3 common patterns (TTL, LRU, thread-safe)
- **Migration Strategy**: 5-phase approach (setup → wrapper → discovery → replacement → validation → docs)
- **File Changes**: 8 files to modify/create
- **Risk Assessment**: Low overall risk, clear mitigation strategies
- **Performance Impact**: Negligible (C implementation expected 1-10% faster)
- **Testing Strategy**: Unit + integration + regression tests
- **Rollback Plan**: Clear revert procedures

---

### 3. Tasks (`tasks.md`) — 245 lines

**Purpose**: Phased work breakdown with detailed acceptance criteria.

**Phases** (6 phases, 13-15 total tasks):

1. **Setup** (2 tasks, 2 min)
   - Add cachetools dependency (NOTE: already present)
   - Verify test environment

2. **Wrapper** (2 tasks, 5 min)
   - Create `src/lib/project_cache.py`
   - Write unit tests + usage guide

3. **Discovery** (1 task, 3 min)
   - Search for all custom cache implementations
   - Create discovery map

4. **Migration** (3-5 tasks, 10-15 min)
   - Per custom cache: identify → baseline → replace → test → delete
   - Parallelizable after discovery

5. **Validation** (3 tasks, 5 min)
   - Full test suite
   - Quality gates
   - Code reduction measurement

6. **Documentation** (2 tasks, 5 min)
   - Update library-first audit
   - Archive change documentation

**Total Effort**: ~13-15 tasks, 30-35 min wall clock (parallelizable)

---

### 4. Synthesis (`../CONVERSATION_DUMP_2026-02-18-cache-synthesis.md`) — 462 lines

**Purpose**: Executive summary, implementation readiness confirmation, and quick reference.

**Covers**:

- Executive summary of the entire change
- Change rationale and library choice evaluation
- Complete implementation plan with phased breakdown
- Architecture overview and wrapper design
- Dependency status (already present ✅)
- Phase-by-phase detailed steps
- Risk assessment with mitigation
- Testing strategy and rollback plan
- Next steps for implementation
- Command cheatsheet and key APIs

---

## Quick Start

### For Readers (Understanding the Change)

1. **Start here**: Read `proposal.md` (5 min)
   - Understand the problem and goals
   - See success criteria

2. **Then read**: Read `design.md` (10 min)
   - Understand the technical approach
   - See wrapper API and usage patterns
   - Review affected files

3. **Reference**: Use `tasks.md` and synthesis for detailed execution

### For Implementers (Executing the Change)

1. **Read all**: proposal.md → design.md → tasks.md (20 min total)
2. **Verify**: Run Phase 1 tasks (setup, verify dependencies)
3. **Execute**: Follow tasks.md phase-by-phase
4. **Commit**: Per-phase commits (not per-task)
5. **Validate**: Quality gates after each phase
6. **Handoff**: Archive docs and close change

### For Reviewers (Auditing the Change)

1. **Check**: Does implementation match design.md?
2. **Verify**: Were all tasks.md acceptance criteria met?
3. **Test**: Do all tests pass? Coverage maintained?
4. **Review**: Is wrapper <50 LOC? No new suppressions?
5. **Approve**: Confirm success criteria from proposal.md

---

## Key Decisions

| Decision                  | Rationale                        | Status               |
| ------------------------- | -------------------------------- | -------------------- |
| Use cachetools v6.0.0     | Mature, zero deps, battle-tested | ✅ Approved          |
| Thin wrapper in src/lib/  | Project conventions, consistency | ✅ Approved          |
| <50 LOC wrapper           | Minimize overhead                | ✅ Target            |
| Phased implementation     | Risk management, parallelization | ✅ Strategy          |
| >150 LOC reduction target | Justify refactoring effort       | ✅ Success criterion |

---

## Status Checklist

- ✅ Proposal complete and approved
- ✅ Design complete and detailed
- ✅ Task breakdown complete with acceptance criteria
- ✅ Dependency (cachetools) already present in pyproject.toml
- ✅ Risk assessment: Low overall
- ✅ Test strategy defined
- ✅ Rollback plan documented
- 🟡 Implementation: Pending (ready to start)
- ⭕ Verification: Pending (after implementation)
- ⭕ Deployment: Pending (after verification)

---

## Success Metrics

| Metric                       | Target   | Tracking                       |
| ---------------------------- | -------- | ------------------------------ |
| Custom cache classes removed | 100%     | Count in discovery phase       |
| Code reduction (LOC)         | >150     | Diff before/after              |
| Test pass rate               | 100%     | pytest output                  |
| Coverage maintained          | 80%+     | pytest --cov                   |
| Quality gates                | 0 errors | task quality output            |
| Wrapper size                 | <50 LOC  | wc -l src/lib/project_cache.py |
| New suppressions             | 0        | ruff check output              |

---

## Related Documentation

### Governance & Standards

- `docs/research/LIBRARY_FIRST_AUDIT_AND_PLAN.md` — Library-First Policy mandate
- `docs/guides/anti-patterns.md` — Custom implementations as anti-pattern
- `CLAUDE.md` — Project library preferences
- `docs/research/PROACTIVE_GOVERNANCE_EVOLUTION_PLAN.md` — Governance evolution process

### Similar Changes

- `docs/changes/research-library-retry/` — Using tenacity for retries
- `docs/changes/research-library-watch/` — Using watchdog for file watching

### Implementation Support

- `Taskfile.yml` — Build automation (task quality, task test)
- `.pre-commit-config.yaml` — Linting and security checks
- `pyproject.toml` — Project dependencies and tool config

---

## Implementation Workflow

### Step 1: Prepare (5 min)

```bash
# Verify cachetools is installed
python -c "import cachetools; print(f'cachetools {cachetools.__version__}')"

# Verify test environment
pytest --co -q | head -5
```

### Step 2: Implement (20 min)

Follow `tasks.md` phases in order:

- Phase 1: Verify setup
- Phase 2: Create wrapper
- Phase 3: Discover custom caches
- Phase 4: Replace per cache (parallelizable)
- Phase 5: Validate
- Phase 6: Document

### Step 3: Validate (5 min)

```bash
# Full test suite
pytest tests/ -v --cov=src/ -q

# Quality gates
task quality

# Coverage check
pytest tests/ --cov=src/ --cov-fail-under=80
```

### Step 4: Complete (5 min)

- Commit changes (per-phase)
- Update documentation
- Archive change docs
- Link to merge commit

---

## Common Questions

**Q: Is cachetools already a dependency?**
A: Yes! Check `pyproject.toml` — already listed as `cachetools>=5.3.3`. Proposal recommends pinning to `==6.0.0` for consistency.

**Q: What if we find no custom caches?**
A: Mark as WONTFIX. Archive documentation. Focus on preventing future custom implementations.

**Q: What if we find >10 custom caches?**
A: Still feasible (larger timeline, 45-60 min). Parallelize Phase 4 across multiple agents.

**Q: Can we parallelize the work?**
A: Yes! Phases 1-3 must be sequential. Phase 4 (per-cache replacement) can run in parallel. Phase 5 aggregates results. Phase 6 finalizes.

**Q: What if a custom cache has edge cases?**
A: Write a baseline test first (before replacing). This captures current behavior. Compare behavior before/after to ensure compatibility.

**Q: Do we need to update documentation?**
A: Yes. Tasks 6.1 updates the Library-First Audit and project CLAUDE.md. Docs creation happens in Task 2.2.

---

## Timeline

| Phase      | Tasks     | Effort        | Dependencies        | Parallelizable?                        |
| ---------- | --------- | ------------- | ------------------- | -------------------------------------- |
| Setup      | 2         | 2 min         | None                | ✅ N/A (short)                         |
| Wrapper    | 2         | 5 min         | Setup               | ❌ Sequential                          |
| Discovery  | 1         | 3 min         | None                | ✅ Can run in parallel with Phases 1-2 |
| Migration  | 3-5       | 10-15 min     | Wrapper + Discovery | ✅ Highly parallelizable               |
| Validation | 3         | 5 min         | Migration           | ❌ Sequential (aggregates results)     |
| Docs       | 2         | 5 min         | Validation          | ✅ Can start after Phase 5             |
| **Total**  | **13-15** | **30-35 min** | —                   | **20-25 min critical path**            |

**Critical Path**: Setup → Wrapper → Discovery (parallel) → Migration (parallel) → Validation → Docs

---

## Next Steps

### Immediate Actions

1. **Verify readiness**: Check `pyproject.toml` for cachetools version
2. **Understand scope**: Run discovery (Phase 3) to find custom caches
3. **Estimate effort**: Count custom caches × ~3-5 min per cache
4. **Assign work**: Create tasks in issue tracker per phase
5. **Begin Phase 1**: Verify environment and dependencies

### For Integration

- This change aligns with the **Library-First Policy** mandate
- Governance hook will flag custom cache implementations as anti-pattern
- Completion updates the **Library-First Audit** (mandatory governance)

---

## Document Index

| File         | Lines    | Purpose                               |
| ------------ | -------- | ------------------------------------- |
| proposal.md  | 70       | Problem, goals, rationale             |
| design.md    | 241      | Architecture, patterns, files         |
| tasks.md     | 245      | Phased breakdown, acceptance criteria |
| synthesis.md | 462      | Executive summary, quick reference    |
| **Total**    | **1018** | Complete implementation package       |

---

## Version History

| Version | Date       | Changes                                        |
| ------- | ---------- | ---------------------------------------------- |
| 1.0     | 2026-02-18 | Initial research completion, synthesis writeup |

---

## Contact & Support

- **Questions about proposal/design**: See `proposal.md` and `design.md` sections
- **Questions about implementation**: See `tasks.md` acceptance criteria
- **Questions about next steps**: See synthesis.md "Next Steps" section
- **Report issues**: Create task from `tasks.md` checklist

---

**Status**: ✅ Research Complete
**Readiness**: 🟢 Ready for Implementation
**Approval**: Pending (start with Phase 1)
**Archive**: Move to `docs/changes/archive/` after merge
