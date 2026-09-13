### [WL-7400]

**Title:** Classify Claude headless run unexpected failures beyond timeout handling
**Source:** [thegent/src/thegent/doctor.py:925]
**Acceptance checklist:**

- [ ] Replace broad Claude headless exception handling with explicit process-launch, decode, and environment error branches.
- [ ] Preserve current timeout warning behavior and failed-run reporting contract.
- [ ] Add tests for successful Claude headless run, timeout path, and non-timeout execution failure.
      **Notes:** The catch-all at line 925 obscures non-timeout failure causes after command execution attempts.

### [WL-7401]

**Title:** Preserve Codex headless diagnostics by separating runtime failure categories
**Source:** [thegent/src/thegent/doctor.py:985]
**Acceptance checklist:**

- [ ] Replace broad Codex headless exception handling with typed subprocess, decode, and environment failure categories.
- [ ] Preserve existing success/fail/warn status semantics for healthy and timeout runs.
- [ ] Add tests for successful Codex headless validation, timeout warning, and non-timeout execution errors.
      **Notes:** Line 985 currently folds heterogeneous Codex headless failures into one generic error message.

### [WL-7402]

**Title:** Distinguish Droid headless command faults from expected shim and timeout conditions
**Source:** [thegent/src/thegent/doctor.py:1045]
**Acceptance checklist:**

- [ ] Replace broad Droid headless exception handling with explicit command-invocation and output-parse failure branches.
- [ ] Preserve existing FileNotFound and timeout pathways already modeled above this block.
- [ ] Add tests for successful Droid probe, missing-command warning, timeout warning, and unexpected runtime failure.
      **Notes:** The fallback catch at line 1045 masks root causes that should be separated from modeled timeout and missing-binary states.

### [WL-7403]

**Title:** Bound process leak analysis failures with explicit inspection-stage diagnostics
**Source:** [thegent/src/thegent/doctor.py:1205]
**Acceptance checklist:**

- [ ] Replace broad process-analysis exception handling with typed process-enumeration, inspection, and reporting failure categories.
- [ ] Preserve current warning status contract when analysis cannot complete.
- [ ] Add tests for successful leak analysis, psutil access issues, and unexpected aggregation failures.
      **Notes:** Line 1205 currently compresses multi-stage leak analysis failures into one warning path.

### [WL-7404]

**Title:** Separate runtime infrastructure import errors from initialization state evaluation failures
**Source:** [thegent/src/thegent/doctor.py:1231]
**Acceptance checklist:**

- [ ] Replace broad runtime infrastructure exception handling with explicit import-time and runtime-check failure branches.
- [ ] Preserve existing initialized/not-initialized result semantics on healthy paths.
- [ ] Add tests for successful initialization detection, missing runtime module, and check-time exceptions.
      **Notes:** The catch-all at line 1231 hides whether failure occurred while loading runtime helpers or executing the check.

### [WL-7405]

**Title:** Classify resource statistics retrieval faults before emitting generic monitoring warnings
**Source:** [thegent/src/thegent/doctor.py:1274]
**Acceptance checklist:**

- [ ] Replace broad resource monitoring exception handling with explicit stats-fetch, shape-validation, and render-path failure categories.
- [ ] Preserve current suspicion-level reporting behavior for valid stats payloads.
- [ ] Add tests for healthy stats reporting, malformed stats objects, and runtime access failures.
      **Notes:** Line 1274 currently masks whether failures originate from data retrieval or downstream formatting.

### [WL-7406]

**Title:** Preserve process registry check root-cause visibility with typed failure branches
**Source:** [thegent/src/thegent/doctor.py:1468]
**Acceptance checklist:**

- [ ] Replace broad process registry exception handling with explicit registry-read, parse, and summarization failure categories.
- [ ] Preserve existing tracked-process status output for valid registry data.
- [ ] Add tests for healthy registry checks, malformed registry records, and filesystem access errors.
      **Notes:** The generic handler at line 1468 collapses distinct registry failure modes into one warning result.

### [WL-7407]

**Title:** Bound MCP tools check outer failure handling to actionable transport and parsing classes
**Source:** [thegent/src/thegent/doctor.py:1535]
**Acceptance checklist:**

- [ ] Replace outer broad MCP tools exception handling with explicit unexpected-state, response-shape, and orchestration failure branches.
- [ ] Preserve current per-transport diagnostic behavior already handled in inner branches.
- [ ] Add tests for valid MCP health success, malformed top-level flow state, and uncaught non-HTTP runtime faults.
      **Notes:** Line 1535 currently allows unrelated outer-flow errors to be surfaced as one generic MCP tools warning.

### [WL-7408]

**Title:** Distinguish DLQ escalation integration failures from enqueue success paths in execution pipeline
**Source:** [thegent/src/thegent/execution.py:942]
**Acceptance checklist:**

- [ ] Replace broad DLQ auto-escalation exception handling with explicit escalation-queue import, initialization, and enqueue failure branches.
- [ ] Preserve current non-blocking DLQ item handling semantics when escalation fails.
- [ ] Add tests for successful escalation dispatch, queue initialization failure, and enqueue-time errors.
      **Notes:** The catch-all at line 941 merges import and runtime escalation failures, reducing triage precision.

### [WL-7409]

**Title:** Preserve provider score loading diagnostics instead of returning silent empty-score defaults
**Source:** [thegent/src/thegent/execution.py:1080]
**Acceptance checklist:**

- [ ] Replace broad provider score load suppression with explicit JSON decode and file-read failure categories.
- [ ] Preserve current default score seed behavior when score file is absent.
- [ ] Add tests for valid score file loading, malformed JSON payloads, and unreadable score file conditions.
      **Notes:** Line 1079 currently swallows score-loading failures and returns `{}`, which can hide scoring regressions.
