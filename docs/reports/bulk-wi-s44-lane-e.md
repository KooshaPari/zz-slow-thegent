### [WL-7760]

**Title:** Make CLI preflight failures include missing-tool install hints
**Source:** [thegent/src/thegent/cli/preflight.py:74]
**Acceptance checklist:**

- [ ] Add explicit missing-tool hints (tool name + install command suggestion) in preflight failures.
- [ ] Preserve current non-zero exit behavior when required tools are unavailable.
- [ ] Add tests for all-tools-present, one-tool-missing, and multiple-tools-missing scenarios.
      **Notes:** Current preflight failures identify missing binaries but do not provide immediate remediation guidance.

### [WL-7761]

**Title:** Prevent spinner corruption by serializing concurrent terminal status writes
**Source:** [thegent/src/thegent/ui/spinner.py:121]
**Acceptance checklist:**

- [ ] Add a single-writer guard for spinner/status updates emitted from concurrent tasks.
- [ ] Preserve existing status message formats and frame cadence.
- [ ] Add tests for single-task updates, concurrent updates, and clean shutdown flushing.
      **Notes:** Interleaved writes from parallel jobs can produce unreadable terminal output during long runs.

### [WL-7762]

**Title:** Improve config override UX by showing effective key path on type mismatch
**Source:** [thegent/src/thegent/config/overrides.py:98]
**Acceptance checklist:**

- [ ] Include full effective config key path and expected type in override validation errors.
- [ ] Preserve successful override application for valid keys and values.
- [ ] Add tests for unknown key, type mismatch, and valid override merge behavior.
      **Notes:** Override errors are currently too terse for fast correction during iterative local runs.

### [WL-7763]

**Title:** Harden log file rotation by detecting partial write failures before rename
**Source:** [thegent/src/thegent/logging/rotation.py:166]
**Acceptance checklist:**

- [ ] Validate buffered write completion before rotating and renaming log segments.
- [ ] Preserve current rotation thresholds and filename scheme.
- [ ] Add tests for successful rotation, interrupted write simulation, and retry-safe recovery.
      **Notes:** Rare partial writes can lead to truncated rotated logs that hide root-cause context.

### [WL-7764]

**Title:** Add deterministic ordering to plugin hook execution diagnostics
**Source:** [thegent/src/thegent/plugins/hook_dispatch.py:143]
**Acceptance checklist:**

- [ ] Emit hook execution diagnostics in stable sorted order independent of plugin registration timing.
- [ ] Preserve existing hook invocation semantics and short-circuit behavior.
- [ ] Add tests for stable ordering, mixed-success hooks, and exception propagation.
      **Notes:** Non-deterministic diagnostic ordering makes regression triage noisy between equivalent runs.

### [WL-7765]

**Title:** Improve temp-dir cleanup reliability with explicit symlink boundary checks
**Source:** [thegent/src/thegent/fs/temp_cleanup.py:57]
**Acceptance checklist:**

- [ ] Reject cleanup targets that escape the temp root via symlink traversal.
- [ ] Preserve successful cleanup of valid in-root temp artifacts.
- [ ] Add tests for in-root cleanup, escaping symlink target rejection, and missing target handling.
      **Notes:** Cleanup safety currently depends on implicit path normalization and can be brittle on edge layouts.

### [WL-7766]

**Title:** Reduce retry noise by collapsing duplicate network error bursts in progress logs
**Source:** [thegent/src/thegent/net/retry_log.py:89]
**Acceptance checklist:**

- [ ] Coalesce repeated identical retry errors into counted summaries over a short window.
- [ ] Preserve final terminal error visibility and full debug-mode detail.
- [ ] Add tests for repeated identical errors, mixed error classes, and immediate-success retries.
      **Notes:** High-frequency retry logs can drown actionable signals during transient network incidents.

### [WL-7767]

**Title:** Make session resume safer by validating stale PID metadata before attach
**Source:** [thegent/src/thegent/session/resume.py:132]
**Acceptance checklist:**

- [ ] Verify stored PID metadata still maps to the expected process identity before resume attach.
- [ ] Preserve fast-path resume behavior for healthy live sessions.
- [ ] Add tests for valid live PID, recycled PID mismatch, and missing metadata cases.
      **Notes:** PID reuse can cause confusing attach failures when old session metadata survives crashes.

### [WL-7768]

**Title:** Improve schema drift debugging with focused diff previews for validation failures
**Source:** [thegent/src/thegent/schema/validator.py:205]
**Acceptance checklist:**

- [ ] Include compact expected-vs-actual field diff previews in schema validation errors.
- [ ] Preserve current strict validation semantics and error exit codes.
- [ ] Add tests for missing field, unexpected field, type drift, and valid payload acceptance.
      **Notes:** Current validation output is accurate but too verbose to quickly isolate the first meaningful drift.

### [WL-7769]

**Title:** Stabilize file-watch restarts with debounce windows keyed by normalized paths
**Source:** [thegent/src/thegent/watch/reloader.py:111]
**Acceptance checklist:**

- [ ] Debounce rapid file events by normalized path to prevent duplicate restart storms.
- [ ] Preserve immediate restart behavior for isolated single-file changes.
- [ ] Add tests for bursty duplicate events, distinct-path changes, and no-op metadata-only events.
      **Notes:** Duplicate watcher events can trigger redundant restart loops that slow local dev feedback cycles.
