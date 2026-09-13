### [WL-7100]

**Title:** Preserve malformed JSON context when extracting session IDs from run registry lines
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:14]
**Acceptance checklist:**

- [ ] Replace blanket exception swallowing in `extract_session_id` with typed parse and payload-shape handling.
- [ ] Emit lightweight malformed-line diagnostics without interrupting registry scans.
- [ ] Add tests for started entries, malformed JSON lines, and non-start events.
      **Notes:** Silent parse drops can hide registry corruption and break session correlation during investigations.

### [WL-7101]

**Title:** Differentiate parse failures from missing run_id values in run-id extraction
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:24]
**Acceptance checklist:**

- [ ] Refactor `extract_run_id` to separate decode failures from records that legitimately lack `run_id`.
- [ ] Preserve `None` for non-matching entries while exposing parse-failure counts.
- [ ] Add tests for valid entries, malformed JSON, and entries without `run_id`.
      **Notes:** Treating malformed rows like normal misses reduces audit reliability.

### [WL-7102]

**Title:** Harden run-state transitions against malformed finish-event payloads
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:45]
**Acceptance checklist:**

- [ ] Replace broad exception fallback in `update_run_state` with explicit parse and field checks.
- [ ] Preserve current-state fallback only for recognized non-fatal data gaps.
- [ ] Add tests for started, finish, pause, resume, and malformed event records.
      **Notes:** Silent state-transition failures can leave runs stuck in stale states.

### [WL-7103]

**Title:** Surface dropped run-map updates caused by invalid registry rows
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:62]
**Acceptance checklist:**

- [ ] Add typed exception handling in `process_run_entry` for decode and key-shape failures.
- [ ] Report skipped rows through bounded diagnostics while keeping ingestion resilient.
- [ ] Add tests for create, update, finish, and malformed-entry handling.
      **Notes:** Suppressed failures can undercount completed runs and skew summaries.

### [WL-7104]

**Title:** Track session-id match parse failures without converting them into false negatives
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:72]
**Acceptance checklist:**

- [ ] Replace catch-all exception behavior in `check_session_id` with structured parse handling.
- [ ] Preserve boolean return semantics while making parse-failure causes inspectable.
- [ ] Add tests for correlation-id match, run-id match, mismatch, and malformed JSON input.
      **Notes:** Hidden parse errors can appear as routine non-matches and delay triage.

### [WL-7105]

**Title:** Preserve token-match ranking intent when event payload parsing fails
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:91]
**Acceptance checklist:**

- [ ] Refactor `process_token_match` to avoid blanket exception suppression.
- [ ] Keep best-candidate selection stable while recording malformed lines.
- [ ] Add tests for finish and feedback updates, candidate replacement, and malformed records.
      **Notes:** Silent parse loss can keep stale token matches instead of the newest valid candidate.

### [WL-7106]

**Title:** Improve calibration scan observability for malformed feedback events
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:112]
**Acceptance checklist:**

- [ ] Replace broad exception suppression in `process_calibration_entry` with typed error branches.
- [ ] Ensure valid agent and feedback updates continue after malformed rows.
- [ ] Add tests for finish, feedback, agent filters, and malformed JSON scenarios.
      **Notes:** Calibration metrics can drift if invalid events are dropped without traceability.

### [WL-7107]

**Title:** Separate domain-tag parse errors from legitimate missing tag values
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:121]
**Acceptance checklist:**

- [ ] Refine `extract_domain_tag` error handling to distinguish decode failures from empty fields.
- [ ] Keep tuple return contract while exposing parse-failure counters.
- [ ] Add tests for valid domain tags, missing fields, and malformed payloads.
      **Notes:** Returning `(None, None)` for all failure modes obscures taxonomy data quality issues.

### [WL-7108]

**Title:** Guard timestamp parsing in retention filtering with explicit failure categories
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:139]
**Acceptance checklist:**

- [ ] Add explicit handling for invalid timestamp formats in `filter_expired_record`.
- [ ] Preserve non-expired fallback behavior while tagging invalid timestamp records.
- [ ] Add tests for ISO timestamps, invalid timestamps, and timezone-naive normalization.
      **Notes:** Timestamp parse ambiguity can weaken retention-policy confidence.

### [WL-7109]

**Title:** Prevent catch-all expiry fallback from hiding retention-scan regressions
**Source:** [thegent/src/thegent/execution_run_scan_helpers.py:151]
**Acceptance checklist:**

- [ ] Replace blanket exception fallback in `filter_expired_record` with classified error handling.
- [ ] Ensure unexpected failures are surfaced via diagnostics without halting scans.
- [ ] Add tests for domain lookup issues, malformed records, and stable fallback semantics.
      **Notes:** Silent fallbacks may keep expired records indefinitely when parsing logic regresses.
