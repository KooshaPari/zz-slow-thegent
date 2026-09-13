# Cross-Platform Shell Strategy Design

**Date**: 2026-02-18
**Status**: Design
**Related Proposal**: [proposal.md](./proposal.md)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Design](#component-design)
3. [Shell-Specific Patterns](#shell-specific-patterns)
4. [Library Design](#library-design)
5. [Initialization Strategy](#initialization-strategy)
6. [Testing Architecture](#testing-architecture)
7. [Performance Considerations](#performance-considerations)
8. [Backward Compatibility](#backward-compatibility)

---

## Architecture Overview

### Execution Flow

#### POSIX Flow (bash/sh)

```
User Command
    ↓
Bash Shim (~/.local/bin/thegent)
    ↓
Dispatcher (Rust binary or Python)
    ├─ Detects: POSIX shell
    ├─ Sources: hooks/lib/bash_lib.sh
    └─ Executes: hooks/qa-check.sh
         ├─ Calls: validate_changes() [from bash_lib]
         ├─ Invokes: uv run thegent validate-changes
         └─ Returns: status
```

#### PowerShell Flow (pwsh)

```
User Command
    ↓
PowerShell Shim (~/.local/bin/thegent.ps1 or Alias)
    ↓
Dispatcher (Language-agnostic entry point)
    ├─ Detects: PowerShell
    ├─ Sources: hooks/lib/pwsh_lib.ps1 (module import)
    └─ Executes: hooks/qa-check.ps1
         ├─ Calls: Validate-Changes [from pwsh_lib]
         ├─ Invokes: uv run thegent validate-changes
         └─ Returns: status
```

### Directory Structure

```
thegent/
├── hooks/
│   ├── hook-dispatcher/           # Rust binary (shell-agnostic router)
│   │   ├── src/main.rs
│   │   ├── src/dispatcher.rs
│   │   ├── src/shell_detector.rs
│   │   └── Cargo.toml
│   ├── bin/
│   │   └── hook-dispatcher        # Compiled binary
│   ├── lib/
│   │   ├── bash_lib.sh            # POSIX helper functions
│   │   ├── pwsh_lib.ps1           # PowerShell helper module
│   │   └── shared_utils.py        # Python utilities (invoked by both)
│   ├── qa-check.sh                # POSIX version
│   ├── qa-check.ps1               # PowerShell version
│   └── ... (other hooks, both .sh and .ps1)
├── scripts/
│   ├── thegent.sh                 # POSIX CLI wrapper
│   ├── thegent.ps1                # PowerShell CLI wrapper
│   └── install-shims.sh           # Installation script
├── tests/
│   ├── shell/
│   │   ├── test_bash_lib.sh       # POSIX library tests
│   │   ├── test_pwsh_lib.ps1      # PowerShell library tests
│   │   └── test_dispatcher.rs     # Dispatcher unit tests
│   └── integration/
│       ├── test_cross_platform.sh # Cross-platform test harness
│       └── conftest.py            # pytest fixtures for shell tests
└── docs/
    ├── changes/
    │   └── research-cross-platform-shell/
    │       ├── proposal.md
    │       ├── design.md (this file)
    │       └── tasks.md
    └── guides/
        └── CROSS_PLATFORM_SHELL_PATTERNS.md
```

---

## Component Design

### 1. Shell-Agnostic Dispatcher

**Purpose**: Route hooks to appropriate shell runner; detect environment; handle errors

**Implementation**: Rust binary (performance-critical path)

**Inputs**:

- Hook name (e.g., `qa-check`)
- Hook event (e.g., `PostToolUse`)
- Context (file paths, environment variables)

**Logic**:

```rust
// pseudo-code
fn dispatch(hook_name: &str, event: &str, context: &Dict) -> Result<()> {
    let shell = detect_shell(); // POSIX, PowerShell, or error
    let hook_file = match shell {
        Shell::POSIX => format!("hooks/{}.sh", hook_name),
        Shell::PowerShell => format!("hooks/{}.ps1", hook_name),
    };

    if !Path::new(&hook_file).exists() {
        return Err(format!("Hook not found: {}", hook_file));
    }

    let runner = match shell {
        Shell::POSIX => PosixRunner::new(),
        Shell::PowerShell => PowerShellRunner::new(),
    };

    runner.execute(&hook_file, context)
}
```

**Error Handling**:

- Graceful fallback if hook unavailable (log warning, continue)
- Timeout handling (configurable, default 30s)
- Stderr capture and logging

**Outputs**:

- Exit status (0=success, non-zero=failure)
- Stdout/stderr logged to `~/.thegent/logs/hooks.log`

---

### 2. POSIX Hook Runner

**Language**: Bash
**Location**: `hooks/lib/bash_lib.sh`

**Responsibilities**:

- Source hook file
- Provide helper functions (logging, validation, etc.)
- Execute hook with error handling
- Capture and return status

**Implementation Pattern**:

```bash
#!/bin/bash
set -euo pipefail  # Strict mode

# Source library
source "$(dirname "$0")/lib/bash_lib.sh"

# Hook logic
log_info "Starting QA check..."
validate_changes "${@}" || return 1
log_info "QA check passed"
```

**Key Features**:

- Strict mode by default (`set -euo pipefail`)
- Structured logging (timestamp, level, message)
- Common helper functions (file checks, path resolution)
- Consistent error handling and exit codes

---

### 3. PowerShell Hook Runner

**Language**: PowerShell 7+
**Location**: `hooks/lib/pwsh_lib.ps1`

**Responsibilities**:

- Load hook module
- Provide helper functions (equivalent to bash_lib)
- Execute hook with error handling
- Capture and return status

**Implementation Pattern**:

```powershell
# hooks/qa-check.ps1
#Requires -Version 7.0

# Source library (PowerShell module import)
Import-Module -Name "$PSScriptRoot/lib/pwsh_lib.psd1"

# Hook logic
Write-Log -Level Info -Message "Starting QA check..."
Validate-Changes @args
Write-Log -Level Info -Message "QA check passed"
```

**Key Features**:

- PowerShell 7+ (cross-platform; PowerShell 5.1 on Windows legacy systems)
- Strict mode equivalent (`Set-StrictMode -Version Latest`)
- Structured logging (PowerShell Logging Module pattern)
- Common helper functions (file checks, path resolution)
- ErrorActionPreference set to Stop (fail-fast)

**Module Structure**:

```
hooks/lib/pwsh_lib/
├── pwsh_lib.psd1       # Module manifest
├── pwsh_lib.psm1       # Module functions
├── private/            # Private functions
└── public/             # Public functions
```

---

### 4. Cross-Platform Library

**Purpose**: Shared helper functions and utilities for both shells

**Implementation**:

- POSIX: Shell functions in `hooks/lib/bash_lib.sh`
- PowerShell: Functions in `hooks/lib/pwsh_lib.ps1`
- Complex logic: Python utilities invoked by both

**Common Functions**:

| Function                      | POSIX | PowerShell | Purpose                        |
| ----------------------------- | ----- | ---------- | ------------------------------ |
| `log_info` / `Write-Log`      | ✓     | ✓          | Structured logging             |
| `validate_changes`            | ✓     | ✓          | File change validation         |
| `check_lint`                  | ✓     | ✓          | Invoke linter                  |
| `run_tests`                   | ✓     | ✓          | Invoke test runner             |
| `get_env` / `Get-ConfigValue` | ✓     | ✓          | Safe environment lookup        |
| `normalize_path`              | ✓     | ✓          | Cross-platform path resolution |
| `file_changed_since`          | ✓     | ✓          | Timestamp comparison           |

**Delegation Pattern**:

```
User Hook (shell) → Library Function (shell) → Python CLI (complex logic) → Result
```

Example: `validate_changes` implementation

**POSIX**:

```bash
validate_changes() {
  local files=("$@")
  uv run thegent hooks validate-files "${files[@]}"
}
```

**PowerShell**:

```powershell
function Validate-Changes {
    param([string[]]$Files)
    & uv run thegent hooks validate-files @Files
}
```

**Python CLI** (`src/thegent/cli/hooks.py`):

```python
@click.command()
@click.argument("files", nargs=-1, required=True)
def validate_files(files):
    """Validate file changes against governance."""
    validator = FileChangeValidator()
    results = validator.validate(files)
    # ... logic
    sys.exit(0 if results.all_pass else 1)
```

---

### 5. CLI Shims

**Purpose**: User-facing entry points for both POSIX and PowerShell

**POSIX Shim** (`scripts/thegent.sh`):

```bash
#!/bin/bash
# Wrapper that preserves shell environment
exec uv run thegent "$@"
```

**PowerShell Shim** (`scripts/thegent.ps1`):

```powershell
# PowerShell entry point
param([string[]]$Arguments)
& uv run thegent @Arguments
```

**Installation**:

- POSIX: `~/.local/bin/thegent` → points to `scripts/thegent.sh`
- PowerShell: Function alias in profile, or `~/.local/bin/thegent.ps1`

---

## Shell-Specific Patterns

### Error Handling

#### POSIX Pattern

```bash
#!/bin/bash
set -euo pipefail
trap 'log_error "Trap: line $LINENO"' ERR

my_function() {
  if ! validate_input "$1"; then
    log_error "Validation failed"
    return 1
  fi
  log_info "Success"
}
```

#### PowerShell Pattern

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
trap { Write-Log -Level Error -Message $_ }

function My-Function {
    if (-not (Test-Input $arg)) {
        Write-Log -Level Error -Message "Validation failed"
        throw "Validation error"
    }
    Write-Log -Level Info -Message "Success"
}
```

### Path Handling

#### POSIX Pattern

```bash
normalize_path() {
  local path="$1"
  # Handle ~ expansion
  [[ "$path" =~ ^~/ ]] && path="${HOME}${path#~}"
  # Resolve relative
  cd "$(dirname "$path")" && pwd -P && cd - >/dev/null
}
```

#### PowerShell Pattern

```powershell
function Normalize-Path {
    param([string]$Path)
    $expanded = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
    Resolve-Path -Path $expanded -ErrorAction Stop
}
```

### Environment Variables

#### POSIX Pattern

```bash
get_env() {
  local var="$1"
  local default="${2:-}"
  echo "${!var:-$default}"
}

# Usage
LOG_LEVEL=$(get_env LOG_LEVEL "INFO")
```

#### PowerShell Pattern

```powershell
function Get-ConfigValue {
    param(
        [string]$Name,
        [string]$Default = ""
    )
    [Environment]::GetEnvironmentVariable($Name, "Process") -or $Default
}

# Usage
$LogLevel = Get-ConfigValue "LOG_LEVEL" "INFO"
```

---

## Library Design

### Bash Library Structure

**File**: `hooks/lib/bash_lib.sh`

```bash
#!/bin/bash
# Cross-platform bash library
# Provides shared functions for hooks

set -euo pipefail

# Logging
log_info() { printf '[INFO] %s\n' "$*" >&2; }
log_warn() { printf '[WARN] %s\n' "$*" >&2; }
log_error() { printf '[ERROR] %s\n' "$*" >&2; }
log_debug() { [[ "${DEBUG:-0}" == "1" ]] && printf '[DEBUG] %s\n' "$*" >&2; }

# File validation
is_file_changed() {
  local file="$1"
  local since="${2:--1}"
  [[ -f "$file" ]] && [[ $(stat -c%Y "$file" 2>/dev/null || stat -f%m "$file") -gt $since ]]
}

# Python invocation helpers
invoke_python() {
  local module="$1"
  shift
  uv run thegent "$module" "$@"
}

# ... more functions
```

### PowerShell Library Structure

**File**: `hooks/lib/pwsh_lib.ps1`

```powershell
#Requires -Version 7.0

# Cross-platform PowerShell library
# Provides shared functions for hooks

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Logging
function Write-Log {
    param(
        [ValidateSet('Debug', 'Info', 'Warn', 'Error')]
        [string]$Level = 'Info',
        [string]$Message
    )
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "[${timestamp}] [${Level}] ${Message}" | Out-Host -ErrorAction Continue
}

# File validation
function Test-FileChanged {
    param([string]$Path, [int64]$SinceTimestamp = -1)
    if (Test-Path -Path $Path -PathType Leaf) {
        $file = Get-Item -Path $Path
        return $file.LastWriteTimeUtc.ToFileTimeUtc() -gt $SinceTimestamp
    }
    return $false
}

# Python invocation helpers
function Invoke-Python {
    param([string]$Module, [string[]]$Arguments)
    & uv run thegent $Module @Arguments
}

# ... more functions
```

---

## Initialization Strategy

### POSIX Shell Profile Integration

**File**: `scripts/init-posix.sh`

Appended to user's shell profile (`~/.bashrc`, `~/.zshrc`):

```bash
# thegent initialization
if [[ -f ~/.local/share/thegent/init.sh ]]; then
  source ~/.local/share/thegent/init.sh
fi
```

**Content** (`~/.local/share/thegent/init.sh`):

```bash
#!/bin/bash
# thegent initialization for POSIX shells

# Add thegent to PATH if not already present
if [[ ":$PATH:" != *":${HOME}/.local/bin:"* ]]; then
  export PATH="${HOME}/.local/bin:${PATH}"
fi

# Source thegent aliases/functions
if [[ -f ~/.local/share/thegent/aliases.sh ]]; then
  source ~/.local/share/thegent/aliases.sh
fi

# Completions
if [[ -f ~/.local/share/thegent/completions.sh ]]; then
  source ~/.local/share/thegent/completions.sh
fi
```

### PowerShell Profile Integration

**File**: `scripts/init-pwsh.ps1`

Added to user's PowerShell profile (`$PROFILE`):

```powershell
# thegent initialization
$thegentInitPath = "$HOME/.local/share/thegent/init.ps1"
if (Test-Path -Path $thegentInitPath) {
    . $thegentInitPath
}
```

**Content** (`~/.local/share/thegent/init.ps1`):

```powershell
# thegent initialization for PowerShell

# Add thegent to PATH if not already present
$thegentPath = "$HOME/.local/bin"
if ($env:PATH -notmatch [regex]::Escape($thegentPath)) {
    $env:PATH = "$thegentPath;$env:PATH"
}

# Create thegent function
function thegent {
    & "$PSScriptRoot/thegent.ps1" @args
}

# Source completions if available
$completionsPath = "$thegentPath/completions.ps1"
if (Test-Path -Path $completionsPath) {
    . $completionsPath
}
```

---

## Testing Architecture

### Test Structure

```
tests/
├── shell/
│   ├── test_bash_lib.sh           # Unit tests for bash_lib
│   ├── test_pwsh_lib.ps1          # Unit tests for pwsh_lib
│   ├── test_dispatcher.rs         # Unit tests for dispatcher
│   └── fixtures/
│       ├── sample_hook.sh
│       └── sample_hook.ps1
├── integration/
│   ├── conftest.py                # pytest fixtures
│   ├── test_cross_platform.sh     # Integration tests (both shells)
│   └── docker/
│       ├── Dockerfile.linux
│       └── Dockerfile.windows
└── ci/
    ├── test.yml                   # GitHub Actions workflow
    └── test-windows.yml           # Windows-specific tests
```

### Test Framework

**POSIX**: BATS-Core (Bash Automated Testing System)

```bash
# tests/shell/test_bash_lib.bats
@test "log_info outputs to stderr" {
  run log_info "test message"
  [ "$status" -eq 0 ]
  [[ "$output" == *"[INFO] test message"* ]]
}
```

**PowerShell**: Pester

```powershell
# tests/shell/test_pwsh_lib.ps1
Describe 'Write-Log' {
    It 'logs info to output' {
        Write-Log -Level Info -Message "test"
        # Assertion
    }
}
```

**Cross-Platform**: pytest + subprocess

```python
# tests/integration/conftest.py
@pytest.fixture(params=["bash", "pwsh"])
def shell_runner(request):
    """Parameterized shell runner for cross-platform tests"""
    shell = request.param
    return ShellRunner(shell)
```

---

## Performance Considerations

### Latency Analysis

| Operation           | POSIX (bash) | PowerShell | Delta | Notes                        |
| ------------------- | ------------ | ---------- | ----- | ---------------------------- |
| Interpreter startup | ~10ms        | ~50ms      | +40ms | pwsh slower on cold start    |
| Hook dispatch       | <5ms         | <10ms      | +5ms  | Negligible                   |
| Python invocation   | ~100ms       | ~100ms     | 0ms   | Dominant; same across shells |
| Total hook exec     | ~115ms       | ~160ms     | +45ms | ~2% of total build time      |

### Optimization Strategies

1. **Pre-load Python** (where applicable): Use daemon mode if available
2. **Lazy loading**: Only import modules when needed
3. **Caching**: Cache validation results across hook invocations
4. **Async hooks** (future): For non-blocking operations

---

## Backward Compatibility

### Migration Path

**Phase 1**: Dual hooks (`.sh` and `.ps1` exist together)

- Existing POSIX hooks unchanged
- New PowerShell hooks added alongside
- Dispatcher auto-detects and routes

**Phase 2**: Unified library adoption

- Migrate hooks to use common library
- POSIX hooks updated incrementally
- No breaking changes to users

**Phase 3**: Deprecation (if needed)

- Shell-specific versions can coexist indefinitely
- No removal necessary; maintains backward compatibility

### User Impact

- **POSIX users**: No changes; hooks work as before
- **Windows users**: Native PowerShell support (first time)
- **Contributors**: Clear guidelines for writing cross-platform hooks

---

## Open Questions & Future Work

1. **PowerShell 5.1 support**: Design requires PS 7+; should PS 5.1 be supported?
2. **Fallback mechanism**: If PowerShell unavailable, fall back to WSL bash?
3. **Performance profiling**: Benchmark across all shells post-implementation
4. **IDE integration**: Support for VS Code shell debugging?
5. **CI/CD matrix**: Expand GitHub Actions matrix to include Windows runners

---

## Related Documents

- **Proposal**: [proposal.md](./proposal.md)
- **Implementation Tasks**: [tasks.md](./tasks.md)
- **ADR (to be created)**: `docs/reference/ADR-CROSS_PLATFORM_SHELL.md`
