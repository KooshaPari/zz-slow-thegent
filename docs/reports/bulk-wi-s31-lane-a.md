### [WL-7070]

**Title:** Preserve multi-runtime diagnostic failure classes instead of collapsing all import and runtime errors
**Source:** [thegent/src/thegent/doctor.py:146]
**Acceptance checklist:**

- [ ] Replace broad exception handling around multi-runtime diagnostics with typed import and runtime failure branches.
- [ ] Preserve non-fatal CLI flow while exposing bounded diagnostics that distinguish unavailable modules from runtime execution faults.
- [ ] Add tests for successful diagnostics, missing diagnostics module, and runtime failure paths.
      **Notes:** Line 146 currently catches all exceptions and obscures whether diagnostics were unavailable or failed during execution.

### [WL-7071]

**Title:** Differentiate memory-inspection dependency failures from transient metric collection errors
**Source:** [thegent/src/thegent/doctor.py:169]
**Acceptance checklist:**

- [ ] Replace blanket memory-info exception handling with typed `psutil` availability and metric-read error branches.
- [ ] Preserve warning-only behavior while surfacing deterministic diagnostics for unsupported platforms and collection failures.
- [ ] Add tests for successful memory reporting, missing `psutil`, and runtime read exceptions.
      **Notes:** Line 169 suppresses failure classes into one warning path, reducing troubleshooting precision for memory diagnostics.

### [WL-7072]

**Title:** Surface cliproxy configuration parse failures during configured-provider discovery
**Source:** [thegent/src/thegent/doctor.py:530]
**Acceptance checklist:**

- [ ] Replace the catch-all provider configuration suppression with typed YAML parse, file-read, and settings initialization branches.
- [ ] Preserve empty-set fallback semantics while attaching bounded degraded-state diagnostics.
- [ ] Add tests for valid config parsing, malformed YAML, and unreadable config paths.
      **Notes:** Line 530 currently hides whether configured providers were truly absent or dropped due to configuration loading faults.

### [WL-7073]

**Title:** Preserve provider model-resolution fault visibility in fallback model selection
**Source:** [thegent/src/thegent/doctor.py:610]
**Acceptance checklist:**

- [ ] Replace broad exception handling around provider definition lookup with typed import, key-access, and parse failure branches.
- [ ] Keep current fallback behavior for unresolved models while recording why model resolution degraded.
- [ ] Add tests for provider login config resolution, definitions fallback, and definitions load errors.
      **Notes:** Line 610 swallows all model-resolution failures, masking configuration drift in provider metadata.

### [WL-7074]

**Title:** Distinguish provider error-body parse faults from provider API failure payloads
**Source:** [thegent/src/thegent/doctor.py:636]
**Acceptance checklist:**

- [ ] Replace blanket JSON parse suppression on provider error responses with typed decode handling and fallback detail extraction.
- [ ] Preserve current status/fix-hint behavior while exposing parse-failure diagnostics separately from provider-returned errors.
- [ ] Add tests for JSON error payloads, plain-text error payloads, and truncated response bodies.
      **Notes:** Line 636 merges response-body parse failures into generic fallback text, reducing fidelity of provider failure triage.

### [WL-7075]

**Title:** Classify provider health-check transport failures without masking timeout vs protocol errors
**Source:** [thegent/src/thegent/doctor.py:643]
**Acceptance checklist:**

- [ ] Replace broad provider validation request suppression with typed transport, timeout, and protocol error branches.
- [ ] Preserve required-provider failure semantics while reporting deterministic failure class metadata.
- [ ] Add tests for successful validation, timeout failures, and connection/protocol exceptions.
      **Notes:** Line 643 catches all exceptions and obscures root-cause categories for inaccessible providers.

### [WL-7076]

**Title:** Separate top-level provider scan aggregation errors from proxy connectivity degradation
**Source:** [thegent/src/thegent/doctor.py:656]
**Acceptance checklist:**

- [ ] Replace broad outer provider-scan exception handling with typed response-parse, schema, and connectivity branches.
- [ ] Preserve existing warn-vs-fail policy while attaching stable diagnostics for each failure family.
- [ ] Add tests for successful provider scans, malformed model listings, and unavailable proxy endpoints.
      **Notes:** Line 656 centralizes all unexpected failures into one path, making provider scan regressions hard to localize.

### [WL-7077]

**Title:** Surface Ollama model-list retrieval failure classes while retaining warning-only behavior
**Source:** [thegent/src/thegent/doctor.py:720]
**Acceptance checklist:**

- [ ] Replace blanket model retrieval suppression with typed API, parsing, and local daemon response handling.
- [ ] Preserve warning semantics for non-blocking model visibility checks while exposing bounded diagnostics.
- [ ] Add tests for model list success, daemon response errors, and malformed model payloads.
      **Notes:** Line 720 swallows all model-list failures into a generic warning, reducing actionable detail for operators.

### [WL-7078]

**Title:** Differentiate Ollama availability check import failures from runtime daemon probe errors
**Source:** [thegent/src/thegent/doctor.py:729]
**Acceptance checklist:**

- [ ] Replace broad outer exception handling in Ollama status checks with typed import and probe failure branches.
- [ ] Preserve current non-fatal check behavior while recording whether failure was dependency-related or runtime-related.
- [ ] Add tests for healthy daemon checks, missing provider module, and probe execution failures.
      **Notes:** Line 729 conflates dependency and runtime errors, reducing confidence in Ollama-check outcomes.

### [WL-7079]

**Title:** Preserve process-activity classifier error specificity for access and unexpected runtime faults
**Source:** [thegent/src/thegent/doctor.py:813]
**Acceptance checklist:**

- [ ] Replace broad fallback exception handling in process activity classification with typed error branching and bounded diagnostics.
- [ ] Preserve boolean/message return contract while distinguishing expected permission/no-process issues from internal errors.
- [ ] Add tests for active processes, inaccessible processes, and unexpected activity-check exceptions.
      **Notes:** Line 813 currently routes all unexpected classifier errors into one generic message, reducing debuggability for stuck-process detection.
