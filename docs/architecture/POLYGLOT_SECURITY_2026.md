# Thegent 2026: Polyglot Security & Sandboxing Architecture

This document defines the security boundaries and sandboxing mechanisms for the multi-runtime environment, specifically focusing on untrusted agent tools and cross-runtime state access.

---

## 1. Security Domains

| Domain              | Runtime       | Isolation Level  | Access Control                 |
| :------------------ | :------------ | :--------------- | :----------------------------- |
| **Orchestrator**    | Python (PyPy) | Host Process     | Full (Trusted)                 |
| **Atomic Engine**   | Rust          | Shared Memory    | Restricted (SHM only)          |
| **Networking Edge** | Go            | Host Process     | Network + SHM                  |
| **Agent Tools**     | Zig / Wasm    | **Wasm Sandbox** | Deny-by-default (Capabilities) |
| **Compute Kernels** | Mojo          | Host Process     | Memory-safe / Restricted       |

---

## 2. Wasm Sandboxing (The "Atomic" Perimeter)

Agent tools (written in Zig or Rust) are compiled to Wasm and executed via **Extism**.

### A. Capability-Based Security

Each tool must define a `manifest.json` declaring required capabilities:

- `fs_read`: List of allowed directories.
- `net_request`: Allowed domains/IPs.
- `env_vars`: Specific environment variables to expose.

### B. Runtime Enforcement

The orchestrator enforces these limits at the WASI layer:

```python
# Conceptual implementation in WasmDispatcher
with extism.Plugin(wasm_bytes, wasi=True) as plugin:
    # Restrict filesystem access to specific tool-space
    plugin.set_config({"allowed_paths": "/tmp/thegent/sandbox/tool_id"})
```

---

## 3. Shared Memory (SHM) Integrity

Since multiple runtimes (Python, Go, Rust, Mojo) access the same memory-mapped region, we must prevent memory corruption and race conditions.

### A. Ownership Model

- **Rust (thegent-shm)**: Acts as the "Guard". It initializes the memory and defines the layout.
- **Writers**: Go (metrics), Python (status), Mojo (heuristics).
- **Readers**: All.

### B. Atomic Synchronization

- Use **Atomic Ops** (via Rust `std::sync::atomic`) for simple flags and counters.
- Use **Cross-process Futexes** (or `pthread` mutexes on macOS) for complex struct updates.
- **Fail-Safe**: If a process dies while holding a lock, the `SharedStateManager` must detect the PID death and auto-release the lock (implemented in `ipc.py`).

---

## 4. Secret Management (Cross-Runtime)

_Challenge: How to share API keys between Python and Go without leaking them to logs or swap._

- **ID: S4.1 | Memory-Locked Storage**: Rust-backed `thegent-crypto` crate uses `mlock` to pin secrets in non-swappable RAM.
- **ID: S4.2 | Zero-Copy Handover**: Pass pointers to memory-locked secrets between runtimes instead of serializing them to JSON.
- **ID: S4.3 | Transient Environment**: Workers receive short-lived session tokens via the IPC mesh, never persistent keys.

---

## 5. Security Audit Tasks (WBS Extension)

- **ID: S5.1** | Implement **capabilities-checker** for Wasm tools.
- **ID: S5.2** | Develop **shm-validator** to detect corrupted or malformed data in the mesh.
- **ID: S5.3** | Automated **secrets-leak-detector** in the log forwarding stream.
