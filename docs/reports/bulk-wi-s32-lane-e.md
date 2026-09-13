### [WL-7160]

**Title:** Preserve malformed-line visibility when extracting session IDs from registry rows
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:14]
**Acceptance checklist:**

- [ ] Replace broad exception suppression in `extract_session_id` with typed JSON decode handling.
- [ ] Preserve `None` return semantics for non-start rows while exposing malformed input diagnostics.
- [ ] Add tests for valid started rows, malformed JSON, and non-start events.
      **Notes:** Line 14 currently suppresses all parse failures and makes malformed registry records indistinguishable from normal misses.

### [WL-7161]

**Title:** Differentiate run-id parse faults from true missing identifiers in registry scanning
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:24]
**Acceptance checklist:**

- [ ] Replace blanket exception handling in `extract_run_id` with typed decode-error classification.
- [ ] Preserve `None` behavior for rows without `run_id` while surfacing malformed row counts.
- [ ] Add tests for valid rows, malformed JSON payloads, and rows missing `run_id`.
      **Notes:** Line 24 collapses malformed payloads into silent `None`, obscuring upstream schema and log integrity issues.

### [WL-7162]

**Title:** Make run-state transition parse failures observable during status reconstruction
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:45]
**Acceptance checklist:**

- [ ] Replace catch-all suppression in `update_run_state` with typed parse and field-shape handling.
- [ ] Preserve current state fallback for non-matching rows while distinguishing malformed records.
- [ ] Add tests for normal lifecycle events, malformed JSON lines, and incomplete finish-event payloads.
      **Notes:** Line 45 currently hides transition parsing faults, which can leave run state stale without operator signal.

### [WL-7163]

**Title:** Surface dropped run-map updates caused by malformed registry entries
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:62]
**Acceptance checklist:**

- [ ] Replace broad suppression in `process_run_entry` with typed decode and key-access error handling.
- [ ] Preserve resilient ingestion for valid entries while reporting skipped malformed rows.
- [ ] Add tests for start/update/finish ingestion, malformed lines, and entries missing required identifiers.
      **Notes:** Line 62 currently swallows all failures and can silently reduce run-map completeness.

### [WL-7164]

**Title:** Separate session match parse failures from legitimate non-match outcomes
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:72]
**Acceptance checklist:**

- [ ] Replace blanket exception handling in `check_session_id` with typed parse failure paths.
- [ ] Preserve boolean return contract while exposing malformed line diagnostics.
- [ ] Add tests for correlation ID match, run ID match, malformed rows, and expected mismatch cases.
      **Notes:** Line 72 currently converts parse failures into silent `False`, weakening troubleshooting accuracy.

### [WL-7165]

**Title:** Preserve token-correlation quality when idempotency rows fail to parse
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:91]
**Acceptance checklist:**

- [ ] Replace broad exception suppression in `process_token_match` with typed decode and event-shape handling.
- [ ] Preserve best-candidate selection semantics for valid rows while surfacing malformed token rows.
- [ ] Add tests for start/finish/feedback updates, malformed records, and stale-candidate replacement behavior.
      **Notes:** Line 91 currently hides parse faults that can bias idempotency token resolution.

### [WL-7166]

**Title:** Make calibration aggregation skips observable for malformed event rows
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:112]
**Acceptance checklist:**

- [ ] Replace catch-all suppression in `process_calibration_entry` with typed parse and field-validation handling.
- [ ] Preserve aggregation flow for valid records while recording bounded malformed-row diagnostics.
- [ ] Add tests for finish/feedback/agent-filter paths and malformed event payloads.
      **Notes:** Line 112 currently masks row-level failures, making calibration drift harder to diagnose.

### [WL-7167]

**Title:** Distinguish domain-tag decode errors from genuinely empty domain metadata
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:121]
**Acceptance checklist:**

- [ ] Replace broad exception handling in `extract_domain_tag` with typed JSON decode handling.
- [ ] Preserve tuple fallback contract while differentiating malformed lines from missing fields.
- [ ] Add tests for valid domain tags, absent keys, and malformed JSON rows.
      **Notes:** Line 121 currently maps all failure modes to `(None, None)`, obscuring data-quality issues.

### [WL-7168]

**Title:** Classify retention-filter parse failures instead of silently retaining undecodable records
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:151]
**Acceptance checklist:**

- [ ] Replace blanket exception fallback in `filter_expired_record` with typed decode/timestamp error classification.
- [ ] Preserve `(False, line)` compatibility while surfacing why expiry checks were skipped.
- [ ] Add tests for valid expiry decisions, malformed JSON rows, and invalid timestamp formats.
      **Notes:** Line 151 currently suppresses all failures and can silently keep expired records.

### [WL-7169]

**Title:** Differentiate tmux socket probe failures from true no-pane states in terminal discovery
**Source:** [thegent/src/thegent/skills/terminal.py:67]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression in `list_tmux_panes` with typed subprocess error handling.
- [ ] Preserve multi-socket fallback behavior while exposing per-socket probe failures.
- [ ] Add tests for successful pane listing, failed primary socket fallback, and fully unavailable tmux states.
      **Notes:** Line 67 currently suppresses all command failures and makes discovery degradation look identical to empty pane lists.
