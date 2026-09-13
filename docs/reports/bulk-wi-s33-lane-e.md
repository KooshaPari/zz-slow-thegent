### [WL-7210]

**Title:** Preserve resource detector bootstrap failures instead of suppressing development-mode inference errors
**Source:** [thegent/src/thegent/resources/__init__.py:64]
**Acceptance checklist:**

- [ ] Replace broad exception suppression around dev-environment detection with typed filesystem and environment read handling.
- [ ] Preserve current non-fatal startup behavior when project-root inference fails.
- [ ] Add tests for git-root detection success, unreadable working-directory metadata, and fallback behavior.
      **Notes:** Line 64 currently hides initialization failures and can mask why resource backends are not selected as expected.

### [WL-7211]

**Title:** Classify network counter probe failures in interface throughput collection
**Source:** [thegent/src/thegent/resources/network.py:66]
**Acceptance checklist:**

- [ ] Replace blanket counter-read exception handling with typed psutil availability and runtime probe failure categories.
- [ ] Preserve `[]` fallback contract for unrecoverable counter probes.
- [ ] Add tests for successful network counter reads, probe exceptions, and empty-interface fallback behavior.
      **Notes:** Line 66 currently collapses failure modes into a generic error path, limiting operational diagnostics.

### [WL-7212]

**Title:** Surface malformed JSONL record rates instead of silently skipping decode failures
**Source:** [thegent/src/thegent/native/jsonl_parser.py:75]
**Acceptance checklist:**

- [ ] Replace decode-and-continue suppression with bounded malformed-line diagnostics and counters.
- [ ] Preserve parser streaming behavior for valid records after malformed lines.
- [ ] Add tests for all-valid input, mixed valid/invalid rows, and sustained decode error scenarios.
      **Notes:** Line 75 currently drops malformed rows without visibility, weakening data quality signals.

### [WL-7213]

**Title:** Distinguish terminal resize ioctl failures from normal no-op resize paths
**Source:** [thegent/src/thegent/tui/widgets/terminal_pane.py:116]
**Acceptance checklist:**

- [ ] Replace silent `OSError` suppression in resize handling with typed errno-aware diagnostics.
- [ ] Preserve non-blocking UI behavior when PTY resize cannot be applied.
- [ ] Add tests for successful resize, expected transient resize failures, and repeated resize attempts.
      **Notes:** Line 116 currently swallows resize faults, making PTY layout drift difficult to troubleshoot.

### [WL-7214]

**Title:** Preserve shell health-check inspection failures before returning safeguard guidance
**Source:** [thegent/src/thegent/shell_cli.py:176]
**Acceptance checklist:**

- [ ] Replace catch-all suppression with typed configuration parse and probe error handling.
- [ ] Preserve current command output contract while appending bounded failure context.
- [ ] Add tests for healthy inspection, malformed input state, and unexpected probe exceptions.
      **Notes:** Line 176 currently hides inspection failures and can misreport safeguard status.

### [WL-7215]

**Title:** Surface parent-process discovery failures in agent-name derivation
**Source:** [thegent/src/thegent/discovery/__init__.py:93]
**Acceptance checklist:**

- [ ] Replace broad parent-process lookup suppression with typed process-introspection failure branches.
- [ ] Preserve fallback naming behavior when parent metadata is unavailable.
- [ ] Add tests for recognized parent agent names, inaccessible process metadata, and default-name fallback.
      **Notes:** Line 93 currently masks discovery failures that affect deterministic agent identity naming.

### [WL-7216]

**Title:** Classify model-pricing metadata parse failures in cost aggregation
**Source:** [thegent/src/thegent/cost/aggregator.py:61]
**Acceptance checklist:**

- [ ] Replace blanket metadata exception suppression with typed schema and conversion error handling.
- [ ] Preserve aggregation continuity for rows with valid pricing metadata.
- [ ] Add tests for valid metadata, malformed metadata payloads, and missing-price fallback behavior.
      **Notes:** Line 61 currently swallows metadata issues, which can silently distort aggregate cost metrics.

### [WL-7217]

**Title:** Preserve status-bar clock update failures as bounded UI telemetry
**Source:** [thegent/src/thegent/tui/widgets/statusbar.py:154]
**Acceptance checklist:**

- [ ] Replace silent clock-render suppression with typed widget lookup and render-update diagnostics.
- [ ] Preserve status-bar refresh loop continuity when clock updates fail.
- [ ] Add tests for normal clock updates, missing clock widget, and render exceptions.
      **Notes:** Line 154 currently suppresses clock update failures and obscures degraded UI state.

### [WL-7218]

**Title:** Differentiate process-scan permission errors from terminated-process churn in launcher counting
**Source:** [thegent/src/thegent/planning/auto_launch.py:82]
**Acceptance checklist:**

- [ ] Replace silent per-process suppression with bounded counters for access-denied and no-such-process outcomes.
- [ ] Preserve resilient scan behavior across concurrent process churn.
- [ ] Add tests for accessible process sets, transient process exits, and permission-denied entries.
      **Notes:** Line 82 currently discards per-item errors, reducing visibility into launcher count accuracy.

### [WL-7219]

**Title:** Surface disk I/O probe failures in resource telemetry collection
**Source:** [thegent/src/thegent/resources/disk.py:95]
**Acceptance checklist:**

- [ ] Replace broad disk counter suppression with typed psutil probe and permission failure diagnostics.
- [ ] Preserve `[]` fallback semantics when disk counters cannot be retrieved.
- [ ] Add tests for successful disk counter reads, probe exceptions, and empty-device fallback behavior.
      **Notes:** Line 95 currently returns empty metrics for all probe failures without exposing root cause.
