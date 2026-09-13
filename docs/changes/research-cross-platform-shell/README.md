# Cross-Platform Shell Strategy: Research & Implementation

**Status**: Research Phase Complete → Ready for Implementation Planning
**Date**: 2026-02-18
**Priority**: P1 (Windows User Experience)

---

## Quick Start

This research package contains the strategy, design, and implementation plan for adding native PowerShell support to thegent while maintaining full backward compatibility with POSIX environments.

**Three-document structure**:

1. **[proposal.md](./proposal.md)** - Problem statement, requirements, high-level architecture
2. **[design.md](./design.md)** - Technical deep-dive, component design, patterns
3. **[tasks.md](./tasks.md)** - Phased breakdown, 184 engineering hours, weekly milestones

---

## Key Insight

**"Write Once, Run Everywhere" via Language Bindings**: Minimize shell-specific code by delegating complex logic to Python/Rust, then providing thin shell wrappers for both POSIX and PowerShell.

```
Shell (POSIX/PowerShell) → Invoke Python CLI → Python (logic) → Result
```

This allows both shells to call shared library functions (`validate_changes()`, `log_info()`, etc.) that invoke Python for the hard work.

---

## Problem We're Solving

### Current State

- thegent is POSIX-only (bash/sh)
- Windows users need WSL or MSYS2 (non-native experience)
- Hooks system doesn't support PowerShell
- No cross-shell abstraction patterns

### Desired State

- Native PowerShell support for Windows users
- Single codebase with shell-specific variants
- Hooks work seamlessly in both POSIX and PowerShell
- Performance parity (no Windows penalty)

---

## High-Level Solution

### Dual-Shell Strategy

```
┌─────────────────────────────────────────────────┐
│  User Hooks (POSIX .sh / PowerShell .ps1)      │
└─────────────────────────────────────────────────┘
           ↓                          ↓
    POSIX Runner                 PWShell Runner
   (bash/sh handler)           (pwsh handler)
           ↓                          ↓
┌──────────────────────────────────────────────────┐
│  Shell-Agnostic Dispatcher (Rust binary)        │
│  Routes based on platform/shell detected        │
└──────────────────────────────────────────────────┘
           ↓                          ↓
┌──────────────────────────────────────────────────┐
│  Cross-Platform Library                         │
│  - bash_lib.sh (POSIX)                          │
│  - pwsh_lib.ps1 (PowerShell)                    │
│  Shared Python logic underneath                 │
└──────────────────────────────────────────────────┘
```

### Key Components

| Component             | Purpose                                | Status              |
| --------------------- | -------------------------------------- | ------------------- |
| **Dispatcher**        | Route hooks to shell-specific runner   | To implement (Rust) |
| **POSIX Runner**      | Execute bash/sh hooks                  | Existing (refactor) |
| **PowerShell Runner** | Execute .ps1 hooks                     | To implement        |
| **Shared Library**    | Common functions in both shells        | To implement        |
| **CLI Shims**         | Entry points for both shells           | To implement        |
| **Test Framework**    | Cross-platform testing (BATS + Pester) | To implement        |

---

## Design Highlights

### Shell Pattern: Delegation to Python

Rather than duplicate business logic in both shells, use thin wrappers:

**POSIX** (`hooks/lib/bash_lib.sh`):

```bash
validate_changes() {
  uv run thegent hooks validate-files "$@"
}
```

**PowerShell** (`hooks/lib/pwsh_lib.ps1`):

```powershell
function Validate-Changes {
    & uv run thegent hooks validate-files @args
}
```

**Python** (`src/thegent/cli/hooks.py`):

```python
@click.command()
def validate_files(files):
    """Complex validation logic here"""
```

### Initialization Strategy

**POSIX**: Append to `~/.bashrc` / `~/.zshrc`

```bash
source ~/.local/share/thegent/init.sh
```

**PowerShell**: Append to `$PROFILE`

```powershell
. $HOME/.local/share/thegent/init.ps1
```

### Error Handling

**POSIX**:

```bash
set -euo pipefail
trap 'log_error "Line $LINENO"' ERR
```

**PowerShell**:

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
trap { Write-Log -Level Error }
```

---

## Implementation Timeline

### Phase 1: Foundation (Weeks 1–2) — 62 hours

- [ ] Design dispatcher (ADR)
- [ ] Implement Rust dispatcher binary
- [ ] Create PowerShell library module
- [ ] Refactor POSIX library for consistency
- [ ] Set up cross-platform testing (BATS + Pester + CI matrix)
- [ ] Write contributor guide

### Phase 2: Integration (Weeks 3–4) — 60 hours

- [ ] Wire dispatcher into hook pipeline
- [ ] Implement CLI shims (both shells)
- [ ] Shell profile integration (bash, zsh, PowerShell)
- [ ] Migrate critical hooks to common library
- [ ] Integration test suite

### Phase 3: Hardening (Weeks 5–6) — 62 hours

- [ ] Performance benchmarking
- [ ] Security audit
- [ ] Comprehensive documentation
- [ ] Windows-native testing
- [ ] CI/CD pipeline expansion
- [ ] Launch planning & monitoring

**Total**: ~184 engineering hours, 6 weeks

---

## Acceptance Criteria (Phase 1 Gate)

- [ ] AC-1: Hook dispatcher supports both POSIX and PowerShell runners
- [ ] AC-2: POSIX hooks continue to work without modification
- [ ] AC-3: PowerShell hooks can be written and executed with feature parity
- [ ] AC-4: Library functions available in both shells
- [ ] AC-5: CLI shims work on both bash and PowerShell
- [ ] AC-6: Cross-platform test suite passes on Linux, macOS, Windows (CI)
- [ ] AC-7: Documentation includes contributor guide with examples
- [ ] AC-8: No performance degradation (<5% latency increase)
- [ ] AC-9: All linters pass (ShellCheck + PSScriptAnalyzer)
- [ ] AC-10: New hook examples provided in both shells

---

## Architecture Decisions (Key Trade-offs)

| Decision                          | Rationale                              | Trade-off                                                   |
| --------------------------------- | -------------------------------------- | ----------------------------------------------------------- |
| Shell-agnostic dispatcher (Rust)  | Neutral, fast, avoid shell bias        | Small build step; worth it for clarity                      |
| Delegate to Python for logic      | Easier testing, single source of truth | Minor latency (100ms Python startup offset by code quality) |
| Dual hook files (.sh + .ps1)      | Self-documenting, auto-detect          | Duplicate hook definitions mitigated by shared library      |
| Test via Docker containers        | Reproducible, scalable, CI-friendly    | Container setup; pays off in reliability                    |
| Dual initialization (bash + pwsh) | User experience: automatic setup       | Platform-specific bootstrapping; mitigated by docs          |

---

## Risk & Mitigation

| Risk                       | Mitigation                                                    |
| -------------------------- | ------------------------------------------------------------- |
| PowerShell 7+ adoption low | Support PS 5.1 legacy path; document minimum requirements     |
| Performance degradation    | Early benchmarking (Task 3.1); optimize before launch         |
| POSIX regression           | Comprehensive regression testing; backward compatibility gate |
| Windows CI slow            | Cache Rust binary; parallelize tests                          |
| User confusion             | Clear documentation; auto-detection in code                   |

---

## Success Metrics (Post-Launch)

- **POSIX users**: 0% breaking changes (100% backward compatible)
- **Windows adoption**: >50% Windows users in first 3 months
- **Hook latency**: <160ms end-to-end (both shells, <10ms parity)
- **Test coverage**: ≥80% for all code
- **Documentation**: Complete for all platforms (Linux, macOS, Windows)
- **Issue triage**: <24 hour response time

---

## Related Documents

### In This Package

- [proposal.md](./proposal.md) - Requirements, problem statement, technology selection
- [design.md](./design.md) - Architecture, component design, patterns, testing strategy
- [tasks.md](./tasks.md) - 3-phase breakdown, 184 hours, weekly milestones

### To Be Created (Post-Approval)

- `docs/reference/ADR-CROSS_PLATFORM_SHELL.md` - Architecture Decision Record
- `docs/guides/CROSS_PLATFORM_SHELL_PATTERNS.md` - Contributor guidelines
- `docs/guides/CROSS_PLATFORM_INSTALLATION.md` - User installation guide
- `docs/reference/CROSS_PLATFORM_TEST_STRATEGY.md` - Testing approach

### Related Work

- [CONVERSATION_DUMP_2026-02-18.md](../../research/) - Research synthesis
- [CLAUDE.md](../../CLAUDE.md) - Global instruction context
- Shell References: POSIX, PowerShell docs, ShellCheck, PSScriptAnalyzer

---

## Next Steps

1. **Review** this research package with stakeholders
2. **Approve** the proposal and design (or request revisions)
3. **Kick off Phase 1** with architecture and dispatcher implementation
4. **Iterate** with weekly checkpoints and gate reviews
5. **Launch** Phase 2 after Phase 1 verification
6. **Monitor** post-launch adoption and issues

---

## Quick Reference

| Aspect                     | Details                                                             |
| -------------------------- | ------------------------------------------------------------------- |
| **Platforms Supported**    | Linux (bash), macOS (bash/zsh), Windows (PowerShell 7+), WSL (bash) |
| **Shell Minimum Versions** | bash 4.0+, zsh 5.0+, PowerShell 7.0+                                |
| **Key Dependencies**       | Rust (dispatcher), Python (thegent core), uv (package manager)      |
| **Test Frameworks**        | BATS-Core (bash), Pester (PowerShell), pytest (Python)              |
| **CI/CD**                  | GitHub Actions matrix (linux-latest, macos-latest, windows-latest)  |
| **Documentation**          | Markdown (guides), ADRs (decisions), API docs (hook patterns)       |
| **Backward Compatibility** | 100% (POSIX users unaffected; PowerShell is purely additive)        |

---

## File Manifest

```
docs/changes/research-cross-platform-shell/
├── README.md                  ← You are here
├── proposal.md                ← Problem statement & requirements
├── design.md                  ← Technical architecture & patterns
└── tasks.md                   ← Implementation breakdown (184 hours)
```

---

## Questions?

Refer to the detailed documents:

- **"Why cross-platform?"** → See [proposal.md § Problem Statement](./proposal.md#problem-statement)
- **"How does it work?"** → See [design.md § Architecture Overview](./design.md#architecture-overview)
- **"What's the plan?"** → See [tasks.md § Summary Table](./tasks.md#summary-table)
- **"What about my existing hooks?"** → See [design.md § Backward Compatibility](./design.md#backward-compatibility)

---

## Document Maintenance

**Last Updated**: 2026-02-18
**Owner**: Architecture Team
**Status**: Ready for Implementation
**Next Review**: Post-Phase 1 completion

This research package is living documentation. Update as:

- Design decisions evolve
- Implementation reveals new insights
- Community feedback arrives
- Performance tuning completes

---

**Version**: 1.0
**Approval Status**: Pending Stakeholder Review
