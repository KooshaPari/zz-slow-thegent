<DONE>
# Swarm & Resource Optimization — Research Index

> **Purpose**: Master index for all swarm, process, resource, and resilience research. Use this to navigate the full research corpus.
> **Status**: Index | **Date**: 2026-02-16
> **Sprawl**: Linked docs are full research (no fragment sprawl pending). Catalog of fragments/seeds: [RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md).

---

## Sprawl Status

| Document                           | Sprawl Status | Expanded To                                           | BACKLOG Items |
| ---------------------------------- | ------------- | ----------------------------------------------------- | ------------- |
| **LIBRARY_REPLACEMENT_AUDIT_DEEP** | ✅ Complete   | Consolidated into LIBRARY_REPLACEMENT_CONSOLIDATED.md | 9 items       |
| **LIBRARY_FIRST_AUDIT_AND_PLAN**   | ✅ Complete   | Consolidated into LIBRARY_REPLACEMENT_CONSOLIDATED.md | Included      |
| **LIBRARY_REPLACEMENT_PHASE_DWBS** | ✅ Complete   | Consolidated into LIBRARY_REPLACEMENT_CONSOLIDATED.md | Included      |
| **TENACITY_RETRY_AUDIT_PLAN**      | ✅ Complete   | Referenced in LIBRARY_REPLACEMENT_CONSOLIDATED.md     | Included      |
| **Other swarm docs**               | ✅ Complete   | Full research docs, no sprawl needed                  | -             |

**See Also**: [RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

---

## Quick Navigation

| Topic                                      | Primary Doc                                                                                                       | One-Liner                                                                                                                                                                                                                                          | Sprawl Status |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| **User setup**                             | [SWARM_PROCESS_OPTIMIZATIONS](../reference/SWARM_PROCESS_OPTIMIZATIONS.md)                                        | Quick reference: auto-prune, load shaping, spotlight                                                                                                                                                                                               |
| **Automation taxonomy**                    | [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md)                             | Triggers, discovery, prune, platform ecosystem                                                                                                                                                                                                     |
| **Scheduling theory**                      | [SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH](./SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md)                   | Load balancing, ConcurrencyController, industry systems                                                                                                                                                                                            |
| **Smart strategies**                       | [SMART_ROBUST_STRATEGIES_RESEARCH](./SMART_ROBUST_STRATEGIES_RESEARCH.md)                                         | Process lifecycle, LSP multiplexing, child death handling                                                                                                                                                                                          |
| **FD, CPU, resources**                     | [SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH](./SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md)                               | Sampling, limits, Activity Monitor–style metrics                                                                                                                                                                                                   |
| **Resilience**                             | [ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH](./ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH.md)                   | Retry, backoff, jitter, circuit breaker, bulkhead, timeout, health checks, cascading failure                                                                                                                                                       |
| **Memory long-term**                       | [MEMORY_OPTIMIZATION_LONG_TERM_PLAN](./MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md)                                     | LSP triplet, cc-status, Spotlight; phased roadmap                                                                                                                                                                                                  |
| **Tenacity vs custom retry**               | [TENACITY_RETRY_AUDIT_PLAN](./TENACITY_RETRY_AUDIT_PLAN.md)                                                       | Audit custom retry loops; migrate to tenacity; add jitter                                                                                                                                                                                          |
| **Library-first policy**                   | [LIBRARY_FIRST_AUDIT_AND_PLAN](./LIBRARY_FIRST_AUDIT_AND_PLAN.md)                                                 | Prefer library + thin wrapper; retry, cache, file watch, circuit breaker                                                                                                                                                                           |
| **Library replacement (deep)**             | [LIBRARY_REPLACEMENT_AUDIT_DEEP](./LIBRARY_REPLACEMENT_AUDIT_DEEP.md)                                             | ✅ **Consolidated** → [LIBRARY_REPLACEMENT_CONSOLIDATED.md](./LIBRARY_REPLACEMENT_CONSOLIDATED.md) - File-level audit: urllib→httpx, ANSI, psutil; replace libs; code→lib; polish/intuitiveness/robustness/extensibility/enhancements; 47 sections |
| **Library replacement phase DWBs**         | [LIBRARY_REPLACEMENT_PHASE_DWBS](./LIBRARY_REPLACEMENT_PHASE_DWBS.md)                                             | ✅ **Consolidated** → [LIBRARY_REPLACEMENT_CONSOLIDATED.md](./LIBRARY_REPLACEMENT_CONSOLIDATED.md) - Phase task breakdowns for implementation; Phase 1 (urllib→httpx) complete                                                                     |
| **Proactive governance evolution**         | [PROACTIVE_GOVERNANCE_EVOLUTION_PLAN](./PROACTIVE_GOVERNANCE_EVOLUTION_PLAN.md)                                   | Agents identify and update governance gaps without user prompt                                                                                                                                                                                     |
| **Python frontmatter + native backmatter** | [PYTHON_FRONTMATTER_NATIVE_BACKMATTER_AUDIT_PLAN](./PYTHON_FRONTMATTER_NATIVE_BACKMATTER_AUDIT_PLAN.md)           | Rust/Go/C++ binaries with Python interfaces; PyO3, subprocess JSON, BKM tasks                                                                                                                                                                      |
| **Caching, indexing, pre-warming**         | [CACHING_INDEXING_PREWARMING_DEEP_RESEARCH](./CACHING_INDEXING_PREWARMING_DEEP_RESEARCH.md)                       | Multi-level caching, file indexing, frecency algorithms, predictive pre-warming, library landscape                                                                                                                                                 |
| **Advanced storage & workflow systems**    | [ADVANCED_STORAGE_WORKFLOW_AI_SYSTEMS_DEEP_COMPARISON](./ADVANCED_STORAGE_WORKFLOW_AI_SYSTEMS_DEEP_COMPARISON.md) | Memcached/Valkey/Redis/diskcache/NATS comparison, Temporal/Hatchet workflows, Neo4j, PostgreSQL+pgvector+pg_ai, AI codebase indexers, maximum optimality patterns                                                                                  |
| **Prompt history collection**              | [PROMPT_HISTORY_COLLECTION_AND_AUDIT_SYSTEM](../plans/PROMPT_HISTORY_COLLECTION_AND_AUDIT_SYSTEM.md)              | Collect Cursor/Codex/Claude prompts, git-backed audit logs, MCP/CLI tools, artifact extraction (todos/plans), standardized format                                                                                                                  |

---

## By Use Case

| Use Case                                                  | Docs                                                                      |
| --------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Implement prune / orphan logic**                        | SWARM_PROCESS_AUTOMATION, SMART_ROBUST_STRATEGIES                         |
| **Implement resource gates**                              | SYSTEM_RESOURCES_FD_CPU, SWARM_OPTIMIZATION_SCHEDULING                    |
| **Add retry / resilience**                                | ADVANCED_STRATEGIES_AND_RESILIENCE                                        |
| **Choose library vs custom**                              | LIBRARY_FIRST_AUDIT_AND_PLAN                                              |
| **Governance evolves without user prompt**                | PROACTIVE_GOVERNANCE_EVOLUTION_PLAN                                       |
| **Understand process lifecycle**                          | SMART_ROBUST_STRATEGIES                                                   |
| **Understand scheduling / load**                          | SWARM_OPTIMIZATION_SCHEDULING                                             |
| **Reduce memory bloat**                                   | MEMORY_OPTIMIZATION_LONG_TERM_PLAN                                        |
| **Platform-specific (macOS/Linux)**                       | SWARM_PROCESS_AUTOMATION (§27), SYSTEM_RESOURCES                          |
| **Replace Python hot paths with Rust/Go**                 | PYTHON_FRONTMATTER_NATIVE_BACKMATTER_AUDIT_PLAN                           |
| **Optimize caching/indexing**                             | CACHING_INDEXING_PREWARMING_DEEP_RESEARCH                                 |
| **Implement pre-warming**                                 | CACHING_INDEXING_PREWARMING_DEEP_RESEARCH                                 |
| **Choose caching libraries**                              | CACHING_INDEXING_PREWARMING_DEEP_RESEARCH, LIBRARY_REPLACEMENT_AUDIT_DEEP |
| **Compare caching systems (Memcached/Valkey/Redis/NATS)** | ADVANCED_STORAGE_WORKFLOW_AI_SYSTEMS_DEEP_COMPARISON                      |
| **Choose workflow engine (Temporal/Hatchet)**             | ADVANCED_STORAGE_WORKFLOW_AI_SYSTEMS_DEEP_COMPARISON                      |
| **PostgreSQL + pgvector + pg_ai integration**             | ADVANCED_STORAGE_WORKFLOW_AI_SYSTEMS_DEEP_COMPARISON                      |
| **Neo4j graph database for AI**                           | ADVANCED_STORAGE_WORKFLOW_AI_SYSTEMS_DEEP_COMPARISON                      |
| **AI codebase indexers (grepai, claude-context)**         | ADVANCED_STORAGE_WORKFLOW_AI_SYSTEMS_DEEP_COMPARISON                      |
| **Maximum optimality patterns**                           | ADVANCED_STORAGE_WORKFLOW_AI_SYSTEMS_DEEP_COMPARISON                      |
| **Collect prompts from Cursor/Codex/Claude**              | PROMPT_HISTORY_COLLECTION_AND_AUDIT_SYSTEM                                |
| **Git-backed audit logs for prompts**                     | PROMPT_HISTORY_COLLECTION_AND_AUDIT_SYSTEM                                |
| **Extract todos/plans from prompts**                      | PROMPT_HISTORY_COLLECTION_AND_AUDIT_SYSTEM                                |

---

## Doc Dependency Graph

```
SWARM_PROCESS_OPTIMIZATIONS (user-facing)
         │
         ▼
SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH
    ├── SMART_ROBUST_STRATEGIES_RESEARCH
    ├── SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH
    ├── ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH
    ├── SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH
    └── MEMORY_OPTIMIZATION_LONG_TERM_PLAN
```

---

## Implementation Roadmap (Consolidated)

| Phase | Focus                                        | Docs                                               |
| ----- | -------------------------------------------- | -------------------------------------------------- |
| **1** | Orphan-by-ppid, periodic prune, cooldown     | SWARM_PROCESS_AUTOMATION, SMART_ROBUST             |
| **2** | FD sampling on macOS, per-process metrics    | SYSTEM_RESOURCES                                   |
| **3** | Jitter on prune, graceful SIGTERM            | ADVANCED_STRATEGIES, SMART_ROBUST                  |
| **4** | Retry + backoff for MCP/API, circuit breaker | ADVANCED_STRATEGIES                                |
| **5** | Per-owner fairness, bulkhead                 | ADVANCED_STRATEGIES, SWARM_OPTIMIZATION_SCHEDULING |
| **6** | LSP multiplexing, Serena                     | MEMORY_OPTIMIZATION, SMART_ROBUST                  |

---

## See Also

- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) - Master index

---

## 6. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added swarm coordination patterns
2. Added memory sharing strategies
3. Enhanced cross-references

### Cross-References Added

- SWARM_MEMORY_COORDINATION_DEPTH.md
- SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md

### Practical Additions

- Coordination flowcharts
- Memory patterns
