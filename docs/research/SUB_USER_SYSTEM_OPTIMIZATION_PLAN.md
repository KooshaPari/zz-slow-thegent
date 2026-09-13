<DONE>
# Research: Sub-User System Optimization & Polish (Phase 1.5)

**Date:** 2026-02-19
**Status:** Planning
**Priority:** P1
**Focus:** Enhancing the current `SubUserIsolationProvider` for high-performance agent-as-user operations before the full OS User migration.

---

## 1. Executive Summary

The current "Sub-user" system uses deterministic UID mapping and temporary home directories. While functional, it lacks true kernel-level isolation and high-performance lifecycle management. This plan outlines the "Polish & Optimization" phase to make the sub-user system production-ready for thegent agents.

**Key Goals:**

- **Zero-Copy Home Dirs:** Use OverlayFS or Reflinks to create agent environments in <10ms.
- **Resource Guardrails:** Implement per-agent `ulimit` and `cgroups` (where available).
- **Identity Enforcement:** True `setuid`/`setgid` execution (conditional root requirement).
- **Network Scoping:** Restricted outbound access for untrusted sub-users.

---

## 2. Advanced Lifecycle Management

### 2.1 OverlayFS Home Directories (Linux)

Instead of `shutil.copytree` or simple `mkdir`, use OverlayFS to mount a canonical "Agent Base" home directory.

- **Lower Dir:** `/opt/thegent/skel/agent-base` (Read-only)
- **Upper Dir:** `/tmp/thegent/workspaces/<run_id>` (Writable layer)
- **Benefit:** Instant startup, minimal disk usage (only writes are stored), absolute environment parity.

### 2.2 Reflink Bootstrapping (macOS APFS / Btrfs)

On macOS, use APFS `clonefile` (reflinks) to create home directories.

- **Benefit:** Instant "copy" of a 1GB home directory with 0 bytes of initial disk usage.

### 2.3 UID Pool Lease Manager

Move from `hash(tenant_id)` to a stateful `UidLeaseManager`.

- **Mechanism:** Persistent registry of active UIDs.
- **Recycling:** UIDs are released back to the pool after `cleanup_tenant`.
- **Conflict Avoidance:** Prevents collisions inherent in hash-based mapping.

---

## 3. Resource & Security Guardrails

### 3.1 Integrated ulimits

The `SubUserIsolationProvider` will automatically apply limits via `resource.setrlimit` in the `preexec_fn` of subprocesses:

- `RLIMIT_NOFILE`: Max 1024 (prevent FD leaks).
- `RLIMIT_NPROC`: Max 50 (prevent fork bombs).
- `RLIMIT_AS`: Memory capping based on the Harness Card p95 data.

### 3.2 Cgroup v2 Integration (Linux)

If running on a system with cgroups v2 enabled:

- Create `/sys/fs/cgroup/thegent/agents/<tenant_id>`.
- Set `memory.max` and `cpu.max`.
- Ensures agents cannot starve the host user's personal session.

### 3.3 Network Namespaces (Linux Opt-in)

For "Untrusted" agent roles:

- Run in a private network namespace with only a `lo` interface or a scoped `veth` bridge.
- Prevents agents from accessing local network resources (e.g., your NAS, printer, or local dev servers) unless explicitly permitted.

---

## 4. QOL & Environment Injection

### 4.1 "Agent Profile" Injection

The system should automatically inject a `.zshenv` and `.zshrc.agent` into the temp home dir:

- **Fast Path:** Only source essential paths (`~/.local/bin`, `node_modules/.bin`).
- **Silent Mode:** Force `ZSH_AUTOSUGGEST_STRATEGY=none` and minimal prompts to save agent tokens/cycles.
- **Alias Shims:** Inject `git` shims that automatically add the `--owner` tag.
- **Pre-execution Hooks:** Record command start times for the `BottleneckDetector`.

### 4.2 PowerShell "Agent Profile" (pwsh)

Mirroring the Zsh experience for Windows-native agents:

- **Module Sideloading:** Automatically import `thegent` QOL modules into the agent's `$PROFILE`.
- **Command Logging:** Redirect all PowerShell streams (Success, Error, Warning, Verbose, Debug) to a structured JSON log for agent auditability.
- **Execution Policy:** Scoped bypass for agent-specific scripts.

---

## 5. Windows-Specific Polish

### 5.1 Job Objects for Sub-users

Use Windows **Job Objects** to wrap agent processes:

- Cap total CPU cycles.
- Hard memory limits.
- Automatic termination of all child processes when the "tenant" is cleaned up.

### 5.2 SID to UID Mapping (WSL2 Interop)

- **Mechanism:** Maintain a mapping between Windows SIDs and WSL2 UIDs (using `thegent.infra.wsl_interop.map_sid_to_uid`).
- **Sync:** Use `wslpath` and `Get-LocalUser` to ensure consistent file ownership when agents cross the boundary.
- **Automation:** Automatically generate `/etc/wsl.conf` entries for the host user to support metadata and permissions.

### 5.3 Fast-Path WSL2 Translation (`thegent.infra.wsl_interop`)

- **Optimization:** Instead of spawning `wslpath` for every operation (which is slow), use regex-based conversion for common `/mnt/` style paths.
- **Env Sync:** Bidirectional sync of `THEGENT_*` environment variables using `$env:WSLENV`.
- **Automatic Env Mapping:** Detect `$env:USERPROFILE` and map to `/mnt/c/Users/...` in the sub-user context.

---

## 6. Windows QOL & Canonical Setup

### 6.1 Canonical PowerShell Profile (`$PROFILE`)

Thegent provides a managed PowerShell profile that mirrors the Zsh experience:

- **Aliases:** `rg` for `ripgrep`, `fd` for `fd-find`, `g` for `git`, etc.
- **Theme:** Starship integration.
- **Integrations:** `zoxide`, `fzf` (via `PSFzf`), `mise` (shell activation).
- **thegent Hooks:** Automatic loading of `thegent` shell hooks for command interception.

### 6.2 WSL2 Path Translation Layer

Optimize the translation between Windows and WSL2:

- **Fast-Path:** Use pre-calculated mount points (`/mnt/c/` vs `C:\`) instead of calling `wslpath` for every operation.
- **Env Sync:** Bidirectional sync of `THEGENT_*` environment variables.

---

## 6. Implementation Roadmap (Phase 1.5 - 2.0)

| Task                            | Component                        | Effort | Priority |
| :------------------------------ | :------------------------------- | :----- | :------- |
| **UID Lease Manager**           | `isolation/uid_pool.py`          | 2d     | P1       |
| **OverlayFS/Reflink Adapter**   | `isolation/vfs.py`               | 3d     | P1       |
| **preexec_fn Guardrails**       | `isolation/sub_user_provider.py` | 1d     | P1       |
| **Zsh Agent Profile Generator** | `shell/agent_profile.py`         | 2d     | P2       |
| **L1 OS User Manager**          | `infra/os_user_manager.py`       | 5d     | P1       |
| **Windows Job Object Wrapper**  | `isolation/windows_job.py`       | 3d     | P2       |
| **Landlock T3 Sandbox**         | `isolation/linux_sandbox.py`     | 4d     | P2       |

---

## 7. Related Research

- [NESTED_HYBRID_ISOLATION_ARCHITECTURE.md](./NESTED_HYBRID_ISOLATION_ARCHITECTURE.md) - Deep-dive into L1/L2 nesting and T1-T4 isolation tiers.
- [WORKSTATION_QOL_MASTER_PLAN.md](./WORKSTATION_QOL_MASTER_PLAN.md) - Overall system vision.

---

## 8. Success Metrics

- **Startup Latency:** `<50ms` from `allocate_tenant` to first command execution.
- **Isolation Strength:** 100% of fork-bomb attempts caught by `RLIMIT_NPROC`.
- **Environment Parity:** `thegent doctor` passes identically inside a sub-user context as it does in the host.
