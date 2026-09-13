<DONE>
# Zig vs Rust: Ecosystem, Interop, and Comparison Matrix — Deep Research

> **Status**: Research complete | **Date**: 2026-02-19
> **Purpose**: Full-depth research on Zig-Rust interop, Zig ecosystem 2026, and comparison matrix (AX/DX/UX, reliability, security, safety, speed) for thegent muxless session management (zmx integration).

---

## Part 1: Zig–Rust C ABI Interop

### 1.1 Mechanism

Interop is via **C ABI**.

| Direction      | Mechanism                      | Notes                                                                                                           |
| -------------- | ------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| **Rust → Zig** | `extern "C"` or `libloading`   | Rust links Zig DLL/.so. Zig uses `export fn` for C ABI.                                                         |
| **Zig → Rust** | `std.DynLib.open()` + `lookup` | Zig loads Rust `cdylib`. Rust uses `#[no_mangle]` + `extern "C"`-style exports.                                 |
| **Shared**     | C ABI boundary                 | Primitives, fixed-size structs, opaque pointers only. No strings, no GC, no Rust/Zig semantics across boundary. |

### 1.2 Reference Implementations

| Repo                                                                  | Description                                                                                                      | Last Updated |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------ |
| [mkpoli/zig-rust-interop](https://github.com/mkpoli/zig-rust-interop) | Zig↔Rust DLL interop via C ABI. `zig-rust/` (Zig calls Rust), `rust-zig/` (Rust calls Zig).                     | Mar 2024     |
| [Stack-Syndicate/ziggle](https://github.com/Stack-Syndicate/ziggle)   | "Rust-Zig interop made easy"                                                                                     | Dec 2025     |
| [egonik-unlp/zig-rust](https://github.com/egonik-unlp/zig-rust)       | Rust-Zig interop with struct passing. Zig imports Rust lib as `zig_side_lib`; calls `root.takes_struct(person)`. | Jul 2025     |

### 1.3 Patterns (from mkpoli/zig-rust-interop)

**Zig exports for Rust:**

```zig
export fn add(a: i32, b: i32) i32 {
    return a + b;
}
```

**Rust calls Zig:**

```rust
extern "C" {
    fn add(a: i32, b: i32) -> i32;
}
let c = unsafe { add(a, b) };
```

**Rust exports for Zig:**

```rust
#[no_mangle]
pub extern "C" fn add(left: usize, right: usize) -> usize {
    left + right
}
```

**Zig calls Rust:**

```zig
var dll = try std.DynLib.open("rust_lib.dll");
const add = dll.lookup(*fn (i32, i32) i32, "add").?;
_ = add(1, 2);
```

### 1.4 Implications for zmx + thegent

- **zmx** (Zig): Expose C ABI: `zmx_list_sessions`, `zmx_attach`, `zmx_capture_screen`, etc.
- **thegent** (Python/Rust): Call zmx via Rust FFI or Python subprocess.
- **Preferred**: Rust crate wrapping zmx C ABI; Python calls Rust via PyO3.

---

## Part 2: Zig Ecosystem 2026

### 2.1 Version & Hosting

| Item        | Value                             |
| ----------- | --------------------------------- |
| **Latest**  | 0.15.x                            |
| **Hosting** | Codeberg (primary), GitHub mirror |
| **Status**  | Pre-1.0, production-ready         |

### 2.2 Package Registries

| Registry               | URL                                   | Notes                                             |
| ---------------------- | ------------------------------------- | ------------------------------------------------- |
| **zig.pm**             | https://zig.pm                        | Package index; tags: terminal, ansi-terminal, pty |
| **ziglibs/repository** | https://github.com/ziglibs/repository | Community packages, JSON metadata                 |
| **build.zig.zon**      | In-tree                               | Zig 0.11+ native package manifest                 |

### 2.3 Terminal / Session Tooling

| Package       | Author              | Tags                    | Status                                |
| ------------- | ------------------- | ----------------------- | ------------------------------------- |
| **ansi-term** | joachimschmidt557   | ansi-terminal, terminal | ANSI terminal handling                |
| **conc**      | alichraghi          | ANSI terminal           | VT standards, `fgColor4`, etc.        |
| **zmx**       | (Ghostty ecosystem) | session, libghostty-vt  | Zig session persistence; primary tool |

### 2.4 Other Relevant Ecosystem

| Package            | Purpose              |
| ------------------ | -------------------- |
| **async_io_uring** | Event loop, io_uring |
| **apple_pie**      | HTTP server          |
| **bearssl**        | Crypto (BearSSL)     |
| **clap**           | CLI args             |
| **args**           | Option parser        |

### 2.5 Gaps for Terminal/Session

- No PTY library in zig.pm (rely on C libs or std).
- No Selenium-like terminal automation (Python Termitty fills this).
- **zmx** (libghostty-vt) is the main session tool; no Zig-native alternative to tmux.

---

## Part 3: Zig vs Rust Comparison Matrix

### 3.1 AX (Agent Experience)

| Dimension        | Zig                          | Rust       |
| ---------------- | ---------------------------- | ---------- |
| Startup time     | ⭐⭐⭐⭐⭐                   | ⭐⭐⭐⭐   |
| Binary size      | ⭐⭐⭐⭐⭐                   | ⭐⭐⭐     |
| Memory footprint | ⭐⭐⭐⭐⭐                   | ⭐⭐⭐⭐   |
| Predictability   | ⭐⭐⭐⭐⭐ (no hidden alloc) | ⭐⭐⭐⭐   |
| Hot-path latency | ⭐⭐⭐⭐⭐                   | ⭐⭐⭐⭐⭐ |

### 3.2 DX (Developer Experience)

| Dimension         | Zig                | Rust               |
| ----------------- | ------------------ | ------------------ |
| Learning curve    | ⭐⭐⭐⭐⭐         | ⭐⭐⭐             |
| Compile time      | ⭐⭐⭐⭐⭐         | ⭐⭐⭐             |
| C interop         | ⭐⭐⭐⭐⭐         | ⭐⭐⭐             |
| Ecosystem breadth | ⭐⭐⭐             | ⭐⭐⭐⭐⭐         |
| Error handling    | ⭐⭐⭐⭐           | ⭐⭐⭐⭐⭐         |
| Async maturity    | ⭐⭐               | ⭐⭐⭐⭐⭐         |
| Package manager   | ⭐⭐⭐⭐ (zig.zon) | ⭐⭐⭐⭐⭐ (cargo) |

### 3.3 UX (User Experience)

| Dimension     | Zig        | Rust       |
| ------------- | ---------- | ---------- |
| Runtime speed | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Latency       | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Crash rate    | ⭐⭐⭐⭐   | ⭐⭐⭐⭐⭐ |

### 3.4 Reliability

| Dimension              | Zig                       | Rust                |
| ---------------------- | ------------------------- | ------------------- |
| Memory safety          | ⭐⭐⭐⭐⭐                | ⭐⭐⭐⭐⭐          |
| Undefined behavior     | ⭐⭐⭐⭐                  | ⭐⭐⭐⭐⭐          |
| Panic/OOM handling     | ⭐⭐⭐⭐ (explicit alloc) | ⭐⭐⭐ (std panics) |
| No hidden control flow | ⭐⭐⭐⭐⭐                | ⭐⭐⭐⭐            |
| No hidden allocations  | ⭐⭐⭐⭐⭐                | ⭐⭐⭐              |

### 3.5 Security

| Dimension     | Zig        | Rust       |
| ------------- | ---------- | ---------- |
| Memory safety | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Supply chain  | ⭐⭐⭐⭐   | ⭐⭐⭐⭐⭐ |
| Audit surface | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐   |

### 3.6 Safety

| Dimension             | Zig        | Rust   |
| --------------------- | ---------- | ------ |
| Freestanding / no std | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Optional allocator    | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

### 3.7 Speed

| Dimension    | Zig        | Rust       |
| ------------ | ---------- | ---------- |
| Runtime perf | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Compile time | ⭐⭐⭐⭐⭐ | ⭐⭐⭐     |
| Startup      | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐   |

---

## Part 4: Work Items (Derived)

### 4.1 Zig–Rust Interop

| ID                        | Title                                                     | Priority | Depends                   |
| ------------------------- | --------------------------------------------------------- | -------- | ------------------------- |
| impl-zig-rust-interop-poc | Implement Zig–Rust C ABI Interop POC (Rust calls zmx)     | P1       | -                         |
| impl-zmx-c-abi            | Expose zmx C ABI for list/attach/capture (if not present) | P1       | muxless-zmx-integration   |
| impl-rust-zmx-wrapper     | Create Rust crate wrapping zmx C ABI                      | P2       | impl-zig-rust-interop-poc |

### 4.2 Zig Ecosystem

| ID                             | Title                                            | Priority | Depends |
| ------------------------------ | ------------------------------------------------ | -------- | ------- |
| research-zig-terminal-packages | Audit ansi-term, conc for terminal introspection | P2       | -       |
| impl-zig-pty-bindings          | Evaluate Zig bindings to libvterm or PTY C libs  | P3       | -       |

### 4.3 Comparison Matrix

| ID                       | Title                                                                   | Priority | Depends |
| ------------------------ | ----------------------------------------------------------------------- | -------- | ------- |
| docs-zig-rust-comparison | Publish Zig vs Rust comparison matrix (AX/DX/UX, reliability, security) | P2       | -       |

### 4.4 Muxless Integration

| ID                             | Title                                                | Priority | Depends            |
| ------------------------------ | ---------------------------------------------------- | -------- | ------------------ |
| muxless-zmx-integration        | Integrate zmx as muxless session persistence         | P1       | -                  |
| muxless-extend-agent-scanner   | Extend AgentScanner with droid, codex, cursor-agent  | P1       | -                  |
| muxless-termitty-introspection | Add Termitty-based introspection for "last 50 lines" | P2       | -                  |
| muxless-acp-session-endpoints  | Extend ACP with session/attach, inspect, send        | P2       | acp-server-adapter |

---

## Part 5: References

- [Zig official](https://ziglang.org)
- [Zig on Codeberg](https://codeberg.org/ziglang/zig)
- [Why Zig When There is Already C++, D, and Rust?](https://ziglang.org/learn/why_zig_rust_d_cpp/)
- [zig.pm](https://zig.pm)
- [ziglibs/repository](https://github.com/ziglibs/repository)
- [mkpoli/zig-rust-interop](https://github.com/mkpoli/zig-rust-interop)
- [Stack-Syndicate/ziggle](https://github.com/Stack-Syndicate/ziggle)
- [egonik-unlp/zig-rust](https://github.com/egonik-unlp/zig-rust)
- [alichraghi/conc](https://github.com/alichraghi/conc)
- [MUXLESS_AGENT_SESSION_MANAGEMENT_2026-02-19.md](./MUXLESS_AGENT_SESSION_MANAGEMENT_2026-02-19.md)
