### [WL-7520]

**Title:** Preserve checkpoint-match behavior while replacing blanket JSON parse suppression in fallback path
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:86]
**Acceptance checklist:**

- [ ] Replace broad fallback exception handling in `parse_checkpoint_by_id` with typed JSON decode and payload-shape guards.
- [ ] Preserve existing `None` return behavior for non-matching or malformed checkpoint lines.
- [ ] Add tests for valid checkpoint match, malformed JSON, and missing `checkpoint_id` cases.
      **Notes:** Line 86 currently suppresses all fallback parser failures via `except Exception: pass`.

### [WL-7521]

**Title:** Keep circuit failure window semantics while separating timestamp parse and JSON decode errors
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:116]
**Acceptance checklist:**

- [ ] Replace broad fallback exception suppression in `parse_circuit_failure` with explicit JSON decode, timestamp parse, and key-shape handling.
- [ ] Preserve current `(0, None)` behavior for invalid or out-of-window entries.
- [ ] Add tests for matching failure events, invalid timestamps, and malformed JSON input.
      **Notes:** Line 116 currently collapses unrelated fallback failure types into a silent `pass` path.

### [WL-7522]

**Title:** Maintain override-expiration result contract while making fallback parse failures diagnosable
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:143]
**Acceptance checklist:**

- [ ] Narrow fallback exception handling in `parse_override_unexpired` to typed JSON and datetime parsing failures.
- [ ] Preserve existing `False` behavior for missing owner, missing expiry, and malformed records.
- [ ] Add tests for unexpired override, expired override, malformed JSON, and invalid `expires_at_utc` values.
      **Notes:** Line 143 currently converts every fallback exception into `False` without classifying cause.

### [WL-7523]

**Title:** Preserve fatigue-window counting while replacing blanket fallback error suppression
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:161]
**Acceptance checklist:**

- [ ] Replace broad exception suppression in `parse_fatigue_line` with explicit JSON decode and timestamp parsing branches.
- [ ] Preserve current `0` fallback for malformed or out-of-window entries.
- [ ] Add tests for in-window events, stale events, malformed JSON, and missing timestamp fields.
      **Notes:** Line 161 currently catches all fallback failures and silently skips classification.

### [WL-7524]

**Title:** Keep DLQ status/run filters intact while surfacing fallback payload-shape failures
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:184]
**Acceptance checklist:**

- [ ] Replace broad exception handling in `parse_dlq_item` fallback with typed JSON and schema validation handling.
- [ ] Preserve existing filter semantics for `status` and `run_id` and `None` on invalid lines.
- [ ] Add tests for filtered matches, filtered misses, malformed JSON, and non-dict payloads.
      **Notes:** Line 184 currently returns `None` for all fallback exceptions without distinguishing parse vs schema errors.

### [WL-7525]

**Title:** Preserve DLQ resolution update contract while classifying malformed fallback entries
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:197]
**Acceptance checklist:**

- [ ] Replace blanket exception handling in `process_dlq_line` with typed decode and payload-shape guards.
- [ ] Preserve existing `(line, False)` fallback contract on invalid input.
- [ ] Add tests for resolvable pending-review entries, non-matching entries, and malformed JSON lines.
      **Notes:** Line 197 currently routes all fallback failures into one generic recovery result.

### [WL-7526]

**Title:** Keep checkpoint registry parsing semantics while differentiating decode and type-validation failures
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:214]
**Acceptance checklist:**

- [ ] Replace broad fallback exception handling in `parse_checkpoint_line` with explicit JSON decode and payload type checks.
- [ ] Preserve current `None` result for invalid checkpoint registry lines.
- [ ] Add tests for valid checkpoint payloads, malformed JSON, and non-object JSON values.
      **Notes:** Line 214 currently hides all fallback parsing failures behind a single `None` return.

### [WL-7527]

**Title:** Keep native parser load behavior while isolating module import and execution failure classes
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:66]
**Acceptance checklist:**

- [ ] Replace broad native-loader exception handling with explicit import lookup, module execution, and attribute-resolution branches.
- [ ] Preserve existing behavior that falls back to pure-Python parsing when native module loading fails.
- [ ] Add tests for native parser absent, native parser import failure, and successful native load scenarios.
      **Notes:** Line 66 executes dynamic module loading where failures should remain diagnosable without breaking fallback.

### [WL-7528]

**Title:** Preserve native checkpoint parsing fallback while typing native return-shape validation failures
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:78]
**Acceptance checklist:**

- [ ] Add explicit validation branches for unexpected native return types in `parse_checkpoint_by_id` before fallback parse.
- [ ] Preserve existing fallback JSON parsing path when native output is invalid.
- [ ] Add tests for valid native dict output, invalid native output types, and fallback parser success.
      **Notes:** Line 78 currently relies on broad exception capture downstream for native parse anomalies.

### [WL-7529]

**Title:** Maintain circuit timestamp normalization while hardening native parser tuple-shape checks
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:102]
**Acceptance checklist:**

- [ ] Add explicit tuple-length and timestamp-type validation for native `parse_circuit_failure` output.
- [ ] Preserve current fallback behavior when native output is malformed.
- [ ] Add tests for valid native tuple output, malformed tuple payloads, and fallback parse behavior.
      **Notes:** Line 102 converts native timestamp fields and should fail with typed diagnostics instead of broad recovery.
