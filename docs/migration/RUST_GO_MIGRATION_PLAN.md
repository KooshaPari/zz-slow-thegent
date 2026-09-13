# Shell to Rust/Go Migration Plan

## Problem Statement

Shell scripts are causing performance issues:

- `which` command timing out (2m 43s)
- Shell initialization overhead from wrapper functions
- Expensive operations in hot paths (PATH resolution, process scanning)

## Root Cause Analysis

### Why `which` Times Out

1. **Shell Wrapper Functions**: `common.sh` defines wrappers for `find`, `git`, `codex`, etc.
2. **PATH Resolution**: When `which` runs, it triggers PATH scanning
3. **Cascade Effect**: Each wrapper calls `command -v` which may trigger more wrappers
4. **Tool Detection**: `common.sh` runs tool detection on every source, calling `command -v` multiple times

### Performance Bottlenecks

1. **hooks/lib/common.sh** (1674 lines)
   - Tool detection: `command -v` calls for jaq, jq, rg, fd, pgrep, timeout
   - PATH resolution: `resolve_real_binary()` function
   - Git wrapper: Process tree walking for agent detection
   - Find wrapper: File system operations

2. **hooks/lib/fd-wrapper.sh**
   - File discovery wrapper
   - Called frequently by hooks

3. **hooks/lib/git-cache.sh**
   - Git command caching
   - File I/O for cache management

## Migration Priority

### Phase 1: Critical Path (Immediate)

1. **Tool Detection** → Rust binary
   - Current: Multiple `command -v` calls in `common.sh`
   - Target: Single Rust binary `thegent-tool-detect` that caches results
   - Benefit: Eliminate 60ms+ overhead per hook invocation

2. **PATH Resolution** → Rust function
   - Current: `resolve_real_binary()` bash function
   - Target: Rust function in `thegent-discovery` crate
   - Benefit: 10-50x faster PATH scanning

3. **Process Scanning** → Already in Rust (`thegent-discovery`)
   - Current: Python fallback using `ps` and `subprocess`
   - Target: Use native Rust extension (needs build)
   - Benefit: 100x faster process tree walking

### Phase 2: High Impact (Next Sprint)

4. **Git Operations** → Rust binary (`thegent-git` crate exists)
   - Current: Bash wrapper with mutex handling
   - Target: Use `thegent-git` crate for all git operations
   - Benefit: Better lock handling, faster operations

5. **File Discovery** → Rust binary (`fd` wrapper)
   - Current: Bash wrapper calling `fd` or `find`
   - Target: Native Rust implementation
   - Benefit: Eliminate subprocess overhead

### Phase 3: Optimization (Future)

6. **Hook Dispatchers** → Go binary
   - Current: Bash scripts (`pretool-dispatcher.sh`, `posttool-dispatcher.sh`)
   - Target: Go binary for better concurrency
   - Benefit: Parallel hook execution, better error handling

## Implementation Strategy

### Step 1: Build Rust Extension (Immediate)

```bash
cd thegent/crates/thegent-discovery
maturin develop --release --features python
```

### Step 2: Create Fast Tool Detection Binary

Create `thegent/crates/thegent-tool-detect/src/main.rs`:

- Single binary that detects all tools
- Caches results in `/tmp/thegent-tools-{uid}.cache`
- Returns JSON with tool paths
- Called once per session instead of per-hook

### Step 3: Migrate PATH Resolution

Move `resolve_real_binary()` to Rust:

- Add to `thegent-discovery` crate
- Expose as Python function
- Update `common.sh` to call Python function (temporary)
- Eventually replace `common.sh` entirely

### Step 4: Replace Shell Wrappers

Gradually replace bash wrappers:

1. Keep bash wrappers as fallback
2. Add Rust/Go binaries that do the same work
3. Update hooks to prefer binaries
4. Remove bash wrappers once stable

## Expected Performance Improvements

| Operation        | Current (bash) | Target (Rust/Go) | Speedup |
| ---------------- | -------------- | ---------------- | ------- |
| Tool detection   | 60ms           | 1ms              | 60x     |
| PATH resolution  | 20ms           | 0.5ms            | 40x     |
| Process scanning | 50ms           | 0.5ms            | 100x    |
| Git operations   | 100ms          | 10ms             | 10x     |
| File discovery   | 30ms           | 2ms              | 15x     |
| Hook dispatch    | 200ms          | 50ms             | 4x      |

## Migration Checklist

- [ ] Build `thegent_discovery` Rust extension
- [ ] Create `thegent-tool-detect` binary
- [ ] Migrate PATH resolution to Rust
- [ ] Update `common.sh` to use Rust functions
- [ ] Migrate git operations to `thegent-git`
- [ ] Create Rust file discovery binary
- [ ] Migrate hook dispatchers to Go
- [ ] Remove bash wrapper functions
- [ ] Performance testing and validation

## Immediate Fixes

### Fix `which` Timeout

1. **Skip shell initialization for `which`**:

   ```bash
   # In .zshrc or .bashrc
   which() {
       command which "$@"
   }
   ```

2. **Lazy load `common.sh`**:
   - Only source when actually needed
   - Don't source during PATH resolution

3. **Cache tool paths**:
   - Use existing `_TOOL_CACHE_FILE` mechanism
   - Pre-populate cache on shell startup (background)

## Files to Migrate

### High Priority (Performance Critical)

- `hooks/lib/common.sh` → Rust library + Python bindings
- `hooks/lib/fd-wrapper.sh` → Rust binary
- `hooks/lib/git-cache.sh` → Rust binary (use `thegent-git`)
- `hooks/lib/git-wrapper.sh` → Rust binary (use `thegent-git`)

### Medium Priority (Frequently Called)

- `hooks/pretool-dispatcher.sh` → Go binary
- `hooks/posttool-dispatcher.sh` → Go binary
- `hooks/lib/procs-wrapper.sh` → Rust binary

### Low Priority (Less Critical)

- Individual hook scripts (keep as bash for flexibility)
- Utility scripts (migration scripts, etc.)

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
