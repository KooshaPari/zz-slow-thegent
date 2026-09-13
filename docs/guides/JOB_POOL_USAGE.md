# Job Pool System - Usage Guide

## Overview

The Job Pool system provides lightweight bounded concurrency control for parallel execution of linting and security tools in shell scripts. It works with any shell command and enforces a maximum concurrency limit to control resource usage.

## Core Concept

Instead of running tools sequentially or launching unlimited parallel jobs, the job pool system ensures at most N jobs run concurrently. When the limit is reached, new jobs wait for existing jobs to complete before launching.

## Basic API

### `job_pool_init()`

Initialize the job pool. Must be called before using the pool.

```bash
job_pool_init
```

### `job_parallel_launch <max_concurrent> <command> [args...]`

Launch a command with bounded concurrency control. This function waits if max_concurrent jobs are already running.

```bash
# Launch with max 4 concurrent executions
job_parallel_launch 4 ruff check file.py &
job_parallel_launch 4 pylint file.py &
job_parallel_launch 4 mypy file.py &
wait
```

### `job_pool_add <max_concurrent> <command> [args...]`

Alias for `job_parallel_launch`. Provided for backward compatibility.

### `job_pool_wait()` / `job_pool_wait_all()`

Wait for all background jobs to complete.

```bash
wait  # bash builtin - simpler than job_pool_wait
job_pool_wait_all  # explicit wait function
```

### `job_pool_status()`

Get the count of currently running background jobs.

```bash
running=$(job_pool_status)
echo "Running jobs: $running"
```

## Common Patterns

### Pattern 1: Simple Parallel Tools

Run multiple tools in parallel with bounded concurrency:

```bash
#!/bin/bash
job_pool_init

# Launch all tools with max 4 concurrent
job_parallel_launch 4 ruff check "${PY_FILES[@]}" &
job_parallel_launch 4 pylint "${PY_FILES[@]}" &
job_parallel_launch 4 mypy "${PY_FILES[@]}" &

# Wait for all to complete
wait
```

### Pattern 2: Language-Grouped Parallel Tools

Group tools by language, then parallelize within each group:

```bash
#!/bin/bash
job_pool_init

# Python tools (up to 3 concurrent)
if [[ -n "$PY_FILES" ]]; then
  job_parallel_launch 3 ruff check "${PY_FILES[@]}" &
  job_parallel_launch 3 pylint "${PY_FILES[@]}" &
  job_parallel_launch 3 vulture "${PY_FILES[@]}" &
fi

# TypeScript tools (up to 3 concurrent)
if [[ -n "$TS_FILES" ]]; then
  job_parallel_launch 3 oxlint "${TS_FILES[@]}" &
  job_parallel_launch 3 eslint "${TS_FILES[@]}" &
  job_parallel_launch 3 knip &
fi

# Security tools (up to 2 concurrent)
if [[ -n "$CHANGED_FILES" ]]; then
  job_parallel_launch 2 gitleaks detect --source . &
  job_parallel_launch 2 semgrep --config=auto "${CHANGED_FILES[@]}" &
fi

# Wait for all tools to complete
wait
```

### Pattern 3: Sequential Tool Stages with Concurrency

Run tools in logical stages, with concurrency within each stage:

```bash
#!/bin/bash
job_pool_init

# Stage 1: All linters (max 4 concurrent)
echo "Running linters..."
job_parallel_launch 4 ruff check "${PY_FILES[@]}" &
job_parallel_launch 4 shellcheck "${SH_FILES[@]}" &
job_parallel_launch 4 oxlint "${TS_FILES[@]}" &
job_parallel_launch 4 golangci-lint run "${GO_FILES[@]}" &
wait  # Wait for all linters to finish

# Stage 2: Security tools (max 2 concurrent)
echo "Running security scans..."
job_parallel_launch 2 gitleaks detect --source . &
job_parallel_launch 2 bandit -r . &
wait  # Wait for all security scans to finish

# Stage 3: Analysis (max 1, sequential)
echo "Running analysis..."
job_parallel_launch 1 jscpd . &
wait
```

## Output Handling

### Capturing Output from Parallel Jobs

Output from parallel jobs can interleave. To keep output separate:

```bash
LINT_TMP=$(mktemp -d)
trap 'rm -rf "$LINT_TMP"' EXIT

# Redirect output from each tool to separate files
job_parallel_launch 4 bash -c 'ruff check "${PY_FILES[@]}"' \
  > "$LINT_TMP/ruff.out" 2>&1 &

job_parallel_launch 4 bash -c 'pylint "${PY_FILES[@]}"' \
  > "$LINT_TMP/pylint.out" 2>&1 &

wait

# Collect all output
cat "$LINT_TMP"/*.out | tee "$REPORT"
```

### Timeout Handling

Each command execution can have its own timeout via `run_with_timeout`:

```bash
job_parallel_launch 4 bash -c 'run_with_timeout 10 ruff check file.py' &
job_parallel_launch 4 bash -c 'run_with_timeout 15 pylint file.py' &
wait
```

## Performance Tuning

### Choosing Max Concurrent Jobs

- **For linters (CPU-bound):** `num_cores - 1` (typically 4)
- **For security tools (mixed I/O + CPU):** `3-4`
- **For network tools (I/O-bound):** `8-10`

```bash
# Detect CPU cores and use num_cores - 1
MAX_JOBS=$(($(nproc || echo 4) - 1))
job_parallel_launch "$MAX_JOBS" tool args &
```

### Measuring Speedup

```bash
# Sequential execution (baseline)
time bash hooks/quality-gate.sh < event.json
# Expected: ~4 seconds

# Parallel execution with job pool
time bash hooks/quality-gate.sh-optimized < event.json
# Expected: ~2 seconds (50% speedup)
```

## Error Handling

### Checking Exit Codes

```bash
job_parallel_launch 4 tool1 args &
pid1=$!
job_parallel_launch 4 tool2 args &
pid2=$!

wait $pid1
rc1=$?

wait $pid2
rc2=$?

[[ $rc1 -ne 0 ]] && echo "tool1 failed with code $rc1"
[[ $rc2 -ne 0 ]] && echo "tool2 failed with code $rc2"
```

### Collecting Failures

```bash
declare -a failed_pids=()

job_parallel_launch 4 tool1 &
pids[0]=$!

job_parallel_launch 4 tool2 &
pids[1]=$!

for pid in "${pids[@]}"; do
  if ! wait "$pid"; then
    failed_pids+=("$pid")
  fi
done

if [[ ${#failed_pids[@]} -gt 0 ]]; then
  echo "FAIL: ${#failed_pids[@]} tools failed"
  exit 1
fi
```

## Implementation Details

### How It Works

1. `_job_pool_wait_for_slot(max_jobs)`: Internal helper that blocks until fewer than `max_jobs` are running
2. `job_parallel_launch`: Calls `_job_pool_wait_for_slot`, then executes the command
3. Commands are launched in the background with `&`, tracked by the shell
4. `wait` waits for all background jobs to complete

### Resource Limitations

- **OS process limit:** System ulimit may limit total processes. Default max 4 is safe on all systems.
- **Memory:** Each process consumes memory. Monitor with `top` for memory-bound workloads.
- **File descriptors:** Parallel processes may hit open file limit. Check with `ulimit -n`.

### Bash Compatibility

- Works on bash 3.x, 4.x, 5.x
- Uses only standard bash builtins: `jobs`, `wait`, `background jobs (&)`
- No external tools required

## Troubleshooting

### Jobs not running concurrently

**Symptom:** All jobs run sequentially despite using `job_parallel_launch`
**Cause:** Running jobs directly instead of in background with `&`
**Fix:** Ensure `&` is used: `job_parallel_launch 4 tool & `

### Too much memory usage

**Symptom:** OOM killer triggered
**Cause:** Max concurrency too high for available memory
**Fix:** Reduce `max_jobs` parameter, e.g., from 8 to 4

### Tool hangs

**Symptom:** Job pool waits indefinitely
**Cause:** Tool doesn't terminate properly
**Fix:** Use timeout: `run_with_timeout 30 tool args`

## See Also

- `hooks/lib/common.sh` - Source code for job pool functions
- `hooks/quality-gate.sh` - Example using job pool for linting
- `tests/test-job-pool.sh` - Unit tests demonstrating usage

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
