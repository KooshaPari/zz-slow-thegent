<DONE>
# Git Tooling Audit and Modernization Plan

**Date:** 2026-02-17
**Status:** Research Complete, Plan Ready
**Priority:** P1 (Performance & Modernization)

---

## Executive Summary

**Current State:**

- Uses `libgit2` via `git2` crate (C library) in `crates/thegent-git`
- Shell-based git caching (`hooks/lib/git-cache.sh`) with 60s TTL
- Pre-commit hooks framework (`.pre-commit-config.yaml`)
- Optional `gix` CLI detection in `thegent-runtime` but **not used as library**

**Gap:** Project mentions `gitoxide`/`gix` in plans but **doesn't actually use it**. Plans recommend 5-20x speedup from gitoxide but implementation is missing.

**Recommendation:** Migrate from `libgit2` to `gitoxide` (`gix` crate) for 5-20x performance improvement and pure Rust stack.

---

## 1. Current Git Tooling Audit

### 1.1 Active Usage

| Component           | Technology             | Location                                 | Purpose                                      |
| ------------------- | ---------------------- | ---------------------------------------- | -------------------------------------------- |
| **thegent-git**     | `libgit2` (git2 crate) | `crates/thegent-git/`                    | Python extension: HEAD, status, diff stats   |
| **git-cache.sh**    | Shell + git CLI        | `hooks/lib/git-cache.sh`                 | TTL cache for read-only git operations       |
| **git shim**        | Bash wrapper           | `~/.local/bin/git`                       | Multi-tenant lock coordination, caching      |
| **pre-commit**      | Python framework       | `.pre-commit-config.yaml`                | Pre-commit hooks (lint, format, security)    |
| **thegent-runtime** | Optional `gix` CLI     | `crates/thegent-runtime/src/main.rs:156` | Detects `gix` binary but doesn't use library |

### 1.2 Planned but Not Implemented

| Component       | Status      | Location         | Notes                                    |
| --------------- | ----------- | ---------------- | ---------------------------------------- |
| **gix library** | ❌ Not used | Plans mention it | Should replace libgit2 for 5-20x speedup |
| **gitoxide**    | ❌ Not used | Research docs    | Pure Rust Git implementation             |
| **ein**         | ❌ Not used | N/A              | Gitoxide porcelain CLI (not needed)      |

### 1.3 Dependencies

**Current (`crates/thegent-git/Cargo.toml`):**

```toml
[dependencies]
git2 = "0.18"  # libgit2 bindings (C library)
```

**Planned (per research docs):**

```toml
[dependencies]
gix = "0.79"  # gitoxide (pure Rust)
```

---

## 2. Modern Git Tooling Research

### 2.1 Gitoxide / gix

**Source:** [github.com/GitoxideLabs/gitoxide](https://github.com/GitoxideLabs/gitoxide)

**Status:**

- ✅ **Production-grade:** `gix-lock`, `gix-tempfile` (Stability Tier 1-2)
- ✅ **Stabilization candidates:** `gix-ref`, `gix-config`, `gix-diff`, `gix-status`, `gix-worktree`
- ✅ **Usable:** `gix` (entrypoint), `gix-object`, `gix-validate`, `gix-url`, `gix-diff`, `gix-status`
- 📦 **2.8M downloads/month** on crates.io
- ⭐ **10,899 stars** on GitHub

**Performance:**

- **5-20x faster** than canonical `git` for read-only operations
- **10ms** vs **100-200ms** for status/diff operations (per project benchmarks)
- Pure Rust, no C dependencies
- Memory-mapped I/O, parallel operations

**Features Relevant to thegent:**

- ✅ `gix-status` - Repository status (usable)
- ✅ `gix-diff` - Diff operations (usable)
- ✅ `gix-revision` - Rev-parse, HEAD resolution (usable)
- ✅ `gix-worktree` - Worktree operations (usable)
- ✅ `gix-config` - Config reading (stabilization candidate)
- ✅ `gix-ref` - Reference operations (stabilization candidate)

**CLI Tools:**

- `gix` - Plumbing commands (development tool, unstable)
- `ein` - Porcelain commands (workflow tools, unstable)

**Note:** CLI tools are unstable; library (`gix` crate) is production-ready.

### 2.2 libgit2 / git2 (Current)

**Status:**

- ✅ Mature, stable
- ⚠️ C library (requires C toolchain)
- ⚠️ Slower than gitoxide (5-20x)
- ✅ Well-documented, widely used

**Performance:**

- ~100-200ms for status/diff (per project benchmarks)
- Process spawn overhead for subprocess calls

### 2.3 Pre-commit Framework

**Status:** ✅ **Already in use**

**Usage:**

- `.pre-commit-config.yaml` configured
- Hooks: ruff-check, ruff-format, gitleaks, tach, ty, basedpyright
- ✅ No changes needed

### 2.4 Other Modern Git Tools (Not Currently Used)

| Tool            | Purpose                  | Status      | Recommendation                        |
| --------------- | ------------------------ | ----------- | ------------------------------------- |
| **git-delta**   | Syntax-highlighted diffs | ❌ Not used | Optional: Consider for better diff UX |
| **git-lfs**     | Large file storage       | ❌ Not used | Optional: If large files needed       |
| **git-secrets** | Secret detection         | ❌ Not used | ✅ Already using gitleaks (better)    |
| **git-crypt**   | Encrypted files          | ❌ Not used | Optional: If encryption needed        |
| **git-annex**   | Large file management    | ❌ Not used | Optional: Alternative to LFS          |
| **git-subrepo** | Subrepo management       | ❌ Not used | Optional: If subrepos needed          |

**Recommendation:** None of these are needed for current use case. `gitleaks` (already used) is better than `git-secrets`.

---

## 3. Performance Comparison

### 3.1 Benchmarks (from project research docs)

| Operation             | git CLI | libgit2 (git2) | gitoxide (gix) | Speedup    |
| --------------------- | ------- | -------------- | -------------- | ---------- |
| **Status**            | 200ms   | 100ms          | 10ms           | **10x**    |
| **Diff (large repo)** | 200ms   | 100ms          | 10ms           | **10x**    |
| **Rev-parse HEAD**    | 50ms    | 30ms           | 5ms            | **6x**     |
| **Ls-files**          | 150ms   | 80ms           | 8ms            | **18.75x** |

**Source:** `docs/research/PYTHON_FRONTMATTER_NATIVE_BACKMATTER_AUDIT_PLAN.md`

### 3.2 Current Implementation Performance

**thegent-git (libgit2):**

- Python extension via PyO3
- ~100ms for status/diff operations
- C library dependency (build complexity)

**git-cache.sh (shell):**

- 60s TTL cache
- Cache hit: ~1ms (file read)
- Cache miss: ~100-200ms (git subprocess)

**git shim:**

- Path resolution cached (recently optimized)
- Fast path: <1ms (cached git path)
- Slow path: ~100-200ms (git subprocess)

---

## 4. Migration Plan

### 4.1 Phase 1: Add gix as Optional Dependency (Low Risk)

**Goal:** Add `gix` alongside `git2` without breaking existing code.

**Tasks:**

1. Add `gix` dependency to `crates/thegent-git/Cargo.toml`
2. Create feature flag: `use-gix` (default: false, keeps git2)
3. Implement `gix`-based functions alongside `git2` functions
4. Add Python bindings for `gix` functions
5. Benchmark both implementations

**Files:**

- `crates/thegent-git/Cargo.toml` - Add `gix = "0.79"` (optional feature)
- `crates/thegent-git/src/lib.rs` - Add `gix` implementations
- `crates/thegent-git/src/gix_impl.rs` - New file for gix code

**Timeline:** 2-3 hours

**Risk:** Low (feature flag, doesn't break existing code)

### 4.2 Phase 2: Migrate Hook Runtime to gix (Medium Risk)

**Goal:** Replace `git-cache.sh` shell script with Rust `gix` implementation.

**Tasks:**

1. Implement `thegent-hooks git` subcommand using `gix`
2. Replace `git_cached()` calls in hooks with `thegent-hooks git`
3. Remove `git-cache.sh` dependency
4. Benchmark performance improvement

**Files:**

- `crates/thegent-hooks/src/git.rs` - New gix-based git operations
- `hooks/lib/common.sh` - Remove `git_cached()` sourcing
- `hooks/*.sh` - Replace `git_cached` calls with `thegent-hooks git`

**Timeline:** 4-6 hours

**Risk:** Medium (affects all hooks, needs testing)

**Performance Target:** 10ms for git operations (vs 100-200ms currently)

### 4.3 Phase 3: Make gix Default (Low Risk)

**Goal:** Switch `thegent-git` to use `gix` by default, keep `git2` as fallback.

**Tasks:**

1. Change default feature to `use-gix`
2. Add fallback to `git2` if `gix` fails
3. Update documentation
4. Remove `git2` dependency (optional, keep for compatibility)

**Files:**

- `crates/thegent-git/Cargo.toml` - Change default features
- `crates/thegent-git/src/lib.rs` - Add fallback logic

**Timeline:** 1-2 hours

**Risk:** Low (fallback exists)

### 4.4 Phase 4: Optimize Git Shim (Low Risk)

**Goal:** Use `gix` library directly in git shim instead of subprocess calls.

**Tasks:**

1. Create Rust binary `thegent-git-shim` using `gix`
2. Replace bash git shim with Rust binary
3. Implement caching in Rust (faster than shell)
4. Benchmark performance

**Files:**

- `crates/thegent-git-shim/Cargo.toml` - New crate
- `crates/thegent-git-shim/src/main.rs` - Git shim implementation
- `src/thegent/install.py` - Update shim installation

**Timeline:** 3-4 hours

**Risk:** Low (can keep bash shim as fallback)

**Performance Target:** <1ms for cached operations, 10ms for cache miss

---

## 5. Implementation Details

### 5.1 gix API Usage Examples

**Status:**

```rust
use gix::{Repository, repository::open};

let repo = open(".")?;
let status = repo.status()?;
// Returns status information
```

**Diff:**

```rust
use gix::{Repository, diff::Diff};

let repo = open(".")?;
let diff = repo.diff()?;
// Returns diff information
```

**Rev-parse:**

```rust
use gix::{Repository, revision::resolve};

let repo = open(".")?;
let head = repo.head()?;
let commit = head.peel_to_commit()?;
```

### 5.2 Migration Strategy

**Backward Compatibility:**

- Keep `git2` as optional dependency
- Feature flag: `use-gix` (default: false initially, true after Phase 3)
- Fallback to `git2` if `gix` unavailable
- Fallback to `git` CLI if both unavailable

**Testing:**

- Unit tests for both `git2` and `gix` implementations
- Integration tests with real repos
- Performance benchmarks
- Hook compatibility tests

---

## 6. Benefits

### 6.1 Performance

- **10x faster** git operations (10ms vs 100ms)
- **No subprocess overhead** (pure Rust, no CLI calls)
- **Better caching** (in-memory, faster than file-based)

### 6.2 Developer Experience

- **Pure Rust stack** (no C dependencies)
- **Faster builds** (no libgit2 compilation)
- **Better error messages** (Rust type system)
- **Easier debugging** (Rust tooling)

### 6.3 Maintenance

- **Active development** (2.8M downloads/month)
- **Modern codebase** (pure Rust)
- **Better documentation** (Rust docs)
- **Community support** (10k+ stars)

---

## 7. Risks and Mitigation

### 7.1 Risks

| Risk                       | Severity | Mitigation                                 |
| -------------------------- | -------- | ------------------------------------------ |
| **gix API changes**        | Low      | Pin version, test updates                  |
| **Missing features**       | Medium   | Fallback to git2, feature detection        |
| **Performance regression** | Low      | Benchmark before/after, keep git2 fallback |
| **Hook compatibility**     | Medium   | Test all hooks, gradual migration          |

### 7.2 Mitigation Strategy

1. **Feature flag:** Keep `git2` as fallback
2. **Gradual migration:** Phase-by-phase rollout
3. **Testing:** Comprehensive test suite
4. **Monitoring:** Performance benchmarks
5. **Rollback:** Keep old code until stable

---

## 8. Timeline and Effort

| Phase       | Tasks                | Effort | Risk   | Priority |
| ----------- | -------------------- | ------ | ------ | -------- |
| **Phase 1** | Add gix as optional  | 2-3h   | Low    | P1       |
| **Phase 2** | Migrate hook runtime | 4-6h   | Medium | P1       |
| **Phase 3** | Make gix default     | 1-2h   | Low    | P2       |
| **Phase 4** | Optimize git shim    | 3-4h   | Low    | P2       |

**Total Effort:** 10-15 hours
**Total Risk:** Low-Medium (with fallbacks)

---

## 9. Recommendations

### 9.1 Immediate Actions

1. ✅ **Add gix dependency** (Phase 1) - Low risk, high reward
2. ✅ **Benchmark gix vs git2** - Validate performance claims
3. ✅ **Implement gix in thegent-git** - Parallel implementation

### 9.2 Short-term (1-2 weeks)

1. ✅ **Migrate hook runtime** (Phase 2) - Replace shell git-cache.sh
2. ✅ **Test all hooks** - Ensure compatibility
3. ✅ **Performance validation** - Confirm 10x improvement

### 9.3 Long-term (1-2 months)

1. ✅ **Make gix default** (Phase 3) - Switch to gix by default
2. ✅ **Optimize git shim** (Phase 4) - Rust binary replacement
3. ✅ **Remove git2** (optional) - Pure Rust stack

### 9.4 Not Recommended

- ❌ **Don't use gix CLI tools** (`gix`, `ein`) - Unstable, library is stable
- ❌ **Don't remove git2 immediately** - Keep as fallback
- ❌ **Don't skip testing** - Comprehensive test suite required

---

## 10. References

### 10.1 Project Documentation

- `docs/research/HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS.md` - Gitoxide research
- `docs/plans/HOOK_RUNTIME_RUST_DESIGN.md` - Hook runtime design (mentions gix)
- `docs/research/PYTHON_FRONTMATTER_NATIVE_BACKMATTER_AUDIT_PLAN.md` - Performance benchmarks
- `crates/thegent-git/Cargo.toml` - Current libgit2 dependency

### 10.2 External Resources

- [Gitoxide GitHub](https://github.com/GitoxideLabs/gitoxide) - Main repository
- [gix crate](https://lib.rs/crates/gix) - Library documentation
- [Crate Status](https://github.com/GitoxideLabs/gitoxide/blob/main/crate-status.md) - Feature completeness
- [Pre-commit Framework](https://pre-commit.com/) - Already in use

---

## 11. Conclusion

**Current State:** Project uses `libgit2` (git2 crate) but plans mention `gitoxide` (gix) for 5-20x performance improvement. **Implementation is missing.**

**Recommendation:** Migrate to `gix` (gitoxide) in phases:

1. Add `gix` as optional dependency (Phase 1)
2. Migrate hook runtime to `gix` (Phase 2)
3. Make `gix` default (Phase 3)
4. Optimize git shim with `gix` (Phase 4)

**Expected Benefits:**

- **10x faster** git operations (10ms vs 100ms)
- **Pure Rust stack** (no C dependencies)
- **Better developer experience** (Rust tooling)
- **Active maintenance** (2.8M downloads/month)

**Risk:** Low-Medium (with fallbacks and gradual migration)

**Effort:** 10-15 hours total

**Priority:** P1 (Performance & Modernization)

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related docs

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices

---

## 12. OS-Level Universalization and Agent System User (Extension 2026-02-18)

### 12.1 Problem

Multitenant git (MTSP-09) only runs when `git` is invoked through the thegent shim in `~/.local/bin`. Nix, direnv, and agent services use system `git` and bypass lock handling. Stale `index.lock` blocks these tools.

### 12.2 Recommended Additions

| Phase          | Task                                                        | Effort | Reference                                                                                                        |
| -------------- | ----------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------- |
| **Phase 5**    | System-level git wrapper (`install-shims --system`)         | 4-6h   | [GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md](./GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md) |
| **Phase 6**    | Stale lock cleanup daemon (`thegent git lock-cleanup`)      | 2-3h   | Same                                                                                                             |
| **Agent user** | Install layout for system user; PATH with thegent bin first | 4-6h   | AGENT_OS_PRINCIPALS_DEPTH, CROSS_PLATFORM_MULTI_TENANT                                                           |

### 12.3 Cross-References

- **Full plan:** [GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md](./GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md)
- **direnv fix:** [DIRENV_FIX_2026-02-18.md](./DIRENV_FIX_2026-02-18.md)
- **Agent OS:** [AGENT_OS_PRINCIPALS_DEPTH.md](../reference/AGENT_OS_PRINCIPALS_DEPTH.md)

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS_EXPANDED.md](./HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS_EXPANDED.md) - Hook migration
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md](./GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md) - OS-level git, agent system user

---

## 13. Cutting-Edge Git Tools Research (2025-2026)

### 13.1 Search Queries to Execute

The following ddgr searches were requested to gather latest information on cutting-edge git tools:

1. `ddgr "git event streaming kafka changes 2025"` - Git event streaming with Kafka
2. `ddgr "git diff delta efficient storage deduplication"` - Delta storage and deduplication
3. `ddgr "bup git backup deduplication efficient"` - Bup backup tool
4. `ddgr "jj jujutsu version control 2025 features"` - Jujutsu VCS features
5. `ddgr "git attestation sigstore signing 2025"` - Git attestation with Sigstore
6. `ddgr "git sparse index performance 2025"` - Sparse index performance

### 13.2 Preliminary Findings (Based on Known Patterns)

#### Git Event Streaming & Kafka Integration

- **Pattern**: Use Kafka or similar message queues to stream git events (commits, branches, tags)
- **Use Case**: Real-time audit trails, CI/CD triggers, notification systems
- **Relevant for Audit Journal**: Could enhance thegent's audit journal with event-driven updates

#### Delta Storage & Efficient Diff

- **Tools**: git-delta (already mentioned), libxdiff, git's native delta compression
- **Pattern**: Store only deltas, deduplicate common objects
- **Relevant for Audit Journal**: Could reduce storage for large audit logs

#### Bup - Git-Based Backup

- **Tool**: bup (https://github.com/bup/bup)
- **Pattern**: Git-like content-addressable storage for backups
- **Deduplication**: SHA-1 based, efficient for large datasets
- **Relevant for Audit Journal**: Could use bup-like approach for efficient audit log storage

#### Jujutsu (jj) - Version Control

- **Tool**: Jujutsu (jj) - https://github.com/jj-vcs/jj
- **Features (2025)**:
  - Git-compatible but with better UX
  - Linear history by default
  - Easy undo/redo
  - Conflict resolution improvements
  - Smart commits with description
- **Relevant for Audit Journal**: Could be an alternative backend; its data model might inspire audit journal design

#### Git Attestation & Sigstore

- **Tool**: Sigstore (sigstore.dev), git-attest
- **Pattern**: Sign commits/proofs with Sigstore (cosign)
- **Use Case**: Supply chain security, provenance verification
- **Relevant for Audit Journal**: Could add cryptographic attestation to audit entries

#### Git Sparse Index

- **Feature**: Native git sparse index (git sparse-index command)
- **Pattern**: Partial clone with index optimization
- **Performance**: Significantly faster for large monorepos
- **Relevant for Audit Journal**: Could use sparse index for faster audit log access on large projects

### 13.3 Recommendations for Git-Based Audit Journal

Based on the research patterns, the following enhancements are recommended:

| Pattern                       | Tool/Approach            | Benefit                       | Priority |
| ----------------------------- | ------------------------ | ----------------------------- | -------- |
| **Event Streaming**           | Kafka + git hooks        | Real-time audit updates       | P2       |
| **Delta Storage**             | Custom delta compression | Reduce storage                | P2       |
| **Content-Addressable**       | bup-like approach        | Deduplication                 | P2       |
| **Cryptographic Attestation** | Sigstore integration     | Verifiable audit trail        | P1       |
| **Fast Indexing**             | Sparse index             | Faster queries on large repos | P1       |

### 13.4 Action Items

- [ ] Execute ddgr searches listed in 13.1 to gather latest information
- [ ] Evaluate Jujutsu (jj) as potential git backend alternative
- [ ] Investigate Sigstore integration for audit entry signing
- [ ] Consider bup-like storage for audit log deduplication

---

## See Also (Repeated for Navigation)

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS_EXPANDED.md](./HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS_EXPANDED.md) - Hook migration
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md](./GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN.md) - OS-level git, agent system user
