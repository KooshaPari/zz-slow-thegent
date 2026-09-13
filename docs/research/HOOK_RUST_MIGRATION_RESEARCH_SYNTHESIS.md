<DONE>
# Hook Runtime Rust Migration: Research Synthesis

**Purpose:** Synthesize local codebase, existing plans, and web research for the hook runtime Rust migration.
**Date:** 2026-02-17
**Status:** Research Complete
**Feeds:** [HOOK_RUNTIME_RUST_DESIGN.md](../plans/HOOK_RUNTIME_RUST_DESIGN.md)

---

## 1. Local Codebase Summary

### 1.1 Plans and Design Docs (Relevant to Hooks / Rust)

| Document                                                | Location                                                               | Relevance                                                                                                |
| ------------------------------------------------------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **HOOK_RUNTIME_RUST_DESIGN**                            | `docs/plans/HOOK_RUNTIME_RUST_DESIGN.md`                               | Full Rust migration design: `thegent-hooks` binary, subcommands, phases, deprecation of common.sh        |
| **RUST_GO_MIGRATION_PLAN**                              | `docs/migration/RUST_GO_MIGRATION_PLAN.md`                             | Shell→Rust/Go: tool detection, PATH resolution, git, fd; `thegent-tool-detect`, `thegent-discovery`      |
| **COMPREHENSIVE_PERFORMANCE_ANALYSIS**                  | `docs/migration/COMPREHENSIVE_PERFORMANCE_ANALYSIS.md`                 | Root cause (which timeout, cascade), bottlenecks, target 200ms→20ms hook latency                         |
| **HOOK_OPTIMIZATION_STRATEGY**                          | `docs/reference/HOOK_OPTIMIZATION_STRATEGY.md`                         | Current hook optimizations (cache, circuit breaker, prewarm, learning, affected-tests); config           |
| **PROCESS_OPTIMIZATION_PLAN**                           | `docs/plans/PROCESS_OPTIMIZATION_PLAN.md`                              | MTSP; hook-dispatcher as Rust consolidation; Phase 3: "Native Rust rewrite of critical path shell hooks" |
| **CACHING_INDEXING_PREWARMING_DEEP_RESEARCH**           | `docs/research/CACHING_INDEXING_PREWARMING_DEEP_RESEARCH.md`           | Multi-level cache, TTL/LRU/frecency, cache key strategy, invalidation; Rust ecosystem (ripgrep, fd)      |
| **RUNTIME_OPTIMIZATION**                                | `docs/guides/RUNTIME_OPTIMIZATION.md`                                  | Zsh startup, Bun, fd/rg in hooks (grep/fd wrappers), git-wrapper                                         |
| **SHELL_CONFIG_AUDIT_AND_CONSOLIDATION_PLAN**           | `docs/research/SHELL_CONFIG_AUDIT_AND_CONSOLIDATION_PLAN.md`           | Canonical shell config; user vs agent; no common.sh in global git shim (already done)                    |
| **CROSS_PLATFORM_EXTENSIONS_WIDER_DEEPER_OPTIMIZATION** | `docs/research/CROSS_PLATFORM_EXTENSIONS_WIDER_DEEPER_OPTIMIZATION.md` | Circuit breaker, error taxonomy, headless/CI; aligns with hook runtime resilience                        |
| **00-MASTER-INDEX**                                     | `docs/plans/00-MASTER-INDEX.md`                                        | WBS, phases, source map; hook-dispatcher under `hooks/`                                                  |

### 1.2 Hooks and Library Layout

- **Hook dispatcher (Rust):** `hooks/hook-dispatcher/` — workspace member via `crates/Cargo.toml` (`hooks/hook-dispatcher`). Reads stdin JSON, builds env, runs bash hook scripts; has native implementations for doc_location_guard, session_cleanup, prompt_submit_guard, governance_scan. Does **not** replace common.sh; each hook script still sources common.sh when run by shell dispatchers or when not dispatched.
- **Common.sh:** `hooks/lib/common.sh` (~1685 lines). Defines hook_init, hook_init_full, hook_cache_key/check/read/write, hook_cache_wrap, git_cached (via git-cache.sh), git() (via git-wrapper.sh), tool detection (JQ_CMD, RG_CMD, FD_CMD, etc.), hook_shared_changed_files, breaker, debounce, incremental, config, learning, prewarm, reports, affected_tests, etc.
- **Git layer:** `hooks/lib/git-cache.sh`, `hooks/lib/git-wrapper.sh` — TTL cache for read-only git, agent passthrough, index.lock wait.
- **Wrappers:** `hooks/lib/fd-wrapper.sh`, `grep-wrapper.sh`, `procs-wrapper.sh`, `builtin-wrapper.sh`, `pkg-wrapper.sh`.
- **Hooks that source common.sh:** Many (e.g. test-maturity.sh, task-completed.sh, teammate-idle.sh, complexity-ratchet.sh, security-pipeline.sh, quality-gate.sh). Some use "ultra-fast cache check BEFORE common.sh" to avoid sourcing when cache hit.
- **Config:** `hooks/hook-config.yaml` — cache_ttl, prewarm_on_session_start, learning_skip, timeout_overrides, per-hook run_if/timeout/scope.

### 1.3 Existing Rust Crates (Workspace)

| Crate                    | Path                           | Role                                                                                                                              |
| ------------------------ | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| **hook-dispatcher**      | `hooks/hook-dispatcher/`       | Orchestrator: stdin JSON → env → run bash hooks; native doc_location_guard, session_cleanup, prompt_submit_guard, governance_scan |
| **thegent-git**          | `crates/thegent-git/`          | libgit2 Python extension: get_head_sha, get_branch_name, is_dirty, get_status_short, get_diff                                     |
| **thegent-tool-detect**  | `crates/thegent-tool-detect/`  | CLI: `--export` (shell vars), `--json`; detects jq/jaq, rg, fd, etc.; cache-friendly                                              |
| **thegent-discovery**    | `crates/thegent-discovery/`    | Process scanning, PATH resolution (for Python/agents)                                                                             |
| **thegent-path-resolve** | `crates/thegent-path-resolve/` | Path resolution                                                                                                                   |
| **thegent-parser**       | `crates/thegent-parser/`       | Parsing utilities                                                                                                                 |
| **thegent-crypto**       | `crates/thegent-crypto/`       | Crypto helpers                                                                                                                    |
| **thegent-watcher**      | `crates/thegent-watcher/`      | File watcher                                                                                                                      |
| **thegent-runtime**      | `crates/thegent-runtime/`      | Runtime/install                                                                                                                   |
| **thegent-resources**    | `crates/thegent-resources/`    | Resources                                                                                                                         |
| **thegent-shm**          | `crates/thegent-shm/`          | Shared memory                                                                                                                     |

Workspace root: `crates/Cargo.toml`; hook-dispatcher is included as `"hooks/hook-dispatcher"`.

### 1.4 Gaps Between Plans and Code

- **RUST_GO_MIGRATION_PLAN** proposes `thegent-tool-detect` (exists), PATH resolution in Rust (thegent-discovery/path-resolve exist), git via thegent-git (thegent-git is libgit2, used from Python). It does **not** describe a single `thegent-hooks` binary with init/cache/git/changed-files subcommands; that is in HOOK_RUNTIME_RUST_DESIGN.
- **PROCESS_OPTIMIZATION_PLAN** Phase 3 says "Native Rust rewrite of critical path shell hooks (Quality Gates)" — aligns with HOOK_RUNTIME_RUST_DESIGN Phase 4 (optional run-hook quality-gate in Rust).
- **common.sh** is still sourced by many hooks; git shim no longer sources it (fix already applied). No Rust binary yet implements hook_init, hook_cache_key, or git_cached for hooks to call.

---

## 2. Existing Research Plans (Index)

### 2.1 Master Index (00-MASTER-INDEX.md)

- **Process & Tool Optimization:** [PROCESS_OPTIMIZATION_PLAN](../plans/PROCESS_OPTIMIZATION_PLAN.md) — MTSP, hook-dispatcher, efficient tool migration (rg/fd/jaq), Phase 3 native Rust hooks.
- **08-OPTIMIZATION-CATALOG:** 93 enhancement items; performance, hardening, UX.
- **06-IMPLEMENTATION-GUIDE:** Code conventions; new modules.

### 2.2 Research Index (docs/research/)

- **CACHING_INDEXING_PREWARMING_DEEP_RESEARCH:** Multi-level cache (memory → disk → network), eviction (LRU+TTL, frecency), cache key normalization, version-based invalidation; Rust (ripgrep, fd, bat); recommendation: multi-level cache, file indexing, prewarm, blake3/sha for keys.
- **SHELL_CONFIG_AUDIT_AND_CONSOLIDATION_PLAN:** Canonical zsh config; user vs agent; no heavy sourcing in global PATH.
- **CONVERSATION_DUMP_2026-02-16:** Handoff summary; git shim fix, find/ps shim fixes, Rust migration direction.
- **CROSS*PLATFORM*\***:\*\* Broader platform/headless/CI; circuit breaker, error taxonomy — consistent with hook runtime resilience.

### 2.3 Migration Docs (docs/migration/)

- **RUST_GO_MIGRATION_PLAN:** Priority: tool detection → PATH → process scan → git → fd → dispatchers (Go). Files to migrate: common.sh, fd-wrapper, git-cache, git-wrapper → Rust; pretool/posttool dispatchers → Go (design doc chose Rust for full hook runtime, not Go for dispatchers).
- **COMPREHENSIVE_PERFORMANCE_ANALYSIS:** Cascade (which → common.sh → wrappers → command -v); target hook 200ms→20ms; subprocess spawn cost; JSON parse 5ms→0.1ms with serde_json.

---

## 3. Web Research Summary

### 3.1 Gitoxide / gix

- **Source:** [github.com/byron/gitoxide](https://github.com/byron/gitoxide), [lib.rs/crates/gix](https://lib.rs/crates/gix).
- **Description:** Pure Rust Git implementation; library entrypoint is `gix` crate. Status: production-grade (gix-lock, gix-tempfile); stabilization candidates (gix-ref, gix-config, gix-diff, gix-status, gix-worktree, etc.). CLI: `gix` (plumbing), `ein` (porcelain).
- **Relevance for hook runtime:** Use `gix` for read-only operations (status, diff, rev-parse, worktree) to avoid subprocess `git` and get native speed. thegent-git currently uses **libgit2** (C); adding optional **gix** for hook path allows pure-Rust, no libgit2. Crate-status.md and docs.rs list gix-status, gix-diff, gix-revision, gix-worktree as usable. **Recommendation:** Phase 1 can keep `Command::new("git")` or thegent-git (libgit2); Phase 2 add optional `gix` for cached read-only to reduce process spawn and align with "pure Rust" stack.

### 3.2 blake3

- **Source:** [docs.rs/blake3](https://docs.rs/blake3/latest/blake3/).
- **Description:** BLAKE3 in Rust; fast, cryptographic; incremental hashing; optional rayon/mmap for large inputs.
- **Relevance for hook runtime:** Cache keys (hook_name + head_sha + changed_files), file content hashes for incremental/manifest. Use `blake3::hash()` or `Hasher::new().update(...).finalize()` for key derivation; no need for crypto strength, but blake3 is faster than sha256 and good for cache keys. **Recommendation:** Use blake3 for hook_cache_key and file-hash in thegent-hooks.

### 3.3 Rust CLI and Caching (from CACHING_INDEXING_PREWARMING)

- **ripgrep (rg), fd, bat:** Rust CLI tools; hooks already use wrappers (grep-wrapper, fd-wrapper) that prefer rg/fd. thegent-hooks can emit RG_CMD/FD_CMD from config or tool-detect; no need to reimplement find/grep in Rust for Phase 1.
- **Multi-level cache:** Memory (TTL) → disk (file-based) → compute. Hook cache is disk-based under HOOK_CACHE_DIR; design doc keeps that; optional in-memory layer in Rust can be added later.

---

## 4. Alignment Matrix

| Topic           | RUST_GO_MIGRATION_PLAN | COMPREHENSIVE_PERFORMANCE | HOOK_RUNTIME_RUST_DESIGN             | PROCESS_OPTIMIZATION   | Current Code                                 |
| --------------- | ---------------------- | ------------------------- | ------------------------------------ | ---------------------- | -------------------------------------------- |
| Tool detection  | thegent-tool-detect    | 60ms→1ms                  | Use tool-detect or init exports      | —                      | thegent-tool-detect exists                   |
| PATH resolution | thegent-discovery      | 20ms→0.5ms                | init/resolve PROJECT_DIR             | —                      | thegent-path-resolve, discovery              |
| Git read-only   | thegent-git (libgit2)  | 100ms→10ms                | git subcommand: cache + passthrough  | MTSP-09                | thegent-git (Python); hooks use git-cache.sh |
| Hook init       | —                      | —                         | init subcommand, stdin JSON → env    | —                      | common.sh hook_init_full                     |
| Cache key       | —                      | —                         | cache-key, blake3                    | —                      | common.sh hook_cache_key, hash_for_cache     |
| Changed files   | —                      | —                         | changed-files subcommand             | —                      | hook_shared_changed_files                    |
| Dispatcher      | Go binary (planned)    | —                         | Extend hook-dispatcher (Rust)        | hook-dispatcher (Rust) | hook-dispatcher Rust, runs bash hooks        |
| common.sh       | Migrate to Rust        | Source overhead           | Replace by thegent-hooks subcommands | —                      | Still sourced by many hooks                  |

---

## 5. Recommendations

1. **Treat HOOK_RUNTIME_RUST_DESIGN as the single design** for "full common.sh replacement" in Rust. RUST_GO_MIGRATION_PLAN covers tool detection and PATH (already implemented in crates); the design doc covers init, cache, git, changed-files, config, breaker, etc., and phased deprecation of common.sh.
2. **Reuse existing crates:** thegent-tool-detect for JQ_CMD/RG_CMD/FD_CMD (or call from thegent-hooks init); thegent-git for head_sha/status/diff from Python or via a small ffi/shim; hook-dispatcher stays as orchestrator and can call into a new thegent-hooks lib for env/cache/git.
3. **New crate:** Add `thegent-hooks` (or extend hook-dispatcher) under `crates/thegent-hooks/` with subcommands as in the design doc. Keep hook-dispatcher in `hooks/hook-dispatcher/` for orchestration; thegent-hooks provides the "common.sh replacement" surface (init, cache-key, cache-check/read/write, git, changed-files, config-get, ...).
4. **Git layer:** Phase 1: use `std::process::Command::new("git")` with file-based TTL cache and agent passthrough. Optional: add `gix` for read-only status/diff in Rust for maximum performance and no subprocess. thegent-git (libgit2) remains for Python callers.
5. **Hashing:** Use `blake3` for cache keys and file-hash in thegent-hooks (fast, good for non-crypto use).
6. **Index the design doc in 00-MASTER-INDEX:** Add an entry for HOOK_RUNTIME_RUST_DESIGN and link this research synthesis in the plans/research index so future work finds both.

---

## 6. Document Cross-References

- **Full shell → Rust (inventory + phases):** [FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md](../plans/FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md)
- **Design (implementation spec):** [HOOK_RUNTIME_RUST_DESIGN.md](../plans/HOOK_RUNTIME_RUST_DESIGN.md)
- **Migration priority (shell→Rust):** [RUST_GO_MIGRATION_PLAN.md](../migration/RUST_GO_MIGRATION_PLAN.md)
- **Performance analysis:** [COMPREHENSIVE_PERFORMANCE_ANALYSIS.md](../migration/COMPREHENSIVE_PERFORMANCE_ANALYSIS.md)
- **Hook optimizations (current):** [HOOK_OPTIMIZATION_STRATEGY.md](../reference/HOOK_OPTIMIZATION_STRATEGY.md)
- **Process/MTSP and native hooks:** [PROCESS_OPTIMIZATION_PLAN.md](../plans/PROCESS_OPTIMIZATION_PLAN.md)
- **Caching strategies:** [CACHING_INDEXING_PREWARMING_DEEP_RESEARCH.md](CACHING_INDEXING_PREWARMING_DEEP_RESEARCH.md)
- **Master index:** [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md)

---

## 7. Summary

Local codebase has a clear split: **hook-dispatcher** (Rust) orchestrates and runs bash hooks; **common.sh** provides init, cache, git, config, and helpers. Existing plans (RUST_GO_MIGRATION_PLAN, COMPREHENSIVE_PERFORMANCE_ANALYSIS, PROCESS_OPTIMIZATION_PLAN) and research (CACHING_INDEXING_PREWARMING, SHELL_CONFIG) support a full Rust hook runtime. HOOK_RUNTIME_RUST_DESIGN is the single place that specifies thegent-hooks subcommands and phased migration. Web research confirms **gix** (gitoxide) and **blake3** as suitable dependencies for Git and cache keys. This synthesis ties those together and recommends implementing thegent-hooks per the design doc while reusing thegent-tool-detect, thegent-git, and hook-dispatcher.

---

## 10. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added Rust hook implementation examples
2. Added migration phases
3. Enhanced cross-references

### Cross-References Added

- LIBRARY_REPLACEMENT_AUDIT_DEEP.md
- PROACTIVE_GOVERNANCE_EVOLUTION_PLAN.md

### Practical Additions

- Rust hook templates
- Migration checklist

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (6 BACKLOG items)
- [HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS_EXPANDED.md](./HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS_EXPANDED.md) - Expanded version
- [HOOK_RUST_MIGRATION_COMPLETE.md](./HOOK_RUST_MIGRATION_COMPLETE.md) - Complete guide
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
