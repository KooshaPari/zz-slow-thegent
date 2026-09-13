# Phase 3 - Job Pool Implementation Report

## Objective

Implement a reusable bounded job concurrency system for parallel execution of linters and security tools, targeting 30-50% speedup through better parallelization with resource limits.

## Implementation Summary

### 1. Job Pool Library (hooks/lib/common.sh)

**Added Functions:**

- `job_pool_init()` - Initialize pool state
- `job_pool_add(max_jobs, command)` - Add job with bounded concurrency
- `job_pool_wait()` - Wait for all jobs, collect failures
- `job_pool_status()` - Get current job count
- `job_pool_get_failures()` - Get list of failed job temp files
- `job_pool_collect_output()` - Collect output from job temp files

**Design Principles:**

- Bash 3.x compatible (no associative arrays in portable code)
- Automatic job failure tracking without early exit
- Temp file-based output buffering (clean stdout separation)
- Built-in timeout support via `run_with_timeout()`
- Configurable max concurrency (default 4 parallel jobs)

**Key Features:**

```bash
# Example: Parallel linting with bounded concurrency
job_pool_init
job_pool_add 4 "ruff check file1.py" &
job_pool_add 4 "pylint file1.py" &
job_pool_add 4 "mypy file1.py" &
job_pool_wait  # Wait for all, return non-zero if any failed
```

### 2. Integration Points

#### quality-gate.sh

- **Current state:** Already uses language group parallelization (lint_python &, lint_shell &, etc.)
- **Enhancement opportunity:** Within each language group, parallelize tool invocations
  - Python: ruff lint, ruff F401, vulture can run in parallel (3 concurrent)
  - TypeScript/JS: oxlint, eslint, knip can run in parallel (3 concurrent)
  - Security: brakeman, psalm can run in parallel (2 concurrent)

#### security-pipeline.sh

- **Current state:** Layer-based parallel execution (Layer 1, Layer 2, etc. in parallel)
- **Within-layer enhancement:** Parallelize sub-tools within each security layer
  - Layer 2 SAST: semgrep, bandit, gosec run in parallel (3 concurrent)
  - Layer 3 Deps: pip-audit, cargo-audit, govulncheck run in parallel (3 concurrent)

### 3. Bounded Concurrency Strategy

**Configuration:**

- Default max_jobs = 4 (tunable per use case)
- Wait-and-slot mechanism: job pool tracks running jobs, waits for slots to open
- Sleep interval: 10ms between slot checks (prevents busy-wait)

**Resource Bounds:**

```
quality-gate.sh: 4 max concurrent linters
  - Each linter: 10-15s timeout
  - Total expected: 2-4 seconds (was 2-4 sequential)

security-pipeline.sh: 4 max concurrent security tools
  - Each tool: 15-20s timeout
  - Total expected: 15-30 seconds (was 30-60 sequential)
```

### 4. Error Handling

**Design:**

- All job failures are tracked but do NOT exit early
- Collect all failures in `_JOB_POOL_FAILURES[]` array
- Return non-zero from `job_pool_wait()` if any jobs failed
- Caller must handle failure reporting

**Example:**

```bash
job_pool_wait || {
  # Some jobs failed - collect and report
  job_pool_get_failures | while read tmpfile; do
    echo "TOOL FAILED: $tmpfile"
    cat "$tmpfile" >> "$REPORT"
  done
}
```

### 5. Temp File Management

**Strategy:**

- Each job writes output to unique temp file (mktemp)
- Caller tracks temp files for cleanup (via trap EXIT)
- Allows clean separation of concurrent tool output

**Cleanup:**

```bash
LINT_TMP="$(mktemp -d)"
trap 'rm -rf "$LINT_TMP"' EXIT

job_pool_add 4 "tool1 args" > "$LINT_TMP/tool1.out" &
job_pool_add 4 "tool2 args" > "$LINT_TMP/tool2.out" &
job_pool_wait

# Temp files auto-cleaned at script exit
```

## Files Modified

### /hooks/lib/common.sh

- **Lines added:** ~100 (new Job Pool section at EOF)
- **Changes:** Added 6 new functions for job pool management
- **Backward compatibility:** 100% (new functions only, no changes to existing code)

### /hooks/quality-gate.sh (Planned)

- **Enhancement:** Parallelize within-group tool invocations
- **Python group:** ruff, ruff F401, vulture in parallel (3 concurrent)
- **JS/TS group:** oxlint, eslint, knip in parallel (3 concurrent)
- **Ruby group:** brakeman in parallel (1, no change)
- **PHP group:** psalm in parallel (1, no change)

### /hooks/security-pipeline.sh (Planned)

- **Layer 2 (SAST):** semgrep, bandit, gosec in parallel (3 concurrent)
- **Layer 3 (Deps):** pip-audit, cargo-audit, govulncheck in parallel (3 concurrent)
- **Layer 4 (Infra):** hadolint, tfsec, trivy in parallel (3 concurrent)

## Testing Plan

### Unit Tests

1. **Job pool initialization**

   ```bash
   job_pool_init
   [[ "$_JOB_POOL_INITIALIZED" == "true" ]] || die "init failed"
   ```

2. **Simple job addition and wait**

   ```bash
   job_pool_add 4 "echo test" &
   job_pool_wait && echo "PASS: job pool wait succeeded"
   ```

3. **Bounded concurrency (max_jobs respected)**

   ```bash
   for i in {1..10}; do
     job_pool_add 2 "sleep 0.5" &
   done
   job_pool_wait  # Should respect max=2
   ```

4. **Failure tracking**
   ```bash
   job_pool_add 2 "exit 1" &  # Intentional failure
   ! job_pool_wait            # Should return non-zero
   [[ -n "$(job_pool_get_failures)" ]] || die "no failures tracked"
   ```

### Integration Tests

1. **quality-gate.sh on Python project**

   ```bash
   cd test-projects/python-project
   bash hooks/quality-gate.sh < {test_event}
   # Verify: all linters ran, output preserved, timing < 5s
   ```

2. **security-pipeline.sh on mixed project**

   ```bash
   cd test-projects/mixed-project
   bash hooks/security-pipeline.sh < {test_event}
   # Verify: all 5 layers completed, timing < 45s
   ```

3. **Failure scenarios**
   - Simulate linter timeout: tool takes >30s
   - Simulate tool crash: exit with error code
   - Simulate tool not found: skip with SKIP status

### Performance Tests

1. **quality-gate.sh speedup measurement**

   ```bash
   # Before (sequential tools):
   time bash hooks/quality-gate.sh < event.json
   # Expected: ~4 seconds

   # After (parallel tools with job pool):
   time bash hooks/quality-gate.sh < event.json
   # Expected: ~2 seconds (50% speedup)
   ```

2. **security-pipeline.sh speedup measurement**

   ```bash
   # Before (sequential layers, some within-layer parallel):
   time bash hooks/security-pipeline.sh < event.json
   # Expected: ~45 seconds

   # After (full within-layer parallelization):
   time bash hooks/security-pipeline.sh < event.json
   # Expected: ~25 seconds (45% speedup)
   ```

## Rollout Plan

### Phase 1: Library Only (DONE)

- Add job pool functions to hooks/lib/common.sh
- No changes to quality-gate.sh or security-pipeline.sh
- Backward compatible - existing hooks unaffected

### Phase 2: Selective Integration (RECOMMENDED NEXT)

- Update quality-gate.sh Python group first (safest, no behavioral change)
- Run tests on Python projects
- Measure performance improvement
- Verify output correctness (same linting results)

### Phase 3: Full Integration

- Apply job pool to remaining quality-gate.sh groups
- Apply job pool to security-pipeline.sh layers
- Comprehensive testing on diverse projects

### Phase 4: Tuning

- Profile to find optimal max_jobs per language/tool
- Adjust timeouts based on real-world data
- Document performance baseline

## Success Metrics

| Metric                       | Baseline           | Target               | Verification            |
| ---------------------------- | ------------------ | -------------------- | ----------------------- |
| quality-gate.sh runtime      | ~4s                | <2s                  | time measurement        |
| security-pipeline.sh runtime | ~45s               | <25s                 | time measurement        |
| Test output accuracy         | 100%               | 100%                 | output diff vs baseline |
| Error handling               | Pass/Fail binary   | Collected failures   | failure tracking test   |
| CPU utilization              | ~20% (single core) | ~70-80% (multi-core) | top/htop during run     |

## Known Limitations

1. **Bash 3.x compatibility:** Uses `declare -A` for internal tracking, but only in common.sh which may not run on ancient bash versions. Quality-gate.sh and security-pipeline.sh remain portable.

2. **Timeout handling:** Each job wrapped with `run_with_timeout()`, which may add 0.1-0.5s overhead per job. Acceptable for tool invocations lasting 5-20s.

3. **Output ordering:** With parallel execution, tool output in log files may appear interleaved. Mitigation: separate temp files per tool, collected post-execution.

4. **Resource limits:** System may have hard limits on process count. Job pool respects max_jobs, but if set too high (e.g., 16) on memory-constrained systems, may hit ulimit. Default 4 is safe on all systems.

## Future Enhancements

1. **Dynamic load adjustment:** Monitor CPU/memory during execution, adjust max_jobs dynamically
2. **Adaptive timeouts:** Tools that consistently exceed timeout get increased threshold
3. **Caching:** Results of identical tool invocations cached, reducing redundant work
4. **Tool grouping:** Cluster tools by resource requirements (e.g., memory-heavy tools separate from CPU-bound)

## References

- Bash job control: https://www.gnu.org/software/bash/manual/html_node/Job-Control.html
- Background process management patterns
- mktemp safety: https://pubs.opengroup.org/onlinepubs/9699919799/utilities/mktemp.html
