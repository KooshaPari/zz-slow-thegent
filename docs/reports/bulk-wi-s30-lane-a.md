### [WL-7020]

**Title:** Fall back to env defaults with explicit settings-load diagnostics for critical lane slots
**Source:** [thegent/src/thegent/execution.py:167]
**Acceptance checklist:**

- [ ] Replace the blanket settings initialization catch with typed configuration and validation failure handling.
- [ ] Preserve fallback behavior for critical lane slot defaults while exposing bounded diagnostics for degraded config loading.
- [ ] Add tests for valid settings load, invalid settings payload, and env-var fallback paths.
      **Notes:** Line 167 suppresses all settings initialization failures, which obscures whether slot defaults came from config or emergency fallback.

### [WL-7021]

**Title:** Preserve deadline monitor unregister failures as non-fatal diagnostics
**Source:** [thegent/src/thegent/execution.py:448]
**Acceptance checklist:**

- [ ] Replace catch-all unregister suppression with typed import and monitor operation failure branches.
- [ ] Keep release-path behavior non-blocking while recording unregister failure context.
- [ ] Add tests for successful unregister, missing monitor module, and monitor runtime error paths.
      **Notes:** Line 448 silently drops deadline monitor cleanup failures and can hide stale soft-deadline state.

### [WL-7022]

**Title:** Classify provider score load failures instead of returning an undifferentiated empty score map
**Source:** [thegent/src/thegent/execution.py:1076]
**Acceptance checklist:**

- [ ] Replace broad score-file parsing suppression with explicit file-read and JSON decode failure handling.
- [ ] Preserve safe fallback behavior while exposing deterministic diagnostics for malformed or unreadable score data.
- [ ] Add tests for valid score files, malformed JSON, and permission-denied score paths.
      **Notes:** Line 1076 collapses all score-load failures into `{}`, reducing triage visibility for ranking regressions.

### [WL-7023]

**Title:** Surface calibration factor registry read failures without changing default-factor behavior
**Source:** [thegent/src/thegent/execution.py:1262]
**Acceptance checklist:**

- [ ] Replace catch-all calibration-read suppression with typed parse and filesystem error branches.
- [ ] Preserve `1.0` default factor behavior for missing data while reporting parse/read degradation.
- [ ] Add tests for valid calibration data, malformed JSON, and unreadable registry files.
      **Notes:** Line 1262 hides whether default factors are expected or caused by a broken calibration registry.

### [WL-7024]

**Title:** Track chat-line parse failure classes instead of silently discarding invalid records
**Source:** [thegent/src/thegent/execution.py:1386]
**Acceptance checklist:**

- [ ] Replace blanket chat-line parse suppression with typed validation and decode failure handling.
- [ ] Preserve skip-invalid-record behavior while exposing bounded malformed-record diagnostics.
- [ ] Add tests for valid chat records, malformed JSON payloads, and schema-invalid records.
      **Notes:** Line 1386 returns `None` for every failure mode, making ingestion data loss hard to diagnose.

### [WL-7025]

**Title:** Differentiate message-line decode failures from non-pending status filtering
**Source:** [thegent/src/thegent/execution.py:1398]
**Acceptance checklist:**

- [ ] Replace broad exception handling in pending-message parsing with typed decode and validation branches.
- [ ] Preserve pending-only filtering semantics while separating parse failure accounting from normal status filtering.
- [ ] Add tests for pending entries, non-pending entries, and malformed message records.
      **Notes:** Line 1398 swallows parse faults and blends them into normal non-pending filtering behavior.

### [WL-7026]

**Title:** Make registry tail-hash read failures observable during hash-chain reconstruction
**Source:** [thegent/src/thegent/execution.py:1461]
**Acceptance checklist:**

- [ ] Replace catch-all tail-hash read suppression with typed file I/O and JSON parse handling.
- [ ] Preserve null-hash fallback behavior while recording why tail-hash resolution failed.
- [ ] Add tests for valid tail-hash reads, malformed final record JSON, and unreadable registry paths.
      **Notes:** Line 1461 currently suppresses all failures and can mask broken hash-chain continuity.

### [WL-7027]

**Title:** Distinguish pending-message discovery failures from true empty pending queues
**Source:** [thegent/src/thegent/execution.py:1806]
**Acceptance checklist:**

- [ ] Replace broad pending-list lookup suppression with typed session-meta, path, and registry read error handling.
- [ ] Preserve empty-list return contract where intended while attaching deterministic degraded-state diagnostics.
- [ ] Add tests for pending messages present, missing session metadata, and unreadable message registry files.
      **Notes:** Line 1806 returns `[]` for all failure classes, creating false-no-pending signals.

### [WL-7028]

**Title:** Surface environment transition state read failures separately from missing-state defaults
**Source:** [thegent/src/thegent/execution.py:2102]
**Acceptance checklist:**

- [ ] Replace catch-all transition-state read suppression with typed decode and filesystem error branches.
- [ ] Preserve `None` fallback semantics for absent state while exposing malformed/unreadable state diagnostics.
- [ ] Add tests for valid transition state, malformed JSON state, and permission-denied state file paths.
      **Notes:** Line 2102 currently flattens missing-state and corrupted-state outcomes into the same result.

### [WL-7029]

**Title:** Capture escalation queue parse-drop metrics for skipped malformed records
**Source:** [thegent/src/thegent/execution.py:2460]
**Acceptance checklist:**

- [ ] Replace silent per-line parse suppression with bounded malformed-record counters and optional debug context.
- [ ] Preserve resilient queue scanning behavior while reporting skipped-record totals to callers or diagnostics.
- [ ] Add tests for fully valid queues, mixed valid/invalid lines, and large queues with repeated malformed entries.
      **Notes:** Line 2460 silently discards malformed escalation records, which can hide SLA-related data quality issues.
