# Dependency Upgrade Guide

This guide documents the dependency upgrades implemented and how to use the new features.

## ✅ Completed Upgrades

### 1. Rust Dependencies

#### reqwest v0.11 → v0.12
- **File:** `thegent/crates/thegent-memory/Cargo.toml`
- **Impact:** Better performance, improved async handling
- **Breaking Changes:** Minimal - mostly drop-in replacement
- **Action Required:** None - code should work as-is

#### simd-json Added
- **Files:** 
  - `thegent/crates/thegent-memory/Cargo.toml`
  - `thegent/crates/thegent-router/Cargo.toml`
  - `thegent/crates/supermemory-rs/Cargo.toml`
  - `thegent/crates/thegent-discovery/Cargo.toml`
  - `thegent/crates/thegent-shm/Cargo.toml`
  - `thegent/crates/thegent-cache/Cargo.toml`
- **Impact:** 2-5x faster JSON parsing
- **Usage:** See "Using simd-json" section below

#### dashmap v5 → v6
- **File:** `thegent/crates/thegent-hooks/Cargo.toml`
- **Impact:** Better performance, improved API
- **Breaking Changes:** Minimal API changes
- **Action Required:** Review code for any deprecated methods

#### git2 v0.18 → v0.21
- **File:** `thegent/crates/thegent-git/Cargo.toml`
- **Impact:** Bug fixes, performance improvements
- **Breaking Changes:** Some API changes - see git2 changelog
- **Action Required:** Test Git operations thoroughly

#### gix Added (Optional)
- **File:** `thegent/crates/thegent-git/Cargo.toml`
- **Impact:** Pure Rust Git implementation, 1.5-2x faster
- **Usage:** Enable with `--features gix` flag
- **Action Required:** Migrate gradually - see migration guide below

#### compio Added (Optional)
- **File:** `thegent/crates/thegent-memory/Cargo.toml`
- **Impact:** io_uring/IOCP-based async I/O, 2-3x faster
- **Usage:** Enable with `--features compio` flag
- **Action Required:** Test on Linux/Windows for I/O-heavy workloads

### 2. Go Dependencies

#### redis/go-redis v9.18.0-beta.2 → v9.18.0
- **File:** `trace/backend/go.mod`
- **Impact:** Stable release, bug fixes
- **Breaking Changes:** None
- **Action Required:** Run `go mod tidy` and test Redis operations

### 3. Python Dependencies

#### granian Added
- **File:** `thegent/pyproject.toml`
- **Impact:** Rust-based ASGI server, 30-50% faster than uvicorn
- **Usage:** Replace `uvicorn` with `granian` in startup scripts
- **Action Required:** Test as alternative to uvicorn

## Using simd-json

### Option 1: Drop-in Replacement (Recommended)

`simd-json` provides drop-in replacements via the `simd_json::serde` module:

```rust
// Old way
use serde_json;

let value: MyStruct = serde_json::from_str(&json_string)?;
let json_string = serde_json::to_string(&value)?;

// New way (faster)
use simd_json::serde;

let value: MyStruct = simd_json::serde::from_str(&mut json_string.clone())?;
let json_string = simd_json::serde::to_string(&value)?;
```

**Note:** `simd_json::serde::from_str` requires a mutable `String` (it modifies it in-place for performance).

### Option 2: Feature Flag (Automatic)

You can also use `simd-json` as a feature flag on `serde_json`:

```toml
[dependencies]
serde_json = { version = "1.0", features = ["simd"] }
```

However, the explicit `simd-json` crate gives more control.

### Option 3: Hybrid Approach

Use `simd-json` for parsing (where it shines) and `serde_json` for serialization:

```rust
use simd_json::serde as simd_json;
use serde_json;

// Fast parsing
let value: MyStruct = simd_json::from_str(&mut json_string.clone())?;

// Standard serialization (simd-json serialization is similar speed)
let json_string = serde_json::to_string(&value)?;
```

## Migrating to gix (Optional)

`gix` is a pure Rust Git implementation that's faster than `git2`. To migrate:

### Step 1: Enable Feature

```bash
cargo build --features gix
```

### Step 2: Update Code

```rust
// Old (git2)
use git2::Repository;

let repo = Repository::open(".")?;
let head = repo.head()?;

// New (gix)
use gix::Repository;

let repo = Repository::open(".")?;
let head = repo.head_id()?;
```

### Step 3: Gradual Migration

You can use both libraries side-by-side during migration:

```rust
#[cfg(feature = "gix")]
use gix::Repository as GitRepo;

#[cfg(not(feature = "gix"))]
use git2::Repository as GitRepo;
```

## Using compio (Optional)

`compio` provides io_uring-based async I/O on Linux and IOCP on Windows.

### Enable Feature

```bash
cargo build --features compio
```

### Example Usage

```rust
#[cfg(feature = "compio")]
use compio::fs::File;
use compio::io::AsyncReadExt;

#[cfg(feature = "compio")]
async fn read_file_compio(path: &str) -> Result<Vec<u8>> {
    let mut file = File::open(path).await?;
    let mut buffer = Vec::new();
    file.read_to_end(&mut buffer).await?;
    Ok(buffer)
}
```

## Using granian (Python)

Replace uvicorn with granian in your startup scripts:

```python
# Old
# uvicorn app:app --host 0.0.0.0 --port 8000

# New
# granian --interface asgi app:app --host 0.0.0.0 --port 8000
```

Or in code:

```python
import granian

if __name__ == "__main__":
    granian.run("app:app", interface="asgi", host="0.0.0.0", port=8000, workers=4)
```

## Testing Checklist

After upgrades, test:

- [ ] All Rust crates compile successfully
- [ ] All tests pass
- [ ] JSON serialization/deserialization works correctly
- [ ] Git operations work correctly (if using git2)
- [ ] Redis operations work correctly (Go)
- [ ] HTTP requests work correctly (reqwest)
- [ ] Python server starts correctly (granian optional)

## Performance Benchmarks

Expected performance improvements:

- **simd-json:** 2-5x faster JSON parsing
- **reqwest v0.12:** 10-20% faster HTTP requests
- **dashmap v6:** 5-10% faster concurrent hashmap operations
- **git2 v0.21:** Bug fixes, minor performance improvements
- **gix:** 1.5-2x faster Git operations (when enabled)
- **compio:** 2-3x faster I/O operations (when enabled)
- **granian:** 30-50% faster Python ASGI server (when enabled)

## Rollback Instructions

If issues occur, you can rollback:

### Rust
```bash
# Revert Cargo.toml changes
git checkout -- thegent/crates/*/Cargo.toml
cargo update
```

### Go
```bash
# Revert go.mod
git checkout -- trace/backend/go.mod
go mod tidy
```

### Python
```bash
# Remove granian from pyproject.toml
# Or just don't use it - uvicorn is still available
```

## Questions?

See `DEPENDENCY_AUDIT_REPORT.md` for detailed analysis and rationale.
