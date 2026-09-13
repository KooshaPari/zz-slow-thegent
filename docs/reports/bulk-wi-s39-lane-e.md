### [WL-7510]

**Title:** Preserve JSON decode failure visibility when extracting session identifiers from run registry entries
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:15]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression in `extract_session_id` with typed JSON decode and schema-shape handling.
- [ ] Preserve current `None` return contract for lines that are not valid start events.
- [ ] Add tests for valid start events, malformed JSON lines, and missing identifier fields.
      **Notes:** Line 15 currently swallows all parsing failures with `pass`.

### [WL-7511]

**Title:** Surface malformed run entry errors in run ID extraction without changing caller contract
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:25]
**Acceptance checklist:**

- [ ] Narrow exception handling in `extract_run_id` to decode and payload-shape failures.
- [ ] Preserve existing `None` behavior for records without `run_id`.
- [ ] Add tests for valid run records, malformed JSON, and non-dict payloads.
      **Notes:** Line 25 suppresses all parse failures via a broad `except` + `pass`.

### [WL-7512]

**Title:** Keep run-state transition diagnostics while guarding against malformed registry lines
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:46]
**Acceptance checklist:**

- [ ] Replace broad exception suppression in `update_run_state` with typed parse and state-mapping error handling.
- [ ] Preserve current fallback behavior that returns `current_state` on invalid entries.
- [ ] Add tests for each transition event, malformed JSON input, and unknown status values.
      **Notes:** Line 46 currently suppresses all exceptions, hiding state-update failure causes.

### [WL-7513]

**Title:** Preserve run-map update observability when processing invalid JSONL entries
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:63]
**Acceptance checklist:**

- [ ] Replace catch-all suppression in `process_run_entry` with explicit JSON and payload validation branches.
- [ ] Preserve in-memory map update semantics for valid `finish` and non-`finish` events.
- [ ] Add tests for valid events, malformed lines, and missing `run_id` values.
      **Notes:** Line 63 uses `pass`, which can silently discard malformed entries without diagnostics.

### [WL-7514]

**Title:** Differentiate malformed entry errors from non-matching session IDs in registry filtering
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:73]
**Acceptance checklist:**

- [ ] Replace broad exception suppression in `check_session_id` with decode-specific handling and bounded diagnostics.
- [ ] Preserve boolean matching behavior for valid correlation and run IDs.
- [ ] Add tests for matching IDs, non-matching IDs, and malformed JSON lines.
      **Notes:** Line 73 currently masks all failures and returns `False`, conflating errors with true misses.

### [WL-7515]

**Title:** Retain idempotency token reconciliation fidelity under malformed registry payloads
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:92]
**Acceptance checklist:**

- [ ] Replace blanket exception handling in `process_token_match` with typed parse and field-access validation.
- [ ] Preserve current merge semantics for `finish`, `feedback`, and newest-started runs.
- [ ] Add tests for token matches across event types, malformed lines, and incomplete payloads.
      **Notes:** Line 92 suppresses all exceptions, which can hide merge regressions in token matching.

### [WL-7516]

**Title:** Surface calibration stream parsing failures while preserving aggregation continuity
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:113]
**Acceptance checklist:**

- [ ] Replace catch-all suppression in `process_calibration_entry` with typed decode and schema-guard handling.
- [ ] Preserve current calibration aggregation behavior for `finish`, `feedback`, and agent-start events.
- [ ] Add tests for normal calibration updates, malformed entries, and missing run identifiers.
      **Notes:** Line 113 currently swallows all exceptions and can silently skip calibration updates.

### [WL-7517]

**Title:** Make domain-tag extraction failures observable without breaking retention workflows
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:121]
**Acceptance checklist:**

- [ ] Narrow exception handling in `extract_domain_tag` to JSON decode and type-validation failures.
- [ ] Preserve existing tuple return contract for valid entries.
- [ ] Add tests for valid domain-tag payloads, malformed JSON lines, and non-dict records.
      **Notes:** Line 121 catches every exception and returns `(None, None)` without distinguishing error causes.

### [WL-7518]

**Title:** Preserve retention expiration error taxonomy during timestamp parsing and domain lookup
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:151]
**Acceptance checklist:**

- [ ] Replace broad suppression in `filter_expired_record` with explicit datetime-parse, timezone, and payload-shape handling.
- [ ] Preserve current `(False, line)` fallback for non-expirable malformed records.
- [ ] Add tests for valid expiry checks, invalid timestamps, and missing domain metadata.
      **Notes:** Line 151 currently hides all exception categories behind a generic non-expired fallback.

### [WL-7519]

**Title:** Enforce meaningful runtime status initialization invariants in diagnostic model lifecycle
**Source:** [thegent/src/thegent/infra/multi_runtime_diagnostics.py:33]
**Acceptance checklist:**

- [ ] Replace no-op `RuntimeStatus.__post_init__` with explicit invariant checks for required fields and tier values.
- [ ] Preserve compatibility for existing runtime check helpers that construct `RuntimeStatus` instances.
- [ ] Add tests for valid status objects and invalid initialization inputs.
      **Notes:** Line 33 defines a no-op `__post_init__` (`pass`), leaving dataclass invariants unenforced.
