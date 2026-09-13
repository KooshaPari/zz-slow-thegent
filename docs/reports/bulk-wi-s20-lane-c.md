### [WL-6540]

**Title:** Replace `sync reset` stub path with real local-state rollback execution
**Source:** [thegent/src/thegent/commands/sync.py:741]
**Acceptance checklist:**

- [ ] Implement destructive reset flow behind explicit confirmation and non-interactive override flags.
- [ ] Remove auto-incorporated fragments and reconcile hook/config artifacts instead of returning `"stub": true` metadata.
- [ ] Add tests covering dry-run safety, successful rollback, and partial cleanup failure reporting.
      **Notes:**
- Current implementation always reports success without mutating local state.

### [WL-6541]

**Title:** Implement native `diff_stat` bridge in `GitNative` instead of zeroed placeholder metrics
**Source:** [thegent/src/thegent/native/git_native.py:56]
**Acceptance checklist:**

- [ ] Add `diff_stat` support in the `thegent-git` native extension and expose it through `GitNative.diff_stat()`.
- [ ] Return real file/insert/delete counts for tracked and staged changes with deterministic typing.
- [ ] Add integration tests that compare native output against known fixture repositories.
      **Notes:**
- The current fallback silently returns zeroes and can hide meaningful repository churn.

### [WL-6542]

**Title:** Add Windows home-directory provisioning in `_create_windows_user` instead of no-op branch
**Source:** [thegent/src/thegent/infra/os_user_adapter.py:96]
**Acceptance checklist:**

- [ ] Implement the `home_dir` path assignment flow for Windows users via supported PowerShell/WMI APIs.
- [ ] Validate permissions/ownership on created profile directories and surface actionable errors.
- [ ] Add platform-gated tests for user creation with and without explicit home directory input.
      **Notes:**
- The `home_dir` branch currently executes `pass`, so caller intent is ignored.

### [WL-6543]

**Title:** Surface `RLIMIT_NPROC` probe failures with structured diagnostics in `get_process_limit`
**Source:** [thegent/src/thegent/infra/resource_limits.py:71]
**Acceptance checklist:**

- [ ] Replace silent exception swallowing with debug-level diagnostics that include the failing limit primitive.
- [ ] Differentiate unsupported-limit environments from transient probe failures in return metadata.
- [ ] Add tests validating fallback behavior and emitted diagnostics across mocked error modes.
      **Notes:**
- Silent fallback to defaults obscures misconfigured host environments.

### [WL-6544]

**Title:** Handle SHM heartbeat metric write failures explicitly in worker loop
**Source:** [thegent/src/thegent/infra/worker_node.py:63]
**Acceptance checklist:**

- [ ] Replace broad `except` suppression with bounded retry + structured warning fields (runtime, pid, failure type).
- [ ] Ensure heartbeat emission continues while preserving failure counters for observability.
- [ ] Add tests for psutil/SHM failure paths to confirm non-crashing behavior with visible diagnostics.
      **Notes:**
- Current swallow-on-error behavior hides telemetry regressions during runtime degradation.

### [WL-6545]

**Title:** Remove silent alias-check exception path in `shell doctor` and report probe failures
**Source:** [thegent/src/thegent/shell_cli.py:177]
**Acceptance checklist:**

- [ ] Capture and display alias probe failures as non-fatal doctor findings instead of dropping exceptions.
- [ ] Preserve command timeout behavior while emitting reasoned remediation guidance.
- [ ] Add unit tests for subprocess timeout and execution-failure branches.
      **Notes:**
- The empty `except` currently makes shell diagnostics look healthy when the probe itself fails.

### [WL-6546]

**Title:** Replace fragile prompt regex heuristics in tmux readiness detection with robust idle-state checks
**Source:** [thegent/src/thegent/infra/shell_injection.py:66]
**Acceptance checklist:**

- [ ] Replace single-line regex matching with prompt-state detection that accounts for multiline output and shell variants.
- [ ] Add configurable prompt signatures per runtime instead of hard-coded literals.
- [ ] Add tests covering false-positive and false-negative readiness cases.
      **Notes:**
- Current patterns are narrow and can misclassify busy sessions as ready.

### [WL-6547]

**Title:** Preserve fallback session discovery errors instead of returning empty results silently
**Source:** [thegent/src/thegent/native/discovery_native.py:60]
**Acceptance checklist:**

- [ ] Capture subprocess failure details (exit code, stderr, timeout) and surface them in diagnostic payloads.
- [ ] Distinguish “no sessions found” from “discovery command failed” in caller-visible responses.
- [ ] Add tests for tmux missing, tmux failure, and successful discovery scenarios.
      **Notes:**
- Returning `[]` on all exceptions collapses operational failures into false “clean” states.

### [WL-6548]

**Title:** Replace hash-randomized SID mapping with stable deterministic UID derivation
**Source:** [thegent/src/thegent/infra/wsl_interop.py:119]
**Acceptance checklist:**

- [ ] Replace Python `hash()` usage with a stable algorithm (for example SHA-256 truncation) to guarantee cross-process consistency.
- [ ] Define and enforce collision-handling semantics for SID-to-UID assignments.
- [ ] Add reproducibility tests verifying identical SID mappings across interpreter restarts.
      **Notes:**
- Python hash randomization makes current mappings nondeterministic between runs.

### [WL-6549]

**Title:** Implement pattern-correct ignore matching for `FastFileOps.copy_tree`
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:93]
**Acceptance checklist:**

- [ ] Replace substring-based ignore checks with glob-style matching semantics compatible with `shutil.ignore_patterns` behavior.
- [ ] Deduplicate ignore hits and ensure directory-level patterns are handled correctly.
- [ ] Add tests for exact-name, wildcard, and nested-path ignore cases.
      **Notes:**
- Substring filtering can over-ignore unrelated files and under-ignore expected patterns.
