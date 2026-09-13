# 🔍 Deep Legacy Dependency Audit & Modern Alternatives

**Date:** February 18, 2026  
**Scope:** Comprehensive audit of Rust, Go, and Python dependencies

## Executive Summary

Found **3 HIGH priority** legacy dependencies that should be replaced immediately, plus several medium/low priority improvements.

## 🚨 HIGH PRIORITY Replacements

### 1. **Rust: `lazy_static` → `std::sync::OnceLock`**

**Current Status:**
- Found in: `thegent-hooks/Cargo.toml`
- Version: 1.4.x

**Why Replace:**
- `lazy_static` is **deprecated** in favor of `std::sync::OnceLock` (Rust 1.70+)
- No external dependency needed
- Better performance (no macro overhead)
- Standard library support

**Migration:**
```rust
// Old (lazy_static)
use lazy_static::lazy_static;
lazy_static! {
    static ref CONFIG: HashMap<String, String> = HashMap::new();
}

// New (std::sync::OnceLock)
use std::sync::OnceLock;
static CONFIG: OnceLock<HashMap<String, String>> = OnceLock::new();
fn get_config() -> &'static HashMap<String, String> {
    CONFIG.get_or_init(|| HashMap::new())
}
```

**Effort:** Medium  
**Benefit:** Remove dependency, better performance

---

### 2. **Rust: `md5` → `sha2` or `blake3`**

**Current Status:**
- Found in: `thegent-runtime/Cargo.toml`
- Version: 0.7.x

**Why Replace:**
- **MD5 is cryptographically broken** (collision attacks)
- Security vulnerability
- Use SHA-256 (`sha2`) or BLAKE3 for better security

**Migration:**
```rust
// Old (md5)
use md5::{Md5, Digest};
let hash = Md5::digest(data);

// New (sha2 - secure)
use sha2::{Sha256, Digest};
let hash = Sha256::digest(data);

// Or (blake3 - fastest)
use blake3;
let hash = blake3::hash(data);
```

**Effort:** Low  
**Benefit:** **Critical security improvement**

---

### 3. **Go: `github.com/lib/pq` → `github.com/jackc/pgx/v5`**

**Current Status:**
- Found in: `trace/backend/go.mod` (4 files)
- Version: v1.11.1

**Why Replace:**
- `lib/pq` is **unmaintained** (last update 2023)
- `pgx/v5` is faster, more modern, actively maintained
- Better type safety and error handling
- Native support for PostgreSQL features

**Migration:**
```go
// Old (lib/pq)
import "github.com/lib/pq"
db, err := sql.Open("postgres", connStr)

// New (pgx/v5)
import "github.com/jackc/pgx/v5"
conn, err := pgx.Connect(context.Background(), connStr)
```

**Effort:** Medium  
**Benefit:** Better performance, modern API, maintained

---

## ⚠️ MEDIUM PRIORITY Improvements

### 4. **Rust: `thiserror 1.0` → `thiserror 2.0`**

**Current Status:**
- Found in: 4 crates
- Version: 1.0.x

**Why Upgrade:**
- Better error handling with const generics
- Improved performance
- Better diagnostics

**Migration:** Mostly drop-in replacement, check changelog

**Effort:** Low  
**Benefit:** Better error types

---

### 5. **Rust: `hex 0.4` → `base16ct` or `base16`**

**Current Status:**
- Found in: 4 crates
- Version: 0.4.x

**Why Replace:**
- `base16ct` is faster and more modern
- Better maintained
- Constant-time operations (security)

**Migration:**
```rust
// Old (hex)
use hex;
let encoded = hex::encode(data);

// New (base16ct)
use base16ct;
let encoded = base16ct::lower::encode_string(&data);
```

**Effort:** Low  
**Benefit:** Better performance, maintained

---

### 6. **Go: `github.com/gorilla/mux` → `github.com/go-chi/chi`**

**Current Status:**
- Found in: 3 go.mod files
- Version: v1.8.1

**Why Replace:**
- `chi` is lighter and faster
- More modern API
- Better middleware support
- Or use stdlib `net/http` for simplicity

**Migration:**
```go
// Old (gorilla/mux)
import "github.com/gorilla/mux"
r := mux.NewRouter()

// New (chi)
import "github.com/go-chi/chi/v5"
r := chi.NewRouter()

// Or (stdlib - simplest)
import "net/http"
// Use http.ServeMux directly
```

**Effort:** Medium  
**Benefit:** Smaller binary, better performance

---

### 7. **Go: `gorm.io/gorm` → `sqlc` or `sqlx`**

**Current Status:**
- Found in: 3 go.mod files
- Version: v1.31.1

**Why Consider:**
- `sqlc` generates type-safe code from SQL
- `sqlx` is faster and lighter than GORM
- Better performance, type safety

**Note:** GORM is fine if you need ORM features. Consider migration only if performance is critical.

**Effort:** High  
**Benefit:** Type safety, better performance

---

### 8. **Python: `psycopg2-binary` → `psycopg` (v3) or `asyncpg`**

**Current Status:**
- Found in: 8 pyproject.toml files
- Version: 2.9.11

**Why Upgrade:**
- `psycopg` (v3) is modern, async-native
- `asyncpg` is fastest for async workloads
- Better async support

**Migration:**
```python
# Old (psycopg2)
import psycopg2

conn = psycopg2.connect(...)

# New (psycopg3 - sync)
import psycopg

conn = psycopg.connect(...)

# Or (asyncpg - async)
import asyncpg

conn = await asyncpg.connect(...)
```

**Effort:** Medium  
**Benefit:** Better async support, modern API

---

## 📋 LOW PRIORITY (Optional Improvements)

### 9. **Rust: `chrono` → `time` crate**

**Why Consider:**
- `time` crate is lighter and faster
- Smaller binary size

**Note:** `chrono` is fine if you need its features. Only migrate if binary size matters.

**Effort:** Medium  
**Benefit:** Smaller binary

---

### 10. **Rust: `crossbeam-channel` → `tokio::sync::mpsc`**

**Why Consider:**
- If already using tokio, use tokio channels
- Fewer dependencies

**Note:** Only if using tokio runtime. crossbeam-channel is fine for non-async code.

**Effort:** Medium  
**Benefit:** Fewer dependencies

---

## ✅ Already Modern (No Action Needed)

- ✅ `pyyaml` → Already using `ruamel.yaml`
- ✅ `watchdog` → Already using `watchfiles`
- ✅ `uvicorn` → Already added `granian`
- ✅ `pydantic` → Already using v2.x
- ✅ `httpx` → Already modern, `curl-cffi` in optional deps
- ✅ `which` → Already updated to 6.0+
- ✅ `log` → Already using `tracing`

---

## 📊 Migration Priority Matrix

| Dependency | Priority | Effort | Impact | Recommendation |
|------------|----------|--------|--------|-----------------|
| `lazy_static` | HIGH | Medium | High | ✅ Replace immediately |
| `md5` | HIGH | Low | Critical | ✅ Replace immediately (security) |
| `lib/pq` | HIGH | Medium | High | ✅ Replace (unmaintained) |
| `thiserror` | MEDIUM | Low | Medium | ⚠️ Upgrade to 2.0 |
| `hex` | MEDIUM | Low | Low | ⚠️ Consider base16ct |
| `gorilla/mux` | MEDIUM | Medium | Medium | ⚠️ Consider chi or stdlib |
| `gorm` | MEDIUM | High | High | ⚠️ Consider if performance critical |
| `psycopg2` | MEDIUM | Medium | Medium | ⚠️ Consider psycopg3/asyncpg |
| `chrono` | LOW | Medium | Low | 💡 Optional |
| `crossbeam-channel` | LOW | Medium | Low | 💡 Optional |

---

## 🎯 Recommended Action Plan

### Phase 1: Critical Security (Week 1)
1. ✅ Replace `md5` with `sha2` or `blake3`
2. ✅ Replace `lazy_static` with `std::sync::OnceLock`

### Phase 2: Unmaintained Dependencies (Week 2)
3. ✅ Replace `lib/pq` with `pgx/v5`

### Phase 3: Performance Improvements (Week 3-4)
4. ⚠️ Upgrade `thiserror` to 2.0
5. ⚠️ Consider `base16ct` for `hex`
6. ⚠️ Consider `chi` for `gorilla/mux`

### Phase 4: Optional (As Needed)
7. 💡 Consider `psycopg3`/`asyncpg` for Python
8. 💡 Consider `time` crate if binary size matters
9. 💡 Consider `sqlc`/`sqlx` if GORM performance is an issue

---

## 📝 Implementation Scripts

See:
- `legacy_audit.py` - Audit script
- `LEGACY_AUDIT_REPORT.json` - Detailed JSON report

---

## 🔗 References

- [Rust OnceLock docs](https://doc.rust-lang.org/std/sync/struct.OnceLock.html)
- [pgx documentation](https://pkg.go.dev/github.com/jackc/pgx/v5)
- [chi router](https://github.com/go-chi/chi)
- [psycopg3 docs](https://www.psycopg.org/psycopg3/)
- [asyncpg docs](https://magicstack.github.io/asyncpg/)

---

**Generated:** 2026-02-18  
**Next Review:** After Phase 1 completion
