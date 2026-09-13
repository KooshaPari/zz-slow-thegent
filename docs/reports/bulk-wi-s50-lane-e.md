### [WL-8060]

**Title:** Add stable sorting for queue list output in `thegent run queue`
**Source:** [thegent/src/thegent/cli/apps/queue.py:42]
**Acceptance checklist:**

- [ ] Sort queue items deterministically by `status`, `owner`, and `updated_at` before display.
- [ ] Keep ANSI table and JSON modes equivalent in ordering.
- [ ] Add tests for empty queue, mixed status values, and stable ties.
      **Notes:** Deterministic ordering reduces "flaky diff" churn in local queue checks and CI snapshots.

### [WL-8061]

**Title:** Add bounded backoff for transient `thegent run` startup probe failures
**Source:** [thegent/src/thegent/cli/services/run_cmds.py:173]
**Acceptance checklist:**

- [ ] Retry transient probe failures with bounded exponential backoff during orchestrator startup.
- [ ] Fail immediately on non-retryable probe errors while preserving existing exit codes.
- [ ] Add tests for success-after-retry, exhausting retry budget, and immediate failure cases.
      **Notes:** Startups that race with service readiness currently generate intermittent false negatives for developers.

### [WL-8062]

**Title:** Surface per-step timing in command diagnostics when execution stalls
**Source:** [thegent/src/thegent/cli/services/run_execution_core_helpers.py:215]
**Acceptance checklist:**

- [ ] Add a compact phase-timing summary for command boot, orchestration, and teardown.
- [ ] Include timing output only in verbose mode to avoid noise.
- [ ] Add tests for normal run and timeout cases validating no missing/misordered phases.
      **Notes:** Timing visibility helps quickly isolate slow local execution paths.

### [WL-8063]

**Title:** Add explicit cache directory health check in `thegent run` preflight
**Source:** [thegent/src/thegent/cli/services/session_path_helpers.py:101]
**Acceptance checklist:**

- [ ] Validate cache directory path and permissions before workstream kickoff.
- [ ] Report clear remediation instructions when the cache is unwritable or path is missing.
- [ ] Add tests for writable, missing, and permission-denied scenarios.
      **Notes:** Early clarity prevents wasted local runs and repeated mid-run failures.

### [WL-8064]

**Title:** Improve cancel-path messaging for interrupted run sessions
**Source:** [thegent/src/thegent/cli/services/process_helpers.py:132]
**Acceptance checklist:**

- [ ] Emit a concise user-facing cancellation summary with resource cleanup status.
- [ ] Keep process teardown behavior unchanged and avoid swallowing errors.
- [ ] Add tests for SIGINT, SIGTERM, and cleanup failure surfacing.
      **Notes:** Better exit messaging improves incident triage for long-running local sessions.

### [WL-8065]

**Title:** Add optional `--json` diagnostics for `thegent run --status` without changing default output
**Source:** [thegent/src/thegent/cli/services/run_health_helpers.py:66]
**Acceptance checklist:**

- [ ] Add machine-readable status fields for run duration, last heartbeat, and dependency checks.
- [ ] Keep human-readable output unchanged when `--json` is not passed.
- [ ] Add tests for JSON schema fields and backward-compatible text output.
      **Notes:** Enables scriptable monitors while preserving current UX.

### [WL-8066]

**Title:** Add `--dry-run` mode for queue reordering commands
**Source:** [thegent/src/thegent/cli/services/work_stream_orchestration.py:118]
**Acceptance checklist:**

- [ ] Show planned reordering operations and final order without applying changes.
- [ ] Ensure default dry-run off behavior remains unchanged.
- [ ] Add tests for dry-run no-op writes, diff preview, and explicit apply mode.
      **Notes:** Reduces accidental priority churn during workflow tuning.

### [WL-8067]

**Title:** Add startup warning for stale session lock files
**Source:** [thegent/src/thegent/cli/services/run_guard_helpers.py:58]
**Acceptance checklist:**

- [ ] Detect and warn on session lock files older than configured staleness threshold.
- [ ] Offer a safe cleanup command path without auto-deleting locks.
- [ ] Add tests for fresh lock, stale lock warning, and malformed lock handling.
      **Notes:** Prevents confusing hangs when prior sessions left resources behind.

### [WL-8068]

**Title:** Standardize progress update cadence in long-running health checks
**Source:** [thegent/src/thegent/cli/services/observability.py:54]
**Acceptance checklist:**

- [ ] Emit progress updates at fixed intervals with last-updated timestamps.
- [ ] Reduce duplicate progress spam by coalescing unchanged states.
- [ ] Add tests for cadence enforcement, duplicate suppression, and timestamp monotonicity.
      **Notes:** More predictable progress output improves UX during slow local diagnostics.

### [WL-8069]

**Title:** Add actionable hints to plan validation errors for missing CLI prerequisites
**Source:** [thegent/src/thegent/cli/commands/plan_output_helpers.py:97]
**Acceptance checklist:**

- [ ] Append remediation hints for common missing prereq failures (e.g., binaries, env vars, tokens).
- [ ] Keep error codes/messages stable while adding hint context.
- [ ] Add tests for each hint path and no-hint pass-through cases.
      **Notes:** Faster recovery from predictable local setup failures improves developer velocity.
