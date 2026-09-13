<DONE>
# Research: Nested & Hybrid Isolation Architecture (L1/L2)

**Date**: 2026-02-19
**Status**: Research & Design
**Focus**: Deep-dive into L1 (OS User) and L2 (Sub-user) nesting, hybrid isolation, and minimal-overhead sandboxing.

---

## 1. The L1/L2 Nesting Model

To balance performance, identity, and security, `thegent` uses a nested hierarchy:

### 1.1 Layer 1: The OS User (Persistence & Identity)

- **Role**: Acts as the "Team Lead" or "Manager" principal.
- **Implementation**: A real system account (e.g., `tg_frontend_lead`).
- **Characteristics**:
  - Persistent `/home/tg_frontend_lead`.
  - Real entry in `/etc/passwd` (Linux) or Directory Service (macOS/Windows).
  - Owns long-lived artifacts (node_modules, build caches).
  - **Permissions**: Can be granted specific `sudo` rules or group access to host project files.

### 1.2 Layer 2: The Sub-user / Instance (Ephemeral & Isolated)

- **Role**: Acts as the "Specialist" execution context.
- **Implementation**: A sub-process spawned by L1 with additional restrictions.
- **Characteristics**:
  - Ephemeral `$HOME` (via OverlayFS or Reflink).
  - Restricted permissions (cannot write to L1's persistent config).
  - **Isolation**: Minimal overhead via kernel namespaces or low-integrity tokens.

### 1.3 The Hybrid Flow

1. **Host User** (You) triggers a project task.
2. **thegent Orchestrator** identifies the task requires "Frontend" expertise.
3. **Orchestrator** switches to **L1 OS User** (`tg_frontend_lead`).
4. **L1 User** spawns multiple **L2 Sub-users** (e.g., `specialist_auth`, `specialist_ui`).
5. **L2 Agents** execute in parallel, sharing L1's cache but isolated from each other's temporary workspace.

---

## 2. Hybrid Isolation Tiers

Different tasks require different levels of paranoia. `thegent` implements four tiers of isolation:

| Tier   | Name         | Technology              | Overhead | Use Case                                         |
| :----- | :----------- | :---------------------- | :------- | :----------------------------------------------- |
| **T1** | **Process**  | Env Vars + ulimit       | <1ms     | Trusted local scripts, formatters.               |
| **T2** | **Sub-user** | UID Map + OverlayFS     | <10ms    | General coding, research, local dev.             |
| **T3** | **Sandbox**  | Landlock / AppContainer | <20ms    | Running untrusted npm/pip packages.              |
| **T4** | **Hardware** | Firecracker / gVisor    | >500ms   | Running unknown binary blobs / malware analysis. |

### 2.1 Linux: Landlock & Bubblewrap (T3)

- **Landlock**: A stackable LSM (Linux Security Module) that allows a process (the agent) to restrict its own access to the filesystem.
  - _Benefit_: No root required. Extremely low overhead.
  - _Mapping_: L2 agent can "lock" itself into `$PROJECT_ROOT` and its own `$HOME`.
- **Bubblewrap**: Uses namespaces to create a sandbox.
  - _Mapping_: Provides private `/tmp`, `/dev`, and `/proc`.

### 2.2 Windows: AppContainer & Job Objects (T3)

- **AppContainer**: Uses Low Integrity Levels (IL) and Capabilities.
  - _Mapping_: L2 agent is restricted from accessing the registry, network, or user files outside of a specific "Package Sid" directory.
- **Windows Sandbox**: Lightweight VM for T4 isolation.

---

## 3. High-Performance Filesystem Interop

The biggest bottleneck in isolation is often I/O overhead (e.g., Docker Desktop on macOS).

### 3.1 Zero-Copy Clones (Host -> L1 -> L2)

- **OverlayFS (Linux)**:
  - **Lower**: Project Root (Read-only for Agent).
  - **Upper**: Agent Workspace (Writable).
- **Reflinks (macOS/APFS)**:
  - `cp -c` equivalent for home directories. Instant duplication of build artifacts without disk cost.

### 3.2 Security Scoping (Bind Mounts)

Instead of giving an agent access to the whole disk, we "mount" only what is needed:

- `/mnt/project` -> `$PROJECT_ROOT`
- `/mnt/cache` -> `~/.cache/thegent/shared`

---

## 4. OS Interop & Communication

How does the L1 "Lead" coordinate L2 "Specialists"?

### 4.1 Signal Propagation

- **Process Groups**: L1 creates a new PGID for its L2 specialists.
- **Graceful Shutdown**: `SIGTERM` sent to the PGID ensures all specialists cleanup their OverlayFS mounts before L1 exits.

### 4.2 Environment structured passing

- **THEGENT_CONTEXT**: A JSON file path injected into the agent's environment.
- **Metadata**: Contains parent UID, trace ID, and resource quotas.

---

## 5. Security Posture

### 5.1 No-Network Default

T3/T4 agents run with `CLONE_NEWNET` (Linux) or disabled network capabilities (Windows) by default.

- **Proxy Bridge**: If an agent needs to fetch documentation, it must request a "URL Fetch" from the L1 Lead, which acts as a security proxy.

### 5.2 Escape Prevention

- **User Namespaces**: Prevents L2 from seeing or signaling L1 processes.
- **No-New-Privs**: Ensures `setuid` binaries (like `sudo`) cannot be used to escape the sandbox.

---

## 6. Implementation Strategy (Phase 2.0)

1. **L1 OS User Manager**: Automate `useradd` / `dscl` / `New-LocalUser`.
2. **Landlock/AppContainer Wrapper**: A Rust-based utility to "drop" privileges before executing the Python agent.
3. **VFS Mount Manager**: Orchestrate OverlayFS and Bind mounts.
4. **Identity Bridge**: SSS (Shared Session Socket) for agents to communicate within the same L1 context.
