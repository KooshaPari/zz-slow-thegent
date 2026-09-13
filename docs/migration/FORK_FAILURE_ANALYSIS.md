# Fork Failure (EAGAIN) Analysis & Solutions

## Problem: "Resource temporarily unavailable" (EAGAIN)

**Symptoms:**

- `which` command times out (2m 43s)
- Fork failures: `/usr/bin/cat: fork: retry: Resource temporarily unavailable`
- System becomes unresponsive
- Too many processes spawned

## Root Cause

### The Cascade Effect

```
which codex
  → Shell initialization
    → Sources hooks/lib/common.sh
      → Tool detection (6-8 subprocesses)
        → Each subprocess may trigger more initialization
          → Exponential process spawn
            → System resource exhaustion
              → EAGAIN (Resource temporarily unavailable)
                → Timeout
```

### Contributing Factors

1. **Shell Wrapper Functions**: Every command wrapped triggers initialization
2. **Recursive Sourcing**: `common.sh` sources other scripts
3. **Tool Detection**: Multiple `command -v` calls per initialization
4. **No Process Limits**: No throttling of subprocess spawns
5. **Cache Miss**: Cache not populated during PATH resolution

## System Limits

**macOS Default Limits:**

```bash
ulimit -u  # Max user processes: typically 709 or 1064
ulimit -n  # Max open files: typically 256 or unlimited
```

**When Exceeded:**

- `fork()` returns EAGAIN
- System becomes unresponsive
- Commands timeout

## Solutions

### Solution 1: Fast-Path Detection (Immediate)

**Prevent wrappers from triggering during PATH resolution:**

```bash
# In hooks/lib/common.sh - ALREADY IMPLEMENTED
find() {
  if [[ -n "${_RESOLVING_PATH:-}" ]]; then
    command find "$@" 2>/dev/null || true
    return $?
  fi
  # ... rest of wrapper
}
```

**Add to shell config:**

```bash
# ~/.zshrc or ~/.bashrc
which() {
  _RESOLVING_PATH=1 command which "$@"
}
```

### Solution 2: Lazy Loading (Short-term)

**Only source common.sh when actually needed:**

```bash
# In hooks - check if already loaded
if [[ -z "${_HOOK_LIB_LOADED:-}" ]]; then
  source "${BASH_SOURCE[0]%/*}/lib/common.sh"
fi
```

**Skip during PATH resolution:**

```bash
# Skip if resolving PATH
if [[ -n "${_RESOLVING_PATH:-}" ]]; then
  return 0
fi
```

### Solution 3: Process Throttling (Medium-term)

**Limit concurrent subprocesses:**

```bash
# In common.sh
_MAX_CONCURRENT_PROCS="${MAX_CONCURRENT_PROCS:-10}"
_CURRENT_PROCS=0

wait_for_slot() {
  while [[ $_CURRENT_PROCS -ge $_MAX_CONCURRENT_PROCS ]]; do
    sleep 0.01
    _CURRENT_PROCS=$(jobs -r | wc -l)
  done
  ((_CURRENT_PROCS++))
}
```

### Solution 4: Rust Migration (Long-term)

**Replace subprocess-heavy operations with native Rust:**

1. **Tool Detection**: Single Rust binary instead of 6-8 subprocesses
2. **PATH Resolution**: Native Rust instead of bash loops
3. **Process Scanning**: sysinfo crate instead of `ps` subprocess

**Expected Impact:**

- Eliminate 90%+ of subprocess spawns
- Reduce process count from 100+ to <10 per hook
- Eliminate fork failures entirely

## Immediate Actions

1. **Apply fast-path fix:**

   ```bash
   bash thegent/scripts/fix-which-timeout.sh
   ```

2. **Increase process limits (temporary):**

   ```bash
   ulimit -u 2048  # Increase max processes
   ```

3. **Restart shell** to clear process count

4. **Monitor process count:**
   ```bash
   ps aux | wc -l  # Should be <100 normally
   ```

## Prevention

### 1. Process Monitoring

**Add to common.sh:**

```bash
_check_process_count() {
  local count=$(ps aux | wc -l)
  if [[ $count -gt 500 ]]; then
    echo "WARNING: High process count: $count" >&2
    return 1
  fi
  return 0
}
```

### 2. Circuit Breaker

**Stop spawning if failures detected:**

```bash
if [[ -f "/tmp/thegent-fork-failures" ]]; then
  local failures=$(cat /tmp/thegent-fork-failures)
  if [[ $failures -gt 3 ]]; then
    # Use fallback mode (no wrappers)
    return 0
  fi
fi
```

### 3. Early Exit

**Exit early if in PATH resolution:**

```bash
# At top of common.sh
if [[ -n "${_RESOLVING_PATH:-}" ]]; then
  # Minimal initialization only
  return 0
fi
```

## Migration Priority

1. **Immediate**: Fast-path detection (prevents cascades)
2. **Short-term**: Lazy loading (reduces initialization)
3. **Medium-term**: Process throttling (prevents exhaustion)
4. **Long-term**: Rust migration (eliminates problem)

## Testing

**Test which command:**

```bash
time which codex  # Should be <10ms
```

**Monitor processes:**

```bash
watch -n 1 'ps aux | wc -l'
```

**Test fork resilience:**

```bash
for i in {1..100}; do which codex & done
wait
# Should complete without EAGAIN errors
```

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
