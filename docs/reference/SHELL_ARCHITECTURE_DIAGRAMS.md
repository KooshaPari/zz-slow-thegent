# Cross-Platform Shell Architecture — Visual Diagrams

**Date:** 2026-02-19
**Purpose:** Visual reference for dual-shell architecture design
**Audience:** Architects, developers, reviewers

---

## 1. High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  thegent CLI / Python Code                      │
│           (High-level commands and workflows)                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ├─ Detect Platform (os.name, sys.platform)
                           │
        ┌──────────────────┴────────────────────┐
        │                                       │
   ┌────▼─────────────┐                 ┌─────▼──────────┐
   │  Platform Layer  │                 │  Shell Layer   │
   │  - MACOS         │                 │  - POSIX       │
   │  - LINUX         │                 │  - PowerShell  │
   │  - WINDOWS       │                 │  - WSL2        │
   │  - WSL2          │                 └────┬───────────┘
   └────┬─────────────┘                      │
        │                                    │
        └────────────────┬───────────────────┘
                         │
        ┌────────────────▼──────────────────┐
        │  ShellEnvironment (Python)        │
        │  - Detect shell type              │
        │  - Prepare environment            │
        │  - Cache detection                │
        └────┬───────────────────────────────┘
             │
        ┌────▼──────────────────────────────┐
        │  ShellDispatcher (Rust Binary)    │
        │  - Route to appropriate runner    │
        │  - Handle errors & timeouts       │
        │  - Log execution                  │
        └────┬───────────────────────────────┘
             │
      ┌──────┴──────────────┐
      │                     │
 ┌────▼────────────┐  ┌────▼──────────────┐
 │  POSIX Runner   │  │ PowerShell Runner │
 │  ├─ bash_lib.sh │  │ ├─ pwsh_lib.ps1   │
 │  ├─ hooks/*.sh  │  │ ├─ hooks/*.ps1    │
 │  └─ Error hdl   │  │ └─ Error hdl      │
 └────┬────────────┘  └────┬──────────────┘
      │                    │
      └────────┬───────────┘
               │
        ┌──────▼─────────────┐
        │ Shared Utilities   │
        │ - Validation       │
        │ - File operations  │
        │ - Logging          │
        │ - Process mgmt     │
        └────────────────────┘
```

---

## 2. Execution Flow: POSIX (bash/zsh)

```
User Action
    │
    ├─ Run Hook (e.g., "qa-check post-tool-use")
    │
┌───▼────────────────────────────────────────┐
│ Hook Dispatcher (Rust binary)              │
│ - Receives: hook_name, event, context      │
│ - Detects: Platform = Linux                │
│ - Detects: Shell = bash/zsh                │
└───┬────────────────────────────────────────┘
    │
    ├─ Checks: hooks/qa-check.sh exists
    │
┌───▼────────────────────────────────────────┐
│ bash -euo pipefail -c                      │
│  'source hooks/lib/bash_lib.sh             │
│   exec hooks/qa-check.sh'                  │
└───┬────────────────────────────────────────┘
    │
┌───▼────────────────────────────────────────┐
│ hooks/qa-check.sh                          │
│ - Sources bash_lib.sh                      │
│ - Calls: log_info(), validate_changes()    │
│ - Exits with status                        │
└───┬────────────────────────────────────────┘
    │
┌───▼────────────────────────────────────────┐
│ bash_lib.sh Functions                      │
│ - log_info()        → logs to stderr       │
│ - validate_changes()→ calls Python CLI     │
│ - check_lint()      → runs linter          │
│ - handle errors     → exit code             │
└───┬────────────────────────────────────────┘
    │
┌───▼────────────────────────────────────────┐
│ Python CLI (complex logic)                 │
│ - uv run thegent validate-changes          │
│ - uv run thegent lint                      │
│ - Returns: exit code                       │
└───┬────────────────────────────────────────┘
    │
    └─ Dispatcher captures exit code & logs
       Returns status to caller
```

---

## 3. Execution Flow: PowerShell (Windows)

```
User Action
    │
    ├─ Run Hook (e.g., "qa-check post-tool-use")
    │
┌───▼────────────────────────────────────────┐
│ Hook Dispatcher (Rust binary)              │
│ - Receives: hook_name, event, context      │
│ - Detects: Platform = Windows              │
│ - Detects: Shell = PowerShell              │
└───┬────────────────────────────────────────┘
    │
    ├─ Checks: hooks/qa-check.ps1 exists
    │
┌───▼────────────────────────────────────────┐
│ pwsh -NoProfile -File hooks/qa-check.ps1   │
│ -Arguments <hook_event> <context>          │
└───┬────────────────────────────────────────┘
    │
┌───▼────────────────────────────────────────┐
│ hooks/qa-check.ps1                         │
│ - #Requires -Version 7.0                   │
│ - Import-Module hooks/lib/pwsh_lib         │
│ - Calls: Write-Log, Invoke-ValidateChgs   │
│ - Returns exit code                        │
└───┬────────────────────────────────────────┘
    │
┌───▼────────────────────────────────────────┐
│ pwsh_lib.ps1 Functions (Module)            │
│ - Write-Log           → Write-Verbose      │
│ - Invoke-ValidateChgs → calls Python CLI   │
│ - Invoke-CheckLint    → runs linter        │
│ - Error handling      → exception/exit     │
└───┬────────────────────────────────────────┘
    │
┌───▼────────────────────────────────────────┐
│ Python CLI (complex logic)                 │
│ - uv run thegent validate-changes          │
│ - uv run thegent lint                      │
│ - Returns: exit code                       │
└───┬────────────────────────────────────────┘
    │
    └─ Dispatcher captures exit code & logs
       Returns status to caller
```

---

## 4. Component Dependencies

```
Layer 1 (User-Facing)
    ├─ Python hooks, agents, CLI commands
    └─ Shell selection via environment/config

        ▼

Layer 2 (Detection & Routing)
    ├─ ShellEnvironment (Python)
    │  - Detect shell type
    │  - Cache result
    │  - Prepare environment
    └─ Hook Dispatcher (Rust)
       - Route to appropriate shell runner
       - Handle errors & timeouts

        ▼

Layer 3 (Shell-Specific Runners)
    ├─ POSIX Runner
    │  ├─ bash_lib.sh (library)
    │  ├─ hooks/*.sh (hooks)
    │  └─ Error handling
    │
    └─ PowerShell Runner
       ├─ pwsh_lib.ps1 (module)
       ├─ hooks/*.ps1 (hooks)
       └─ Error handling

        ▼

Layer 4 (Shared Logic)
    ├─ Python utilities (validation, file ops)
    ├─ Logging (structured, consistent)
    ├─ Process management
    └─ Environment utilities

        ▼

Layer 5 (System Calls)
    ├─ bash subprocess execution
    ├─ PowerShell subprocess execution
    ├─ Process creation (with platform flags)
    └─ OS system calls
```

---

## 5. Shell Detection Decision Tree

```
                    START
                     │
          ┌──────────▼──────────┐
          │  Check env var:     │
          │ THGENT_AGENT_SHELL  │
          │ THGENT_SHELL        │
          └──────┬──────┬───────┘
               YES │    │ NO
                   │    └──┐
              ┌────▼┐      │
              │USE  │      └─────┐
              │IT   │            │
              └────┬┘            │
                   │      ┌──────▼──────────┐
                   │      │ Check config:   │
                   │      │ ~/.thegent/cfg  │
                   │      │ shell section   │
                   │      └──────┬──────┬───┘
                   │           YES│    │NO
                   │             │    └──┐
                   │        ┌────▼┐      │
                   │        │USE  │      │
                   │        │IT   │      │
                   │        └────┬┘      │
                   │             │      │
                   │      ┌──────▼──────────────┐
                   │      │ Detect Platform    │
                   │      │ (os, architecture) │
                   │      └──────┬──────────────┘
                   │             │
        ┌──────────┴─────────────┼────────────────┐
        │                        │                │
   ┌────▼───────┐    ┌──────────▼─────┐   ┌─────▼──────────┐
   │ POSIX       │    │ WINDOWS        │   │ WSL2           │
   │ (macOS/     │    │ (native)       │   │ (Linux+        │
   │ Linux)      │    │                │   │  Windows)      │
   └────┬───────┘    └────┬───────────┘   └────┬───────────┘
        │                 │                    │
    ┌───▼─────────┐   ┌───▼────────────┐   ┌──▼──────────┐
    │Try order:   │   │Try order:      │   │Try order:   │
    │ 1. zsh      │   │ 1. pwsh (7+)   │   │ 1. bash     │
    │ 2. bash     │   │ 2. bash (WSL2) │   │ 2. zsh      │
    │ 3. sh       │   │ 3. error       │   │ 3. sh       │
    └───┬─────────┘   └────┬──────────┘   └──┬──────────┘
        │                  │                 │
        └──────┬───────────┴────────────┬────┘
               │                        │
        ┌──────▼────────────────────────▼────┐
        │ Return: Shell Type (enum)           │
        │ ├─ shell path                       │
        │ ├─ shell_env (prepared environ)    │
        │ └─ runner (callable)                │
        └─────────────────────────────────────┘
```

---

## 6. File Structure (Before & After)

### BEFORE (Phase 1)

```
hooks/
├── *.sh                      # All POSIX hooks
├── lib/
│   └── bash_lib.sh          # (future location)
└── hook-dispatcher/         # (future location)

src/thegent/
├── utils/shell.py           # Shell detection (POSIX only)
└── infra/
    └── fast_subprocess.py   # Subprocess execution (platform-aware)
```

### AFTER (Phase 2)

```
hooks/
├── *.sh                      # POSIX versions
├── *.ps1                     # PowerShell versions (NEW)
├── lib/
│   ├── bash_lib.sh          # POSIX library
│   ├── pwsh_lib.ps1         # PowerShell library (NEW)
│   └── shared_utils.py      # Shared Python utilities (NEW)
├── hook-dispatcher/         # Rust dispatcher (NEW)
│   ├── src/
│   │   ├── main.rs
│   │   ├── dispatcher.rs
│   │   └── shell_detector.rs
│   ├── Cargo.toml
│   └── tests/
└── tests/                    # (test files moved here)

src/thegent/
├── utils/
│   ├── shell.py             # Updated with new classes
│   └── shell/               # (NEW module)
│       ├── __init__.py
│       ├── detection.py     # ShellType, detect_shell()
│       ├── environment.py   # ShellEnvironment class
│       ├── executor.py      # ShellExecutor class
│       └── adapters/        # OS-specific adapters
│           ├── user_creation.py
│           ├── desktop_automation.py
│           ├── process_monitor.py
│           └── file_watcher.py
└── infra/
    └── fast_subprocess.py   # Updated to use ShellEnvironment
```

---

## 7. Class Diagram: ShellEnvironment & ShellExecutor

```
┌─────────────────────────────────────┐
│     ShellEnvironment (Python)       │
├─────────────────────────────────────┤
│ Attributes:                         │
│  - platform: Platform               │
│  - shell_type: ShellType            │
│  - shell_path: str                  │
│  - environment: dict[str, str]      │
├─────────────────────────────────────┤
│ Methods:                            │
│  + __init__(platform, prefer)       │
│  + run_command(cmd, **kwargs)       │
│  + get_env_var(name) -> str|None    │
│  + update_env(key, value)           │
│  - _detect_shell() -> ShellType     │
│  - _resolve_shell_path() -> str     │
│  - _prepare_environment() -> dict   │
└─────────────────────────────────────┘
           △
           │ uses
           │
┌─────────────────────────────────────┐
│      ShellExecutor (Python)         │
├─────────────────────────────────────┤
│ Attributes:                         │
│  - env: ShellEnvironment            │
├─────────────────────────────────────┤
│ Methods:                            │
│  + __init__(env=None)               │
│  + run_hook(name, *args) -> Result  │
│  + run_script(path, *args) -> Res   │
│  + run_command(cmd) -> Result       │
└─────────────────────────────────────┘
           △
           │ uses
           │
┌─────────────────────────────────────┐
│   ShellDispatcher (Rust Binary)     │
├─────────────────────────────────────┤
│ Inputs:                             │
│  - hook_name: &str                  │
│  - hook_event: &str                 │
│  - context: Dict                    │
├─────────────────────────────────────┤
│ Logic:                              │
│  1. detect_shell() -> Shell         │
│  2. resolve_hook_file()             │
│  3. run_posix_hook() OR             │
│     run_powershell_hook()           │
│  4. capture result, return exit code│
└─────────────────────────────────────┘
```

---

## 8. Library Function Parity Matrix

```
┌──────────────────┬─────────────────┬──────────────────┐
│ Function         │ POSIX (bash)    │ PowerShell       │
├──────────────────┼─────────────────┼──────────────────┤
│ Logging          │                 │                  │
│ log_info()       │ fn in lib       │ Write-Log        │
│ log_error()      │ fn in lib       │ Write-Log        │
├──────────────────┼─────────────────┼──────────────────┤
│ Environment      │                 │                  │
│ get_env_var()    │ fn in lib       │ Get-ConfigValue  │
│ safe_env_get()   │ fn in lib       │ $env:VAR         │
├──────────────────┼─────────────────┼──────────────────┤
│ File Ops         │                 │                  │
│ normalize_path() │ fn in lib       │ Normalize-Path   │
│ file_exists()    │ fn in lib       │ Test-Path        │
│ file_changed()   │ fn in lib       │ Test-FileChanged │
├──────────────────┼─────────────────┼──────────────────┤
│ Validation       │                 │                  │
│ validate_chg()   │ fn→Python CLI   │ Invoke-Validate  │
│ check_lint()     │ fn→Python CLI   │ Invoke-CheckLint │
├──────────────────┼─────────────────┼──────────────────┤
│ Process Mgmt     │                 │                  │
│ run_with_to()    │ fn in lib       │ Invoke-WithTO    │
│ get_process()    │ fn in lib       │ Get-ProcessInfo  │
└──────────────────┴─────────────────┴──────────────────┘

All functions have:
  ✓ Identical API (names may differ due to language convention)
  ✓ Identical behavior (return types, error handling)
  ✓ Same documentation
```

---

## 9. Error Handling Flow

```
User runs hook
    │
    └─> Hook Dispatcher (Rust)
         │
         ├─ Shell detection fails
         │  └─> Error: "No suitable shell found"
         │      Log & return non-zero
         │
         ├─ Hook file not found
         │  └─> Error: "Hook not found: hooks/qa-check.sh"
         │      Log warning, skip
         │
         ├─ Hook execution fails (non-zero)
         │  ├─ Capture stderr
         │  ├─ Log [ERROR] message
         │  └─ Return exit code
         │
         ├─ Hook timeout (>30s)
         │  ├─ Kill process
         │  ├─ Log [ERROR] "Hook timeout"
         │  └─ Return 124
         │
         └─ Hook succeeds (exit 0)
            ├─ Log [INFO] "Hook completed"
            └─ Return 0

┌─────────────────────────────────────────┐
│ All errors logged to:                   │
│ ~/.thegent/logs/hooks.log               │
│ Format: [LEVEL] TIMESTAMP message       │
└─────────────────────────────────────────┘
```

---

## 10. WSL2-Specific Integration

```
Windows Machine
    │
    ├─ WSL2 Instance (Linux kernel in Hyper-V)
    │  │
    │  ├─ /mnt/c/... (Windows drive mounted)
    │  ├─ /usr/bin/bash (native Linux bash)
    │  ├─ /usr/bin/zsh (optional)
    │  └─ thegent repo (either native or in WSL2)
    │
    └─ Windows Native
       ├─ PowerShell 7+ (installed separately)
       ├─ thegent repo
       └─ Git (optional, may conflict with WSL2 git)

Detection Flow for WSL2:
    │
    ├─ Detect Platform = WSL2 (via /proc/version or env vars)
    │
    ├─ Shell availability:
    │  ├─ Option 1: Use WSL2 bash → mount /mnt/c/...
    │  ├─ Option 2: Use Windows pwsh → native paths
    │  └─ Prefer POSIX (more portable)
    │
    └─ Path conversion (if needed):
       ├─ C:\Users\... <→ /mnt/c/Users/...
       └─ Use wslpath command

Environment Setup for WSL2:
    │
    ├─ If using bash in WSL2:
    │  ├─ Disable Windows git (conflicts)
    │  ├─ Set PATH to WSL2 paths only
    │  └─ Mount points: /mnt/c/...
    │
    └─ If using pwsh native:
       ├─ Set PATH to Windows paths
       └─ Convert /mnt/c/... to C:\...
```

---

## 11. Performance Impact

```
Current (Phase 1):
    Shell detection: ~2-5ms (using shutil.which cached)
    Hook execution: ~100-200ms (mostly I/O)
    Total overhead: ~0-5ms

After Phase 2A (Dispatcher):
    Dispatcher startup: ~10-20ms (Rust binary)
    Shell detection: ~2-5ms (same logic)
    Hook execution: ~100-200ms (same as before)
    Total overhead: ~10-25ms (12-20% increase, acceptable)

After Phase 2C (Python integration):
    ShellEnvironment init: ~5-10ms
    Caching enabled: detection happens once per session
    Hook execution: ~100-200ms (unchanged)
    Total overhead per hook: ~0-5ms (cached)

Cumulative Impact:
    ├─ First hook: +20ms (dispatcher startup)
    ├─ Subsequent hooks: +0-5ms (cached)
    └─ Overall: <2% user-noticeable impact
```

---

## 12. Rollout Phases (Timeline View)

```
Week 1-2: Phase 2A Foundation
    ├─ Dispatcher binary (Rust)
    ├─ bash_lib.sh
    ├─ pwsh_lib.ps1
    └─ Python ShellEnvironment class
        → 0% user impact (hidden)

Week 3-4: Phase 2B Hook Migration
    ├─ qa-check (POSIX + PowerShell)
    ├─ doc-location-guard
    ├─ change-doc-tracker
    ├─ complexity-ratchet
    └─ security-pipeline
        → Rolled out to 10% of users

Week 5-6: Phase 2C Python Integration
    ├─ fast_subprocess migration
    ├─ Agent subprocess execution
    ├─ Config & CLI updates
    └─ Installer updates
        → Rolled out to 50% of users

Week 7-8: Phase 2D OS Adapters
    ├─ User creation adapter
    ├─ Desktop automation
    ├─ Process monitoring
    └─ File watcher
        → Rolled out to 100% of users (if needed)

Week 9-10: Phase 2E Rollout & Docs
    ├─ Comprehensive testing
    ├─ Migration guide
    ├─ Announcement
    └─ Production deployment
        → All users on Phase 2

Rollback Plan (any week):
    └─ Disable via env var: THGENT_DUAL_SHELL_ENABLED=0
       → Fallback to direct bash (Phase 1 behavior)
```

---

## Legend

```
┌───┐
│   │ = Component/Layer
└───┘

  ▲   = Input/Dependency
  │

  ▼   = Output/Result
  │

─>    = Control flow

═>    = Data flow (primary)

◄─>   = Bidirectional
```

---

**End of Diagrams**

These diagrams are meant to be printed or viewed alongside the detailed design documents:

- `research-cross-platform-shell.md` — Full technical design
- `SHELL_IMPLEMENTATION_CHECKLIST_PHASE2.md` — Task-level breakdown
- `POSIX_PWSH_SHELL_STRATEGY.md` — Configuration guide
