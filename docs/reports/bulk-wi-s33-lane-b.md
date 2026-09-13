### [WL-7180]

**Title:** Separate session-count enumeration failures from writable-directory pass state
**Source:** [thegent/src/thegent/doctor.py:1529]
**Acceptance checklist:**

- [ ] Replace silent session-count exception suppression with typed iteration and permission failure diagnostics.
- [ ] Preserve writable-directory success semantics when counting child session directories is unavailable.
- [ ] Add tests for successful session counting, permission-denied iteration, and non-fatal count fallback behavior.
      **Notes:** Silent suppression in session directory counting masks directory traversal faults that should be observable as degraded diagnostics.

### [WL-7181]

**Title:** Classify stale shadow directory stat failures in project-hints scanning
**Source:** [thegent/src/thegent/doctor.py:1580]
**Acceptance checklist:**

- [ ] Replace generic stale-shadow stat exception handling with explicit missing-path and permission failure categories.
- [ ] Preserve continued scanning of sibling `.shadow-*` directories after per-path stat faults.
- [ ] Add tests for stale-dir detection, stat permission failure, and mixed valid/invalid shadow directory sets.
      **Notes:** Current broad OSError continuation obscures whether stale-shadow counting skips entries due to permissions, races, or invalid paths.

### [WL-7182]

**Title:** Preserve create-path failure classes during automatic mkdir-based doctor fixes
**Source:** [thegent/src/thegent/doctor.py:1657]
**Acceptance checklist:**

- [ ] Replace broad mkdir fix exception handling with typed path-resolution, permission, and filesystem-state error categories.
- [ ] Preserve current successful fix reporting and state transitions for newly created paths.
- [ ] Add tests for successful path creation, permission-denied creation, and invalid expanded-path handling.
      **Notes:** The catch-all around fix-time directory creation compresses actionable failure causes into a single opaque error branch.

### [WL-7183]

**Title:** Distinguish command-timeout failures from generic fix execution errors
**Source:** [thegent/src/thegent/doctor.py:1800]
**Acceptance checklist:**

- [ ] Preserve timeout-specific reporting while tightening non-timeout exception classification for fix command execution.
- [ ] Ensure timeout and non-timeout failures produce stable, machine-readable fix status values.
- [ ] Add tests for timed-out fix commands, non-timeout execution exceptions, and successful command completion.
      **Notes:** Timeout handling is explicit, but adjacent generic exception reporting can still blur distinct runtime failure categories.

### [WL-7184]

**Title:** Separate fix-report status synthesis errors from successful command outcomes
**Source:** [thegent/src/thegent/doctor.py:1813]
**Acceptance checklist:**

- [ ] Harden status derivation logic to avoid misclassifying non-success result strings as generic failures.
- [ ] Preserve existing success and dry-run status mapping behavior.
- [ ] Add tests for success, dry-run, timeout, and structured error-prefixed result values.
      **Notes:** Inline conditional status synthesis risks collapsing nuanced fix outcomes into ambiguous aggregate statuses.

### [WL-7185]

**Title:** Classify diagnostics rendering failures in doctor fix report presentation
**Source:** [thegent/src/thegent/doctor.py:1866]
**Acceptance checklist:**

- [ ] Add bounded presentation-failure handling for table rendering and summary output generation.
- [ ] Preserve fix-report data integrity even when rich output rendering partially fails.
- [ ] Add tests for normal fix report display, malformed entry rendering, and fallback summary-only output.
      **Notes:** Unprotected report rendering paths can terminate user-visible diagnostics when formatting-time issues occur.

### [WL-7186]

**Title:** Preserve actionable-hint normalization failures without aborting result summaries
**Source:** [thegent/src/thegent/doctor.py:1947]
**Acceptance checklist:**

- [ ] Add bounded failure handling around hint normalization and dedupe processing.
- [ ] Preserve sorted actionable hint output for well-formed hint collections.
- [ ] Add tests for normal hint normalization, malformed hint values, and mixed valid/invalid hint sets.
      **Notes:** Hint normalization currently assumes valid strings and can jeopardize summary output if unexpected hint payloads appear.

### [WL-7187]

**Title:** Differentiate provider-matrix message-parse faults from absent model-count metadata
**Source:** [thegent/src/thegent/doctor.py:1977]
**Acceptance checklist:**

- [ ] Replace implicit string-shape assumptions in provider matrix parsing with explicit parse and fallback branches.
- [ ] Preserve current model-count extraction when provider messages follow expected formatting.
- [ ] Add tests for expected provider messages, missing parentheses metadata, and malformed status message strings.
      **Notes:** Provider matrix extraction logic can silently degrade when message shape drifts, reducing dashboard accuracy.

### [WL-7188]

**Title:** Classify memory diagnostics fetch failures beyond generic virtual-memory exceptions
**Source:** [thegent/src/thegent/doctor.py:165]
**Acceptance checklist:**

- [ ] Replace broad memory diagnostics exception handling with typed psutil import, access, and runtime retrieval failure branches.
- [ ] Preserve existing successful memory diagnostics output formatting and units.
- [ ] Add tests for successful memory diagnostics, psutil runtime errors, and unavailable memory metric scenarios.
      **Notes:** Generic memory-diagnostics exception handling obscures whether failures originate in dependency loading or metric collection.

### [WL-7189]

**Title:** Separate runtime diagnostics import failures from execution-time status collection errors
**Source:** [thegent/src/thegent/doctor.py:141]
**Acceptance checklist:**

- [ ] Replace broad runtime diagnostics exception handling with explicit import, invocation, and display failure categories.
- [ ] Preserve optional runtime diagnostics behavior when `--runtime` is enabled.
- [ ] Add tests for successful runtime diagnostics, missing diagnostics module import, and runtime status retrieval failures.
      **Notes:** A single catch-all branch for runtime diagnostics hides whether optional feature failures come from missing modules or execution faults.
