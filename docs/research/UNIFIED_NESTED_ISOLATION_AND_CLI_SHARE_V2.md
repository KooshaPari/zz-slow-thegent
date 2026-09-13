<DONE>
# Research: Unified Nested Isolation & CLI-Share Deep Dive (v2.0)

**Date**: 2026-02-19
**Status**: Finalized Research & Architectural Specification
**Focus**: Extreme Performance, Predictive Resource Governance, and Secure Identity Proxying.

---

## 1. Low-Latency L1/L2 Bridge: The SHM Protocol

While Maildir-style IPC is robust, it introduces filesystem latency (~1-5ms). For high-frequency agent coordination, we implement the **SHM Bridge**.

### 1.1 Shared Memory State (`state.shm`)

- **Technology**: Rust-based `thegent_shm` utilizing memory-mapped files.
- **L1 (Owner)**: Initializes the SHM segment and manages the **Global Registry**.
- **L2 (Reader/Writer)**: Map the segment into their address space.
- **Data Structures**:
  - **Atomic Counters**: For `total_active_processes` across all tenants.
  - **Race Track**: A ring-buffer for speculative results, allowing L1 to detect a "winner" in <100µs.
  - **Lock Table**: Command hashes for debouncing (see Section 3).

### 1.2 Hybrid IPC Strategy

- **Control Plane**: SHM for locks, heartbeats, and racing.
- **Data Plane**: Maildir/Filesystem for large logs and artifact handoffs.

---

## 2. Predictive Resource Governance

The `ADVANCED_RESOURCE_MANAGEMENT_SYSTEM` is now deeply integrated into the isolation lifecycle.

### 2.1 Speculative Throttling

- **The Problem**: Running 5 speculative L2 branches might be fine on a Threadripper but will swap-death a MacBook Air.
- **The Solution**: L1 queries the `ResourcePredictionEngine` before spawning any L2.
  - **Trend Check**: If `mem_available_mb` trend is negative, L1 reduces `max_speculative_branches` from 5 to 2.
  - **Harness Awareness**: L1 uses **Harness Cards** (e.g., `claude-card`) to predict that 3 new L2s will consume ~1.5GB of p95 memory. If only 1GB is available, the speculators are **queued** instead of spawned.

### 2.2 Adaptive ulimits

- Instead of static 1GB limits, L1 dynamically calculates `RLIMIT_AS` for each L2 based on the **statistical peak** from its Harness Card, adding a 10% safety buffer.

---

## 3. CLI-Share: Debouncing & Similarity Merging

### 3.1 Adaptive Command Debouncing

- **L1 Command Cache**: L1 maintains a persistent cache of `(cmd_hash, environment_hash) -> result_path`.
- **Merge-on-Read**: If L2_A and L2_B both trigger `thegent install-shims`, L1 detects the identical hash in SHM.
  - L2_B is suspended (`SIGSTOP`).
  - L2_A finishes.
  - L1 clones the results into L2_B's OverlayFS layer and resumes L2_B (`SIGCONT`).

### 3.2 Cross-Project Similarity Queue

- Similarity is determined by **Project DNA** (hashes of `package.json`, `Cargo.toml`, and `.thegent/config`).
- Similar projects share a **Dependency Lane** in the `ConcurrencyController`, preventing redundant downloads across multiple workspaces.

---

## 4. Secure Identity Proxying

How does an isolated L2 agent use your SSH keys without compromising the host?

### 4.1 The SSH Proxy Bridge

- **Mechanism**: L1 acts as an SSH Agent Forwarder.
- **Process**:
  1. L2 requests a Git operation.
  2. The Git shim in L2 detects the isolation and routes the SSH request through a Unix Domain Socket back to the L1 Lead.
  3. L1 performs the signing/authentication using the host's real keys and returns the signature.
- **Security**: L2 _never_ sees the private key; it only sees the authenticated result.

### 4.2 Git Attribution

- Every L2 commit is automatically injected with:
  - `user.name`: "TheGent Agent (L2: <agent_id>)"
  - `user.email`: "<host_user>+thegent@users.noreply.github.com"
  - `thegent.parent_run`: "<L1_Run_ID>"

---

## 5. Declarative Security Policies (thegent.yaml)

Security is no longer hardcoded. It is declared:

```yaml
# Example thegent.yaml Policy
isolation:
  tier: T3 # Landlock / AppContainer
  network: restricted # Only allows proxy access to docs.python.org
  filesystem:
    - path: ${PROJECT_ROOT}
      mode: read-write
    - path: ~/.cache/pip
      mode: read-only # Shared cache from L1
  capabilities:
    - git-sign # Allow SSH Proxy Bridge
    - fs-reflink # Allow instant copy-on-write
```

---

## 6. Implementation Roadmap (Final)

| Task                    | Component                              | Priority | Status            |
| :---------------------- | :------------------------------------- | :------- | :---------------- |
| **SHM Race Track**      | `crates/thegent-shm`                   | P1       | Research Complete |
| **Predictive Throttle** | `orchestration/resource_management.py` | P1       | Research Complete |
| **SSH Proxy Bridge**    | `infra/identity_proxy.py`              | P2       | Research Complete |
| **DSP Parser**          | `governance/policy_loader.py`          | P2       | Research Complete |

---

## 7. Conclusion

This architecture makes `thegent` the most performant and secure agentic workstation environment in 2026. By combining **Nested Isolation** with **Predictive Resource Governance** and **SHM-backed CLI-Share**, we eliminate the overhead of multi-tenancy while maximizing safety.
