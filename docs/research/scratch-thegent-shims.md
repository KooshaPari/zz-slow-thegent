<DONE>
# Thegent-Shims (Rust) Implementation Documentation

> **WORK_STREAM ID:** scratch-thegent-shims
> **Priority:** P1
> **Status:** ✅ Documentation Complete (Implementation in progress by other agents)

## Summary

This document provides implementation documentation for `thegent-shims`, a Rust-based shim system for git/grep/find/agent operations. This is Phase 2 of the FULL_SHELL_TO_RUST migration.

## Architecture

### Purpose

Replace shell-based shims with fast Rust binaries for:

- Git operations (multi-tenant lock coordination, index.lock handling)
- Tool accelerators (grep→rg, find→fd, jq→jaq)
- Agent accelerators (codex, copilot)
- Role accelerators (run, bg, ps → `thegent {role}`)

### Implementation Status

**Current State**: Multiple agents working on implementation (see WORK_STREAM.md CLAIMED section)

**Components**:

- Rust binary: `thegent-shims` (in development)
- Shim installation: `install-shims` command (exists)
- Integration: Hook system and CLI (planned)

**Related Work**:

- `thegent-hooks` Rust binary already exists (Phase 1 complete)
- Shell shims currently in use (`hooks/lib/git-wrapper.sh`, etc.)
- Migration path: Shell → Rust shims → Full Rust hooks

## Design

### Shim Types

1. **Git Shim**
   - Multi-tenant lock coordination
   - `index.lock` handling
   - `git_cached` wrapper

2. **Tool Accelerators**
   - `grep` → `rg` (ripgrep)
   - `find` → `fd`
   - `jq` → `jaq`

3. **Agent Accelerators**
   - `codex` → exec real binary
   - `copilot` → exec real binary

4. **Role Accelerators**
   - `run`, `bg`, `ps` → `thegent {role}`

### Implementation Plan

**Phase 1**: Core shim framework

- [ ] Rust project structure
- [ ] Command routing logic
- [ ] Binary build system

**Phase 2**: Git shim implementation

- [ ] Lock coordination
- [ ] Index.lock handling
- [ ] Git command passthrough

**Phase 3**: Tool accelerator shims

- [ ] rg, fd, jaq wrappers
- [ ] Fallback to system binaries

**Phase 4**: Agent accelerator shims

- [ ] codex/copilot exec wrappers
- [ ] Path resolution

**Phase 5**: Integration

- [ ] Install-shims integration
- [ ] Hook system integration
- [ ] Testing and validation

## References

- [FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md](../plans/FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md) - Migration plan
- [WORK_STREAM.md](../reference/WORK_STREAM.md)
- [scratchpad/session_review.md](../scratchpad/session_review.md)

## Notes

- Supersedes ultra-shim (Go) project
- Focus on performance-critical paths
- Maintain compatibility with existing shell scripts during migration
