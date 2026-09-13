# Rust Migration Status & Opportunities

**Date:** February 23, 2026

---

## Current Rust Crates

| Crate               | Purpose                      | Python Bindings       |
| ------------------- | ---------------------------- | --------------------- |
| `thegent-shims`     | Git, grep, find, agent shims | Partial (thegent-git) |
| `thegent-git`       | Git operations               | ✅ PyO3               |
| `thegent-parser`    | CLI parsing                  | ✅ PyO3               |
| `thegent-cache`     | Caching layer                | Partial               |
| `thegent-crypto`    | Crypto utilities             | Partial               |
| `thegent-jsonl`     | JSONL parsing                | ✅ PyO3               |
| `thegent-watcher`   | File watching                | Partial               |
| `thegent-shm`       | Shared memory                | ✅ PyO3               |
| `thegent-discovery` | Tool discovery               | ✅ PyO3               |
| `thegent-hooks`     | Hook system                  | ✅ PyO3               |
| + 23 more           | Various                      | Varies                |

---

## Python Subprocess Hot Paths (Candidates for Rust)

### High Priority (80+ files with subprocess)

| Category            | Files | LOC | Migration Target    |
| ------------------- | ----- | --- | ------------------- |
| Git operations      | 15    | ~3K | `thegent-git`       |
| Shell execution     | 12    | ~2K | `thegent-shims`     |
| File discovery      | 8     | ~1K | `thegent-discovery` |
| Process management  | 10    | ~2K | `thegent-runtime`   |
| LSP/IDE integration | 6     | ~1K | New crate           |

### Already Has Rust Backend

| Python Module                | Rust Crate          | Status    |
| ---------------------------- | ------------------- | --------- |
| `native/git_native.py`       | `thegent-git`       | ✅ Active |
| `native/jsonl_parser.py`     | `thegent-jsonl`     | ✅ Active |
| `native/discovery_native.py` | `thegent-discovery` | ✅ Active |
| `native/state_shm.py`        | `thegent-shm`       | ✅ Active |
| `native/watcher_daemon.py`   | `thegent-watcher`   | ✅ Active |

---

## Migration Strategy

### Phase 1: Expand Existing Crates

1. **thegent-git**: Add more git operations
2. **thegent-shims**: Add shell execution helpers
3. **thegent-discovery**: Add tool detection

### Phase 2: New Crates

1. **thegent-subprocess**: Safe subprocess wrappers
2. **thegent-process**: Process lifecycle management
3. **thegent-ide**: IDE/LSP integration

### Phase 3: Hot Path Migration

1. Replace subprocess calls with Rust bindings
2. Add Python fallbacks for compatibility
3. Benchmark and optimize

---

## Estimated Impact

| Migration          | Python LOC Reduced | Rust LOC Added |
| ------------------ | ------------------ | -------------- |
| Git operations     | -3,000             | +2,000         |
| Subprocess         | -5,000             | +3,000         |
| File operations    | -2,000             | +1,500         |
| Process management | -3,000             | +2,500         |
| **Total**          | **-13,000**        | **+9,000**     |

---

## Implementation Order

1. ✅ Create execution/ module split (done)
2. 🔲 Expand thegent-git bindings
3. 🔲 Create thegent-subprocess crate
4. 🔲 Migrate infra/subprocess_manager.py
5. 🔲 Migrate mesh/git.py operations
6. 🔲 Migrate automation/ subprocess calls
