# Thegent Polyglot Architecture & Migration Plan (2026)

## 1. Current State Audit

| Component              | Language      | Runtime     | Current Efficiency | Target Efficiency     |
| :--------------------- | :------------ | :---------- | :----------------- | :-------------------- |
| **Orchestrator**       | Python        | PyPy 3.11   | High (JIT)         | Ultra (Multi-process) |
| **API Proxy**          | Go            | Native      | Very High          | Maximum               |
| **Routing Engine**     | Python / Rust | PyO3        | High               | Ultra (Mojo/Rust)     |
| **IPC / Shared State** | Python        | File-based  | Medium             | Ultra (SHM / Rust)    |
| **Agent Tools**        | Python        | Interpreted | Medium             | High (Zig/Wasm)       |

---

## 2. Polyglot Matrix 2026

### Core Languages

- **Python (PyPy 3.11 / CPython 3.14)**: The "Glue". Used for high-level orchestration, plugin discovery, and CLI UX.
- **Rust**: The "Engine". Used for memory-safe, high-concurrency tasks, Shared Memory (SHM), and core routing algorithms.
- **Go**: The "Network". Used for high-throughput API proxying and concurrent telemetry gathering.

### Emerging Accelerators

- **Mojo**: The "Compute". Used for JIT-accelerated math and logic that requires Python-like syntax but Rust-level performance.
- **Zig**: The "Plugin". Used for writing ultra-small, fast, and sandboxed Wasm tools.

---

## 3. Recommended Libraries & Packages

### Python Interop (The "Glue")

- **Rust**: `PyO3` (Native bindings), `maturin` (Build system).
- **Mojo**: `Mojo.Python` (Native Mojo-to-Python), `C-ABI` (Python-to-Mojo).
- **Zig**: `Extism` (Universal Wasm plugin system), `wasmer` (Alternative Wasm runtime).
- **Go**: `gopy` or JSON-RPC over Unix Sockets for clean process separation.

### Infrastructure & IPC

- **Shared Memory**: `thegent-shm` (Rust).
- **IPC**: `nanomsg-next-gen (nng)` or `zero-mq` (Rust/Go bindings).
- **Serialization**: `orjson` (Python/Rust), `capnproto` (Cross-language zero-copy).

---

## 4. Migration Plan (WBS)

### Phase 1: Native IPC Foundation (Immediate)

- **P1.1**: Implement `thegent-ipc` Rust crate to replace `ipc.py` file-based logic.
- **P1.2**: Standardize on `capnproto` for cross-runtime message serialization (Python <-> Rust <-> Go).
- **P1.3**: Migrate `MaildirQueue` to a memory-mapped ring buffer in Rust.

### Phase 2: Mojo Acceleration (Next 4 Weeks)

- **P2.1**: Establish `thegent-mojo-bridge` for calling compiled Mojo modules from Python.
- **P2.2**: Port `router_logic.py` and complex heuristics to Mojo.
- **P2.3**: Benchmark Mojo vs. PyPy vs. CPython 3.14 (freethreaded).

### Phase 3: Wasm-Based Tooling (Next 8 Weeks)

- **P3.1**: Standardize the Agent Tool interface using Wasm (Extism).
- **P3.2**: Provide Zig and Rust SDKs for creating "Atomic Tools".
- **P3.3**: Implement a "Tool Sandbox" in `thegent` to run untrusted Zig-compiled Wasm tools.

### Phase 4: Unified Multi-Runtime Manager (Next 12 Weeks)

- **P4.1**: Upgrade `multi_runtime_bridge.py` to support "Language Workers" (e.g., a worker can be a Zig binary).
- **P4.2**: Implement centralized logging and telemetry that spans Python, Rust, Go, and Mojo processes.

---

## 5. Risk Assessment

- **Complexity**: Managing 4+ toolchains (`uv`, `cargo`, `go`, `mojo`, `zig`) increases dev overhead. _Mitigation: Use `Taskfile.yml` as the single entry point._
- **Debugging**: Cross-language stack traces are difficult. _Mitigation: Implement unified OpenTelemetry spans across all runtimes._
- **Mojo Maturity**: Mojo is fast but the ecosystem is still growing. _Mitigation: Use Mojo only for pure-logic "hot-spots"._
