# Cross-Platform Shell Strategy Proposal (POSIX + PowerShell)

**Date**: 2026-02-18
**Status**: Proposed
**Priority**: P1

---

## Executive Summary

Establish a **dual-shell strategy** for thegent to support both POSIX environments (Linux, macOS, WSL) and Windows PowerShell natively. This proposal defines a unified approach to shell scripting that maintains code quality, consistency, and performance across platforms without requiring users to translate between shell languages.

**Key Goals**:

- Enable Windows PowerShell as a first-class citizen alongside POSIX (bash/sh)
- Eliminate platform-specific code branches in critical paths (hooks, commands, startup)
- Establish automated testing and validation across both shell environments
- Define clear patterns for library-like shell code reusability
- Support user-provided hooks and scripts in both shells

---

## Problem Statement

**Current State**:

- thegent uses POSIX shell exclusively (`#!/bin/bash`, `#!/bin/sh`)
- Windows users must rely on WSL or MSYS2 (non-native experience)
- Hooks system is shell-specific; PowerShell hooks not supported
- CLI shims assume bash availability
- No cross-shell abstraction layer or patterns

**Desired State**:

- Native PowerShell support for Windows users
- Single codebase with shell-specific variants (not separate branches)
- Hooks work seamlessly in both POSIX and PowerShell
- Cross-platform CLI commands without user translation
- Performance parity: no Windows performance penalty
- Clear guidelines for contributors on cross-platform shell patterns

---

## Scope

### In Scope

- Hook dispatcher (convert to shell-agnostic dispatcher + language-specific hooks)
- CLI entry points (shims) for Windows PowerShell
- Core shell scripts (`scripts/`, `hooks/lib/`)
- Shell initialization (`.zshrc`, `.bashrc` → PowerShell profile equivalent)
- Cross-platform testing and CI/CD validation
- Documentation and contributor guidelines

### Out of Scope (Phase 2+)

- Rewriting thegent-resources and thegent-discovery in PowerShell (Rust preferred)
- Full Python migration (thegent core remains Python + shell hybrid)
- macOS-specific optimizations (e.g., BSD coreutils vs GNU)

### Phase 1 Deliverables

- Unified hook dispatcher (shell-agnostic entry point)
- PowerShell hook runners and library patterns
- Cross-shell test infrastructure
- Guidelines and ADR

---

## Requirements

### Functional Requirements

| FR-ID          | Description                                                       | Priority | Platform |
| -------------- | ----------------------------------------------------------------- | -------- | -------- |
| **FR-CSH-001** | POSIX hook runners (bash, sh)                                     | P0       | POSIX    |
| **FR-CSH-002** | PowerShell hook runners                                           | P0       | Windows  |
| **FR-CSH-003** | Shell-agnostic hook dispatcher                                    | P0       | Both     |
| **FR-CSH-004** | Unified library (shell wrappers around Python)                    | P0       | Both     |
| **FR-CSH-005** | CLI shims for PowerShell (`thegent.ps1`)                          | P1       | Windows  |
| **FR-CSH-006** | PowerShell profile integration                                    | P1       | Windows  |
| **FR-CSH-007** | Cross-platform test runner (validates both shells)                | P1       | Both     |
| **FR-CSH-008** | User hook examples in both shells                                 | P2       | Both     |
| **FR-CSH-009** | Shell capability detection (`posix_sh()`, `pwsh()` functions)     | P1       | Both     |
| **FR-CSH-010** | Fallback mechanisms (POSIX if PowerShell unavailable, vice versa) | P2       | Both     |

### Non-Functional Requirements

| NFR-ID          | Requirement                         | Target                                      |
| --------------- | ----------------------------------- | ------------------------------------------- |
| **NFR-CSH-001** | Hook execution latency parity       | <10ms diff between shells                   |
| **NFR-CSH-002** | Initialization time (shell profile) | <200ms both platforms                       |
| **NFR-CSH-003** | Test coverage (cross-shell)         | ≥80% both shells                            |
| **NFR-CSH-004** | Documentation completeness          | All patterns documented with examples       |
| **NFR-CSH-005** | Backward compatibility              | No breaking changes to existing POSIX hooks |
| **NFR-CSH-006** | Contributor onboarding              | <30min to understand patterns               |

---

## High-Level Architecture

### Layer Model

```
┌─────────────────────────────────────────────────┐
│  User Hooks / Commands (POSIX .sh / .ps1)      │
│  User-provided lifecycle & validation logic     │
└─────────────────────────────────────────────────┘
           ↑                          ↑
    POSIX Shell                 PowerShell
           │                          │
┌──────────┴──────────────────────────┴──────────┐
│  Shell-Agnostic Dispatcher (Rust/Python)      │
│  - Detects shell environment                   │
│  - Routes to language-specific runner          │
│  - Unified error handling & logging            │
└──────────────────────────────────────────────────┘
           ↑                          ↑
    POSIX Runner                 PWShell Runner
   (bash/sh handler)           (pwsh handler)
           │                          │
┌──────────┴──────────────────────────┴──────────┐
│  Cross-Platform Library Layer                  │
│  - Helper functions (posix_sh / pwsh wrappers) │
│  - Python invocations (thegent CLI)            │
│  - Utilities (path handling, env setup)        │
└──────────────────────────────────────────────────┘
           ↑                          ↑
      POSIX Utils                PowerShell Utils
      (bash scripts)             (PowerShell modules)
           │                          │
┌──────────┴──────────────────────────┴──────────┐
│  Python Core (thegent CLI, MCP server)         │
│  Language-agnostic; shell-independent         │
└──────────────────────────────────────────────────┘
```

### Component Breakdown

| Component             | Purpose                              | Platforms | Status              |
| --------------------- | ------------------------------------ | --------- | ------------------- |
| **Dispatcher**        | Route hooks to shell-specific runner | Both      | To design           |
| **POSIX Runner**      | Execute bash/sh hooks                | POSIX     | Existing            |
| **PWShell Runner**    | Execute PowerShell hooks             | Windows   | To implement        |
| **Library (POSIX)**   | Helper functions, utilities          | POSIX     | Existing (refactor) |
| **Library (PWShell)** | Equivalent helpers in PowerShell     | Windows   | To implement        |
| **Test Harness**      | Cross-platform test framework        | Both      | To implement        |
| **CLI Shims**         | Entry points for both shells         | Both      | To design           |
| **Initialization**    | Shell profile setup                  | Both      | To design           |

---

## Design Approach

### Strategy: "Write Once, Run Everywhere" (via Language Bindings)

**Philosophy**: Minimize shell-specific code by delegating complexity to Python/Rust.

**Principle**:

```
─────────────────────────────────────────────────
Shell → Invoke Python CLI → Python (logic) → Result
─────────────────────────────────────────────────
```

**Benefits**:

- Reduces code duplication (business logic lives in Python)
- Easier testing (Python tests cover both shells)
- Maintainability (single source of truth)
- Performance (shell just invokes CLI, Python does work)

**Pattern**:

1. **POSIX**: `bash_lib.sh` provides helper functions that call Python
2. **PowerShell**: `pwsh_lib.ps1` provides equivalent functions that call Python
3. **Both**: User writes hooks in their native shell, calls common library functions

### Example Pattern

**Shared Logic (Python)**:

```python
# src/thegent/hooks/validators.py
def validate_file_changes(files: list[str]) -> dict:
    """Validate file changes against governance."""
    # complex logic here
```

**POSIX Library Wrapper**:

```bash
# hooks/lib/bash_lib.sh
validate_file_changes() {
  uv run thegent hooks validate-files "$@"
}
```

**PowerShell Library Wrapper**:

```powershell
# hooks/lib/pwsh_lib.ps1
function Validate-FileChanges {
  & uv run thegent hooks validate-files @args
}
```

**User Hook (POSIX)**:

```bash
# hooks/qa-my-hook.sh
source hooks/lib/bash_lib.sh
validate_file_changes "${files[@]}"
```

**User Hook (PowerShell)**:

```powershell
# hooks/qa-my-hook.ps1
. hooks/lib/pwsh_lib.ps1
Validate-FileChanges @files
```

---

## Key Design Decisions

### D1: Shell-Agnostic Dispatcher

**Decision**: Create language-agnostic dispatcher (Rust binary or Python)
**Rationale**: Avoid shell-specific logic in dispatcher; keep it neutral and fast
**Alternatives Rejected**:

- Bash dispatcher with PowerShell fallback (biased toward POSIX)
- Separate dispatcher binaries (maintainability burden)

**Trade-offs**: Adds minimal Rust/Python build step; improves clarity and performance

### D2: Delegation to Python for Complex Logic

**Decision**: Push all complex logic into Python; shell is thin wrapper
**Rationale**:

- Business logic is easier to test in Python
- Reduces shell-specific bugs
- Single source of truth

**Alternatives Rejected**:

- Write duplicate logic in both shells (maintenance nightmare)
- Use shell-only for everything (performance and maintainability issues)

**Trade-offs**: Minor latency (Python startup) offset by code quality and testability

### D3: Hook File Naming Convention

**Decision**: Use extensions to indicate shell (`.sh` for POSIX, `.ps1` for PowerShell)
**Rationale**: Self-documenting; dispatcher can auto-detect
**Alternatives Rejected**:

- Single `.hook` file with shebang (harder to edit)
- Language detection via content analysis (fragile)

**Trade-offs**: Duplicate hook definitions for dual support; mitigated by shared library pattern

### D4: Initialization Strategy

**Decision**: Detect shell and source appropriate profile/module at startup
**Rationale**: User experience: automatic setup without manual steps
**Alternatives Rejected**:

- Manual profile editing per shell (error-prone)
- Single `.shellrc` (doesn't match shell conventions)

**Trade-offs**: Requires platform-specific bootstrapping; mitigated by clear documentation

### D5: Testing Strategy

**Decision**: Use Docker containers for cross-platform testing (Linux, macOS via Act, Windows via containers)
**Rationale**: Reproducible environments; CI/CD integration
**Alternatives Rejected**:

- Manual testing on each platform (doesn't scale)
- VM snapshots (slow, resource-intensive)

**Trade-offs**: Container setup overhead; pays off in reliability

---

## Acceptance Criteria

- [ ] **AC-1**: Hook dispatcher supports both POSIX and PowerShell runners
- [ ] **AC-2**: POSIX hooks continue to work without modification
- [ ] **AC-3**: PowerShell hooks can be written and executed with feature parity
- [ ] **AC-4**: Library functions available in both shells (`validate_*`, `log_*`, etc.)
- [ ] **AC-5**: CLI shims work in both bash and PowerShell
- [ ] **AC-6**: Cross-platform test suite passes on Linux, macOS, and Windows (via CI)
- [ ] **AC-7**: Documentation includes contributor guide with examples
- [ ] **AC-8**: No performance degradation (<5% latency increase)
- [ ] **AC-9**: All linters pass (shellcheck for bash, PSScriptAnalyzer for PowerShell)
- [ ] **AC-10**: New hook examples provided in both shells

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1–2)

- Design shell-agnostic dispatcher
- Implement PowerShell hook runners
- Create cross-platform library stubs
- Set up cross-platform testing infrastructure
- Write ADR and contributor guidelines

### Phase 2: Integration (Weeks 3–4)

- Migrate existing hooks to use common library
- Implement CLI shims for PowerShell
- Shell profile integration
- User documentation and examples

### Phase 3: Hardening (Weeks 5–6)

- Cross-platform testing automation (CI/CD)
- Performance benchmarking and optimization
- User feedback and iteration

---

## Related Documents

- **Architecture**: [design.md](./design.md)
- **Implementation Tasks**: [tasks.md](./tasks.md)
- **ADR (to be created)**: `docs/reference/ADR-CROSS_PLATFORM_SHELL.md`
- **Contributor Guide (to be created)**: `docs/guides/CROSS_PLATFORM_SHELL_PATTERNS.md`
- **Test Strategy**: `docs/reference/CROSS_PLATFORM_TEST_STRATEGY.md`

---

## See Also

- POSIX Shell Reference: https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html
- PowerShell Documentation: https://learn.microsoft.com/en-us/powershell/
- ShellCheck (POSIX linter): https://www.shellcheck.net/
- PSScriptAnalyzer (PowerShell linter): https://github.com/PowerShell/PSScriptAnalyzer
- Cross-Platform Testing: https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners
