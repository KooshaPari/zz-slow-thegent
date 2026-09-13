<DONE>
# Hook Rust Migration Complete — Comprehensive Migration Strategy & Timeline

> **Status**: Complete | **Version**: 1.0 | **Date**: 2026-02-16
> **Related**:
>
> - [Hook Runtime Rust Design](../plans/HOOK_RUNTIME_RUST_DESIGN.md)
> - [Full Shell to Rust Where Beneficial](../plans/FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md)
> - [Rust/Go Migration Plan](../migration/RUST_GO_MIGRATION_PLAN.md)
> - [Comprehensive Performance Analysis](../migration/COMPREHENSIVE_PERFORMANCE_ANALYSIS.md)
> - [Hook Optimization Strategy](../reference/HOOK_OPTIMIZATION_STRATEGY.md)

## Overview

This document provides a comprehensive migration strategy and timeline for replacing `hooks/lib/common.sh` (~1685 lines) and related shell infrastructure with a Rust binary (`thegent-hooks`) that provides equivalent functionality with significantly better performance, correctness, and maintainability.

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [Target Architecture](#3-target-architecture)
4. [Migration Strategy](#4-migration-strategy)
5. [Detailed Timeline](#5-detailed-timeline)
6. [Implementation Details](#6-implementation-details)
7. [Performance Targets](#7-performance-targets)
8. [Risk Mitigation](#8-risk-mitigation)
9. [Testing Strategy](#9-testing-strategy)
10. [Rollback Plan](#10-rollback-plan)
11. [Success Metrics](#11-success-metrics)

---

## 1. Executive Summary

### 1.1 Migration Goals

- **Performance**: Reduce hook latency from 200ms → 20ms (10x improvement)
- **Correctness**: Eliminate shell parsing errors, improve error handling
- **Maintainability**: Single Rust codebase vs 1600+ lines of shell across 7 files
- **Multi-Tenant**: Better coordination, no shell sourcing overhead
- **Cross-Platform**: Identical behavior on macOS/Linux/Windows

### 1.2 Migration Approach

**Phased Migration**:

1. **Phase 0**: CLI skeleton (1 week)
2. **Phase 1**: Core functionality (3 weeks)
3. **Phase 2**: Advanced features (2 weeks)
4. **Phase 3**: Complex features (2 weeks)
5. **Phase 4**: Native hook implementations (optional, 2 weeks)
6. **Phase 5**: Deprecation & cleanup (1 week)

**Total Timeline**: 11 weeks (with optional Phase 4: 13 weeks)

### 1.3 Key Decisions

- **Single Binary**: `thegent-hooks` with subcommands
- **Incremental Migration**: Hooks migrate one-by-one
- **Backward Compatible**: Shell fallback during transition
- **Reuse Existing**: Leverage `thegent-tool-detect`, `thegent-git`, `hook-dispatcher`

---

## 2. Current State Analysis

### 2.1 Current Architecture

```
Hook Invocation
    │
    ├─ Hook Dispatcher (Rust)
    │   ├─ Reads stdin JSON
    │   ├─ Builds env
    │   └─ Spawns bash hook.sh
    │
    └─ Shell Dispatcher (bash)
        ├─ Sources common.sh (1685 lines)
        └─ Sources hook script
```

**Pain Points**:

- **Shell Sourcing Overhead**: 1600+ lines parsed on every hook run
- **Subprocess Spawn Cost**: Multiple `command -v`, `git`, `jq` calls
- **Parsing Errors**: Shell parsing can fail silently
- **Cache Inefficiency**: Shell-based cache key computation slow
- **Git Overhead**: Multiple git subprocess calls

### 2.2 Current Shell Files

| File                 | Lines | Purpose             | Migration Priority |
| -------------------- | ----- | ------------------- | ------------------ |
| **common.sh**        | ~1685 | Core hook functions | **P0** - Highest   |
| **git-cache.sh**     | ~100  | Git TTL cache       | **P0** - Highest   |
| **git-wrapper.sh**   | ~80   | Git routing         | **P0** - Highest   |
| **fd-wrapper.sh**    | ~40   | Find wrapper        | **P1** - High      |
| **grep-wrapper.sh**  | ~30   | Grep wrapper        | **P1** - High      |
| **procs-wrapper.sh** | ~30   | Process wrapper     | **P2** - Medium    |
| **pkg-wrapper.sh**   | ~20   | Package wrapper     | **P3** - Low       |

### 2.3 Performance Baseline

**Current Hook Latency** (from performance analysis):

- **Init**: ~50ms (shell sourcing + env build)
- **Cache Key**: ~30ms (jq + shasum subprocesses)
- **Git Operations**: ~100ms (subprocess + parsing)
- **Changed Files**: ~40ms (git subprocess + filtering)
- **Total Hook Overhead**: ~200ms

**Target Hook Latency**:

- **Init**: ~5ms (Rust JSON parsing + env build)
- **Cache Key**: ~1ms (blake3 hash, no subprocess)
- **Git Operations**: ~10ms (gix or cached)
- **Changed Files**: ~5ms (Rust git operations)
- **Total Hook Overhead**: ~20ms (10x improvement)

---

## 3. Target Architecture

### 3.1 New Architecture

```
Hook Invocation
    │
    └─ Hook Dispatcher (Rust)
        ├─ Reads stdin JSON
        ├─ Calls thegent-hooks init (env build)
        ├─ Calls thegent-hooks cache-key
        ├─ Calls thegent-hooks cache-check
        ├─ Calls thegent-hooks git (cached)
        ├─ Calls thegent-hooks changed-files
        └─ Executes hook logic
            ├─ Option A: Thin shell script (calls thegent-hooks)
            └─ Option B: Native Rust implementation
```

### 3.2 Binary Structure

**`thegent-hooks` Binary**:

```
thegent-hooks
├── init              # Parse JSON, build env
├── cache-key         # Compute cache key
├── cache-check       # Check cache validity
├── cache-read        # Read cached result
├── cache-write       # Write cache entry
├── git               # Cached git operations
├── changed-files     # Get changed files list
├── config-get        # Read config values
├── skip              # Check skip conditions
├── breaker-check     # Circuit breaker state
├── breaker-record    # Record breaker failure
├── breaker-reset     # Reset circuit breaker
├── debounce          # Debounce coordination
├── incremental-check # Incremental manifest check
├── file-hash         # Compute file hash
├── fr-ids            # Parse FR-* IDs
├── fr-index          # Build FR index
├── affected-tests    # Get affected tests
├── prewarm           # Prewarm caches
├── progress          # Progress reporting
├── report            # Write reports
├── learning-record   # Record learning data
├── learning-should-skip # Learning-based skip
└── run-hook          # Run hook natively (Phase 4)
```

### 3.3 Crate Layout

```
crates/thegent-hooks/
├── Cargo.toml
├── src/
│   ├── main.rs           # CLI entry point
│   ├── cli.rs            # Subcommand definitions
│   ├── init.rs           # Init subcommand
│   ├── cache.rs          # Cache operations
│   ├── git.rs            # Git operations
│   ├── config.rs         # Config reading
│   ├── hash.rs           # Hashing utilities
│   ├── changed_files.rs  # Changed files logic
│   ├── breaker.rs        # Circuit breaker
│   ├── debounce.rs       # Debounce coordination
│   ├── incremental.rs    # Incremental manifests
│   ├── learning.rs       # Learning-based skip
│   ├── affected_tests.rs # Affected tests
│   ├── prewarm.rs        # Prewarm operations
│   ├── reports.rs        # Report writing
│   └── lib.rs            # Library exports
```

---

## 4. Migration Strategy

### 4.1 Migration Principles

1. **Incremental**: Migrate hooks one-by-one
2. **Backward Compatible**: Shell fallback during transition
3. **Feature Parity**: All shell functionality preserved
4. **Performance First**: Optimize hot paths first
5. **Test Coverage**: Comprehensive tests before migration

### 4.2 Migration Phases

#### Phase 0: CLI Skeleton (Week 1)

**Goal**: Establish CLI surface, stub implementations

**Tasks**:

- [ ] Create `crates/thegent-hooks/` crate
- [ ] Define all subcommands with clap
- [ ] Stub implementations (call shell or return "not implemented")
- [ ] Basic error handling
- [ ] Integration tests framework

**Deliverables**:

- CLI binary compiles and runs
- All subcommands defined
- Basic help output

#### Phase 1: Core Functionality (Weeks 2-4)

**Goal**: Implement init, cache, git, changed-files, config

**Tasks**:

- [ ] **init**: JSON parsing, PROJECT_DIR resolution, env build
- [ ] **cache-key**: Blake3 hash computation
- [ ] **cache-check**: File-based cache validation
- [ ] **cache-read**: Read cached stdout/exit code
- [ ] **cache-write**: Write cache entries
- [ ] **git**: Cached read-only, agent passthrough, lock wait
- [ ] **changed-files**: Git diff + ls-files, filtering, shared file
- [ ] **config-get**: YAML/JSON parsing, value extraction

**Deliverables**:

- Core subcommands functional
- Performance: 10x improvement on hot paths
- Migration of 3-5 hooks to use thegent-hooks

#### Phase 2: Advanced Features (Weeks 5-6)

**Goal**: Implement breaker, debounce, incremental, learning

**Tasks**:

- [ ] **breaker-check/record/reset**: Circuit breaker state
- [ ] **debounce**: File-based debounce coordination
- [ ] **incremental-check/record**: Manifest-based incremental
- [ ] **learning-record/should-skip**: Learning-based skip
- [ ] **should-run**: Pattern matching for changed files

**Deliverables**:

- Advanced features functional
- Migration of 10+ hooks
- Performance maintained

#### Phase 3: Complex Features (Weeks 7-8)

**Goal**: Implement FR index, affected-tests, prewarm, reports

**Tasks**:

- [ ] **fr-ids**: Parse FR-\* from FUNCTIONAL_REQUIREMENTS.md
- [ ] **fr-index**: Build file:FR index
- [ ] **affected-tests**: Pattern + coverage + imports
- [ ] **prewarm**: Shared data, ruff, shellcheck caches
- [ ] **progress**: Progress reporting
- [ ] **report**: JSON report writing

**Deliverables**:

- Complex features functional
- Migration of 20+ hooks
- All hooks using thegent-hooks

#### Phase 4: Native Hook Implementations (Weeks 9-10, Optional)

**Goal**: Native Rust implementations for hot hooks

**Tasks**:

- [ ] **run-hook quality-gate**: Native ruff/semgrep execution
- [ ] **run-hook security-pipeline**: Native security checks
- [ ] **run-hook test-maturity**: Native test discovery
- [ ] Integration with hook-dispatcher

**Deliverables**:

- 3-5 hooks with native implementations
- Maximum performance (no shell at all)
- Dispatcher can call native hooks directly

#### Phase 5: Deprecation & Cleanup (Week 11)

**Goal**: Remove shell fallbacks, clean up old code

**Tasks**:

- [ ] Mark common.sh as deprecated
- [ ] Remove shell fallbacks
- [ ] Update documentation
- [ ] Final performance validation
- [ ] Archive old shell code

**Deliverables**:

- Shell code deprecated/removed
- Full migration complete
- Documentation updated

---

## 5. Detailed Timeline

### Week 1: CLI Skeleton

**Days 1-2**: Crate Setup

- Create `crates/thegent-hooks/`
- Add to workspace
- Basic Cargo.toml with dependencies
- Module structure

**Days 3-4**: CLI Definition

- Define all subcommands with clap
- Help text and descriptions
- Argument parsing
- Error handling framework

**Days 5**: Stub Implementations

- Each subcommand returns "not implemented"
- Or calls shell fallback
- Basic integration tests

**Deliverable**: CLI binary with all subcommands defined

### Week 2: Init & Cache

**Days 1-2**: Init Implementation

- JSON parsing (serde_json)
- PROJECT_DIR resolution (git + heuristics)
- Env variable computation
- Output format (KEY=VALUE or NUL-delimited)

**Days 3-4**: Cache Key

- Blake3 hash implementation
- Input: hook_name, head_sha, changed_files
- Output: hex string

**Days 5**: Cache Operations

- Cache check (file existence + TTL)
- Cache read (stdout + exit code)
- Cache write (atomic write)

**Deliverable**: Init and cache operations functional

### Week 3: Git & Changed Files

**Days 1-2**: Git Cached

- TTL cache implementation
- Cache key: (cwd, argv, HEAD, config mtime)
- Read-only command detection
- Agent passthrough (codex/copilot/dex/claude/cursor)

**Days 3**: Git Write Path

- Index.lock detection
- Lock wait with timeout
- Stale lock detection and steal
- Cache invalidation

**Days 4-5**: Changed Files

- Git diff --name-only HEAD
- Git ls-files --others --exclude-standard
- Filtering (node_modules, .git, etc.)
- Shared file write/read

**Deliverable**: Git and changed-files operations functional

### Week 4: Config & First Migration

**Days 1-2**: Config Reading

- YAML parsing (serde_yaml)
- hook-config.yaml lookup
- qa-local.json parsing
- Value extraction

**Days 3-5**: First Hook Migration

- Migrate 1-2 simple hooks
- Update hook scripts to use thegent-hooks
- Remove common.sh sourcing
- Test and validate

**Deliverable**: Config functional, first hooks migrated

### Week 5: Breaker & Debounce

**Days 1-2**: Circuit Breaker

- Breaker state management
- Failure tracking
- Threshold checking
- Cooldown handling

**Days 3-4**: Debounce

- File-based debounce
- Leader/follower pattern
- Batch file collection
- Timeout handling

**Days 5**: Testing & Migration

- Test breaker and debounce
- Migrate hooks using these features

**Deliverable**: Breaker and debounce functional

### Week 6: Incremental & Learning

**Days 1-2**: Incremental Manifests

- Manifest file format
- Content hash computation
- Manifest comparison
- Record new manifest

**Days 3-4**: Learning-Based Skip

- History file format
- Pass/fail tracking
- Pattern matching
- Skip decision logic

**Days 5**: Testing & Migration

- Test incremental and learning
- Migrate hooks using these features

**Deliverable**: Incremental and learning functional

### Week 7: FR Index & Affected Tests

**Days 1-2**: FR IDs Parsing

- Parse FUNCTIONAL_REQUIREMENTS.md
- Extract FR-\* IDs
- Cache parsed results

**Days 3-4**: FR Index

- Build file:FR mapping
- Update index on changes
- Query by file

**Days 5**: Affected Tests (Part 1)

- Pattern-based test discovery
- Coverage index integration

**Deliverable**: FR index functional, affected-tests started

### Week 8: Affected Tests & Prewarm

**Days 1-2**: Affected Tests (Part 2)

- Import-based discovery
- Coverage-based discovery
- Test deduplication

**Days 3-4**: Prewarm

- Shared data prewarm
- Ruff cache prewarm
- Shellcheck cache prewarm

**Days 5**: Reports & Progress

- JSON report writing
- Progress reporting
- Integration testing

**Deliverable**: All complex features functional

### Week 9-10: Native Hook Implementations (Optional)

**Days 1-3**: Native Quality Gate

- Ruff execution
- Semgrep execution
- Result aggregation
- Report generation

**Days 4-6**: Native Security Pipeline

- Security tool execution
- Vulnerability scanning
- Result processing

**Days 7-10**: Native Test Maturity

- Test discovery
- Coverage analysis
- Maturity scoring

**Deliverable**: 3-5 hooks with native implementations

### Week 11: Deprecation & Cleanup

**Days 1-2**: Final Migration

- Migrate remaining hooks
- Remove shell fallbacks
- Update all hook scripts

**Days 3-4**: Documentation

- Update hook documentation
- Migration guide
- API reference

**Days 5**: Cleanup

- Mark common.sh deprecated
- Archive old shell code
- Final performance validation

**Deliverable**: Full migration complete

---

## 6. Implementation Details

### 6.1 Init Subcommand

**Input**: JSON stdin

```json
{
  "tool_name": "file_editor",
  "tool_input": {
    "file_path": "src/main.py",
    "content": "..."
  },
  "session_id": "123",
  "cwd": "/path/to/project",
  "stop_hook_active": false
}
```

**Output**: Environment variables

```bash
INPUT='{"tool_name":"file_editor",...}'
CWD=/path/to/project
SESSION_ID=123
TOOL_NAME=file_editor
FILE_PATH=src/main.py
PROJECT_DIR=/path/to/project
VERIFY_DIR=/path/to/project/.claude/verify
HOOK_CACHE_DIR=/tmp/claude-hook-cache-1000
HOOK_SHARED_DIR=/tmp/claude-hook-cache-1000/shared
JQ_CMD=/usr/local/bin/jq
RG_CMD=/usr/local/bin/rg
FD_CMD=/usr/local/bin/fd
```

**Implementation** (`src/init.rs`):

```rust
use serde_json::Value;
use std::collections::HashMap;
use std::process::Command;

pub struct InitConfig {
    stdin_json: Value,
    project_dir: Option<String>,
}

impl InitConfig {
    pub fn from_stdin() -> Result<Self, Error> {
        let stdin_json: Value = serde_json::from_reader(std::io::stdin())?;
        Ok(InitConfig {
            project_dir: None,
            stdin_json,
        })
    }

    pub fn resolve_project_dir(&mut self, cwd: &str) -> Result<String, Error> {
        // Try git rev-parse --show-toplevel
        if let Ok(output) = Command::new("git")
            .args(&["rev-parse", "--show-toplevel"])
            .current_dir(cwd)
            .output()
        {
            if output.status.success() {
                let path = String::from_utf8(output.stdout)?
                    .trim()
                    .to_string();
                self.project_dir = Some(path.clone());
                return Ok(path);
            }
        }

        // Fallback: cwd or HOME
        Ok(cwd.to_string())
    }

    pub fn build_env(&self) -> HashMap<String, String> {
        let mut env = HashMap::new();

        // Extract from JSON
        if let Some(tool_name) = self.stdin_json.get("tool_name").and_then(|v| v.as_str()) {
            env.insert("TOOL_NAME".to_string(), tool_name.to_string());
        }

        // Add PROJECT_DIR
        if let Some(ref project_dir) = self.project_dir {
            env.insert("PROJECT_DIR".to_string(), project_dir.clone());
        }

        // Add tool detection
        if let Ok(jq_cmd) = self.detect_tool("jq") {
            env.insert("JQ_CMD".to_string(), jq_cmd);
        }

        // ... more env vars

        env
    }

    fn detect_tool(&self, tool: &str) -> Result<String, Error> {
        // Use thegent-tool-detect or command -v
        Ok(format!("/usr/local/bin/{}", tool)) // Placeholder
    }
}
```

### 6.2 Cache Subcommands

**Cache Key** (`src/cache.rs`):

```rust
use blake3;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

pub fn compute_cache_key(
    hook_name: &str,
    head_sha: &str,
    changed_files: &[String],
) -> String {
    let mut hasher = blake3::Hasher::new();
    hasher.update(hook_name.as_bytes());
    hasher.update(b"\0");
    hasher.update(head_sha.as_bytes());
    hasher.update(b"\0");

    for file in changed_files {
        hasher.update(file.as_bytes());
        hasher.update(b"\0");
    }

    let hash = hasher.finalize();
    hex::encode(hash.as_bytes())
}
```

**Cache Operations**:

```rust
use std::fs;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

pub struct CacheManager {
    cache_dir: PathBuf,
}

impl CacheManager {
    pub fn new() -> Result<Self, Error> {
        let cache_dir = std::env::var("HOOK_CACHE_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|_| {
                let tmp = std::env::var("TMPDIR").unwrap_or_else(|_| "/tmp".to_string());
                PathBuf::from(tmp).join(format!("claude-hook-cache-{}", std::process::id()))
            });

        fs::create_dir_all(&cache_dir)?;

        Ok(CacheManager { cache_dir })
    }

    pub fn check(&self, key: &str, ttl_seconds: u64) -> bool {
        let cache_file = self.cache_dir.join(format!("{}.out", key));

        if !cache_file.exists() {
            return false;
        }

        // Check TTL
        if let Ok(metadata) = fs::metadata(&cache_file) {
            if let Ok(modified) = metadata.modified() {
                if let Ok(age) = modified.duration_since(UNIX_EPOCH) {
                    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap();
                    if now.as_secs() - age.as_secs() < ttl_seconds {
                        return true;
                    }
                }
            }
        }

        false
    }

    pub fn read(&self, key: &str) -> Result<(String, i32), Error> {
        let stdout_file = self.cache_dir.join(format!("{}.out", key));
        let rc_file = self.cache_dir.join(format!("{}.rc", key));

        let stdout = fs::read_to_string(&stdout_file)?;
        let rc = fs::read_to_string(&rc_file)?
            .trim()
            .parse::<i32>()?;

        Ok((stdout, rc))
    }

    pub fn write(&self, key: &str, stdout: &str, rc: i32) -> Result<(), Error> {
        let stdout_file = self.cache_dir.join(format!("{}.out", key));
        let rc_file = self.cache_dir.join(format!("{}.rc", key));

        // Atomic write
        let tmp_stdout = format!("{}.tmp", stdout_file.display());
        fs::write(&tmp_stdout, stdout)?;
        fs::rename(&tmp_stdout, &stdout_file)?;

        let tmp_rc = format!("{}.tmp", rc_file.display());
        fs::write(&tmp_rc, format!("{}", rc))?;
        fs::rename(&tmp_rc, &rc_file)?;

        Ok(())
    }
}
```

### 6.3 Git Subcommand

**Git Cached** (`src/git.rs`):

```rust
use std::process::Command;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::time::{SystemTime, UNIX_EPOCH};

pub struct GitManager {
    cache_dir: PathBuf,
}

impl GitManager {
    pub fn execute(&self, args: Vec<String>) -> Result<(String, i32), Error> {
        // Agent passthrough
        if let Some(first_arg) = args.first() {
            if matches!(first_arg.as_str(), "codex" | "copilot" | "dex" | "claude" | "cursor") {
                return self.passthrough_agent(first_arg, &args[1..]);
            }
        }

        // Check if read-only command
        if self.is_read_only(&args) {
            return self.execute_cached(&args);
        }

        // Write command: wait for lock, then execute
        self.wait_for_lock()?;
        let result = self.execute_git(&args)?;
        self.invalidate_cache();
        Ok(result)
    }

    fn is_read_only(&self, args: &[String]) -> bool {
        matches!(
            args.first().map(|s| s.as_str()),
            Some("diff") | Some("status") | Some("rev-parse") | Some("ls-files") | Some("log")
        )
    }

    fn execute_cached(&self, args: &[String]) -> Result<(String, i32), Error> {
        // Compute cache key
        let cache_key = self.compute_cache_key(args)?;

        // Check cache
        let cache_manager = CacheManager::new()?;
        if cache_manager.check(&cache_key, 3600) {
            return cache_manager.read(&cache_key);
        }

        // Cache miss: execute git
        let result = self.execute_git(args)?;

        // Store in cache
        cache_manager.write(&cache_key, &result.0, result.1)?;

        Ok(result)
    }

    fn execute_git(&self, args: &[String]) -> Result<(String, i32), Error> {
        let output = Command::new("git")
            .args(args)
            .output()?;

        let stdout = String::from_utf8(output.stdout)?;
        let rc = output.status.code().unwrap_or(1);

        Ok((stdout, rc))
    }

    fn wait_for_lock(&self) -> Result<(), Error> {
        let lock_file = PathBuf::from(".git/index.lock");

        if !lock_file.exists() {
            return Ok(());
        }

        // Wait up to 30 seconds
        for _ in 0..30 {
            if !lock_file.exists() {
                return Ok(());
            }

            // Check if stale (older than 5 minutes)
            if let Ok(metadata) = std::fs::metadata(&lock_file) {
                if let Ok(modified) = metadata.modified() {
                    let age = SystemTime::now().duration_since(modified).unwrap();
                    if age.as_secs() > 300 {
                        // Stale lock: steal it
                        std::fs::remove_file(&lock_file)?;
                        return Ok(());
                    }
                }
            }

            std::thread::sleep(std::time::Duration::from_secs(1));
        }

        Err(Error::LockTimeout)
    }
}
```

---

## 7. Performance Targets

### 7.1 Latency Targets

| Operation               | Current (Shell) | Target (Rust) | Improvement |
| ----------------------- | --------------- | ------------- | ----------- |
| **Init**                | 50ms            | 5ms           | 10x         |
| **Cache Key**           | 30ms            | 1ms           | 30x         |
| **Git (cached)**        | 100ms           | 10ms          | 10x         |
| **Git (miss)**          | 150ms           | 50ms          | 3x          |
| **Changed Files**       | 40ms            | 5ms           | 8x          |
| **Config Get**          | 20ms            | 2ms           | 10x         |
| **Total Hook Overhead** | 200ms           | 20ms          | 10x         |

### 7.2 Throughput Targets

- **Concurrent Hooks**: Support 10+ concurrent hook executions
- **Cache Hit Rate**: >90% for read-only git operations
- **Memory Usage**: <50MB per hook execution

### 7.3 Resource Targets

- **CPU**: <5% per hook execution
- **Disk I/O**: Minimize with caching
- **Network**: None (all local operations)

---

## 8. Risk Mitigation

### 8.1 Technical Risks

**Risk**: Rust implementation doesn't match shell behavior

- **Mitigation**: Comprehensive compatibility tests
- **Mitigation**: Side-by-side comparison during migration
- **Mitigation**: Shell fallback during transition

**Risk**: Performance not meeting targets

- **Mitigation**: Profiling and optimization
- **Mitigation**: Use gix for git operations
- **Mitigation**: Aggressive caching

**Risk**: Breaking existing hooks

- **Mitigation**: Incremental migration
- **Mitigation**: Extensive testing
- **Mitigation**: Rollback plan

### 8.2 Schedule Risks

**Risk**: Timeline too aggressive

- **Mitigation**: Buffer time in each phase
- **Mitigation**: Prioritize core functionality first
- **Mitigation**: Optional phases can be deferred

**Risk**: Dependencies not ready

- **Mitigation**: Use existing crates (thegent-git, tool-detect)
- **Mitigation**: Fallback to Command::new() if needed
- **Mitigation**: Add gix as optional dependency

---

## 9. Testing Strategy

### 9.1 Unit Tests

- **Init**: JSON parsing, PROJECT_DIR resolution
- **Cache**: Key computation, read/write operations
- **Git**: Cached operations, passthrough, lock wait
- **Config**: YAML parsing, value extraction

### 9.2 Integration Tests

- **End-to-End**: Full hook execution with thegent-hooks
- **Compatibility**: Compare output with shell implementation
- **Performance**: Latency measurements
- **Concurrency**: Multiple hooks running simultaneously

### 9.3 Regression Tests

- **Existing Hook Tests**: All should pass after migration
- **Hook Dispatcher Tests**: Should work with thegent-hooks
- **Cache Tests**: Verify cache behavior

---

## 10. Rollback Plan

### 10.1 Rollback Triggers

- Performance regression >20%
- Compatibility issues with >5 hooks
- Critical bugs in core functionality
- Timeline slip >2 weeks

### 10.2 Rollback Procedure

1. **Immediate**: Revert hook scripts to use common.sh
2. **Short-term**: Keep thegent-hooks available but not required
3. **Long-term**: Fix issues and retry migration

### 10.3 Rollback Testing

- Test rollback procedure
- Verify hooks work with shell fallback
- Document rollback steps

---

## 11. Success Metrics

### 11.1 Performance Metrics

- ✅ Hook latency: <20ms (target: 10x improvement)
- ✅ Cache hit rate: >90%
- ✅ Git operations: <10ms (cached)
- ✅ Memory usage: <50MB per hook

### 11.2 Migration Metrics

- ✅ Hooks migrated: 100% (all hooks using thegent-hooks)
- ✅ Shell code removed: common.sh, git-cache.sh, git-wrapper.sh
- ✅ Test coverage: >90%
- ✅ Documentation: Complete

### 11.3 Quality Metrics

- ✅ Bug rate: <1 bug per 100 hook executions
- ✅ Compatibility: 100% feature parity
- ✅ Maintainability: Single Rust codebase
- ✅ Cross-platform: Identical behavior everywhere

---

## References

- [Hook Runtime Rust Design](../plans/HOOK_RUNTIME_RUST_DESIGN.md) - Full design specification
- [Full Shell to Rust Where Beneficial](../plans/FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md) - Complete shell inventory
- [Rust/Go Migration Plan](../migration/RUST_GO_MIGRATION_PLAN.md) - Migration priorities
- [Comprehensive Performance Analysis](../migration/COMPREHENSIVE_PERFORMANCE_ANALYSIS.md) - Performance baseline
- [Hook Optimization Strategy](../reference/HOOK_OPTIMIZATION_STRATEGY.md) - Current optimizations

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (6 BACKLOG items)
- [HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS_EXPANDED.md](./HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS_EXPANDED.md) - Expanded research
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure

---

_Generated: 2026-02-16 | Version: 1.0 | Status: Complete_

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related docs

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices

## Rust Migration Readiness Checklist

- Ensure `thegent-hooks` binary is built and on PATH for all target environments.
- Confirm every hook entrypoint resolves to Rust runtime with no shell-only dependency.
- Run a full hook matrix (start, prompt-submit, pre/post-tool, stop) and verify zero regressions.
- Validate parity for env handling, exit codes, and hook output contracts against baseline logs.
- Keep a tagged rollback point and tested restore command ready before production cutover.

## Hook Cutover Safety Checks

- Enable staged rollout (dev → staging → prod) with explicit go/no-go at each stage.
- Compare hook latency and failure rate to baseline; block cutover on regressions.
- Verify telemetry coverage (hook name, duration, exit status, error surface) is complete.
- Execute rollback drill in staging and confirm recovery time and behavior.
- Freeze non-migration hook changes during cutover window to reduce confounding risk.

## Migration Rollback Drills

- Pre-stage rollback artifact (`thegent-hooks` previous known-good build) and verify checksum before cutover.
- Simulate failed cutover in staging: force hook runtime switch back, restart hook host, and replay hook matrix.
- Time recovery from fault detect → stable hooks; require recovery within agreed SLO before production go-live.
- Record exact rollback command sequence and on-call owner in cutover runbook.

## Post-Cutover Validation

- Run full production hook matrix on canary repos; compare outputs and exit codes with pre-cutover baseline.
- Verify p95 hook latency, error rate, and cache hit rate for 60 minutes remain within migration targets.
- Confirm telemetry ingestion for all hook phases and alert routing to on-call.
- Perform one real rollback/roll-forward rehearsal in production window and capture lessons learned.

## Cutover Rehearsal Matrix

- Rehearse `dev`, `staging`, and `prod-canary` in order; require explicit sign-off before moving forward.
- Execute hook suite (`start`, `prompt-submit`, `pre-tool`, `post-tool`, `stop`) with baseline diff checks each stage.
- Enforce cutover gate: no stage advances if failure rate >0.5% or p95 latency exceeds baseline by >20%.
- Time rollback rehearsal end-to-end; require recovery to known-good runtime within 5 minutes.

## Regression Containment Rules

- Freeze non-migration hook changes during cutover and validation windows.
- Auto-revert to last known-good Rust binary on any repeated hook crash or contract mismatch (2+ events in 10 minutes).
- Block further rollout when telemetry is missing for hook name, exit code, or duration fields.
- Keep canary scope capped until 60 minutes of stable metrics are observed after each promotion.

## Hook Readiness Signals

- `thegent-hooks --version` matches approved release in all environments.
- Hook matrix (`start`, `prompt-submit`, `pre-tool`, `post-tool`, `stop`) passes with baseline parity.
- p95 hook latency and error rate stay within cutover thresholds for 60 minutes.
- Required telemetry fields (hook, duration, exit status, error) are complete and alerting.

## Rust Hook Failure Playbook

- Detect and classify: crash, timeout, contract mismatch, or telemetry loss.
- Contain fast: pause rollout and pin to canary scope only.
- Recover: switch to last known-good Rust build; if needed, execute shell fallback.
- Verify: rerun hook matrix plus parity checks before resuming promotions.
- Close out: log incident timeline, root cause, and hardening actions in runbook.

## Rust Hook Metrics Baseline

- Record pre-cutover baseline: `p50/p95 latency`, `error rate`, `cache hit rate`, and `timeout count` per hook type.
- Gate rollout on concrete limits: latency regression `<=20%`, error rate `<=0.5%`, and zero contract-diff failures.
- Capture 60-minute steady-state windows for `dev`, `staging`, and `prod-canary` before promotion.
- Store baseline and post-cutover snapshots in the cutover log with timestamp + release SHA.

## Rollback Verification Commands

- Verify active binary: `thegent-hooks --version`
- Run parity matrix: `./hooks/test-hook-matrix.sh --baseline ./tmp/hook-baseline.json`
- Check health metrics: `./scripts/hook-metrics-check.sh --max-latency-regression 20 --max-error-rate 0.5`
- Execute rollback switch: `./scripts/hook-runtime-switch.sh --to last-known-good`
- Confirm rollback parity: `./hooks/test-hook-matrix.sh --compare ./tmp/hook-baseline.json`

## Hook Cutover Roll-Forward Steps

- Confirm rollback point exists and `thegent-hooks --version` matches approved release.
- Promote in order (`dev` → `staging` → `prod-canary` → `prod`) only after 60-minute stable metrics per stage.
- Gate each promotion on hook-matrix parity and thresholds (`p95` regression `<=20%`, error rate `<=0.5%`).
- Keep rollout paused on any contract mismatch, telemetry gap, or repeated crash until fixed and revalidated.

## Crash Recovery Commands

- `thegent-hooks --version`
- `./scripts/hook-runtime-switch.sh --to last-known-good`
- `./hooks/test-hook-matrix.sh --compare ./tmp/hook-baseline.json`
- `./scripts/hook-metrics-check.sh --max-latency-regression 20 --max-error-rate 0.5`
- `./scripts/hook-runtime-switch.sh --to approved-release && ./hooks/test-hook-matrix.sh --compare ./tmp/hook-baseline.json`
