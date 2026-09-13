### [WL-7570]

**Title:** Preserve checkpoint lookup behavior while replacing blanket parse suppression in fallback JSON path
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:86]
**Acceptance checklist:**

- [ ] Replace broad exception suppression in `parse_checkpoint_by_id` with typed JSON decode and payload-shape checks.
- [ ] Preserve current `None` return behavior for malformed lines and non-matching checkpoint IDs.
- [ ] Add tests for valid match, malformed JSON, and missing `checkpoint_id` fields.
      **Notes:** Line 86 currently uses `except Exception: pass`, which hides decode vs schema failures.

### [WL-7571]

**Title:** Guard circuit-failure timestamp normalization against invalid native payload types
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:102]
**Acceptance checklist:**

- [ ] Add explicit native timestamp type validation before `datetime.fromisoformat` in `parse_circuit_failure`.
- [ ] Preserve fallback behavior when native parser output is malformed.
- [ ] Add tests for valid native tuple output, non-string timestamps, and empty timestamp fields.
      **Notes:** Line 102 assumes string-form ISO timestamps and can misclassify native parser shape errors.

### [WL-7572]

**Title:** Keep circuit failure-window semantics while separating JSON decode and datetime parse failures
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:116]
**Acceptance checklist:**

- [ ] Replace broad fallback exception suppression in `parse_circuit_failure` with typed JSON and datetime error handling.
- [ ] Preserve `(0, None)` behavior for malformed or out-of-window events.
- [ ] Add tests for in-window failures, stale entries, malformed JSON, and invalid `timestamp` values.
      **Notes:** Line 116 currently collapses unrelated failure classes into a silent skip path.

### [WL-7573]

**Title:** Preserve DLQ resolution contract while classifying malformed input vs non-matching records
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:197]
**Acceptance checklist:**

- [ ] Replace blanket exception handling in `process_dlq_line` with typed decode and object-shape checks.
- [ ] Preserve existing `(line, False)` fallback for invalid payloads.
- [ ] Add tests for successful resolution updates, non-matching records, and malformed JSON lines.
      **Notes:** Line 197 currently routes all parse and shape failures into one generic outcome.

### [WL-7574]

**Title:** Sanitize conversation IDs before filename construction to prevent invalid paths and traversal tokens
**Source:** [thegent/src/thegent/session/conversation_dumper.py:155]
**Acceptance checklist:**

- [ ] Normalize `conversation_id` into a safe filename segment before building markdown dump paths.
- [ ] Preserve existing naming convention and timestamp precision for valid IDs.
- [ ] Add tests for IDs containing slashes, spaces, and path traversal characters.
      **Notes:** Line 155 directly interpolates raw IDs into filenames, which can produce unsafe or invalid paths.

### [WL-7575]

**Title:** Bound JSON dump serialization size to prevent large metadata payloads from stalling write operations
**Source:** [thegent/src/thegent/session/conversation_dumper.py:211]
**Acceptance checklist:**

- [ ] Add explicit limits or truncation policy for oversized metadata before JSON serialization.
- [ ] Preserve valid JSON dump structure and UTF-8 write behavior for normal-sized records.
- [ ] Add tests covering normal metadata, oversized metadata rejection/truncation, and write success.
      **Notes:** Line 211 serializes unbounded payloads, which can create reliability and latency issues on large dumps.

### [WL-7576]

**Title:** Expand dump listing filter behavior to include JSON artifacts when querying by conversation ID
**Source:** [thegent/src/thegent/session/conversation_dumper.py:232]
**Acceptance checklist:**

- [ ] Add an option to list both markdown and JSON dump files for a given conversation ID.
- [ ] Preserve current default ordering by modification time (newest first).
- [ ] Add tests for markdown-only, JSON-only, and combined listing behavior.
      **Notes:** Line 232 currently hardcodes markdown patterns, reducing operator visibility into JSON dump outputs.

### [WL-7577]

**Title:** Reduce append-turn memory churn by making deep-copy behavior configurable for trusted call paths
**Source:** [thegent/src/thegent/session/manager.py:59]
**Acceptance checklist:**

- [ ] Introduce an explicit API control for copy strategy in `append_turn` with safe default behavior.
- [ ] Preserve isolation guarantees for default session history mutation semantics.
- [ ] Add tests validating default deep-copy isolation and opt-in lower-overhead append mode.
      **Notes:** Line 59 deep-copies every turn payload unconditionally, which can be expensive for large transcripts.

### [WL-7578]

**Title:** Support zero-turn rollback as a no-op to simplify idempotent rollback workflows
**Source:** [thegent/src/thegent/session/manager.py:85]
**Acceptance checklist:**

- [ ] Change rollback validation to allow `n_turns == 0` and return current turn count.
- [ ] Preserve existing error behavior for negative or out-of-range rollback requests.
- [ ] Add tests for no-op rollback, valid rollback, and overflow rollback attempts.
      **Notes:** Line 85 rejects zero rollback requests, which complicates idempotent orchestration logic.

### [WL-7579]

**Title:** Improve config resolution diagnostics by classifying OpenTelemetry import failures explicitly
**Source:** [thegent/src/thegent/config_provider.py:94]
**Acceptance checklist:**

- [ ] Add explicit error classification and logging context around OpenTelemetry import/use in `EnvConfigProvider.resolve`.
- [ ] Preserve successful config resolution semantics and override merge behavior.
- [ ] Add tests for environments with and without OpenTelemetry dependencies.
      **Notes:** Line 94 performs a runtime import with no dedicated diagnostic path, making dependency issues harder to triage.
