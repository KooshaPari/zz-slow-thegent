# Cross-Platform Shell Strategy Implementation Tasks

**Date**: 2026-02-18
**Status**: Task Breakdown
**Related Documents**: [proposal.md](./proposal.md), [design.md](./design.md)

---

## Overview

**Objective**: Implement dual-shell support (POSIX + PowerShell) for thegent
**Timeline**: 6 weeks (Phases 1–3)
**Estimated Effort**: 120–160 engineering hours
**Delivery Cadence**: Weekly milestones with verification gates

---

## Phase 1: Foundation (Weeks 1–2)

**Goal**: Establish shell-agnostic infrastructure, PowerShell library, and testing framework

### Task 1.1: Design & Review Shell-Agnostic Dispatcher

**Description**: Design Rust binary that routes hooks to appropriate shell runner
**Acceptance Criteria**:

- [ ] Dispatcher design document finalized (ADR-CROSS_PLATFORM_SHELL.md)
- [ ] Shell detection logic specified (environment checks, fallback strategy)
- [ ] Error handling patterns defined (timeout, missing hooks, failures)
- [ ] Design reviewed and approved by team lead

**Estimated Effort**: 8 hours
**Type**: Design
**Owner**: Architecture team
**Depends On**: Nothing

### Task 1.2: Implement Rust Dispatcher Binary

**Description**: Build shell-agnostic dispatcher (Rust); compile and test locally
**Acceptance Criteria**:

- [ ] Rust project scaffolded (`hooks/hook-dispatcher/Cargo.toml`)
- [ ] Shell detection implemented (returns Shell::POSIX or Shell::PowerShell)
- [ ] Hook routing logic implemented (selects .sh or .ps1 file)
- [ ] Error handling & logging complete
- [ ] Binary compiles without warnings
- [ ] Unit tests pass (70% coverage min)
- [ ] `task hooks:bin` builds successfully

**Estimated Effort**: 16 hours
**Type**: Implementation
**Owner**: Backend team
**Depends On**: 1.1

**Definition of Done**:

```bash
cd hooks/hook-dispatcher
cargo test
cargo clippy --all-targets
```

### Task 1.3: Create PowerShell Library Module

**Description**: Implement PowerShell library functions (equivalent to bash_lib.sh)
**Files**:

- `hooks/lib/pwsh_lib/pwsh_lib.psd1` (manifest)
- `hooks/lib/pwsh_lib/pwsh_lib.psm1` (module)
- `hooks/lib/pwsh_lib/public/*.ps1` (public functions)
- `hooks/lib/pwsh_lib/private/*.ps1` (private functions)

**Functions to Implement**:

- [ ] `Write-Log` (info, warn, error, debug levels)
- [ ] `Test-FileChanged` (timestamp comparison)
- [ ] `Invoke-Python` (wrapper for uv run thegent)
- [ ] `Get-ConfigValue` (safe env lookup)
- [ ] `Test-InputValid` (basic validation)
- [ ] `Normalize-Path` (cross-platform path resolution)
- [ ] Error trap handling and recovery

**Acceptance Criteria**:

- [ ] Module loads without errors: `Import-Module hooks/lib/pwsh_lib`
- [ ] All functions exported correctly
- [ ] PSScriptAnalyzer passes (no warnings)
- [ ] Functions have help documentation (`Get-Help`)
- [ ] Module tests pass (Pester suite, 70% coverage min)

**Estimated Effort**: 12 hours
**Type**: Implementation
**Owner**: PowerShell specialist
**Depends On**: Nothing

**Testing**:

```powershell
Import-Module -Name "hooks/lib/pwsh_lib/pwsh_lib.psd1"
Invoke-Pester -Path "tests/shell/test_pwsh_lib.ps1" -Verbose
```

### Task 1.4: Refactor Existing bash_lib.sh

**Description**: Update POSIX library to match PowerShell library interface
**Changes**:

- [ ] Review current `hooks/lib/bash_lib.sh`
- [ ] Ensure consistent function naming with pwsh_lib
- [ ] Add missing functions (align with PowerShell module)
- [ ] Improve error handling & logging
- [ ] Add comprehensive comments

**Acceptance Criteria**:

- [ ] All existing POSIX hooks still work (regression test)
- [ ] Function signatures match PowerShell equivalents (same semantics)
- [ ] ShellCheck passes with no warnings
- [ ] Documentation complete (inline + README)

**Estimated Effort**: 8 hours
**Type**: Refactoring
**Owner**: Backend team
**Depends On**: 1.3

**Testing**:

```bash
shellcheck -x hooks/lib/bash_lib.sh
bash -n hooks/lib/bash_lib.sh
```

### Task 1.5: Set Up Cross-Platform Test Infrastructure

**Description**: Establish testing framework for both shells (BATS + Pester)
**Setup**:

- [ ] Install BATS-Core (for bash tests)
- [ ] Install Pester (for PowerShell tests)
- [ ] Create test fixtures and helpers
- [ ] Build Docker containers for CI (Linux + Windows)
- [ ] GitHub Actions workflows for matrix testing

**Acceptance Criteria**:

- [ ] `task test:shell` runs all shell tests
- [ ] Tests pass on Linux (bash) and Windows (PowerShell) in Docker
- [ ] CI/CD matrix includes linux-bash, macos-bash, windows-pwsh
- [ ] Coverage reporting integrated (70% min for shell code)

**Estimated Effort**: 12 hours
**Type**: Infrastructure
**Owner**: DevOps/QA team
**Depends On**: 1.2, 1.3

**Files**:

- `tests/shell/test_dispatcher.rs` (Rust dispatcher tests)
- `tests/shell/test_bash_lib.bats` (bash library tests)
- `tests/shell/test_pwsh_lib.ps1` (PowerShell tests via Pester)
- `.github/workflows/test-cross-platform.yml` (CI matrix)
- `tests/ci/docker/Dockerfile.linux`
- `tests/ci/docker/Dockerfile.windows`

### Task 1.6: Write Contributor Guide

**Description**: Document cross-platform shell patterns for contributors
**Content**:

- [ ] Pattern examples (error handling, path resolution, env vars)
- [ ] Checklist for new hooks (both shells required)
- [ ] Common pitfalls and how to avoid
- [ ] Testing requirements per shell
- [ ] Naming conventions (.sh vs .ps1)

**File**: `docs/guides/CROSS_PLATFORM_SHELL_PATTERNS.md`

**Acceptance Criteria**:

- [ ] Guide reviewed and approved
- [ ] Examples provided for all pattern categories
- [ ] Checklist can be used by contributors as-is

**Estimated Effort**: 6 hours
**Type**: Documentation
**Owner**: Technical writer
**Depends On**: 1.1–1.4

---

## Phase 2: Integration (Weeks 3–4)

**Goal**: Integrate dispatcher into hooks system; implement CLI shims; profile integration

### Task 2.1: Integrate Dispatcher into Hook Pipeline

**Description**: Wire dispatcher into existing hook system; update hook invocation
**Changes**:

- [ ] Update hook-dispatcher.sh to use Rust binary
- [ ] Pass hook name, event, context to dispatcher
- [ ] Verify POSIX hooks still work (regression)
- [ ] Add PowerShell hook execution test

**Acceptance Criteria**:

- [ ] `hook-dispatcher qa-check PostToolUse` routes correctly
- [ ] POSIX hooks execute without modification
- [ ] PowerShell hooks execute and return status
- [ ] Error cases handled gracefully (missing hook, timeout)
- [ ] Logs written to `~/.thegent/logs/hooks.log`

**Estimated Effort**: 10 hours
**Type**: Integration
**Owner**: Backend team
**Depends On**: 1.2

### Task 2.2: Create PowerShell CLI Shim

**Description**: Implement PowerShell entry point script
**File**: `scripts/thegent.ps1`

**Features**:

- [ ] Parse arguments
- [ ] Invoke `uv run thegent` with args
- [ ] Handle errors and exit codes
- [ ] Support stdin/stdout piping

**Acceptance Criteria**:

- [ ] `.\scripts\thegent.ps1 --help` works
- [ ] Arguments passed through correctly
- [ ] Exit codes propagated

**Estimated Effort**: 4 hours
**Type**: Implementation
**Owner**: PowerShell specialist
**Depends On**: Nothing

### Task 2.3: Create POSIX CLI Shim

**Description**: Update/verify POSIX entry point script
**File**: `scripts/thegent.sh`

**Features**:

- [ ] Parse arguments
- [ ] Invoke `uv run thegent` with args
- [ ] Handle errors and exit codes
- [ ] Support stdin/stdout piping

**Acceptance Criteria**:

- [ ] `./scripts/thegent.sh --help` works
- [ ] Arguments passed through correctly
- [ ] ShellCheck passes

**Estimated Effort**: 2 hours
**Type**: Implementation
**Owner**: Backend team
**Depends On**: Nothing

### Task 2.4: Implement Shim Installation Script

**Description**: Create installation script for CLI entry points
**File**: `scripts/install-shims.sh`

**Behavior**:

- [ ] Install POSIX shim to `~/.local/bin/thegent`
- [ ] Install PowerShell shim to `~/.local/bin/thegent.ps1` (or equivalent)
- [ ] Update PATH if needed
- [ ] Verify installation

**Acceptance Criteria**:

- [ ] Script runs on POSIX systems without errors
- [ ] Script can run on PowerShell (via bash in WSL or native)
- [ ] `which thegent` or `Get-Command thegent` works after installation
- [ ] Uninstall script provided (`scripts/uninstall-shims.sh`)

**Estimated Effort**: 6 hours
**Type**: Implementation
**Owner**: DevOps team
**Depends On**: 2.2, 2.3

### Task 2.5: POSIX Shell Profile Integration

**Description**: Create initialization for bash/zsh
**Files**:

- `scripts/init-posix.sh`
- `scripts/init-posix-completions.sh` (optional)

**Behavior**:

- [ ] Detect shell (bash, zsh, sh)
- [ ] Append init snippet to profile (~/.bashrc, ~/.zshrc)
- [ ] Add thegent to PATH
- [ ] Load functions/aliases

**Acceptance Criteria**:

- [ ] Init script works in bash and zsh
- [ ] Safe to run multiple times (idempotent)
- [ ] PATH contains ~/.local/bin after init
- [ ] thegent command available in new shell session

**Estimated Effort**: 8 hours
**Type**: Implementation
**Owner**: Backend team
**Depends On**: 2.4

### Task 2.6: PowerShell Profile Integration

**Description**: Create initialization for PowerShell
**Files**:

- `scripts/init-pwsh.ps1`
- `scripts/init-pwsh-completions.ps1` (optional)

**Behavior**:

- [ ] Detect PowerShell profile location
- [ ] Append init snippet to profile ($PROFILE)
- [ ] Add thegent to PATH (environment variable)
- [ ] Create function alias

**Acceptance Criteria**:

- [ ] Init script works in PowerShell 7+
- [ ] Safe to run multiple times (idempotent)
- [ ] PATH contains ~/.local/bin after init
- [ ] thegent function available in new PowerShell session

**Estimated Effort**: 8 hours
**Type**: Implementation
**Owner**: PowerShell specialist
**Depends On**: 2.4

### Task 2.7: Migrate Existing Hooks to Common Library

**Description**: Update critical hooks to use common library functions
**Target Hooks** (Phase 2):

- [ ] `hooks/qa-check.sh` → `hooks/qa-check.sh` (refactored)
- [ ] `hooks/qa-check.ps1` (new PowerShell version)
- [ ] `hooks/pre-commit.sh` → `hooks/pre-commit.sh` (refactored)
- [ ] `hooks/pre-commit.ps1` (new PowerShell version)

**Acceptance Criteria**:

- [ ] Hooks use `validate_changes`, `log_info`, etc. from library
- [ ] POSIX versions still work (regression test)
- [ ] PowerShell versions work (new test)
- [ ] No lint warnings (ShellCheck, PSScriptAnalyzer)

**Estimated Effort**: 10 hours
**Type**: Refactoring
**Owner**: Backend team
**Depends On**: 1.4, 1.6

### Task 2.8: Integration Test Suite

**Description**: Write comprehensive cross-platform integration tests
**Files**: `tests/integration/test_cross_platform.sh`

**Test Cases**:

- [ ] Dispatcher routes POSIX hooks correctly
- [ ] Dispatcher routes PowerShell hooks correctly
- [ ] CLI shims work on both platforms
- [ ] Library functions behave identically across shells
- [ ] Error handling works (missing hook, timeout, failure)
- [ ] Environment variables passed correctly

**Acceptance Criteria**:

- [ ] All test cases pass on Linux (bash) and Windows (PowerShell)
- [ ] Tests run in CI matrix
- [ ] Coverage ≥80% for critical paths

**Estimated Effort**: 12 hours
**Type**: QA
**Owner**: QA team
**Depends On**: 2.1–2.7

---

## Phase 3: Hardening & Documentation (Weeks 5–6)

**Goal**: Performance tuning, comprehensive testing, user documentation, cutover

### Task 3.1: Performance Benchmarking

**Description**: Measure and optimize hook execution latency
**Metrics**:

- [ ] Hook dispatcher startup time (target: <5ms)
- [ ] POSIX hook execution time
- [ ] PowerShell hook execution time
- [ ] End-to-end latency (dispatcher + hook + Python CLI)

**Acceptance Criteria**:

- [ ] Latency parity between shells (<10ms difference)
- [ ] No regression vs. baseline (existing hooks)
- [ ] Benchmark report generated (`docs/reference/CROSS_PLATFORM_PERFORMANCE.md`)

**Estimated Effort**: 8 hours
**Type**: Performance
**Owner**: Performance team
**Depends On**: 2.1–2.8

### Task 3.2: Security Audit

**Description**: Review shell scripts for security vulnerabilities
**Checks**:

- [ ] Command injection risks (validate user input)
- [ ] Path traversal risks (normalize paths)
- [ ] Privilege escalation risks
- [ ] Environment variable pollution

**Tools**: ShellCheck (-S for security), shellscan (if available), manual review

**Acceptance Criteria**:

- [ ] All security issues resolved
- [ ] Security audit report generated
- [ ] POSIX and PowerShell scripts equally secure

**Estimated Effort**: 10 hours
**Type**: Security
**Owner**: Security team
**Depends On**: 2.7

### Task 3.3: Comprehensive Documentation

**Description**: Create user-facing documentation
**Documents**:

- [ ] Installation guide (platform-specific)
- [ ] Shell setup guide (bash, zsh, PowerShell)
- [ ] Troubleshooting guide (platform-specific issues)
- [ ] API documentation for hook writers
- [ ] Examples and recipes

**Files**:

- `docs/guides/CROSS_PLATFORM_INSTALLATION.md`
- `docs/guides/CROSS_PLATFORM_SHELL_SETUP.md`
- `docs/guides/CROSS_PLATFORM_TROUBLESHOOTING.md`
- Update `docs/guides/HOOK_DEVELOPMENT.md`

**Acceptance Criteria**:

- [ ] All platforms covered (Linux, macOS, Windows)
- [ ] Examples for bash, zsh, PowerShell
- [ ] Troubleshooting covers common issues
- [ ] Documentation reviewed by tech writer

**Estimated Effort**: 12 hours
**Type**: Documentation
**Owner**: Technical writer
**Depends On**: 2.7, 3.1

### Task 3.4: Windows-Specific Testing

**Description**: Validate on native Windows (PowerShell, not WSL)
**Test Plan**:

- [ ] Run full test suite on Windows 10/11
- [ ] Verify dispatcher on native PowerShell
- [ ] Test CLI shims and profile integration
- [ ] Document Windows-specific quirks (if any)

**Acceptance Criteria**:

- [ ] All tests pass on Windows native
- [ ] No WSL dependency (pure PowerShell)
- [ ] Performance meets targets

**Estimated Effort**: 8 hours
**Type**: QA
**Owner**: QA team (Windows specialist)
**Depends On**: 2.1–2.8

### Task 3.5: CI/CD Pipeline Expansion

**Description**: Expand GitHub Actions to include Windows runners
**Changes**:

- [ ] Add windows-latest runner to matrix
- [ ] Ensure PowerShell-specific tests run on Windows
- [ ] Verify POSIX tests skip on Windows (or run via WSL)
- [ ] Build and cache Rust binary for Windows

**Acceptance Criteria**:

- [ ] CI matrix includes linux-latest, macos-latest, windows-latest
- [ ] All tests pass on all platforms
- [ ] Pipeline completes in reasonable time (<20 min)

**Estimated Effort**: 6 hours
**Type**: Infrastructure
**Owner**: DevOps team
**Depends On**: 1.5

### Task 3.6: Backward Compatibility Verification

**Description**: Ensure no breaking changes to existing users
**Test Plan**:

- [ ] Existing POSIX users unaffected (no required changes)
- [ ] Existing hooks work without modification
- [ ] No new dependencies for POSIX-only users (optional: PowerShell)

**Acceptance Criteria**:

- [ ] POSIX hooks work as before
- [ ] No required changes for existing users
- [ ] PowerShell is purely additive (opt-in)

**Estimated Effort**: 4 hours
**Type**: QA
**Owner**: QA team
**Depends On**: 2.1–3.5

### Task 3.7: Launch & Cutover Planning

**Description**: Plan and execute release
**Checklist**:

- [ ] Release notes prepared
- [ ] Migration guide for Windows users
- [ ] Announcement (blog post, changelog)
- [ ] Support plan (issue templates, FAQ)
- [ ] Rollback plan (if needed)

**Acceptance Criteria**:

- [ ] Release notes reviewed
- [ ] Migration guide clear and tested
- [ ] Support plan covers expected issues

**Estimated Effort**: 6 hours
**Type**: Planning
**Owner**: Product team
**Depends On**: 3.1–3.6

### Task 3.8: Post-Launch Monitoring

**Description**: Monitor adoption and issues in first month
**Metrics**:

- [ ] Windows user adoption rate
- [ ] Issue reports (platform-specific)
- [ ] Performance metrics (hooks, startup)
- [ ] User feedback

**Acceptance Criteria**:

- [ ] Issues triaged and resolved
- [ ] Performance meets targets
- [ ] User satisfaction >90%

**Estimated Effort**: 8 hours (ongoing, first month)
**Type**: Operations
**Owner**: Support team
**Depends On**: 3.7

---

## Summary Table

| Phase  | Task                        | Hours   | Owner       | Status  |
| ------ | --------------------------- | ------- | ----------- | ------- |
| **P1** | 1.1 Design Dispatcher       | 8       | Arch        | Pending |
|        | 1.2 Implement Dispatcher    | 16      | Backend     | Pending |
|        | 1.3 PowerShell Library      | 12      | PowerShell  | Pending |
|        | 1.4 Refactor bash_lib       | 8       | Backend     | Pending |
|        | 1.5 Test Infrastructure     | 12      | QA/DevOps   | Pending |
|        | 1.6 Contributor Guide       | 6       | Tech Writer | Pending |
|        | **P1 Total**                | **62**  |             |         |
| **P2** | 2.1 Dispatcher Integration  | 10      | Backend     | Pending |
|        | 2.2 PowerShell Shim         | 4       | PowerShell  | Pending |
|        | 2.3 POSIX Shim              | 2       | Backend     | Pending |
|        | 2.4 Shim Installation       | 6       | DevOps      | Pending |
|        | 2.5 POSIX Profile Init      | 8       | Backend     | Pending |
|        | 2.6 PowerShell Profile Init | 8       | PowerShell  | Pending |
|        | 2.7 Hook Migration          | 10      | Backend     | Pending |
|        | 2.8 Integration Tests       | 12      | QA          | Pending |
|        | **P2 Total**                | **60**  |             |         |
| **P3** | 3.1 Performance Bench       | 8       | Performance | Pending |
|        | 3.2 Security Audit          | 10      | Security    | Pending |
|        | 3.3 Documentation           | 12      | Tech Writer | Pending |
|        | 3.4 Windows Testing         | 8       | QA          | Pending |
|        | 3.5 CI/CD Expansion         | 6       | DevOps      | Pending |
|        | 3.6 Compat Verify           | 4       | QA          | Pending |
|        | 3.7 Launch Plan             | 6       | Product     | Pending |
|        | 3.8 Post-Launch Monitor     | 8       | Support     | Pending |
|        | **P3 Total**                | **62**  |             |         |
|        | **Grand Total**             | **184** |             |         |

---

## Milestones & Gates

### Milestone 1: Foundation Complete (End of Week 2)

**Gate Criteria**:

- [ ] Dispatcher compiles and passes unit tests
- [ ] PowerShell library functions tested and working
- [ ] POSIX library refactored and tested
- [ ] Test infrastructure ready (BATS, Pester, CI matrix)

### Milestone 2: Integration Complete (End of Week 4)

**Gate Criteria**:

- [ ] Dispatcher wired into hook pipeline
- [ ] CLI shims working on both platforms
- [ ] Shell profile integration working
- [ ] Critical hooks migrated to common library
- [ ] Integration tests passing

### Milestone 3: Launch Ready (End of Week 6)

**Gate Criteria**:

- [ ] Performance & security audits passed
- [ ] Comprehensive documentation complete
- [ ] Windows-native testing passed
- [ ] CI/CD matrix green
- [ ] Backward compatibility verified

---

## Risk Mitigation

| Risk                                  | Probability | Impact | Mitigation                                            |
| ------------------------------------- | ----------- | ------ | ----------------------------------------------------- |
| PowerShell 7+ adoption low on Windows | Medium      | High   | Support PS 5.1 legacy path (Phase 2)                  |
| Performance degradation               | Low         | Medium | Early benchmarking (Task 3.1), optimize before launch |
| POSIX regression                      | Low         | High   | Comprehensive regression testing (Task 2.8)           |
| Windows CI runner slow                | Medium      | Low    | Cache Rust binary; parallelize tests                  |
| User confusion (which shell to use)   | Medium      | Low    | Clear documentation; auto-detection in code           |

---

## Success Criteria (Overall)

- [ ] POSIX users unaffected (backward compatible)
- [ ] Windows users can use native PowerShell (no WSL required)
- [ ] Both shells have feature parity
- [ ] Hook execution latency <160ms (acceptable overhead)
- [ ] Test coverage ≥80% for all code
- [ ] Documentation complete and comprehensive
- [ ] CI/CD matrix covers all platforms
- [ ] User adoption >50% Windows users in first 3 months
- [ ] Issue triage time <24 hours

---

## See Also

- [proposal.md](./proposal.md) - Comprehensive problem statement
- [design.md](./design.md) - Technical architecture & patterns
- `docs/guides/CROSS_PLATFORM_SHELL_PATTERNS.md` - Contributor guidelines
