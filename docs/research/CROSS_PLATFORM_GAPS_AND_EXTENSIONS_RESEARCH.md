<DONE>
# Cross-Platform Gaps and Extensions — Research & Plan

**Purpose:** Fill holes in existing cross-platform, remote compute, and multi-tenant plans. Extend with POSIX+pwsh dual-shell strategy, remote compute implementation detail, and OS-level agent primitives.

**Date:** 2026-02-16
**Status:** Research & Planning
**Extends:** CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md, HYBRID_ENV_IMPLEMENTATION_PLAN.md, CROSS_PLATFORM_MULTI_TENANT_IMPLEMENTATION_PLAN.md

---

## 1. Gap Summary

| Gap                                       | Current State                                                          | This Doc |
| ----------------------------------------- | ---------------------------------------------------------------------- | -------- |
| **POSIX + pwsh dual-shell**               | WSL2 for POSIX; PowerShell for Windows automation; no unified strategy | §2       |
| **Remote compute implementation**         | Phase 4 planned; `thegent run --remote` not specified                  | §3       |
| **OS-level agent primitives**             | Desktop automation = API integration; no "extend OS" design            | §4       |
| **Agents as first-class OS principals**   | Sub-user, OS user; no PAM/auth provider design                         | §5       |
| **Real-time multi-tenant OS integration** | Coordination via locks; no kernel/OS extension                         | §6       |

---

## 2. POSIX + pwsh Dual-Shell Strategy

### 2.1 Problem

- **Hooks:** Bash scripts; POSIX-compatible
- **Windows:** Native = PowerShell; WSL2 = Bash
- **Agent execution:** May need to run bash on Windows (WSL2) or PowerShell on Linux (pwsh-core)
- **Desktop automation:** Windows requires PowerShell for UI Automation, `New-LocalUser`, etc.

### 2.2 Shell Selection Matrix

| Context                | macOS                 | Linux         | Windows (native)     | Windows (WSL2)   |
| ---------------------- | --------------------- | ------------- | -------------------- | ---------------- |
| **Hooks**              | Bash                  | Bash          | WSL2 Bash or pwsh    | Bash             |
| **Agent subprocess**   | Bash/zsh              | Bash          | pwsh or WSL2 Bash    | Bash             |
| **OS user creation**   | dscl/useradd          | useradd       | pwsh (New-LocalUser) | N/A (use native) |
| **Desktop automation** | AppleScript/osascript | Python+AT-SPI | pwsh + UI Automation | N/A              |
| **thegent CLI**        | Python (any)          | Python (any)  | Python (any)         | Python (any)     |

### 2.3 Implementation Plan

#### P2.3.1: Shell Detection Utility

```python
# src/thegent/infra/shell_detection.py
def get_preferred_shell(platform: str, context: Literal["hooks", "agent", "os_admin", "desktop"]) -> str:
    """Return preferred shell for context."""
    if platform == "windows" and context == "os_admin":
        return "pwsh"
    if platform == "windows" and context == "desktop":
        return "pwsh"
    if platform == "windows" and context in ("hooks", "agent"):
        # Prefer WSL2 bash if available
        return "wsl-bash" if _wsl_available() else "pwsh"
    return "bash"
```

#### P2.3.2: Cross-Platform Script Execution

- **Hooks:** Always invoke via `bash -c` or `wsl bash -c` on Windows
- **Agent subprocess:** Configurable `agent_shell`: `bash` | `pwsh` | `wsl-bash`
- **OS admin:** Platform-specific (pwsh on Windows, bash+sudo on Unix)

#### P2.3.3: pwsh Fallback for Hooks

- Add `hooks/lib/pwsh_adapters.ps1` for Windows-native hook logic
- Hooks that need Windows-specific behavior call `pwsh -File` for that block
- Document: `docs/reference/POSIX_PWSH_SHELL_STRATEGY.md`

### 2.4 Tasks (Add to CROSS_PLATFORM_MULTI_TENANT_IMPLEMENTATION_PLAN)

| ID        | Task                                                     | Phase   | Depends   |
| --------- | -------------------------------------------------------- | ------- | --------- |
| P-SHELL-1 | Create `shell_detection.py` with `get_preferred_shell()` | Phase 1 | None      |
| P-SHELL-2 | Add `THGENT_AGENT_SHELL` config (bash\|pwsh\|wsl-bash)   | Phase 1 | P-SHELL-1 |
| P-SHELL-3 | Update hook dispatcher to use shell detection on Windows | Phase 2 | P-SHELL-1 |
| P-SHELL-4 | Create `docs/reference/POSIX_PWSH_SHELL_STRATEGY.md`     | Phase 1 | None      |

---

## 3. Remote Compute Implementation Detail

### 3.1 Current Gap

HYBRID_ENV Phase 4 specifies:

- SSH setup
- "Create remote execution wrapper script"
- "Test `thegent run --remote windows-pc`"
- No spec for: session registry on remote, agent routing, MCP reachability

### 3.2 Remote Execution Architecture

```
Mac (client)                    Windows PC (compute)
┌─────────────────────┐        ┌─────────────────────────────────────┐
│ thegent run --remote│        │ thegent (installed via sync)         │
│   windows-pc "X"    │  SSH   │ - run_registry.jsonl (remote)        │
│        │            │ ──────>│ - MCP server (optional, port 3847)   │
│        v            │        │ - CLIProxy (optional, port 8317)     │
│ ssh windows-pc      │        │ - process-compose                    │
│   "thegent run -d   │        │ - Docker Desktop                     │
│    /path X"         │        └─────────────────────────────────────┘
└─────────────────────┘
```

### 3.3 Design Decisions

| Decision            | Choice                                 | Rationale                              |
| ------------------- | -------------------------------------- | -------------------------------------- |
| **Session storage** | Remote `run_registry.jsonl` on Windows | Sessions live where work runs          |
| **MCP server**      | Optional on remote; Mac MCP can proxy  | Reduce latency for chat clients on Mac |
| **Path mapping**    | `D:\kush\` ↔ `~/kush/` via sync       | Syncthing keeps in sync                |
| **Agent routing**   | `--remote HOST` spawns on HOST via SSH | Explicit; no auto-routing yet          |

### 3.4 CLI Interface

```bash
# Run on remote Windows PC
thegent run --remote windows-pc -d D:/kush/thegent "Build project" gemini

# Background on remote
thegent bg --remote windows-pc -d D:/kush/thegent "Heavy test suite" codex

# List remote sessions
thegent ps --remote windows-pc

# Stream logs from remote
thegent logs --remote windows-pc <session_id>
```

### 3.5 Implementation Tasks (Extend HYBRID_ENV Phase 4)

| ID      | Task                                                         | Est.   | Depends |
| ------- | ------------------------------------------------------------ | ------ | ------- |
| P4.2.1a | Define `RemoteHost` config (host, user, path_mapping)        | 30 min | None    |
| P4.2.1b | Implement `run_remote(host, cwd, prompt, agent)` via SSH     | 1.5 hr | P4.1.7  |
| P4.2.1c | Implement `ps_remote(host)`, `logs_remote(host, session_id)` | 1 hr   | P4.2.1b |
| P4.2.2  | Add `~/.thegent/remote_hosts.yaml` for host definitions      | 30 min | P4.2.1a |
| P4.2.3  | Path mapping: `D:\kush\` ↔ `~/kush/` in prompts             | 30 min | P4.2.1b |
| P4.2.4  | Document `thegent run --remote` in CLI help and guides       | 30 min | P4.2.3  |

### 3.6 Remote Session Registry

- **Location:** `~/.thegent/sessions/` on remote host (or `D:\kush\.thegent\sessions\`)
- **Sync:** Optional: sync `.thegent/sessions/` via Syncthing for unified view
- **Alternative:** `thegent ps --remote` SSH-executes `thegent ps` on remote and parses output

---

## 4. OS-Level Agent Primitives (Extending/Modifying OS)

### 4.1 Scope

"Extending or modifying OS" for real-time multi-tenant agent execution can mean:

| Level        | Mechanism                                | thegent Relevance                     |
| ------------ | ---------------------------------------- | ------------------------------------- |
| **Process**  | subprocess, cgroups, namespaces          | Already: subprocess; planned: cgroups |
| **User**     | OS users, user namespaces                | Planned: OS user creation             |
| **Resource** | cgroups v2, rlimits, Windows Job Objects | Gap: no explicit plan                 |
| **Kernel**   | Custom kernel modules, eBPF              | Out of scope                          |
| **Auth**     | PAM, Windows auth providers              | Gap: no plan                          |

### 4.2 Resource Containment (Fill Gap)

#### Linux: cgroups v2

```python
# src/thegent/infra/resource_containment.py (future)
def create_agent_cgroup(agent_id: str, limits: ResourceLimits) -> Path:
    """Create cgroup for agent with memory/CPU limits."""
    # cgroups v2: /sys/fs/cgroup/thegent/agent-{id}/
    # memory.max, cpu.max
```

**Tasks:**

- [ ] Add `ResourceLimits` (memory_mb, cpu_percent)
- [ ] Implement cgroup creation for Linux (requires root or user cgroups)
- [ ] Integrate with `AgentRunner` when `isolation_mode=osuser` or new `cgroup` mode

#### Windows: Job Objects

```python
# Windows: CreateJobObject, AssignProcessToJobObject
# Limit: JOBOBJECT_EXTENDED_LIMIT_INFORMATION (memory, CPU)
```

**Tasks:**

- [ ] Research Windows Job Objects API (ctypes or pywin32)
- [ ] Implement `create_agent_job(agent_id, limits)` for Windows
- [ ] Assign agent subprocess to job

### 4.3 User Namespaces (Linux)

- **Use case:** Run agents as root-in-namespace without host root
- **Mechanism:** `unshare(CLONE_NEWUSER)` + uid/gid mapping
- **Complexity:** High; Docker already provides this
- **Recommendation:** Defer to Docker isolation; document as future option

### 4.4 Tasks (Add to Implementation Plan)

| ID     | Task                                                        | Phase   | Effort          |
| ------ | ----------------------------------------------------------- | ------- | --------------- |
| P-OS-1 | Design `ResourceLimits` and `ResourceContainment` interface | Phase 2 | 2-3 tool calls  |
| P-OS-2 | Implement Linux cgroups v2 containment (opt-in)             | Phase 3 | 8-12 tool calls |
| P-OS-3 | Implement Windows Job Objects containment (opt-in)          | Phase 3 | 8-12 tool calls |
| P-OS-4 | Add `thegent run --memory-limit 512 --cpu-limit 50`         | Phase 3 | 4-6 tool calls  |

---

## 5. Agents as First-Class OS Principals

### 5.1 Current State

- **Sub-user:** No OS identity; runs as host user
- **OS user:** Real user account; `useradd` / `New-LocalUser`
- **Gap:** No integration with OS auth (PAM, Windows login), no "agent login" concept

### 5.2 Options for Deeper OS Integration

| Option                         | Description                                    | Effort | Use Case               |
| ------------------------------ | ---------------------------------------------- | ------ | ---------------------- |
| **A. Status quo**              | Sub-user or OS user; no auth integration       | —      | Current                |
| **B. PAM module (Linux)**      | Custom PAM module for "agent" auth             | High   | Agent-as-service login |
| **C. Windows Service Account** | Run thegent as Windows Service under agent SID | Medium | Production Windows     |
| **D. systemd scope (Linux)**   | `systemd-run --scope` for agent processes      | Low    | Resource containment   |
| **E. macOS launchd**           | Per-agent launchd plist                        | Medium | Agent daemons on Mac   |

### 5.3 Recommendation

- **Short term:** B, C, D, E are out of scope; focus on sub-user + OS user
- **Medium term:** Add **D (systemd scope)** for Linux when `isolation_mode=osuser` — gives resource containment without cgroups implementation
- **Long term:** Document B, C as "enterprise deployment" options in `docs/reference/AGENT_OS_PRINCIPALS_DEPTH.md`

### 5.4 Tasks

| ID       | Task                                                   | Phase   | Effort         |
| -------- | ------------------------------------------------------ | ------- | -------------- |
| P-AUTH-1 | Create `docs/reference/AGENT_OS_PRINCIPALS_DEPTH.md`   | Phase 2 | 4-6 tool calls |
| P-AUTH-2 | Add `systemd-run --scope` option for Linux osuser mode | Phase 3 | 4-6 tool calls |

---

## 6. Real-Time Multi-Tenant OS Integration

### 6.1 What "Real-Time" Means Here

- **Not** hard real-time (avionics, medical)
- **Soft real-time:** User + agents interact without perceptible conflict; coordination latency < 100ms
- **Concurrent:** User typing while agent automates different app; no blocking

### 6.2 Coordination Primitives (Extend Existing)

| Primitive             | Current                      | Extension                                              |
| --------------------- | ---------------------------- | ------------------------------------------------------ |
| **File lease**        | EditLeaseManager             | Tenant-aware (done in main research)                   |
| **UI lock**           | DesktopAutomationCoordinator | User activity detection (planned)                      |
| **Process namespace** | None                         | Per-agent cgroup/job (new)                             |
| **Desktop/space**     | None                         | macOS: detect Space; switch before automation          |
| **Input focus**       | None                         | Track focused app; deny automation if user app focused |

### 6.3 macOS Space Awareness (New)

```python
# macOS: detect current Space (desktop)
# AppleScript: "tell application \"System Events\" to get index of current desktop"
# Before automation: switch to target app's Space if needed
# Avoid: automating in background Space while user in foreground
```

**Task:** Add to `desktop_automation/macos.py` — `get_current_space()`, `switch_to_space(n)` (optional), `is_user_space_active()`.

### 6.4 Windows Session Awareness (New)

- **Problem:** RDP session vs console; multiple users
- **Solution:** Detect `SessionId`; agent automation only in same session as user (or configurable)
- **API:** `WTSGetActiveConsoleSessionId`, `ProcessIdToSessionId`

**Task:** Add to `desktop_automation/windows.py` — `get_active_session_id()`, `is_same_session_as_user()`.

### 6.5 Tasks (Add to Implementation Plan)

| ID     | Task                                                | Phase   | Effort         |
| ------ | --------------------------------------------------- | ------- | -------------- |
| P-RT-1 | Add macOS Space detection to desktop automation     | Phase 3 | 4-6 tool calls |
| P-RT-2 | Add Windows Session detection to desktop automation | Phase 3 | 4-6 tool calls |
| P-RT-3 | Deny automation if user app focused (configurable)  | Phase 3 | 2-4 tool calls |

---

## 7. Consolidated Extension Plan

### 7.1 New Sections for CROSS_PLATFORM_MULTI_TENANT_IMPLEMENTATION_PLAN

Add after Phase 5:

**Phase 6: Shell Strategy & Remote Compute**

- P-SHELL-1 through P-SHELL-4 (from §2)
- P4.2.1a through P4.2.4 (from §3) — or merge into HYBRID_ENV Phase 4

**Phase 7: OS-Level Primitives**

- P-OS-1 through P-OS-4 (from §4)
- P-AUTH-1, P-AUTH-2 (from §5)
- P-RT-1 through P-RT-3 (from §6)

### 7.2 New Documents to Create

| Document                                             | Purpose                                            |
| ---------------------------------------------------- | -------------------------------------------------- |
| `docs/reference/POSIX_PWSH_SHELL_STRATEGY.md`        | Shell selection matrix, config, hook compatibility |
| `docs/reference/AGENT_OS_PRINCIPALS_DEPTH.md`        | PAM, Windows Service, systemd scope options        |
| `docs/plans/REMOTE_COMPUTE_IMPLEMENTATION_DETAIL.md` | Full spec for `thegent run --remote`               |

### 7.3 Updates to Existing Docs

| Document                                                | Update                                                                              |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| HYBRID_ENV_IMPLEMENTATION_PLAN                          | Add P4.2.1a–P4.2.4 detail from §3                                                   |
| CROSS_PLATFORM_MULTI_TENANT_IMPLEMENTATION_PLAN         | Add Phase 6, 7; P-SHELL, P-OS, P-AUTH, P-RT tasks                                   |
| CROSS_PLATFORM_MASTER_INDEX                             | Add this doc, new reference docs                                                    |
| CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH | Add §40.3 item: "POSIX+pwsh strategy"; "Remote compute spec"; "OS-level primitives" |

---

## 8. References

- [CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md](./CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md)
- [CROSS_PLATFORM_MULTI_TENANT_IMPLEMENTATION_PLAN.md](../plans/CROSS_PLATFORM_MULTI_TENANT_IMPLEMENTATION_PLAN.md)
- [HYBRID_MAC_WIN_DEV_ENVIRONMENT.md](../architecture/HYBRID_MAC_WIN_DEV_ENVIRONMENT.md)
- [HYBRID_ENV_IMPLEMENTATION_PLAN.md](../plans/HYBRID_ENV_IMPLEMENTATION_PLAN.md)
- [AGENT_SANDBOXING_ARCHITECTURE.md](../architecture/AGENT_SANDBOXING_ARCHITECTURE.md)

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added gap analysis patterns
2. Added extension examples
3. Enhanced cross-references

### Cross-References Added

- CROSS_PLATFORM_RESEARCH_INDEX.md
- CROSS_PLATFORM_ADVANCED_PATTERNS.md

### Practical Additions

- Gap templates
- Extension configurations

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md](./CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md) - Consolidated guide
- [CROSS_PLATFORM_ADVANCED_PATTERNS.md](./CROSS_PLATFORM_ADVANCED_PATTERNS.md) - Advanced patterns
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
