### [WL-7380]

**Title:** Separate shell benchmark subprocess failures from parse-time timing extraction faults
**Source:** [thegent/src/thegent/shell_cli.py:262]
**Acceptance checklist:**

- [ ] Replace broad benchmark-loop exception handling with explicit subprocess launch, timeout, and stderr-parse failure branches.
- [ ] Preserve per-iteration continuation so one failed sample does not abort the benchmark run.
- [ ] Add tests for successful timing capture, subprocess timeout, and malformed `time -p` output.
      **Notes:** The current catch-all branch collapses command execution faults and parsing issues into a single generic error path.

### [WL-7381]

**Title:** Differentiate metrics file read, parse, and coercion failures in shell metrics command
**Source:** [thegent/src/thegent/shell_cli.py:341]
**Acceptance checklist:**

- [ ] Replace broad metrics parsing exception handling with explicit file-open, line-parse, and integer-coercion failure categories.
- [ ] Preserve current behavior that exits cleanly when metrics cannot be consumed.
- [ ] Add tests for valid metrics payloads, malformed key-value lines, and non-integer metric values.
      **Notes:** Generic error handling hides whether metrics failures come from file I/O, malformed records, or value conversion.

### [WL-7382]

**Title:** Classify shell job-registry read failures independently from per-PID status checks
**Source:** [thegent/src/thegent/shell_cli.py:388]
**Acceptance checklist:**

- [ ] Replace broad job-registry exception handling with explicit registry-open, line-format, and PID-parse failure branches.
- [ ] Preserve best-effort status probing semantics for individual jobs.
- [ ] Add tests for valid registry entries, malformed lines, and unreadable registry files.
      **Notes:** Catch-all registry failure handling obscures whether job-status degradation is caused by file shape, access, or conversion problems.

### [WL-7383]

**Title:** Preserve critical-lane slot fallback diagnostics when settings bootstrap fails
**Source:** [thegent/src/thegent/execution.py:167]
**Acceptance checklist:**

- [ ] Replace broad settings bootstrap exception handling with explicit config-load and value-resolution failure branches.
- [ ] Preserve deterministic environment/default fallback for `critical_lane_slots`.
- [ ] Add tests for valid settings resolution, settings-load failure, and env-based fallback behavior.
      **Notes:** Current broad fallback masks configuration-layer faults that should remain visible during concurrency manager initialization.

### [WL-7384]

**Title:** Surface deadline monitor unregister failure causes during concurrency release
**Source:** [thegent/src/thegent/execution.py:448]
**Acceptance checklist:**

- [ ] Replace broad deadline-unregister suppression with explicit import, monitor-access, and unregister-call failure classes.
- [ ] Preserve non-blocking release behavior even when deadline cleanup fails.
- [ ] Add tests for successful unregister, missing monitor module, and unregister runtime failure.
      **Notes:** Silent suppression during release can hide deadline monitor drift and stale registrations.

### [WL-7385]

**Title:** Distinguish escalation import failures from queue-enqueue failures for stale critical runs
**Source:** [thegent/src/thegent/execution.py:878]
**Acceptance checklist:**

- [ ] Replace broad stale-task escalation exception handling with explicit escalation dependency, queue-init, and enqueue failure branches.
- [ ] Preserve stale-task scan continuity when escalation cannot complete.
- [ ] Add tests for successful escalation, missing escalation module, and queue write failures.
      **Notes:** A single warning path currently conflates dependency availability issues with operational queue failures.

### [WL-7386]

**Title:** Separate DLQ auto-escalation policy guards from escalation transport/runtime failures
**Source:** [thegent/src/thegent/execution.py:941]
**Acceptance checklist:**

- [ ] Replace broad DLQ auto-escalation exception handling with explicit governance import, queue construction, and escalation submission failure branches.
- [ ] Preserve DLQ enqueue success even if auto-escalation fails.
- [ ] Add tests for successful DLQ auto-escalation, governance-module absence, and escalation submission exceptions.
      **Notes:** Current catch-all logging makes policy decision paths and transport faults hard to distinguish in incident triage.

### [WL-7387]

**Title:** Preserve score-registry corruption diagnostics when provider score file read fails
**Source:** [thegent/src/thegent/execution.py:1079]
**Acceptance checklist:**

- [ ] Replace broad provider-score read exception handling with explicit file-read, JSON-decode, and schema-shape failure categories.
- [ ] Preserve safe fallback behavior when persisted scores are unavailable.
- [ ] Add tests for valid score files, invalid JSON payloads, and structurally invalid score documents.
      **Notes:** Returning an empty score map for all failure modes obscures persistent file corruption versus transient I/O faults.

### [WL-7388]

**Title:** Classify calibration-factor registry parse failures separately from missing-agent defaults
**Source:** [thegent/src/thegent/execution.py:1265]
**Acceptance checklist:**

- [ ] Replace broad calibration factor read exception handling with explicit file-read, JSON-decode, and nested-key extraction failure branches.
- [ ] Preserve default factor semantics when calibration data is absent.
- [ ] Add tests for valid registry reads, malformed registry JSON, and missing agent entries.
      **Notes:** Current blanket defaulting to `1.0` conflates malformed registry state with legitimate missing calibration entries.

### [WL-7389]

**Title:** Differentiate non-JSON REST responses from unexpected response-body decode failures
**Source:** [thegent/src/thegent/mcp/rest_to_mcp.py:126]
**Acceptance checklist:**

- [ ] Replace broad response-body parse exception handling with explicit JSON decode and response-text fallback branches.
- [ ] Preserve current behavior of returning text bodies for non-JSON endpoints.
- [ ] Add tests for valid JSON responses, plain-text responses, and malformed JSON payloads.
      **Notes:** Generic decode fallback currently masks whether a response is intentionally non-JSON or syntactically corrupted JSON.
