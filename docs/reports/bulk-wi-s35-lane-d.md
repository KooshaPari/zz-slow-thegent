### [WL-7300]

**Title:** Classify doctor startup check bootstrap failures by dependency-load versus runtime invocation
**Source:** [thegent/src/thegent/doctor.py:140]
**Acceptance checklist:**

- [ ] Replace broad startup check exception handling with explicit dependency-load and runtime invocation branches.
- [ ] Preserve current check sequencing and aggregated result emission behavior.
- [ ] Add tests for successful startup checks, import-time failures, and invocation-time faults.
      **Notes:** Collapsed bootstrap exceptions at line 140 reduce precision when triaging doctor startup regressions.

### [WL-7301]

**Title:** Distinguish doctor setup check recovery-path failures from primary execution errors
**Source:** [thegent/src/thegent/doctor.py:164]
**Acceptance checklist:**

- [ ] Split setup-check exception handling into primary execution failure and recovery-path failure categories.
- [ ] Preserve current fallback messaging contract for non-fatal setup check failures.
- [ ] Add tests for primary-path success, primary-path failure with recovery success, and dual-path failure.
      **Notes:** Generic exception handling at line 164 obscures whether remediation failed or initial execution failed.

### [WL-7302]

**Title:** Surface shim probe timeout diagnostics separately from subprocess execution faults
**Source:** [thegent/src/thegent/doctor.py:473]
**Acceptance checklist:**

- [ ] Preserve dedicated timeout classification in shim probes and expand metadata for elapsed timeout context.
- [ ] Keep subprocess fault classification distinct from timeout outcomes.
- [ ] Add tests for successful probe, timeout expiry, and non-timeout subprocess failure.
      **Notes:** Timeout and subprocess-failure paths near line 473 need clearer operator-facing differentiation.

### [WL-7303]

**Title:** Bound shim command exception handling to typed failure classes without catch-all suppression
**Source:** [thegent/src/thegent/doctor.py:476]
**Acceptance checklist:**

- [ ] Replace catch-all shim command exception handling with bounded exception classes and structured diagnostics.
- [ ] Preserve existing status reporting semantics for shim availability checks.
- [ ] Add tests for expected command errors, unexpected runtime faults, and successful shim validation.
      **Notes:** Broad exception handling at line 476 can mask actionable shim command failures.

### [WL-7304]

**Title:** Preserve provider preflight request error taxonomy before provider loop fallback evaluation
**Source:** [thegent/src/thegent/doctor.py:556]
**Acceptance checklist:**

- [ ] Expand preflight request error handling to retain timeout, connection, and transport distinctions.
- [ ] Preserve fallback into provider-loop validation when connectivity permits.
- [ ] Add tests for preflight success, connect timeout, and connect refusal scenarios.
      **Notes:** Provider preflight failure collapse near line 556 makes network diagnosis slower during doctor runs.

### [WL-7305]

**Title:** Classify provider model extraction failures without collapsing to generic provider-name fallback
**Source:** [thegent/src/thegent/doctor.py:610]
**Acceptance checklist:**

- [ ] Replace broad model extraction suppression with explicit key-missing, parse, and type-validation branches.
- [ ] Preserve provider-name fallback behavior when model metadata is unavailable.
- [ ] Add tests for valid model extraction, malformed payloads, and absent metadata keys.
      **Notes:** Silent fallback behavior at line 610 can hide systematic provider payload shape regressions.

### [WL-7306]

**Title:** Surface provider error-payload parse failures with bounded response-body diagnostics
**Source:** [thegent/src/thegent/doctor.py:636]
**Acceptance checklist:**

- [ ] Replace broad error-payload parse suppression with explicit JSON-decode and payload-shape classification.
- [ ] Preserve current auth-failure hint behavior for known status codes.
- [ ] Add tests for JSON error payloads, plain-text payloads, and truncated payload handling.
      **Notes:** Generic parsing fallback at line 636 weakens provider error observability.

### [WL-7307]

**Title:** Distinguish run activity sampling faults from terminal process-state evaluation failures
**Source:** [thegent/src/thegent/doctor.py:813]
**Acceptance checklist:**

- [ ] Replace broad process-activity exception handling with typed sampling and state-evaluation failure paths.
- [ ] Preserve current tuple return contract for active/inactive process classification.
- [ ] Add tests for accessible processes, transient sampling errors, and terminal process disappearance.
      **Notes:** Catch-all handling at line 813 hides the exact stage where process-activity evaluation failed.

### [WL-7308]

**Title:** Preserve summary run-enrichment failure context without swallowing per-run anomalies
**Source:** [thegent/src/thegent/summary.py:318]
**Acceptance checklist:**

- [ ] Replace broad per-run enrichment exception suppression with bounded parse and lookup failure categories.
- [ ] Preserve successful enrichment of unaffected runs in mixed-quality datasets.
- [ ] Add tests for complete enrichment, malformed run metadata, and partial enrichment continuation.
      **Notes:** Silent exception handling at line 318 can under-report summary anomalies.

### [WL-7309]

**Title:** Classify native discovery JSON decode failures with payload-size and command metadata
**Source:** [thegent/src/thegent/native/discovery_native.py:150]
**Acceptance checklist:**

- [ ] Expand JSON decode failure handling to include bounded payload and invocation metadata.
- [ ] Preserve fallback behavior when native discovery output is invalid.
- [ ] Add tests for valid JSON output, malformed JSON output, and empty payload edge cases.
      **Notes:** Decode fallback at line 150 currently lacks context needed for native discovery incident triage.
