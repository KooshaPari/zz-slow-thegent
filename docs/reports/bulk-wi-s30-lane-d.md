### [WL-7050]

**Title:** Differentiate zmx session-list command failures from true empty-session state
**Source:** [thegent/src/thegent/session/zmx_backend.py:185]
**Acceptance checklist:**

- [ ] Replace empty-list fallback with explicit command-failure classification for session discovery.
- [ ] Preserve current behavior for legitimate zero-session responses.
- [ ] Add tests for successful session listing, command failure, and timeout handling.
      **Notes:** Returning `[]` on command errors can mask backend or environment regressions.

### [WL-7051]

**Title:** Preserve zmx JSON parse failure context before plain-text fallback activation
**Source:** [thegent/src/thegent/session/zmx_backend.py:299]
**Acceptance checklist:**

- [ ] Record parse-failure diagnostics before returning plain-text fallback results.
- [ ] Keep existing plain-text fallback behavior for non-JSON-capable zmx versions.
- [ ] Add tests for valid JSON output, malformed JSON output, and fallback parsing success.
      **Notes:** Silent parse fallback makes it difficult to distinguish capability gaps from data corruption.

### [WL-7052]

**Title:** Classify zmx process-query fallback empties by transport versus content failures
**Source:** [thegent/src/thegent/session/zmx_backend.py:311]
**Acceptance checklist:**

- [ ] Split catch-all empty fallback into typed command execution and output-shape failure branches.
- [ ] Preserve empty output for true no-process conditions.
- [ ] Add tests for valid process output, command execution failure, and malformed response payloads.
      **Notes:** Collapsing all failures to empty process lists weakens operator confidence during incident triage.

### [WL-7053]

**Title:** Replace shell alias probe suppression with explicit non-fatal diagnostics
**Source:** [thegent/src/thegent/shell_cli.py:176]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression with classified timeout and subprocess error handling.
- [ ] Preserve healthy doctor UX while surfacing degraded alias-probe state.
- [ ] Add tests for successful alias probe, probe timeout, and subprocess failure.
      **Notes:** Silent alias-probe failures can produce misleadingly healthy shell diagnostics.

### [WL-7054]

**Title:** Emit bounded debug signal when proc-version read fallback is activated
**Source:** [thegent/src/thegent/thegent_platform.py:41]
**Acceptance checklist:**

- [ ] Replace silent `OSError` swallow with low-noise diagnostics indicating fallback path use.
- [ ] Preserve Linux/WSL platform classification semantics under unreadable proc state.
- [ ] Add tests for readable proc-version, unreadable proc-version, and non-WSL environments.
      **Notes:** Unreported fallback activation obscures root causes for platform misclassification reports.

### [WL-7055]

**Title:** Distinguish fast file listing read failures from legitimate empty directories
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:95]
**Acceptance checklist:**

- [ ] Replace broad empty-list fallback with explicit path-access and parse failure branches.
- [ ] Preserve current results for actual empty-directory scans.
- [ ] Add tests for readable directories, permission-denied roots, and malformed intermediate state.
      **Notes:** Returning empty results for filesystem failures hides I/O regressions in scan-heavy paths.

### [WL-7056]

**Title:** Preserve fallback session discovery errors as structured degraded metadata
**Source:** [thegent/src/thegent/native/discovery_native.py:60]
**Acceptance checklist:**

- [ ] Replace silent `[]` fallback for session discovery with error-class tagging.
- [ ] Keep fallback session behavior unchanged when no sessions truly exist.
- [ ] Add tests for successful fallback discovery, discovery command failure, and parse failure.
      **Notes:** Empty fallback returns can conceal tmux/tooling breakage during runtime discovery.

### [WL-7057]

**Title:** Differentiate process fallback probe failure from no-match discovery outcomes
**Source:** [thegent/src/thegent/native/discovery_native.py:78]
**Acceptance checklist:**

- [ ] Introduce typed failure handling for process fallback probe execution and decode steps.
- [ ] Preserve empty output semantics for legitimate no-match process scans.
- [ ] Add tests for successful process listing, command failure, and malformed output decoding.
      **Notes:** Treating all probe failures as no-match states can suppress real discovery pipeline faults.

### [WL-7058]

**Title:** Add explicit compositor degradation diagnostics when panel rendering exception boundaries fire
**Source:** [thegent/src/thegent/ui/compositor_manager.py:447]
**Acceptance checklist:**

- [ ] Replace generic exception boundary behavior with bounded panel-level failure diagnostics.
- [ ] Preserve compositor stability and user-visible fallback rendering semantics.
- [ ] Add tests for healthy renders, single-panel failure isolation, and repeated failure suppression.
      **Notes:** Silent compositor error boundaries reduce observability into degraded UI rendering paths.

### [WL-7059]

**Title:** Classify runtime bridge worker startup exceptions before fallback runtime selection
**Source:** [thegent/src/thegent/infra/multi_runtime_bridge.py:127]
**Acceptance checklist:**

- [ ] Replace broad startup exception handling with typed worker-launch and handshake failure categories.
- [ ] Preserve existing runtime fallback behavior for recoverable startup failures.
- [ ] Add tests for primary runtime success, recoverable fallback activation, and unrecoverable startup errors.
      **Notes:** Untyped startup failures make runtime fallback decisions difficult to audit under load.
