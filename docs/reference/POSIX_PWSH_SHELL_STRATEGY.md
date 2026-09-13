# POSIX + pwsh Shell Strategy

**Purpose:** Unified strategy for shell selection across macOS, Linux, and Windows (POSIX vs PowerShell).

**Date:** 2026-02-16
**Extends:** CROSS_PLATFORM_GAPS_AND_EXTENSIONS_RESEARCH.md §2

---

## 1. Shell Selection Matrix

| Context                | macOS        | Linux         | Windows (native)     | Windows (WSL2) |
| ---------------------- | ------------ | ------------- | -------------------- | -------------- |
| **Hooks**              | Bash         | Bash          | WSL2 Bash or pwsh    | Bash           |
| **Agent subprocess**   | Bash/zsh     | Bash          | pwsh or WSL2 Bash    | Bash           |
| **OS user creation**   | dscl/useradd | useradd       | pwsh (New-LocalUser) | N/A            |
| **Desktop automation** | AppleScript  | Python+AT-SPI | pwsh + UI Automation | N/A            |
| **thegent CLI**        | Python       | Python        | Python               | Python         |

---

## 2. Configuration

```yaml
# ~/.thegent/config.yaml
shell:
  agent_shell: "bash" # bash | pwsh | wsl-bash
  hook_shell: "bash" # bash | pwsh | wsl-bash (Windows)
  os_admin_shell: "auto" # auto | pwsh (Windows) | bash (Unix)
```

**Environment:**

- `THGENT_AGENT_SHELL` — Override agent subprocess shell
- `THGENT_HOOK_SHELL` — Override hook execution shell (Windows)
- `THGENT_OS_ADMIN_SHELL` — Override OS admin commands

---

## 3. Hook Compatibility

### 3.1 POSIX Hooks (Default)

- Hooks in `hooks/*.sh` are Bash/POSIX
- On Windows: invoke via `wsl bash -c "..."` if WSL2 available
- Fallback: `pwsh -Command "..."` with adapter for hook logic (limited)

### 3.2 Windows-Native Hook Blocks

- For hooks that need Windows-specific logic, use:
  ```bash
  # In hook: detect Windows, call pwsh for block
  if [ "$THGENT_PLATFORM" = "windows" ]; then
    pwsh -File "$THGENT_ROOT/hooks/lib/pwsh_adapters.ps1" -Action "os_user_create" -Args "$@"
  else
    # POSIX path
  fi
  ```

### 3.3 Adapter Location

- `hooks/lib/pwsh_adapters.ps1` — Windows-native hook logic
- Functions: `Invoke-OsUserCreate`, `Invoke-DesktopAutomation`, etc.

---

## 4. Agent Subprocess Shell

- **bash:** Default on macOS, Linux, WSL2
- **pwsh:** Use when agent needs PowerShell cmdlets (e.g. Azure, Exchange)
- **wsl-bash:** Use on Windows native when agent runs POSIX scripts

---

## 5. References

- [CROSS_PLATFORM_GAPS_AND_EXTENSIONS_RESEARCH.md](../research/CROSS_PLATFORM_GAPS_AND_EXTENSIONS_RESEARCH.md)
- [CROSS_PLATFORM_MULTI_TENANT_QUICK_REFERENCE.md](./CROSS_PLATFORM_MULTI_TENANT_QUICK_REFERENCE.md)

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
