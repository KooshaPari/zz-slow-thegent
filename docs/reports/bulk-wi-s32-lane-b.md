### [WL-7130]

**Title:** Classify Claude headless runtime failures beyond generic execution errors
**Source:** [thegent/src/thegent/doctor.py:925]
**Acceptance checklist:**

- [ ] Replace broad Claude headless exception handling with typed subprocess launch, decode, and runtime failure branches.
- [ ] Preserve required-provider failure semantics while keeping current timeout handling unchanged.
- [ ] Add tests for successful Claude headless checks, launch/runtime exceptions, and malformed output decode paths.
      **Notes:** Catch-all handling at the Claude headless execution boundary compresses distinct runtime faults into one opaque failure message.

### [WL-7131]

**Title:** Preserve Codex headless probe failure specificity for execution and decoding paths
**Source:** [thegent/src/thegent/doctor.py:985]
**Acceptance checklist:**

- [ ] Replace broad Codex headless exception handling with explicit launch, transport, and output-parse failure categories.
- [ ] Preserve current required-feature behavior and fix-hint routing for credential issues.
- [ ] Add tests for successful Codex headless checks, subprocess failures, and malformed stdout/stderr payload handling.
      **Notes:** The current generic exception branch obscures whether Codex headless failures are execution-time faults or output-shape errors.

### [WL-7132]

**Title:** Distinguish Droid probe execution faults from optional-shim degradation states
**Source:** [thegent/src/thegent/doctor.py:1045]
**Acceptance checklist:**

- [ ] Replace broad Droid probe exception handling with typed command execution and response-shape diagnostics.
- [ ] Preserve warning-only semantics for optional Droid tooling while keeping existing timeout and not-found branches.
- [ ] Add tests for successful Droid probe, runtime execution exceptions, and malformed command output handling.
      **Notes:** Generic error collapsing in the Droid probe path hides actionable differences between command runtime and parse-level failures.

### [WL-7133]

**Title:** Separate process-leak analysis runtime faults from dependency availability outcomes
**Source:** [thegent/src/thegent/doctor.py:1205]
**Acceptance checklist:**

- [ ] Replace broad process-analysis exception handling with typed psutil runtime, permission, and aggregation failure categories.
- [ ] Preserve warn-level reporting contract when process analysis cannot fully complete.
- [ ] Add tests for successful leak analysis, partial collection failures, and aggregation-time exceptions.
      **Notes:** A single catch-all branch for process analysis reduces signal on whether failures came from collection, permission, or report synthesis.

### [WL-7134]

**Title:** Classify runtime-infrastructure inspection failures without masking initialization errors
**Source:** [thegent/src/thegent/doctor.py:1231]
**Acceptance checklist:**

- [ ] Replace broad runtime infrastructure check exception handling with typed import, initialization-state, and execution failure branches.
- [ ] Preserve current warn behavior for unavailable runtime checks while improving diagnostic precision.
- [ ] Add tests for initialized infrastructure, import failures, and runtime inspection exceptions.
      **Notes:** Current generic exception handling merges missing-module and runtime-state failures into one ambiguous warning path.

### [WL-7135]

**Title:** Preserve resource-monitoring fetch failure classes in runtime stats diagnostics
**Source:** [thegent/src/thegent/doctor.py:1274]
**Acceptance checklist:**

- [ ] Replace broad resource-stats exception handling with typed stats retrieval, schema, and formatting failure categories.
- [ ] Preserve suspicion-level status mapping for valid stats payloads.
- [ ] Add tests for valid stats reporting, malformed stats objects, and runtime retrieval failures.
      **Notes:** Blanket exception handling at resource stats retrieval hides whether monitoring failed due to missing data shape or runtime fetch errors.

### [WL-7136]

**Title:** Differentiate Ollama validation runtime failures from expected transport error branches
**Source:** [thegent/src/thegent/doctor.py:1343]
**Acceptance checklist:**

- [ ] Replace broad post-transport Ollama exception handling with typed response-parse and validation failure diagnostics.
- [ ] Preserve existing timeout/connect-specific handling and warning semantics.
- [ ] Add tests for successful Ollama validation, malformed API payloads, and unexpected validation exceptions.
      **Notes:** The current final catch-all in Ollama validation can hide parse and schema regressions that are distinct from network reachability issues.

### [WL-7137]

**Title:** Expose process-registry analysis failure families in runtime infrastructure checks
**Source:** [thegent/src/thegent/doctor.py:1468]
**Acceptance checklist:**

- [ ] Replace broad process-registry exception handling with typed registry access, psutil query, and report assembly failure branches.
- [ ] Preserve current warning behavior when registry analysis cannot fully complete.
- [ ] Add tests for successful registry analysis, registry-access failures, and per-process inspection exceptions.
      **Notes:** Catch-all registry analysis failure handling blurs registry read errors with downstream process-inspection faults.

### [WL-7138]

**Title:** Classify MCP health probe failures before top-level tools-check fallback handling
**Source:** [thegent/src/thegent/doctor.py:1505]
**Acceptance checklist:**

- [ ] Replace nested generic MCP probe exception handling with typed connection, timeout, and protocol failure branches.
- [ ] Preserve existing warning behavior when MCP server is unavailable.
- [ ] Add tests for healthy MCP responses, non-200 responses, and transport exceptions during health checks.
      **Notes:** Nested catch-all handling in MCP tools checks reduces observability into whether failures are transport-level or response-level.

### [WL-7139]

**Title:** Separate session-directory state checks from filesystem creation and permission faults
**Source:** [thegent/src/thegent/doctor.py:1547]
**Acceptance checklist:**

- [ ] Replace broad session-directory exception handling with explicit path resolution, permission, and directory-creation failure categories.
- [ ] Preserve current success/fail semantics for writable, non-writable, and newly created session directories.
- [ ] Add tests for writable directories, create-on-missing success, and permission-denied creation paths.
      **Notes:** A top-level catch-all around session directory checks hides whether failures occur during path inspection, access checks, or directory creation.
