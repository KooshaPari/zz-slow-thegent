# Zig-Rust C ABI Interop Design

> **Status**: POC implemented
> **Date**: 2026-02-19
> **Crate**: `crates/thegent-zmx-interop`
> **Research basis**: `docs/research/ZIG_RUST_ECOSYSTEM_RESEARCH_2026-02-19.md`

---

## 1. Overview

This document describes the design of the Zig-to-Rust interop layer that
allows Rust code in thegent to call `zmx` (a Zig session manager) via the C
ABI without spawning a subprocess.

The crate `thegent-zmx-interop` implements two execution paths selected at
compile time via a feature flag:

```
┌─────────────────────────────────────────────────────────────┐
│  Public Rust API                                             │
│  list_sessions() → Result<Vec<String>, ZmxError>            │
│  attach_session(name: &str) → Result<(), ZmxError>          │
│  create_session(name: &str, cmd: &str) → Result<(), ZmxError>│
└──────────────────────┬──────────────────────────────────────┘
                       │
             feature = "zmx-native"?
                  ┌────┴────┐
                 YES        NO
                  │         │
           ┌──────▼──┐  ┌───▼──────────────┐
           │ ffi mod  │  │ subprocess mod    │
           │ extern C │  │ Command("zmx")    │
           │ (unsafe) │  │ (safe, always     │
           └──────────┘  │  available)       │
                         └──────────────────┘
```

---

## 2. C ABI Calling Convention: Zig from Rust

### 2.1 How Zig Exports C ABI Symbols

Zig uses the `export` keyword to expose functions with C calling convention
and no name mangling:

```zig
// In zmx (Zig source):
export fn zmx_list(buf: [*]u8, len: usize) i32 {
    // writes newline-delimited session names into buf
    // returns bytes written (>= 0) or negative errno
}

export fn zmx_attach(name: [*:0]const u8) i32 {
    // attaches to session; returns 0 on success, negative errno on failure
}

export fn zmx_create(name: [*:0]const u8, cmd: [*:0]const u8) i32 {
    // creates new session; returns 0 on success, negative errno on failure
}
```

`export fn` in Zig:

- Uses C calling convention (`extern "C"` equivalent)
- Disables name mangling (symbol name is exactly `zmx_list`, etc.)
- Is compatible with any language that can call C functions

### 2.2 Rust Declarations

```rust
// In thegent-zmx-interop/src/lib.rs:
extern "C" {
    fn zmx_list(buf: *mut u8, len: usize) -> i32;
    fn zmx_attach(name: *const u8) -> i32;
    fn zmx_create(name: *const u8, cmd: *const u8) -> i32;
}
```

The `extern "C"` block declares foreign symbols that will be resolved at link
time against `libzmx`. All calls are `unsafe` — they are wrapped by the safe
public API.

### 2.3 Type Mapping

| Zig type        | Rust type   | Notes                                     |
| :-------------- | :---------- | :---------------------------------------- |
| `[*]u8`         | `*mut u8`   | Writable byte slice pointer               |
| `[*:0]const u8` | `*const u8` | NUL-terminated C string; use `CString`    |
| `usize`         | `usize`     | Platform word size; identical ABI         |
| `i32`           | `i32`       | Return code; negative = errno-style error |

---

## 3. Build System Integration

### 3.1 build.rs Strategy

`build.rs` is responsible for finding and linking `libzmx` when the
`zmx-native` feature is active. It follows this search order:

1. **`pkg-config zmx`**: preferred; distro-agnostic; handles CFLAGS too
2. **Known prefixes**: `/usr/local/lib`, `/usr/lib`, `/opt/homebrew/lib`
3. **`ZMX_LIB_DIR` env var**: user override for non-standard install paths

```rust
// build.rs emits:
println!("cargo:rustc-link-search=native={path}");
println!("cargo:rustc-link-lib=static=zmx");   // static link
// or:
println!("cargo:rustc-link-lib=zmx");           // dynamic link
```

### 3.2 pkg-config Integration

If zmx ships a `zmx.pc` file, the full integration becomes:

```toml
# Cargo.toml (future: replace cc with pkg-config crate)
[build-dependencies]
pkg-config = "0.3"
```

```rust
// build.rs (future):
pkg_config::Config::new()
    .atleast_version("0.1")
    .probe("zmx")
    .expect("zmx not found; set ZMX_LIB_DIR or install zmx");
```

### 3.3 Zig Build System Note

When building zmx from source, the Zig build system (`build.zig`) produces a
static archive (`libzmx.a`) or shared library (`libzmx.so`/`libzmx.dylib`).
To build a C-ABI-compatible library from Zig source:

```bash
zig build-lib zmx.zig -dynamic -OReleaseFast -femit-h
# Produces: libzmx.so + zmx.h
```

The generated `zmx.h` header can be used to validate the Rust `extern "C"`
declarations match the actual Zig exports.

---

## 4. Safety Considerations

### 4.1 The Unsafe Boundary

All `unsafe` is contained within the `ffi` module. The public API is fully
safe:

```rust
// UNSAFE (private):
let written = unsafe { ffi::zmx_list(buf.as_mut_ptr(), buf.len()) };

// SAFE (public):
pub fn list_sessions() -> Result<Vec<String>, ZmxError> { ... }
```

### 4.2 Buffer Safety for zmx_list

The `zmx_list` function writes into a caller-provided buffer. The safe wrapper:

- Allocates a fixed-size heap buffer (64 KiB) before the call
- Passes `buf.len()` as the capacity bound, preventing overflows
- Treats `written > buf.len()` as a protocol error

```rust
const LIST_BUF_SIZE: usize = 65_536;
let mut buf = vec![0u8; LIST_BUF_SIZE];
let written = unsafe { ffi::zmx_list(buf.as_mut_ptr(), buf.len()) };
```

### 4.3 String Safety for zmx_attach / zmx_create

Zig expects NUL-terminated C strings. Rust's `CString` handles this:

```rust
let cname = CString::new(name).map_err(|_| ZmxError::NulInName)?;
// CString::new() returns Err if the input contains an interior NUL byte.
// The as_ptr() is valid for the lifetime of cname.
let rc = unsafe { ffi::zmx_attach(cname.as_ptr() as *const u8) };
```

The `ZmxError::NulInName` variant is returned (not a panic) if the caller
passes a string with an embedded NUL byte.

### 4.4 Lifetime Guarantees

The `CString` value must outlive the FFI call. Rust's ownership rules ensure
this: `cname` is declared in the caller's stack frame and is not dropped until
after the `unsafe` block completes.

### 4.5 Thread Safety

zmx's thread-safety guarantees are not yet documented. Until confirmed:

- Treat `list_sessions()` as non-concurrent-safe
- Use `Mutex<()>` as a guard if calling from multiple threads

---

## 5. Feature Flag Design

| Feature      | Default | Build outcome                                           |
| :----------- | :-----: | :------------------------------------------------------ |
| _(none)_     |   yes   | Subprocess fallback; compiles everywhere; no libzmx dep |
| `zmx-native` |   no    | C ABI FFI path; requires libzmx at link time            |

The subprocess fallback is always the default because:

1. It compiles on any machine without zmx installed (CI, developer laptops)
2. It provides a working implementation immediately
3. It allows the native path to be opt-in and tested independently

To enable the native path:

```toml
# In a crate that depends on thegent-zmx-interop:
thegent-zmx-interop = { path = "...", features = ["zmx-native"] }
```

Or directly:

```bash
cargo test --features zmx-native --include-ignored
```

---

## 6. Error Handling

All errors are structured via `ZmxError` (a `thiserror::Error` enum):

| Variant            | When                                            |
| :----------------- | :---------------------------------------------- |
| `NativeError`      | zmx C function returned a non-zero code         |
| `NulInName`        | Session name/cmd contained an interior NUL byte |
| `Subprocess`       | `Command::new("zmx")` failed to spawn           |
| `SubprocessFailed` | zmx subprocess exited non-zero                  |
| `Utf8`             | zmx output was not valid UTF-8                  |

---

## 7. Future Work

## 7.1 ABI Contract Versioning (WL-132 Slice)

`crates/thegent-zmx-interop/src/lib.rs` now exports:

```rust
pub const ABI_CONTRACT_VERSION: u32 = 1;
```

Contract rule:

1. Bump `ABI_CONTRACT_VERSION` whenever exported Zig C-ABI symbols or call
   semantics change.
2. Keep the non-zero invariant tested in crate unit tests.
3. Gate any ABI promotion on version-aware interop tests before enabling new
   runtime paths.

Canonical gate command:

```bash
task quality:runtime-contracts:zig-abi
```

| Item                         | Notes                                            |
| :--------------------------- | :----------------------------------------------- |
| `impl-rust-zmx-wrapper`      | Richer API: session metadata, send keys, capture |
| `impl-zmx-c-abi`             | If zmx does not export C ABI yet, add it         |
| PyO3 bindings                | Expose `list_sessions()` to Python via PyO3      |
| `zmx_capture_screen` FFI     | Read terminal screen content natively            |
| pkg-config crate in build.rs | Replace manual shell-out with `pkg-config` crate |

---

## 8. References

- `crates/thegent-zmx-interop/src/lib.rs` — implementation
- `crates/thegent-zmx-interop/build.rs` — build system integration
- `docs/research/ZIG_RUST_ECOSYSTEM_RESEARCH_2026-02-19.md` — research basis
- [mkpoli/zig-rust-interop](https://github.com/mkpoli/zig-rust-interop) — reference implementation
- [Zig `export fn` docs](https://ziglang.org/documentation/master/#Exporting-a-C-Library)
