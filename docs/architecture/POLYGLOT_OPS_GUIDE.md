# Thegent 2026: Polyglot Operations & Multi-Runtime Guide

This guide details how to operate and maintain the simultaneous multi-runtime architecture of Thegent.

## 1. Runtime Roles
| Runtime | Role | Primary Use Case | Key Library |
|---------|------|------------------|-------------|
| **Python (PyPy)** | Agent Coordinator | High-level logic, JIT-friendly code | `RouterManager` |
| **Python (3.14)** | System Native | Native extensions, stable ecosystem | `thegent-shm`, `orjson` |
| **Rust** | Atomic Engine | Shared memory, Pareto routing | `pyo3`, `memmap2` |
| **Go** | Networking Edge | High-throughput API proxying | `gin`, `mmap-go` |
| **Mojo** | Math Accelerator | AMX/Tensor heuristics | (Phase 2) |
| **Zig/Wasm** | Sandboxed Tools | Extensible, safe tool execution | `extism` |

## 2. Shared Memory Mesh (SHM)
The Mesh is the "nervous system" of Thegent.
- **Path**: `/tmp/thegent-bridge/state.shm`
- **Ownership**: The Go Proxy and the Python System Native process are the primary writers.
- **Synchronization**: Rust provides atomic operations for counters and circuit breakers.

### Accessing SHM from Python
```python
from thegent.infra.shm_manager import SHMManager

shm = SHMManager()
metrics = shm.get_provider_metrics("claude")
```

### Accessing SHM from Go
```go
import "github.com/router-for-me/CLIProxyAPI/v6/pkg/llmproxy/usage"
usage.SyncToSHM("/tmp/thegent-bridge/state.shm")
```

## 3. Network-Robust Multi-Runtime Orchestration
The `MultiRuntimeBridge` automatically handles asymmetric network conditions.

### Fleet Connectivity
- **Node A (Mac)**: Wi-Fi (requires 5s heartbeats, 60s timeouts).
- **Node B (PC)**: Ethernet (supports 2s heartbeats, 30s timeouts).

### Failover Policy
If PyPy fails to start or crashes repeatedly, the bridge automatically fails over to CPython 3.14 to ensure availability.

## 4. Maintenance Tasks
Use the `Taskfile.yml` for common operations:
- `task polyglot:setup`: Initialize all runtimes.
- `task polyglot:doctor`: Comprehensive health check.
- `task polyglot:shm:clean`: Reset the shared memory state.
- `task polyglot:wasm:build`: Recompile Zig/Rust Wasm plugins.

## 5. Migration Safety Protocol
1. **Contract First**: Define the interface in `runtime_dispatcher.py`.
2. **Shadow Implementation**: Deploy the new runtime version in "shadow mode" (log results but don't use them).
3. **Pareto Switch**: Enable the Rust/PyPy backend once parity is verified.
