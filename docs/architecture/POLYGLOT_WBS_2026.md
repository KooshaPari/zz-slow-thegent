# Thegent 2026 Polyglot WBS & Workstream Assignment

This document defines the Phased Work Breakdown Structure (WBS) for the `thegent` polyglot migration, assigning specific tasks to language-specialized workstreams.

---

## 1. Workstreams Defined

| Stream       | Focus                                        | Primary Toolchain        |
| :----------- | :------------------------------------------- | :----------------------- |
| **[NATIVE]** | Shared Memory, Rust Extensions, Wasm Host    | `cargo`, `zig`, `rustc`  |
| **[NET]**    | High-throughput Proxying, API Interop        | `go`, `cgo`              |
| **[LOGIC]**  | Orchestration, Heuristics, Mojo Acceleration | `uv`, `pypy`, `mojo`     |
| **[INFRA]**  | Build Systems, CI/CD, Telemetry, IPC         | `task`, `docker`, `otel` |

---

## 2. Phase 1: The "Atomic" Foundation (Months 1–2)

**Goal**: Replace slow file-based IPC with high-speed memory-mapped shared state.

### [NATIVE]

- **ID: N1.1** | Develop `thegent-shm` Rust crate. Define memory-mapped structs for provider health, quotas, and circuit breakers.
- **ID: N1.2** | Implement `thegent-ipc` crate. Wrap `nng` or `iceoryx2` for high-speed cross-process messaging.
- **ID: N1.3** | Create C-ABI exports for SHM pointers to allow Go/Mojo access.

### [NET]

- **ID: G1.1** | Integrate `mmap-go` into `cliproxyapi-plusplus`. Allow the Go proxy to write usage metrics directly to Rust-managed SHM.
- **ID: G1.2** | Standardize JSON-RPC control plane in Go for Python-to-Go signaling (e.g., refreshing specific provider configs).

### [LOGIC]

- **ID: L1.1** | Integrate `thegent-shm-python` bindings into the orchestrator.
- **ID: L1.2** | Migrate `MaildirQueue` calls in `multi_runtime_bridge.py` to `thegent-ipc`.

### [INFRA]

- **ID: I1.1** | Unified `Taskfile.yml` implementation for `cargo`, `go`, and `uv`.
- **ID: I1.2** | Implement `thegent doctor --shm` to verify cross-language memory access and permissions.

---

## 3. Phase 2: Compute Acceleration (Months 3–4)

**Goal**: Offload "hot" Python logic to Mojo and Rust for 10x throughput.

### [NATIVE]

- **ID: N2.1** | Refactor `ParetoRouter` (Rust) for zero-copy access to the SHM health matrix.
- **ID: N2.2** | Implement `AtomicDecisionEngine` in Rust for fast-path routing (bypass Python for cached routes).

### [LOGIC]

- **ID: L2.1** | Mojo Environment Setup: Integrate Mojo toolchain with `uv` project structure.
- **ID: L2.2** | Offload `HeuristicOptimizer` and `AgentScorer` logic to Mojo `@mojo` functions.
- **ID: L2.3** | Implement Mojo-to-Python bridge for seamless logic swapping.

### [INFRA]

- **ID: I2.1** | Cross-language Telemetry: Implement OTLP spans for Python -> Mojo -> Rust calls.
- **ID: I2.2** | Automated benchmarks: CI/CD path to verify Mojo speedups vs. PyPy baseline.

---

## 4. Phase 3: The "Atomic Tool" Sandbox (Months 5–6)

**Goal**: Standardize and sandbox high-performance agent tools in Zig/Wasm.

### [NATIVE]

- **ID: N3.1** | Implement `thegent-wasm-host` using Extism. Integrate with Python and Go.
- **ID: N3.2** | Develop Zig SDK for "Atomic Tools" (minimal binary size, <100kb).
- **ID: N3.3** | Build Rust-to-Wasm bridge for heavy compute tools.

### [LOGIC]

- **ID: L3.1** | Standardize `thegent` Tool Interface for Wasm. Define the memory-passing contract.
- **ID: L3.2** | Migrate core tools (File Search, Regex, Token Counting) to Zig/Wasm.

### [INFRA]

- **ID: I3.1** | Build `thegent-registry-wasm`: A central store for compiled .wasm tool assets.
- **ID: I3.2** | Implement Wasm sandboxing security policies (limited FS/Net access).

---

## 5. Phase 4: Production Maturity (Months 7+)

**Goal**: Unified management and 99.99% reliability across all runtimes.

### [NET]

- **ID: G4.1** | High-availability (HA) Go Proxy: Implement cluster-aware state sharing using SHM-over-Network.

### [LOGIC]

- **ID: L4.1** | Self-Healing Orchestrator: Python logic to restart crashed Go/Rust/Mojo workers using the SHM heartbeat.

### [INFRA]

- **ID: I4.1** | Unified CLI: `thegent run ...` handles all polyglot compilation and deployment transparently.
- **ID: I4.2** | Global Performance Matrix: Real-time dashboard showing throughput per language (Python vs. Rust vs. Go).
