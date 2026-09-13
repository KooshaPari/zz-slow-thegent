### [WL-7490]

**Title:** Preserve shell benchmark failure taxonomy by separating subprocess launch faults from timing parse errors
**Source:** [thegent/src/thegent/shell_cli.py:262]
**Acceptance checklist:**

- [ ] Replace broad benchmark exception handling with explicit subprocess, timeout, and parse-failure branches.
- [ ] Preserve per-iteration continuation so a single failed probe does not abort the benchmark run.
- [ ] Add tests for successful timing capture, subprocess timeout, and malformed `time -p` output.
      **Notes:** Current handling at line 262 conflates execution and parsing failures into a single error path.

### [WL-7491]

**Title:** Differentiate metrics file read, row parse, and value coercion failures in shell metrics reporting
**Source:** [thegent/src/thegent/shell_cli.py:341]
**Acceptance checklist:**

- [ ] Replace catch-all metrics parsing exception handling with explicit file-open, record-parse, and integer-coercion branches.
- [ ] Preserve graceful command behavior when metrics are unavailable or malformed.
- [ ] Add tests for valid metrics payloads, malformed key-value rows, and non-integer metric values.
      **Notes:** Line 341 currently collapses distinct metrics failure classes into one generic branch.

### [WL-7492]

**Title:** Surface job-registry failure classes separately from per-PID status probe issues
**Source:** [thegent/src/thegent/shell_cli.py:388]
**Acceptance checklist:**

- [ ] Replace broad job-registry exception handling with explicit unreadable-file, malformed-line, and PID-parse diagnostics.
- [ ] Preserve best-effort status probing for each valid registry record.
- [ ] Add tests for valid registry entries, malformed rows, and unreadable registry files.
      **Notes:** Existing handling at line 388 obscures whether failures come from file shape, access, or conversion.

### [WL-7493]

**Title:** Preserve settings bootstrap diagnostics when resolving `critical_lane_slots` fallback values
**Source:** [thegent/src/thegent/execution.py:167]
**Acceptance checklist:**

- [ ] Replace broad settings bootstrap suppression with explicit config-load and value-resolution failure branches.
- [ ] Preserve deterministic env/default fallback behavior for `critical_lane_slots`.
- [ ] Add tests for valid settings resolution, broken settings payloads, and env-backed fallback.
      **Notes:** Line 167 currently masks bootstrap faults behind a generic fallback path.

### [WL-7494]

**Title:** Expose deadline monitor unregister failure causes during critical-slot release
**Source:** [thegent/src/thegent/execution.py:448]
**Acceptance checklist:**

- [ ] Replace broad unregister suppression with explicit import, monitor-access, and unregister-call failure handling.
- [ ] Preserve non-blocking release behavior even when cleanup fails.
- [ ] Add tests for successful unregister, missing monitor module, and unregister runtime errors.
      **Notes:** At line 448, cleanup failures are swallowed and lose root-cause visibility.

### [WL-7495]

**Title:** Distinguish escalation dependency failures from queue enqueue failures for stale critical runs
**Source:** [thegent/src/thegent/execution.py:878]
**Acceptance checklist:**

- [ ] Replace broad stale-task escalation exception handling with typed dependency-load, queue-init, and enqueue error branches.
- [ ] Preserve stale-task scan continuity if escalation cannot complete.
- [ ] Add tests for successful escalation, missing escalation module, and queue write failure.
      **Notes:** Line 878 currently routes multiple failure types through one warning path.

### [WL-7496]

**Title:** Separate DLQ auto-escalation policy guard failures from escalation transport/runtime errors
**Source:** [thegent/src/thegent/execution.py:941]
**Acceptance checklist:**

- [ ] Replace broad DLQ auto-escalation exception handling with explicit governance import, queue construction, and submission failure branches.
- [ ] Preserve DLQ enqueue success when escalation hooks fail.
- [ ] Add tests for successful auto-escalation, governance-module absence, and submission exceptions.
      **Notes:** Current catch-all handling at line 941 makes policy and runtime failures indistinguishable.

### [WL-7497]

**Title:** Preserve provider score-registry corruption diagnostics during score-map hydration
**Source:** [thegent/src/thegent/execution.py:1079]
**Acceptance checklist:**

- [ ] Replace broad provider-score read exception handling with explicit file-read, JSON-decode, and schema-shape failure categories.
- [ ] Preserve safe fallback behavior when persisted score data is unavailable.
- [ ] Add tests for valid score payloads, invalid JSON, and structurally invalid score documents.
      **Notes:** Line 1079 currently returns an empty map for all failure modes, hiding corruption vs transient I/O faults.

### [WL-7498]

**Title:** Classify calibration-factor registry parse failures apart from legitimate missing-agent defaults
**Source:** [thegent/src/thegent/execution.py:1265]
**Acceptance checklist:**

- [ ] Replace broad calibration read suppression with explicit file-read, JSON-decode, and nested-key extraction failure handling.
- [ ] Preserve default factor behavior for agents missing calibration entries.
- [ ] Add tests for valid calibration reads, malformed registry JSON, and missing agent keys.
      **Notes:** Current logic at line 1265 defaults to `1.0` for all failures and masks malformed registry state.

### [WL-7499]

**Title:** Differentiate intentionally non-JSON REST responses from malformed JSON decode failures
**Source:** [thegent/src/thegent/mcp/rest_to_mcp.py:126]
**Acceptance checklist:**

- [ ] Replace broad response-body parse suppression with explicit JSON decode and plain-text fallback branches.
- [ ] Preserve text passthrough behavior for non-JSON endpoints.
- [ ] Add tests for valid JSON responses, plain-text responses, and malformed JSON payloads.
      **Notes:** Line 126 currently hides whether response bodies are non-JSON by design or syntactically invalid JSON.
