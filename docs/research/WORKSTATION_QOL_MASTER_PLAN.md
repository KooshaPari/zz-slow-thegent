<DONE>
# Workstation QOL & Agent-as-User Master Plan

**Date**: 2026-02-19
**Status**: Phase 1.5 (Active Optimization)
**Platform Scope**: macOS (Darwin), Linux (inc. WSL2), Windows 11 (Native)

---

## 1. Vision: Agents as First-Class OS Principals

TheGent treats AI agents not as simple subprocesses, but as semi-privileged OS users with their own identities, home directories, and resource quotas. This enables true multi-tenancy on a single workstation, allowing you to run multiple research/dev tasks in parallel without environment bleed.

---

## 2. Current Implementation: The Sub-User System (Phase 1.0 - 1.5)

### 2.1 Identity & Isolation

- **Deterministic UID Pooling**: Agents are assigned persistent UIDs (2000-3000) based on their `tenant_id`. This is managed by `thegent.isolation.uid_pool`.
- **Ephemeral Home Directories**: Every agent run gets a fresh home directory using **VFS Optimizations**:
  - **Linux**: OverlayFS (Instant mount/unmount).
  - **macOS**: APFS Reflinks (Instant cloning).
  - **Windows**: Job Objects for process lifecycle management.
- **Resource Guardrails**: Kernel-level limits (ulimit/rlimit) for CPU, Memory (1GB default), and Process Count (100 default).

### 2.2 Dual-Shell Architecture

- **Dispatcher (Rust)**: Routes commands to the appropriate shell based on the environment (Zsh on POSIX, PowerShell on Windows).
- **Zsh Agent Profile**: Minimal, high-performance `.zshrc.agent` with structured execution logging.
- **PowerShell Profile**: A mirror experience for native Windows, including `Starship`, `zoxide`, and `mise` integration.

### 2.3 WSL2 Interop Layer

- **Path Translation**: Fast regex-based conversion between `C:\Users\...` and `/mnt/c/Users/...` (managed by `thegent.infra.wsl_interop`).
- **Identity Sync**: Research into mapping Windows SIDs to Linux UIDs for consistent file permissions across the OS boundary.

---

## 3. Future Roadmap: The "Real Full User" System (Phase 2.0)

### 3.1 OS-Level Account Creation (`OSUserIsolationProvider`)

Transitioning from UID emulation to real system accounts:

- **macOS**: Using `dscl` / `sysadminctl` to create hidden `_thegent_` accounts.
- **Linux**: Using `useradd` with `/sbin/nologin`.
- **Windows**: Using `New-LocalUser` (requires Admin-gated install).
- **Benefit**: True file-system permissions (chmod/ACL) and native OS auditing.

### 3.2 Desktop Automation (Workstation QOL)

Using the agent's identity to manage your physical workstation:

- **macOS**: AppleScript/Apple Events for automating Arc, Raycast, and Window Management.
- **Windows**: UI Automation API for configuring PowerToys, Snap Layouts, and Windows Terminal.
- **Linux**: AT-SPI / DBus for GNOME/KDE customization.

### 3.3 TheGent "Control Plane"

- **Agent Monitor**: A TUI/Dashboard showing all active tenants, their resource usage (from `ADVANCED_RESOURCE_MANAGEMENT_SYSTEM`), and live command traces.
- **Security Scoped Access**: Agents only get access to specific project folders via `Bind Mounts` or `Symbolic Links` in their isolated home dirs.

---

## 4. Pending Tasks & Decisions

| ID      | Task                                                            | Component    | Priority |
| :------ | :-------------------------------------------------------------- | :----------- | :------- |
| **W-1** | Generate Admin-gated `install.ps1` for Real Windows Users       | `scripts/`   | P1       |
| **W-2** | Finalize `wsl.conf` Auto-Generator for UID Mapping              | `infra/wsl/` | P2       |
| **Q-1** | Implement `thegent shell init` for automatic $PROFILE injection | `cli/`       | P1       |
| **I-1** | Create `dscl` adapter for macOS OS-User creation                | `isolation/` | P2       |

---

## 5. Verification: How to Test the System

- **Sub-user Check**: `thegent isolation check --mode sub-user`
- **Windows Profile Check**: `powershell -Command "Test-Path $PROFILE.TheGent"`
- **WSL2 Path Check**: `thegent infra translate-path "C:\Users\Name\Desktop"` (Should return `/mnt/c/Users/Name/Desktop`)
