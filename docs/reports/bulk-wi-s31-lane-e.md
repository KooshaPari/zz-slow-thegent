### [WL-7110]

**Title:** Differentiate git log command failures from true no-commit windows in summary generation
**Source:** [thegent/src/thegent/summary.py:60]
**Acceptance checklist:**

- [ ] Replace blanket exception handling in `get_git_commits` with typed subprocess failure classification.
- [ ] Preserve empty-list behavior for legitimate no-commit ranges.
- [ ] Add tests for successful git history retrieval, non-git directories, and command execution failure.
      **Notes:** Line 60 currently collapses all command and environment faults into `[]`, obscuring summary data integrity issues.

### [WL-7111]

**Title:** Surface malformed log-line parse diagnostics in summary entry extraction
**Source:** [thegent/src/thegent/summary.py:79]
**Acceptance checklist:**

- [ ] Replace broad parse suppression in `_parse_log_entry` with typed JSON and timestamp parse handling.
- [ ] Preserve `None` return semantics for non-user/assistant records and out-of-window events.
- [ ] Add tests for valid entries, malformed JSON lines, and invalid timestamp formats.
      **Notes:** Line 79 suppresses all parsing faults and makes malformed log records indistinguishable from normal filtering.

### [WL-7112]

**Title:** Make per-file chat log read failures observable during summary aggregation
**Source:** [thegent/src/thegent/summary.py:93]
**Acceptance checklist:**

- [ ] Replace silent catch-all in `_read_log_file` with typed file I/O and decode error handling.
- [ ] Preserve successful entry collection for readable files in mixed-quality directories.
- [ ] Add tests for readable logs, unreadable files, and corrupted file contents.
      **Notes:** Line 93 currently hides file-level failures and can silently drop portions of chat history.

### [WL-7113]

**Title:** Classify run timestamp coercion failures during period filtering
**Source:** [thegent/src/thegent/summary.py:145]
**Acceptance checklist:**

- [ ] Replace broad suppression in `summary_impl` run filtering with typed datetime parse handling.
- [ ] Preserve current inclusion rules for valid run timestamps.
- [ ] Add tests for valid run timestamps, malformed `started_at_utc` values, and missing timestamp fields.
      **Notes:** Line 145 currently treats parse failures as invisible skips, reducing trust in run coverage.

### [WL-7114]

**Title:** Distinguish tmux fallback session probe failures from truly empty fallback state
**Source:** [thegent/src/thegent/native/discovery_native.py:59]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression in `_fallback_sessions` with typed subprocess failure handling.
- [ ] Preserve empty return behavior for legitimate no-session output.
- [ ] Add tests for successful tmux parsing, probe execution failure, and malformed row shape.
      **Notes:** Line 59 currently maps all fallback probe failures to `[]`, masking discovery regressions.

### [WL-7115]

**Title:** Preserve dependency-missing diagnostics for psutil-backed fallback process listing
**Source:** [thegent/src/thegent/native/discovery_native.py:77]
**Acceptance checklist:**

- [ ] Replace silent import failure handling in `_fallback_processes` with explicit missing-dependency signaling.
- [ ] Preserve no-process behavior when no matches are found under healthy dependency state.
- [ ] Add tests for present `psutil`, absent `psutil`, and invalid pattern handling.
      **Notes:** Line 77 currently suppresses import failures and makes runtime capability drift hard to detect.

### [WL-7116]

**Title:** Surface per-process inspection failures without silently skewing fallback process results
**Source:** [thegent/src/thegent/native/discovery_native.py:111]
**Acceptance checklist:**

- [ ] Replace broad per-item suppression in `_fallback_processes` with bounded error classification.
- [ ] Preserve continued scanning for unaffected processes.
- [ ] Add tests for healthy process iteration, invalid process info payloads, and intermittent psutil access errors.
      **Notes:** Line 111 currently drops failing process rows silently, which can bias diagnostics under load.

### [WL-7117]

**Title:** Differentiate native discovery execution faults from intentional native bypass
**Source:** [thegent/src/thegent/native/discovery_native.py:143]
**Acceptance checklist:**

- [ ] Replace catch-all suppression in `DiscoveryClient._run` with typed timeout, spawn, and runtime error branches.
- [ ] Preserve existing `None` contract while attaching bounded failure metadata.
- [ ] Add tests for successful native invocation, timeout, and subprocess launch failures.
      **Notes:** Line 143 currently hides command execution failures and collapses them into opaque fallback behavior.

### [WL-7118]

**Title:** Preserve alias-probe failure signal in shell doctor output
**Source:** [thegent/src/thegent/shell_cli.py:177]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression in `shell_doctor` alias check with typed timeout and subprocess handling.
- [ ] Preserve current detection behavior when alias probe succeeds.
- [ ] Add tests for successful alias probe, timeout path, and subprocess failure path.
      **Notes:** Line 176 currently swallows probe faults, potentially producing false healthy doctor results.

### [WL-7119]

**Title:** Expose platform probe degradation when zsh version detection fails
**Source:** [thegent/src/thegent/shell_cli.py:479]
**Acceptance checklist:**

- [ ] Replace broad suppression in `shell_platform` zsh detection with typed subprocess error handling.
- [ ] Preserve table output contract while making probe failure reason observable.
- [ ] Add tests for successful zsh version read and command execution failure.
      **Notes:** Line 479 currently converts all probe failures into generic "Not available", reducing diagnosability.
