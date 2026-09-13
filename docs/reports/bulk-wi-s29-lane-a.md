### [WL-6970]

**Title:** Replace provider-discovery catch-all suppression with typed credential parse diagnostics
**Source:** [thegent/src/thegent/doctor.py:530]
**Acceptance checklist:**

- [ ] Replace blanket exception swallowing in configured-provider discovery with explicit configuration and parsing failure branches.
- [ ] Preserve successful provider discovery while surfacing bounded diagnostics for malformed or unreadable provider config.
- [ ] Add tests for valid configuration, malformed config payloads, and unreadable credential paths.
      **Notes:** Line 530 currently suppresses all failures and can hide provider-discovery regressions behind an empty configured-provider set.

### [WL-6971]

**Title:** Surface provider model-resolution failures instead of silently substituting fallback IDs
**Source:** [thegent/src/thegent/doctor.py:610]
**Acceptance checklist:**

- [ ] Replace broad exception handling around provider model resolution with typed import and config lookup error handling.
- [ ] Preserve current model selection behavior for valid providers while attaching deterministic diagnostics when lookups fail.
- [ ] Add tests for provider definitions present, missing provider definitions, and import/runtime failures during model lookup.
      **Notes:** Line 610 collapses multiple model-resolution failure classes into one fallback path, reducing triage precision.

### [WL-6972]

**Title:** Classify provider error-body decode failures separately from transport failures
**Source:** [thegent/src/thegent/doctor.py:636]
**Acceptance checklist:**

- [ ] Replace catch-all error-body parsing with typed JSON decode handling and explicit fallback text extraction.
- [ ] Preserve provider validation result semantics while exposing parse-failure context in diagnostics.
- [ ] Add tests for structured JSON error bodies, plain-text error bodies, and malformed JSON responses.
      **Notes:** Line 636 currently catches everything, which obscures whether failures come from body format drift or upstream transport issues.

### [WL-6973]

**Title:** Split provider list fetch failure handling into connection, protocol, and payload classes
**Source:** [thegent/src/thegent/doctor.py:656]
**Acceptance checklist:**

- [ ] Replace generic outer exception handling for provider enumeration with typed network, timeout, and payload parsing branches.
- [ ] Preserve warn-vs-fail behavior where intended while attaching deterministic failure-category details.
- [ ] Add tests for connection-refused, timeout, malformed payload, and unexpected runtime error paths.
      **Notes:** Line 656 currently routes diverse failure modes through one broad catch path, reducing operator signal quality.

### [WL-6974]

**Title:** Narrow CLIProxy config read failure handling to explicit YAML and file I/O categories
**Source:** [thegent/src/thegent/doctor_setup_checks.py:60]
**Acceptance checklist:**

- [ ] Replace broad config-read exception handling with typed YAML parse and filesystem error branches.
- [ ] Preserve current pass/fail output contract while surfacing actionable read-versus-parse diagnostics.
- [ ] Add tests for valid config, malformed YAML, and permission-denied configuration files.
      **Notes:** Line 60 captures all exceptions, making invalid format and unreadable file failures indistinguishable.

### [WL-6975]

**Title:** Expose MCP health-probe preflight failures before auto-start fallback
**Source:** [thegent/src/thegent/doctor_setup_checks.py:106]
**Acceptance checklist:**

- [ ] Replace preflight catch-all around MCP health check with typed timeout, connection, and protocol failure reporting.
- [ ] Preserve auto-start behavior while recording why the initial health probe failed.
- [ ] Add tests for healthy MCP response, connection-refused preflight, and timeout preflight branches.
      **Notes:** Line 106 silently suppresses preflight failures and hides root cause when auto-start later fails.

### [WL-6976]

**Title:** Make mise hook file read failures visible during install verification
**Source:** [thegent/src/thegent/install.py:529]
**Acceptance checklist:**

- [ ] Replace broad hook-read suppression with typed file-read and decode failure diagnostics.
- [ ] Preserve hook detection behavior for readable files while reporting skipped unreadable hook sources.
- [ ] Add tests for readable hook files, unreadable files, and invalid encoding scenarios.
      **Notes:** Line 529 silently ignores hook-file read failures and can produce misleading hook-not-found warnings.

### [WL-6977]

**Title:** Preserve process-compose PID discovery failures as structured lockfile diagnostics
**Source:** [thegent/src/thegent/shared_mcp_manager.py:94]
**Acceptance checklist:**

- [ ] Replace blanket exception swallowing in PID discovery with typed subprocess and parse failure handling.
- [ ] Preserve lockfile creation behavior while recording whether PID discovery failed and why.
- [ ] Add tests for successful PID extraction, empty process list, and malformed `pgrep` output.
      **Notes:** Line 94 drops all PID discovery failures silently, reducing observability for shared MCP lifecycle debugging.

### [WL-6978]

**Title:** Track compositor slot render error classes instead of returning generic render placeholders
**Source:** [thegent/src/thegent/ui/compositor_manager.py:447]
**Acceptance checklist:**

- [ ] Replace catch-all render boundary with typed rendering failure classification and bounded diagnostic metadata.
- [ ] Preserve non-crashing slot rendering behavior while keeping error placeholders deterministic.
- [ ] Add tests for successful render, known renderer failure type, and unknown renderer exception handling.
      **Notes:** Line 447 masks renderer fault classes behind a single placeholder string, which limits root-cause isolation.

### [WL-6979]

**Title:** Differentiate KPI fatigue metric import failures from runtime calculation faults
**Source:** [thegent/src/thegent/ux/kpis.py:47]
**Acceptance checklist:**

- [ ] Replace blanket fatigue metric exception suppression with typed import, construction, and computation failure handling.
- [ ] Preserve default KPI rendering contract while exposing bounded degraded-metric diagnostics.
- [ ] Add tests for successful fatigue metric collection, missing dependency import, and runtime computation errors.
      **Notes:** Line 47 silently suppresses all fatigue metric failures and can mask regressions in KPI health signals.
