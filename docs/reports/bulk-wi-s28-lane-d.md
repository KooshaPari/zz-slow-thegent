### [WL-6950]

**Title:** Preserve malformed JSON context when extracting session IDs.
**Source Path+Line:** [thegent/src/thegent/execution_run_scan_helpers.py:14]
**Acceptance Checklist:**

- [ ] Replace blanket exception swallowing in `extract_session_id` with typed parse/shape handling.
- [ ] Emit lightweight diagnostics for malformed registry lines without breaking scan flow.
- [ ] Add tests for valid started entries, malformed JSON, and non-start events.
      **Notes:** Silent parse failures can hide registry corruption during session lookup.

### [WL-6951]

**Title:** Differentiate parse failure from missing run_id in run-id extraction.
**Source Path+Line:** [thegent/src/thegent/execution_run_scan_helpers.py:24]
**Acceptance Checklist:**

- [ ] Refactor `extract_run_id` to separate malformed payload handling from absent `run_id` values.
- [ ] Keep `None` return for non-matching entries while tracking parse-error counts.
- [ ] Add tests for valid lines, malformed JSON, and lines lacking `run_id`.
      **Notes:** Conflating bad input with absent fields reduces observability in audit scans.

### [WL-6952]

**Title:** Harden run-state transitions against malformed finish-event payloads.
**Source Path+Line:** [thegent/src/thegent/execution_run_scan_helpers.py:45]
**Acceptance Checklist:**

- [ ] Replace broad exception fallback in `update_run_state` with explicit parse/field checks.
- [ ] Preserve current-state fallback only for recognized non-fatal data gaps.
- [ ] Add tests for started/finish/pause/resume transitions and malformed event records.
      **Notes:** Silent errors can leave state machines stuck in stale states.

### [WL-6953]

**Title:** Expose dropped run-map updates caused by invalid registry rows.
**Source Path+Line:** [thegent/src/thegent/execution_run_scan_helpers.py:62]
**Acceptance Checklist:**

- [ ] Add typed exception handling in `process_run_entry` for decode and key-shape failures.
- [ ] Report skipped rows through bounded diagnostics while keeping ingestion resilient.
- [ ] Add tests for create/update/finish flows plus malformed entry handling.
      **Notes:** Suppressed failures can undercount run completions and skew summaries.

### [WL-6954]

**Title:** Track session-id matching parse failures without false negatives.
**Source Path+Line:** [thegent/src/thegent/execution_run_scan_helpers.py:72]
**Acceptance Checklist:**

- [ ] Replace catch-all exception path in `check_session_id` with structured parse handling.
- [ ] Preserve boolean contract while making parse-failure causes inspectable.
- [ ] Add tests for correlation-id match, run-id match, mismatch, and malformed JSON.
      **Notes:** Current behavior masks input quality problems as ordinary non-matches.

### [WL-6955]

**Title:** Preserve token-match ranking intent when event payload parsing fails.
**Source Path+Line:** [thegent/src/thegent/execution_run_scan_helpers.py:91]
**Acceptance Checklist:**

- [ ] Refactor `process_token_match` to avoid blanket exception suppression.
- [ ] Keep best-candidate selection stable while recording malformed lines.
- [ ] Add tests for finish/feedback updates, candidate replacement, and malformed records.
      **Notes:** Silent failures can cause stale token matches to survive over newer entries.

### [WL-6956]

**Title:** Improve calibration scan diagnostics for malformed feedback events.
**Source Path+Line:** [thegent/src/thegent/execution_run_scan_helpers.py:112]
**Acceptance Checklist:**

- [ ] Replace broad exception suppression in `process_calibration_entry` with typed error branches.
- [ ] Ensure valid agent and feedback updates continue after malformed rows.
- [ ] Add tests for finish/feedback/agent filters and malformed JSON scenarios.
      **Notes:** Calibration metrics can drift if broken events are dropped without trace.

### [WL-6957]

**Title:** Separate domain-tag parse errors from legitimate missing tag values.
**Source Path+Line:** [thegent/src/thegent/execution_run_scan_helpers.py:121]
**Acceptance Checklist:**

- [ ] Refine `extract_domain_tag` error handling to distinguish decode failures from empty fields.
- [ ] Keep tuple return contract while exposing parse-failure counters.
- [ ] Add tests for valid domain tags, missing fields, and malformed payloads.
      **Notes:** Returning `(None, None)` for all failures obscures taxonomy data quality issues.

### [WL-6958]

**Title:** Guard timestamp parsing in retention filtering with explicit failure categories.
**Source Path+Line:** [thegent/src/thegent/execution_run_scan_helpers.py:139]
**Acceptance Checklist:**

- [ ] Add explicit handling for invalid timestamp formats in `filter_expired_record`.
- [ ] Preserve non-expired fallback behavior while tagging invalid timestamp records.
- [ ] Add tests for ISO timestamps, invalid timestamps, and timezone-naive normalization.
      **Notes:** Timestamp parse ambiguity can weaken retention enforcement confidence.

### [WL-6959]

**Title:** Prevent catch-all expiry fallback from hiding retention-scan regressions.
**Source Path+Line:** [thegent/src/thegent/execution_run_scan_helpers.py:151]
**Acceptance Checklist:**

- [ ] Replace blanket exception return path in `filter_expired_record` with classified error handling.
- [ ] Ensure unexpected failures are surfaced via diagnostics without halting scans.
- [ ] Add tests for run-domain lookup issues, malformed records, and stable fallback semantics.
      **Notes:** Silent fallbacks may keep expired records indefinitely when parsing logic regresses.
