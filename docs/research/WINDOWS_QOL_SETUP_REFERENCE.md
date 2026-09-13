<DONE>
# System Setup & Workstation QOL: Windows 11 (Native & WSL2)

**Date:** 2026-02-19
**Status:** Canonical Reference

---

## 1. Environment Architecture

The workstation QOL strategy for Windows is built on a **Dual-Shell Architecture** that treats **PowerShell (pwsh)** and **POSIX (bash/zsh)** as first-class OS principals. This enables a consistent experience across the "OS boundary."

### 1.1 Native Windows 11 / pwsh

- **Shell:** PowerShell 7.4+ (`pwsh`)
- **Profile:** Managed via `thegent/shell/thegent.profile.ps1`.
- **Package Manager:** `winget`, `scoop`, or `chocolatey`.
- **Runtime:** `uv`, `mise`, `go`, `rustup`.

### 1.2 WSL2 (Ubuntu 22.04 / 24.04)

- **Shell:** Zsh with TheGent bundle.
- **Path Interop:** Fast-path translation using regex (see `thegent.infra.wsl_interop`).
- **Identity Sync:** Mapping SIDs to UIDs for shared file ownership.

---

## 2. Bootstrapping (TheGent Installer)

The bootstrap uses `install.ps1` for native Windows and `install.sh` for WSL2.

**Native Windows:**

```powershell
irm https://raw.githubusercontent.com/kooshapari/thegent/main/scripts/install.ps1 | iex
```

**WSL2:**

```bash
curl -fsSL https://raw.githubusercontent.com/kooshapari/thegent/main/scripts/install.sh | bash
```

---

## 3. Workstation QOL: Canonical Toolset

| Tool         | Windows Native   | WSL2             | Role                 |
| :----------- | :--------------- | :--------------- | :------------------- |
| **Terminal** | Windows Terminal | Windows Terminal | Modern CLI Host      |
| **Editor**   | VS Code / nvim   | nvim / VS Code   | Development          |
| **Search**   | `ripgrep` (rg)   | `ripgrep` (rg)   | Fast find            |
| **Files**    | `fd-find` (fd)   | `fd-find` (fd)   | Better find          |
| **Viewer**   | `bat`            | `bat`            | Better cat           |
| **Nav**      | `zoxide`         | `zoxide`         | Smart cd             |
| **Prompt**   | `starship`       | `starship`       | Context-aware prompt |
| **Versions** | `mise`           | `mise`           | Tooling manager      |

---

## 4. Agent Isolation on Windows

Thegent implements a specialized isolation layer for Windows agents using **Sub-user Identity** and **Job Objects**.

- **Identity:** UIDs are mapped to local SIDs (or Virtual Service Accounts).
- **Resource Limits:** Windows Job Objects enforce hard memory/CPU caps and ensure 100% child-process cleanup.
- **Home Dirs:** Temporary home directories are created in `$env:TEMP\thegent\workspaces`.

---

## 5. thegent PowerShell Profile Highlights

The profile (`thegent/shell/thegent.profile.ps1`) includes:

- **Command Interception:** Hooking native Windows commands to provide proactive help.
- **Path Normalization:** Automatic handling of `C:\` vs `/mnt/c/` style paths.
- **Unified Aliases:** Consistent `g`, `k`, `v`, `ls`, `cat` experience.
- **WSL Interop:** `Use-Wsl` and `Resolve-WslPath` helpers.

---

## 6. Implementation Roadmap

1. **Phase 2:** Complete the Rust-based Shell Dispatcher for native Windows.
2. **Phase 3:** Implement the Windows Job Object wrapper in `isolation/windows_job.py`.
3. **Phase 4:** Expand the Desktop Automation provider using `pywinauto` and UI Automation.
4. **Phase 5:** Implement the full OS User migration specifically for Windows using `New-LocalUser`.
