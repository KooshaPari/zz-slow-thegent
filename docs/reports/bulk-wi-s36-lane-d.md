### [WL-7350]

**Title:** Separate optional runtime diagnostics import faults from runtime execution failures in doctor reporting
**Source:** [thegent/src/thegent/doctor.py:146]
**Acceptance checklist:**

- [ ] Split multi-runtime diagnostics failure handling into import/setup and execution-path categories.
- [ ] Preserve current non-blocking doctor completion behavior when runtime diagnostics fail.
- [ ] Add tests for successful runtime diagnostics, import-time failure, and execution-time exceptions.
      **Notes:** Catch-all handling at line 146 obscures whether diagnostics failed to load or failed during evaluation.

### [WL-7351]

**Title:** Classify memory diagnostics provider-access errors without collapsing all failures into a generic warning
**Source:** [thegent/src/thegent/doctor.py:169]
**Acceptance checklist:**

- [ ] Replace broad memory diagnostics exception handling with typed access, permission, and platform-failure branches.
- [ ] Preserve current informational memory output when psutil data is available.
- [ ] Add tests for normal memory reporting, psutil access denial, and unsupported-platform edge behavior.
      **Notes:** Generic exception output at line 169 weakens triage signal for memory diagnostics regressions.

### [WL-7352]

**Title:** Preserve cliproxy provider configuration load failure context instead of suppressing configuration exceptions
**Source:** [thegent/src/thegent/doctor.py:530]
**Acceptance checklist:**

- [ ] Replace broad configuration-load suppression in provider discovery with bounded parse and import failure classes.
- [ ] Preserve empty configured-provider behavior when no provider entries exist.
- [ ] Add tests for valid configuration extraction, malformed config payloads, and provider helper import failures.
      **Notes:** Silent exception handling at line 530 can hide provider configuration drift and schema mismatches.

### [WL-7353]

**Title:** Distinguish provider model lookup fallback triggers from unexpected model-resolution faults
**Source:** [thegent/src/thegent/doctor.py:610]
**Acceptance checklist:**

- [ ] Split model fallback handling into known missing-model conditions versus unexpected runtime failures.
- [ ] Preserve provider-name fallback semantics for legitimate no-model cases.
- [ ] Add tests for model resolution success, known missing-model fallback, and unexpected lookup exceptions.
      **Notes:** Catch-all fallback at line 610 masks root causes in provider model resolution flow.

### [WL-7354]

**Title:** Surface provider error body parse-path failures with explicit JSON and payload-shape diagnostics
**Source:** [thegent/src/thegent/doctor.py:636]
**Acceptance checklist:**

- [ ] Replace broad error-body parse suppression with explicit JSON decode and schema-shape classifications.
- [ ] Preserve current message fallback behavior for non-JSON provider responses.
- [ ] Add tests for valid JSON error payloads, plain-text responses, and malformed JSON bodies.
      **Notes:** Generic parse fallback at line 636 can hide upstream payload format regressions.

### [WL-7355]

**Title:** Bound provider request execution failures to typed transport categories for actionable remediation hints
**Source:** [thegent/src/thegent/doctor.py:643]
**Acceptance checklist:**

- [ ] Replace catch-all provider request exception handling with typed timeout, connect, and protocol-failure branches.
- [ ] Preserve current failed-provider status contract in doctor output.
- [ ] Add tests for successful validation, transport timeout, and connection-refused failures.
      **Notes:** Broad exception handling at line 643 reduces precision of provider outage diagnostics.

### [WL-7356]

**Title:** Differentiate process-inspection framework faults from expected inaccessible-process outcomes in activity checks
**Source:** [thegent/src/thegent/doctor.py:813]
**Acceptance checklist:**

- [ ] Split process activity error handling into expected psutil access/process-lifecycle failures and unexpected runtime faults.
- [ ] Preserve current return contract for active/inactive process classification.
- [ ] Add tests for active process detection, expected process disappearance, and unexpected checker exceptions.
      **Notes:** Catch-all handling at line 813 conflates infrastructure defects with normal process churn.

### [WL-7357]

**Title:** Preserve summary run-filter parsing anomalies with structured diagnostics instead of silent run drops
**Source:** [thegent/src/thegent/summary.py:318]
**Acceptance checklist:**

- [ ] Replace broad run-parsing suppression with explicit timestamp-parse and payload-shape failure categories.
- [ ] Preserve continuation across unaffected runs in mixed-validity datasets.
- [ ] Add tests for valid run filtering, malformed timestamps, and partial-data continuation.
      **Notes:** Silent suppression at line 318 can undercount run history during period summaries.

### [WL-7358]

**Title:** Classify native discovery JSON decode failures with bounded output context before fallback execution
**Source:** [thegent/src/thegent/native/discovery_native.py:150]
**Acceptance checklist:**

- [ ] Replace opaque JSON decode fallback behavior with explicit decode diagnostics and safe output truncation metadata.
- [ ] Preserve current Python fallback activation when native output is invalid.
- [ ] Add tests for valid JSON output, malformed output, and empty output handling.
      **Notes:** Decode suppression at line 150 hides malformed native responses and complicates discovery debugging.

### [WL-7359]

**Title:** Distinguish zmx list command execution failure from legitimate empty-session output in fallback listing path
**Source:** [thegent/src/thegent/session/zmx_backend.py:299]
**Acceptance checklist:**

- [ ] Split plain-text fallback list handling into command-failure and empty-session cases with explicit diagnostics.
- [ ] Preserve current parsed-session output contract for valid text listings.
- [ ] Add tests for successful empty output, command failure, and non-empty list parsing.
      **Notes:** Combined failure and empty-output behavior at line 299 can mask zmx availability regressions.
