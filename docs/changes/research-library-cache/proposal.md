# Proposal: Replace Custom Caching with cachetools

## Overview

Replace ad-hoc custom caching implementations with the industry-standard `cachetools` library to reduce code complexity, improve maintainability, and leverage battle-tested caching strategies.

## Problem Statement

- **Code duplication**: Multiple custom cache implementations across the codebase (TTL cache, LRU cache, simple dict-based caching)
- **Maintenance burden**: Custom cache logic scattered across modules, difficult to audit and extend
- **Missing features**: No built-in support for eviction policies, cache statistics, or thread safety guarantees
- **Inconsistency**: Different cache behaviors depending on which custom implementation is used
- **No governance**: Custom caching not tracked in library-first audit; violates project standards

## Goals

1. **Replace all custom caches** with cachetools equivalents (LRU, TTL, Least-Frequently-Used)
2. **Reduce code by ~200 LOC** (estimated 80 LOC custom cache code + 120 LOC wrappers/callers)
3. **Improve safety**: Use thread-safe decorators where appropriate
4. **Document patterns**: Create thin wrapper with project conventions for consistent usage
5. **Maintain compatibility**: No breaking changes to calling code (transparent wrapper)

## Success Criteria

- [ ] All custom cache classes removed
- [ ] All cache usages replaced with cachetools (direct or wrapper)
- [ ] Wrapper follows project conventions (<50 LOC)
- [ ] All existing tests pass (no breaking changes)
- [ ] Code reduction: >150 LOC removed
- [ ] Library-first audit updated
- [ ] Zero new warnings from quality gates

## Out of Scope

- Cache persistence/serialization (use diskcache if needed later)
- Custom cache statistics UI (log instead)
- Distributed caching (local-only for now)

## Related Standards

- **Library-First Policy**: `docs/research/LIBRARY_FIRST_AUDIT_AND_PLAN.md`
- **Anti-Patterns**: `docs/guides/anti-patterns.md`
- **CLAUDE.md**: Project library preferences for caching

## Timeline & Effort

- Discovery & mapping: 1-2 tool calls (identify all custom caches)
- Wrapper design: 2-3 tool calls (define thin wrapper)
- Implementation: 4-6 tool calls (replace caches, test)
- Validation: 2-3 tool calls (run tests, quality gates)
- Documentation: 1-2 tool calls (update audit, CLAUDE.md)

**Total**: ~12-17 tool calls (~20-25 min)

---

## Rationale

**Why cachetools?**

- Mature, battle-tested library (10+ years, widely used)
- Minimal dependencies (zero external deps)
- Supports LRU, LFU, TTL, and custom eviction policies
- Thread-safe decorators available
- ~100 LOC overhead vs. custom implementations

**Why now?**

- Library-first governance mandate active
- No active cache refactoring in progress
- Quality gate will flag custom cache implementations as anti-pattern
- Minimal risk (isolated caching logic)
