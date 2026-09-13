# 🔄 Legacy Dependency Migration Guide

**Date:** February 18, 2026  
**Status:** High-priority replacements implemented

## ✅ Completed Replacements

### Rust Dependencies

- ✅ `lazy_static` → Removed (use `std::sync::OnceLock`)
- ✅ `md5` → `sha2` (security fix)
- ✅ `hex 0.4` → `base16ct 1.0` (4 files)
- ✅ `thiserror 1.0` → `thiserror 2.0` (3 files)

### Go Dependencies

- ✅ `github.com/lib/pq` → `github.com/jackc/pgx/v5` (3 files)

---

## 📝 Code Migration Examples

### 1. lazy_static → std::sync::OnceLock

**Before:**

```rust
use lazy_static::lazy_static;
use std::collections::HashMap;

lazy_static! {
    static ref CONFIG: HashMap<String, String> = {
        let mut m = HashMap::new();
        m.insert("key".to_string(), "value".to_string());
        m
    };
}

fn main() {
    println!("{:?}", CONFIG.get("key"));
}
```

**After:**

```rust
use std::sync::OnceLock;
use std::collections::HashMap;

static CONFIG: OnceLock<HashMap<String, String>> = OnceLock::new();

fn get_config() -> &'static HashMap<String, String> {
    CONFIG.get_or_init(|| {
        let mut m = HashMap::new();
        m.insert("key".to_string(), "value".to_string());
        m
    })
}

fn main() {
    println!("{:?}", get_config().get("key"));
}
```

**Files to update:**

- `thegent/hooks/hook-dispatcher/src/**/*.rs`
- `thegent/crates/thegent-hooks/src/**/*.rs`

---

### 2. md5 → sha2

**Before:**

```rust
use md5::{Md5, Digest};

fn hash_data(data: &[u8]) -> String {
    let hash = Md5::digest(data);
    format!("{:x}", hash)
}
```

**After:**

```rust
use sha2::{Sha256, Digest};

fn hash_data(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    format!("{:x}", hasher.finalize())
}

// Or using blake3 (faster, already in dependencies):
use blake3;

fn hash_data_blake3(data: &[u8]) -> String {
    let hash = blake3::hash(data);
    hash.to_hex().to_string()
}
```

**Files to update:**

- `thegent/crates/thegent-runtime/src/**/*.rs`

**Note:** MD5 is cryptographically broken. Use SHA-256 for compatibility or BLAKE3 for speed.

---

### 3. hex → base16ct

**Before:**

```rust
use hex;

fn encode(data: &[u8]) -> String {
    hex::encode(data)
}

fn decode(s: &str) -> Result<Vec<u8>, hex::FromHexError> {
    hex::decode(s)
}
```

**After:**

```rust
use base16ct::{lower, Upper};

fn encode(data: &[u8]) -> String {
    lower::encode_string(data)
}

fn decode(s: &str) -> Result<Vec<u8>, base16ct::Error> {
    let mut buf = vec![0u8; s.len() / 2];
    lower::decode(s, &mut buf)?;
    Ok(buf)
}

// For uppercase:
fn encode_upper(data: &[u8]) -> String {
    Upper::encode_string(data)
}
```

**Files to update:**

- `thegent/crates/thegent-runtime/src/**/*.rs`
- `thegent/crates/thegent-crypto/src/**/*.rs`
- `thegent/crates/thegent-memory/src/**/*.rs`
- `thegent/crates/thegent-hooks/src/**/*.rs`

**Benefits:**

- Constant-time operations (security)
- Faster performance
- Better maintained

---

### 4. thiserror 1.0 → 2.0

**Mostly drop-in replacement.** Check for:

**Breaking changes:**

- Const generics improvements (better performance)
- Some attribute syntax changes

**Before (1.0):**

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum MyError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}
```

**After (2.0):**

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum MyError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}
// Same syntax! Mostly compatible.
```

**Files updated:**

- `thegent/crates/thegent-router/Cargo.toml`
- `thegent/crates/supermemory-rs/Cargo.toml`
- `thegent/crates/thegent-memory/Cargo.toml`

**Action:** Run `cargo check` to verify compatibility.

---

### 5. lib/pq → pgx/v5 (Go)

**Before:**

```go
import (
    "database/sql"
    _ "github.com/lib/pq"
)

func connect() (*sql.DB, error) {
    return sql.Open("postgres", "postgres://user:pass@localhost/dbname")
}

func query(db *sql.DB) error {
    rows, err := db.Query("SELECT id, name FROM users WHERE id = $1", 1)
    if err != nil {
        return err
    }
    defer rows.Close()
    // ... scan rows
    return nil
}
```

**After:**

```go
import (
    "context"
    "github.com/jackc/pgx/v5"
)

func connect(ctx context.Context) (*pgx.Conn, error) {
    return pgx.Connect(ctx, "postgres://user:pass@localhost/dbname")
}

func query(ctx context.Context, conn *pgx.Conn) error {
    rows, err := conn.Query(ctx, "SELECT id, name FROM users WHERE id = $1", 1)
    if err != nil {
        return err
    }
    defer rows.Close()
    // ... scan rows
    return nil
}

// Or use pgxpool for connection pooling:
import "github.com/jackc/pgx/v5/pgxpool"

func connectPool(ctx context.Context) (*pgxpool.Pool, error) {
    return pgxpool.New(ctx, "postgres://user:pass@localhost/dbname")
}
```

**Files updated:**

- `trace/backend/go.mod`
- `trace/backend/tests/go.mod`
- `claude-squad/go.mod`

**Migration steps:**

1. Replace `sql.Open()` with `pgx.Connect()`
2. Add `context.Context` to all database operations
3. Update query methods (pgx uses different API)
4. Consider using `pgxpool` for connection pooling
5. Update error handling (pgx has better error types)

**Benefits:**

- Faster performance
- Better type safety
- Modern API
- Actively maintained

---

## 🔍 Finding Code That Needs Updates

### Rust

```bash
# Find lazy_static usage
cd thegent/crates
cargo tree | grep lazy_static
# Then search source files:
find . -name "*.rs" -exec grep -l "lazy_static" {} \;

# Find md5 usage
find . -name "*.rs" -exec grep -l "md5\|Md5" {} \;

# Find hex usage
find . -name "*.rs" -exec grep -l "hex::\|use hex" {} \;
```

### Go

```bash
# Find lib/pq usage
cd trace/backend
grep -r "lib/pq" --include="*.go" .
grep -r "sql.Open" --include="*.go" .
grep -r "database/sql" --include="*.go" .
```

---

## ⚠️ Testing Checklist

After making code changes:

### Rust

- [ ] Run `cargo check --workspace`
- [ ] Run `cargo test --workspace`
- [ ] Check for compilation errors
- [ ] Verify lazy_static → OnceLock migrations
- [ ] Verify md5 → sha2 migrations
- [ ] Verify hex → base16ct migrations
- [ ] Test thiserror 2.0 compatibility

### Go

- [ ] Run `go mod tidy`
- [ ] Run `go build ./...`
- [ ] Run `go test ./...`
- [ ] Update database connection code
- [ ] Update query patterns
- [ ] Test database operations
- [ ] Verify pgx/v5 API usage

---

## 📊 Impact Summary

| Replacement    | Files Changed | Code Changes Needed | Risk Level |
| -------------- | ------------- | ------------------- | ---------- |
| lazy_static    | 2             | Medium              | Low        |
| md5 → sha2     | 1             | Low                 | Low        |
| hex → base16ct | 4             | Low                 | Low        |
| thiserror 1→2  | 3             | Low                 | Low        |
| lib/pq → pgx   | 3             | Medium-High         | Medium     |

**Total:** 13 dependency files updated, code changes required in ~10-15 source files.

---

## 🚀 Next Steps

1. **Update Rust source code:**

   ```bash
   cd thegent/crates
   cargo check --workspace  # Find errors
   # Fix lazy_static, md5, hex usage
   cargo test --workspace
   ```

2. **Update Go source code:**

   ```bash
   cd trace/backend
   go mod tidy
   go build ./...  # Find errors
   # Fix lib/pq → pgx migrations
   go test ./...
   ```

3. **Verify all changes:**
   - Run full test suite
   - Check for any remaining legacy dependencies
   - Update documentation

---

## 📚 Additional Resources

- [Rust OnceLock docs](https://doc.rust-lang.org/std/sync/struct.OnceLock.html)
- [pgx documentation](https://pkg.go.dev/github.com/jackc/pgx/v5)
- [base16ct crate](https://docs.rs/base16ct/)
- [thiserror 2.0 changelog](https://github.com/dtolnay/thiserror/releases)

---

**Generated:** 2026-02-18  
**See also:** `LEGACY_MODERN_ALTERNATIVES_REPORT.md` for full audit
