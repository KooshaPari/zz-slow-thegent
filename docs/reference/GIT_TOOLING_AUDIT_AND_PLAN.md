# Git Tooling Audit and Migration Plan

**Date:** 2026-02-19
**Status:** COMPLETED — gix is now the default backend in thegent-git
**ADR:** BKM-06 (thegent-git Rust extension)
**Agent:** agent-d6

---

## 1. Inventory: Where Git Is Used

### 1.1 Python Subprocess Calls

Many shell hooks and Python utilities invoke `git` via subprocess. These are intentional — they wrap the system git binary and do not need a Rust library migration.

Key locations:

- `hooks/` — various `.sh` hook scripts call `git status`, `git diff`, `git log`
- `cli/` — Python CLI subcommands use `subprocess.run(["git", ...])` for operations like `git rev-parse`
- `commands/` — command implementations that check HEAD, branch, and diff state

These subprocess calls are **retained as-is**. Migrating them to native Rust would require exposing a Rust CLI binary everywhere Python calls git, which is not warranted.

### 1.2 Rust Native Git (thegent-git crate)

**Crate:** `crates/thegent-git/` (BKM-06)

**Previous state (before BKM-06 migration):**

- Primary dependency: `git2 = "0.20.4"` — libgit2 C bindings
- gix dependency: `gix = "0.79.0"` (optional, stub-only)
- `gix_impl` module: contained stubs returning errors

**Current state (post-migration):**

- Primary dependency: `gix = "0.79.0"` with `status` + `dirwalk` features (enabled by default)
- `git2 = "0.20.4"` retained as required dep for Python extension fallback
- `gix_impl` module: **fully implemented** with real gix calls
- Feature flag `gix` (default): activates real gix backend in `gix_impl`

---

## 2. Migration Decision

**Decision: Use gix in all new Rust crates. git2/libgit2 is deprecated.**

### Rationale

| Criterion     | git2 (libgit2)              | gix (gitoxide)                                    |
| ------------- | --------------------------- | ------------------------------------------------- |
| Language      | C bindings                  | Pure Rust                                         |
| System deps   | libgit2 + openssl + libssh2 | None                                              |
| Async support | Poor (blocking C calls)     | Native async (gix-async)                          |
| Performance   | Good                        | Equal or better (SIMD via `max-performance-safe`) |
| Safety        | C FFI unsafe surface        | Safe Rust throughout                              |
| Binary size   | Larger (C + Rust)           | Smaller (Rust only)                               |
| Cross-compile | Hard (C toolchain needed)   | Easy (cargo cross)                                |
| Status check  | `repo.statuses()`           | `repo.is_dirty()` / `Platform::into_iter()`       |

### Feature Flags (thegent-git)

```
[features]
default = ["gix"]          # gix is on by default
gix    = ["dep:gix"]       # pure-Rust gitoxide backend
cli    = ["dep:clap"]      # CLI binary
python = ["pyo3"]          # Python extension module
```

To revert to git2 only (not recommended):

```
cargo build --no-default-features
```

---

## 3. API Mapping: git2 → gix

| Operation   | git2                                     | gix                                                            |
| ----------- | ---------------------------------------- | -------------------------------------------------------------- |
| Open repo   | `Repository::discover(path)`             | `gix::discover(path)`                                          |
| HEAD SHA    | `repo.head()?.target()`                  | `repo.head_id()?.to_hex()`                                     |
| Branch name | `repo.head()?.shorthand()`               | `repo.head()?.kind` → `Kind::Symbolic(r)` → `r.name.shorten()` |
| Is dirty    | custom status loop                       | `repo.is_dirty()` (requires `status` feature)                  |
| Status list | `repo.statuses()` iterator               | `repo.status(progress).into_iter()`                            |
| Diff text   | `repo.diff_tree_to_workdir_with_index()` | subprocess `git diff` (gix yields structured data)             |
| Diff stats  | `diff.stats()`                           | parse patch text from `git diff --stat`                        |
| Object ID   | `git2::Oid`                              | `gix::ObjectId`                                                |
| Reference   | `git2::Reference`                        | `gix_ref::Reference` (field `.name: FullName`)                 |

### Type Changes

| git2 Type                 | gix Type                                  | Notes                        |
| ------------------------- | ----------------------------------------- | ---------------------------- |
| `git2::Oid`               | `gix::ObjectId`                           | `.to_string()` works on both |
| `git2::Repository`        | `gix::Repository`                         | open via `gix::discover()`   |
| `git2::Reference`         | `gix_ref::Reference`                      | name via `.name.shorten()`   |
| `git2::Status`            | `gix::status::index_worktree::iter::Item` | enum variant matching        |
| `git2::DiffFormat::Patch` | N/A (subprocess)                          | gix produces structured data |

---

## 4. Current Implementation (gix_impl module)

The `pub mod gix_impl` in `crates/thegent-git/src/lib.rs` now provides real gix implementations:

```rust
// Enabled when feature "gix" is active (default)
#[cfg(feature = "gix")]
pub mod gix_impl {
    pub fn get_head_sha(path: Option<String>) -> Result<Option<String>, String>;
    pub fn get_branch_name(path: Option<String>) -> Result<Option<String>, String>;
    pub fn is_dirty(path: Option<String>) -> Result<bool, String>;
}
```

These are imported by `thegent-hooks` as:

```rust
use thegent_git::gix_impl;
```

---

## 5. gix Features Required

For `thegent-git` and any future crates using gix:

```toml
gix = { version = "0.79.0", default-features = false, features = [
    "max-performance-safe",   # SIMD acceleration (safe, no unsafe cross-platform issues)
    "status",                 # repo.is_dirty(), status iterator
    "dirwalk",                # untracked file enumeration
] }
```

The workspace `[workspace.dependencies]` in `crates/Cargo.toml` provides a shared definition:

```toml
[workspace.dependencies]
gix = { version = "0.79.0", default-features = false, features = ["max-performance-safe"] }
```

New crates that need status/dirwalk should add those features locally.

---

## 6. Migration Checklist for Future Crates

When adding git operations to a new Rust crate:

- [ ] Add `gix` as a dependency (use workspace dep where possible)
- [ ] Enable `status` feature if you need `repo.is_dirty()` or status iteration
- [ ] Enable `dirwalk` feature if you need untracked file listing
- [ ] Do NOT add `git2` — it is deprecated
- [ ] For patch text output, use subprocess `git diff` (gix produces structured data)
- [ ] For ObjectId: use `id.to_hex().to_string()` not `.to_string()` directly
- [ ] For branch name: match on `head.kind`, use `r.name.shorten()` for `Symbolic`

---

## 7. Remaining Gaps

The following git2-backed items in `lib.rs` have not been migrated yet because the pre-write validator hook enforces their presence:

1. **Python extension functions** (`get_diff`, `get_diff_stats`, `get_status`) — still use git2 for the Python `cdylib` build path. These can be migrated to call the subprocess `git diff` like the gix backend does.
2. **Public lib functions** (`head_sha`, `branch_name`, `is_dirty`, `status_short`, `diff_stats`) — still use git2 directly. The `gix_impl` module provides the gix-native equivalents; a follow-up task should flip the public functions to delegate to `gix_impl` when the `gix` feature is active.

The `gix_impl` module is now the canonical gix entry point. A follow-up task should:

1. Move Python extension to use `gix_impl::*` functions
2. Deprecate the git2-backed public functions
3. Remove `git2` as a required dep once the Python extension is gix-native

---

## 8. References

- `crates/thegent-git/Cargo.toml` — dependency definition
- `crates/thegent-git/src/lib.rs` — implementation with `gix_impl` module
- `crates/thegent-hooks/src/main.rs` — consumer of `gix_impl`
- `docs/reference/THEGENT_GIT_ENHANCEMENT_PHASE_1_5.md` — Phase 1.5 design doc
- gitoxide docs: https://docs.rs/gix/latest/gix/
