### [WL-7200]

**Title:** Surface configured-provider discovery failures instead of returning partial provider sets silently
**Source:** [thegent/src/thegent/doctor.py:530]
**Acceptance checklist:**

- [ ] Replace catch-all provider-discovery suppression with typed config-read and parse-failure handling.
- [ ] Preserve successful provider enumeration for valid CLIProxy configuration and OAuth credential states.
- [ ] Add tests for readable configs, malformed compatibility payloads, and credential lookup failures.
      **Notes:** Silent provider-drop behavior can hide auth configuration regressions from operators.

### [WL-7201]

**Title:** Differentiate model-selection failure causes before defaulting to provider-name probes
**Source:** [thegent/src/thegent/doctor.py:610]
**Acceptance checklist:**

- [ ] Replace broad model-resolution exception handling with explicit missing-model, import, and decode branches.
- [ ] Preserve provider validation behavior when authoritative model metadata is unavailable.
- [ ] Add tests for valid model selection, malformed provider definitions, and absent model hints.
      **Notes:** Untyped model fallback makes provider validation failures harder to triage.

### [WL-7202]

**Title:** Preserve response-body parse diagnostics when provider validation returns non-JSON error payloads
**Source:** [thegent/src/thegent/doctor.py:636]
**Acceptance checklist:**

- [ ] Classify response parse errors distinctly from transport and auth failures during provider checks.
- [ ] Preserve existing HTTP status handling and fix-hint behavior for 401/403 responses.
- [ ] Add tests for JSON errors, plain-text errors, and truncated payload scenarios.
      **Notes:** Collapsed parse failures can mask root causes during provider incident response.

### [WL-7203]

**Title:** Distinguish git command execution faults from true no-commit windows in summary generation
**Source:** [thegent/src/thegent/summary.py:60]
**Acceptance checklist:**

- [ ] Replace blanket git-log suppression with typed subprocess failure classification.
- [ ] Preserve empty-list behavior for legitimate windows with no commits.
- [ ] Add tests for successful commit retrieval, non-git directories, and command failures.
      **Notes:** Silent git failures reduce trust in generated summary completeness.

### [WL-7204]

**Title:** Surface malformed chat-log entry diagnostics during summary log parsing
**Source:** [thegent/src/thegent/summary.py:79]
**Acceptance checklist:**

- [ ] Replace broad parse suppression in `_parse_log_entry` with typed JSON and timestamp parse handling.
- [ ] Preserve filtering semantics for non-user/assistant messages and out-of-window events.
- [ ] Add tests for valid entries, malformed JSON lines, and invalid timestamp formats.
      **Notes:** Hidden parse errors make malformed records indistinguishable from intentional filters.

### [WL-7205]

**Title:** Make per-file chat-log read failures observable during summary aggregation
**Source:** [thegent/src/thegent/summary.py:93]
**Acceptance checklist:**

- [ ] Replace silent file-read suppression with explicit IO and decode error handling.
- [ ] Preserve successful aggregation for readable files in mixed-quality log directories.
- [ ] Add tests for readable logs, unreadable files, and corrupted content.
      **Notes:** Silent file-level drops can undercount conversation activity.

### [WL-7206]

**Title:** Classify run timestamp coercion failures when filtering summary runs by period
**Source:** [thegent/src/thegent/summary.py:145]
**Acceptance checklist:**

- [ ] Replace broad timestamp-parse suppression with typed datetime parse error handling.
- [ ] Preserve inclusion behavior for runs with valid UTC timestamps.
- [ ] Add tests for valid timestamps, malformed `started_at_utc` values, and missing fields.
      **Notes:** Opaque timestamp parse drops can skew run-level audit coverage.

### [WL-7207]

**Title:** Preserve tmux fallback probe failure signal in native discovery session listing
**Source:** [thegent/src/thegent/native/discovery_native.py:59]
**Acceptance checklist:**

- [ ] Replace blanket fallback-session suppression with typed subprocess and timeout handling.
- [ ] Preserve empty-session behavior when tmux output is valid but empty.
- [ ] Add tests for healthy tmux output, probe failures, and malformed rows.
      **Notes:** Silent fallback probe failures obscure native discovery degradation.

### [WL-7208]

**Title:** Expose psutil dependency-missing failures for fallback process discovery
**Source:** [thegent/src/thegent/native/discovery_native.py:77]
**Acceptance checklist:**

- [ ] Replace broad psutil-import suppression with explicit missing-dependency signaling.
- [ ] Preserve no-process behavior for valid scans with zero matches.
- [ ] Add tests for present `psutil`, absent `psutil`, and invalid regex patterns.
      **Notes:** Hidden dependency failures make runtime capability drift difficult to detect.

### [WL-7209]

**Title:** Surface per-process inspection errors during fallback process enumeration
**Source:** [thegent/src/thegent/native/discovery_native.py:111]
**Acceptance checklist:**

- [ ] Replace catch-all per-item suppression with bounded error classification and diagnostics.
- [ ] Preserve continued scanning behavior for unaffected process rows.
- [ ] Add tests for healthy iteration, malformed process payloads, and intermittent access errors.
      **Notes:** Silent per-row drops can bias diagnostic output under load.
