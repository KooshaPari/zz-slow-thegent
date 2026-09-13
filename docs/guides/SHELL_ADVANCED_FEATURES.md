# Shell Advanced Features Guide

## Overview

The advanced shell optimization system extends thegent's shell environment with enterprise-grade features:

- **Instant Prompt**: Print prompt immediately (< 5ms), load everything else in background
- **Async/Turbo Loading**: Load plugins/tools asynchronously with wait conditions
- **Advanced Caching**: Multi-level caching with predictive preloading
- **Error Recovery**: Circuit breakers, graceful degradation, retry logic
- **Background Job Management**: Track and manage background initialization jobs
- **Cross-Platform Compatibility**: Seamless operation on macOS, Linux, Windows (WSL)
- **Advanced Monitoring**: Detailed metrics, performance tracking, diagnostics

## Features

### 1. Instant Prompt System

**Goal**: Zero perceived startup lag by printing prompt immediately.

**How it works**:

1. Print minimal prompt immediately on shell start
2. Redirect stdout/stderr to temp file during initialization
3. Load expensive plugins/tools in background
4. Restore stdout/stderr and display buffered output
5. Replace prompt with full version once ready

**Configuration**:

```bash
# Enable/disable instant prompt (default: enabled)
export THEGENT_INSTANT_PROMPT_ENABLED=1  # or 0 to disable
```

**Benefits**:

- Zero perceived startup lag
- Can start typing immediately
- Background loading doesn't block interaction

**Cache Location**:

- `~/.cache/thegent/instant-prompt-${USER}.zsh`

### 2. Async/Turbo Loading System

**Goal**: Load plugins/tools asynchronously with wait conditions.

**Wait Conditions**:

- `wait"0"` or `wait` (no value): Load immediately in background
- `wait"N"`: Load after N seconds
- `wait'[[ condition ]]'`: Load when condition is met
- `trigger-load`: Create function that loads plugin on first call

**Usage**:

```bash
# Load plugin immediately in background
_thegent_async_load "0" "_load_plugin" "arg1" "arg2"

# Load plugin after 2 seconds
_thegent_async_load "2" "_load_plugin"

# Load plugin when condition met
_thegent_async_load '[[ -n "$GIT_DIR" ]]' "_load_git_plugin"

# Trigger-load: load on first command use
_thegent_trigger_load "kubectl" "_load_kubectl"
```

**Configuration**:

```bash
# Enable/disable async loading (default: enabled)
export THEGENT_ASYNC_LOADING_ENABLED=1  # or 0 to disable
```

**Benefits**:

- 50-80% faster startup
- Non-blocking initialization
- Progressive enhancement

### 3. Advanced Caching System

**Goal**: Multi-level caching with predictive preloading.

**Cache Levels**:

- **L1 (Memory)**: Fastest, session-scoped, in-memory
- **L2 (File)**: Fast, persistent across sessions, file-based
- **Eval Cache**: Cached `eval "$(tool init -)"` outputs

**Usage**:

```bash
# Get from cache (tries L1, then L2)
_thegent_cache_get "tool:git"

# Set in cache (sets both L1 and L2)
_thegent_cache_set "tool:git" "/usr/bin/git"

# Predictive preloading
_thegent_predictive_preload  # Preloads common tools
```

**Cache Locations**:

- L1: In-memory (session-scoped)
- L2: `~/.cache/thegent/advanced/cache-l2/`
- Eval: `~/.cache/thegent/eval-cache/`

**Benefits**:

- Near-instant tool detection
- Reduced disk I/O
- Better performance for frequently used tools

**Management**:

```bash
# View cache statistics
thegent shell cache-stats

# Clear cache
thegent shell clear-cache
```

### 4. Error Recovery System

**Goal**: Circuit breakers, graceful degradation, retry logic.

**Circuit Breaker Pattern**:

- Tracks failures per service
- Opens circuit after threshold failures
- Cooldown period before retry
- Automatic recovery

**Usage**:

```bash
# Check if circuit breaker is open
_thegent_circuit_breaker_is_open "service_name"

# Record failure (opens circuit if threshold exceeded)
_thegent_circuit_breaker_open "service_name" 5 60  # threshold=5, cooldown=60s

# Reset circuit breaker
_thegent_circuit_breaker_reset "service_name"

# Safe execution with retry logic
_thegent_safe_exec "command" "arg1" "arg2"
```

**Configuration**:

```bash
# Maximum retries (default: 3)
export THEGENT_MAX_RETRIES=3

# Retry delay in seconds (default: 1)
export THEGENT_RETRY_DELAY=1
```

**Benefits**:

- Resilient to transient failures
- Better user experience during outages
- Automatic recovery without manual intervention

**Management**:

```bash
# List all circuit breakers
thegent shell circuit-breaker --list

# Reset circuit breaker
thegent shell circuit-breaker --reset service_name
```

### 5. Background Job Management

**Goal**: Track and manage background initialization jobs.

**Usage**:

```bash
# Register background job
_thegent_job_register "job_name" $PID

# Wait for job to complete
_thegent_job_wait "job_name"

# Cleanup all jobs
_thegent_job_cleanup
```

**Job Registry**:

- Location: `~/.cache/thegent/advanced/jobs/registry`
- Format: `job_name:PID`

**Management**:

```bash
# View background jobs
thegent shell jobs
```

**Benefits**:

- Better visibility into background operations
- Prevents zombie processes
- Cleaner resource management

### 6. Cross-Platform Compatibility

**Goal**: Seamless operation on macOS, Linux, Windows (WSL).

**Platform Detection**:

- Automatically detects platform from `$OSTYPE` or `uname`
- Sets `THEGENT_PLATFORM` variable (`macos`, `linux`, `windows`, `unknown`)

**Platform-Specific Optimizations**:

- **macOS**: Uses `gtimeout` instead of `timeout`
- **Linux**: Uses `timeout`
- **Windows/WSL**: Limited timeout support, fallback to direct execution

**Usage**:

```bash
# Platform-specific timeout command
_thegent_timeout_cmd 30 command find "$@"
```

**Configuration**:

```bash
# View platform information
thegent shell platform
```

**Benefits**:

- Single configuration works everywhere
- Platform-specific optimizations
- Better developer experience

### 7. Advanced Monitoring

**Goal**: Detailed metrics, performance tracking, diagnostics.

**Metrics Collected**:

- Cache hit/miss rates
- Tool detection counts
- Error rates
- Background job statistics
- Performance timings

**Usage**:

```bash
# Record metric
_thegent_metrics_record "cache_hit" 1

# Get metric value
_thegent_metrics_get "cache_hit"

# Generate report
_thegent_metrics_report
```

**Configuration**:

```bash
# Enable/disable metrics (default: disabled)
export THEGENT_METRICS_ENABLED=1  # or 0 to disable
```

**Metrics Location**:

- `~/.cache/thegent/advanced/metrics/stats`

**Management**:

```bash
# View metrics
thegent shell metrics
```

**Benefits**:

- Identify bottlenecks
- Optimize based on real data
- Better debugging capabilities

## CLI Commands

### `thegent shell status`

Show shell environment status and configuration.

### `thegent shell metrics`

Show shell performance metrics and statistics.

### `thegent shell jobs`

Show background job status.

### `thegent shell cache-stats`

Show cache statistics (hit/miss rates, sizes).

### `thegent shell circuit-breaker`

Manage circuit breakers for error recovery.

- `--list`: List all circuit breakers
- `--reset SERVICE`: Reset circuit breaker for service

### `thegent shell platform`

Show platform detection and compatibility information.

### `thegent shell benchmark`

Benchmark shell startup time.

### `thegent shell doctor`

Diagnose shell environment issues.

### `thegent shell clear-cache`

Clear shell optimization cache.

### `thegent shell reload`

Reload shell configuration.

## Configuration

### Environment Variables

```bash
# Instant prompt
export THEGENT_INSTANT_PROMPT_ENABLED=1

# Async loading
export THEGENT_ASYNC_LOADING_ENABLED=1

# Metrics
export THEGENT_METRICS_ENABLED=0

# Cache directory
export THEGENT_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/thegent"

# Error recovery
export THEGENT_MAX_RETRIES=3
export THEGENT_RETRY_DELAY=1
```

### File Locations

- **Advanced cache**: `~/.cache/thegent/advanced/`
- **Instant prompt cache**: `~/.cache/thegent/instant-prompt-${USER}.zsh`
- **Job registry**: `~/.cache/thegent/advanced/jobs/registry`
- **Circuit breakers**: `~/.cache/thegent/advanced/circuit-breakers/`
- **Metrics**: `~/.cache/thegent/advanced/metrics/stats`

## Performance Targets

Based on zsh-bench research and human perception thresholds:

- **First prompt lag**: < 5ms (target: < 1ms)
- **First command lag**: < 50ms (target: < 20ms)
- **Command lag**: < 5ms (target: < 2ms)
- **Input lag**: < 10ms (target: < 5ms)
- **Startup time**: < 100ms (target: < 50ms)

## Troubleshooting

### Instant prompt not working

1. Check `THEGENT_INSTANT_PROMPT_ENABLED=1`
2. Verify cache directory is writable
3. Check for errors in `~/.cache/thegent/instant-prompt-*.zsh`

### Async loading not working

1. Check `THEGENT_ASYNC_LOADING_ENABLED=1`
2. Verify background jobs are running: `thegent shell jobs`
3. Check for errors in job registry

### Cache issues

1. Clear cache: `thegent shell clear-cache`
2. Check cache statistics: `thegent shell cache-stats`
3. Verify cache directory permissions

### Circuit breaker stuck open

1. List circuit breakers: `thegent shell circuit-breaker --list`
2. Reset circuit breaker: `thegent shell circuit-breaker --reset SERVICE`
3. Check failure counts in `~/.cache/thegent/advanced/circuit-breakers/`

### Platform detection issues

1. Check platform: `thegent shell platform`
2. Verify `$OSTYPE` or `uname` output
3. Manually set `THEGENT_PLATFORM` if needed

## Best Practices

1. **Enable instant prompt** for zero perceived startup lag
2. **Use async loading** for expensive plugins/tools
3. **Enable metrics** during development to identify bottlenecks
4. **Monitor cache statistics** to optimize cache usage
5. **Use circuit breakers** for external services/tools
6. **Clean up background jobs** on shell exit
7. **Test on multiple platforms** for cross-platform compatibility

## Migration Guide

### From Basic Optimization

The advanced system extends the basic optimization system. No migration needed - it's automatically loaded if `.zsh_advanced.zsh` exists.

### Enabling Advanced Features

1. Ensure `.zsh_advanced.zsh` is installed: `thegent install --target system`
2. Enable desired features via environment variables
3. Restart shell: `exec zsh`
4. Verify: `thegent shell status`

### Disabling Advanced Features

Set environment variables to `0`:

```bash
export THEGENT_INSTANT_PROMPT_ENABLED=0
export THEGENT_ASYNC_LOADING_ENABLED=0
export THEGENT_METRICS_ENABLED=0
```

## See Also

- [Shell Environment Management Guide](SHELL_ENVIRONMENT_MANAGEMENT.md)
- [Shell Optimization Guide](SHELL_OPTIMIZATION_GUIDE.md)
- [Advanced Enhancement Plan](../plans/SHELL_ENVIRONMENT_ADVANCED_ENHANCEMENT_PLAN.md)

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

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
