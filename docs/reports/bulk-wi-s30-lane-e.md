### [WL-7060]

**Title:** Surface JSON decode failures in session ID extraction instead of silently returning no match
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:14]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression in `extract_session_id` with typed JSON parse handling.
- [ ] Preserve current `None` return contract for non-matching and malformed lines while emitting bounded diagnostics.
- [ ] Add tests for valid started events, malformed JSON lines, and missing identifier fields.
      **Notes:** Line 14 currently swallows all exceptions and hides malformed-run-registry input while scanning for session identifiers.

### [WL-7061]

**Title:** Preserve parse-failure visibility when extracting run IDs from registry lines
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:24]
**Acceptance checklist:**

- [ ] Replace broad exception handling in `extract_run_id` with typed JSON decode handling.
- [ ] Keep `None` semantics for absent run IDs while distinguishing malformed JSON from missing keys.
- [ ] Add tests for valid run rows, invalid JSON payloads, and rows without `run_id`.
      **Notes:** Line 24 currently catches everything, making schema issues and malformed payloads indistinguishable.

### [WL-7062]

**Title:** Differentiate state-transition parse errors from non-target run rows in run-state updates
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:45]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression in `update_run_state` with typed decode and event-shape handling.
- [ ] Preserve existing state machine behavior for known events while surfacing malformed event records.
- [ ] Add tests for valid lifecycle transitions, malformed JSON entries, and unexpected event payload shapes.
      **Notes:** Line 45 suppresses all failures and can silently leave stale run state when registry rows are corrupted.

### [WL-7063]

**Title:** Make registry-entry processing failures observable in run map consolidation
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:62]
**Acceptance checklist:**

- [ ] Replace broad exception suppression in `process_run_entry` with typed JSON and key-access handling.
- [ ] Preserve in-memory run map update behavior for valid entries while logging bounded malformed-row diagnostics.
- [ ] Add tests for start/finish entries, malformed JSON rows, and rows missing `run_id`.
      **Notes:** Line 62 currently masks all processing faults, hiding dropped entries during run map construction.

### [WL-7064]

**Title:** Expose session correlation parse faults in session-ID match checks
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:72]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression in `check_session_id` with typed parse failure handling.
- [ ] Keep boolean return contract unchanged while distinguishing parse failures from true non-matches.
- [ ] Add tests for correlation ID matches, run ID matches, and malformed JSON lines.
      **Notes:** Line 72 swallows all exceptions and collapses parse errors into `False`, reducing scan accuracy diagnostics.

### [WL-7065]

**Title:** Surface idempotency-token scan failure causes during best-run selection
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:91]
**Acceptance checklist:**

- [ ] Replace broad exception suppression in `process_token_match` with typed decode and event-shape handling.
- [ ] Preserve existing best-record selection semantics while surfacing malformed token/event records.
- [ ] Add tests for matching start rows, finish/feedback updates, and malformed token rows.
      **Notes:** Line 91 currently swallows all exceptions, which can hide data-loss in idempotency token correlation.

### [WL-7066]

**Title:** Distinguish calibration aggregation parse failures from non-agent event filtering
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:112]
**Acceptance checklist:**

- [ ] Replace blanket exception handling in `process_calibration_entry` with typed decode and field-validation handling.
- [ ] Preserve current calibration aggregation behavior for valid rows while exposing malformed-record diagnostics.
- [ ] Add tests for finish/feedback updates, agent-scoped rows, and malformed calibration entries.
      **Notes:** Line 112 catches every exception and can silently skip calibration-relevant rows without operator signal.

### [WL-7067]

**Title:** Preserve domain-tag extraction fault visibility while retaining tuple fallback semantics
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:121]
**Acceptance checklist:**

- [ ] Replace broad `except` in `extract_domain_tag` with typed JSON decode handling.
- [ ] Keep `(None, None)` fallback behavior for malformed lines while emitting bounded parse diagnostics.
- [ ] Add tests for valid domain-tag extraction, missing fields, and malformed JSON inputs.
      **Notes:** Line 121 currently converts all failures into a silent null tuple, obscuring registry schema drift.

### [WL-7068]

**Title:** Classify expiration-filter parse and timestamp coercion failures in retention checks
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:151]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression in `filter_expired_record` with typed JSON and timestamp parse handling.
- [ ] Preserve `(False, line)` fallback contract while distinguishing malformed payloads from timezone conversion failures.
- [ ] Add tests for expired records, naive timestamp normalization, invalid timestamp formats, and malformed JSON rows.
      **Notes:** Line 151 currently catches all errors and can quietly retain stale records when expiration parsing fails.

### [WL-7069]

**Title:** Surface argv-scan faults when extracting dex subcommand arguments
**Source:** [thegent/src/thegent/dex_cli_helpers.py:75]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression in `extract_dex_command_args` with typed iteration/index handling.
- [ ] Preserve current argument extraction behavior while exposing bounded diagnostics for malformed argv inputs.
- [ ] Add tests for direct `dex` invocation, path-suffixed `dex` binaries, and malformed/non-string argv entries.
      **Notes:** Line 75 currently suppresses all exceptions and can hide unexpected argv shape regressions in dex command parsing.
