### [WL-6720]

**Title:** Classify directory-creation failures in markdown dump path setup
**Source Path+Line:** [thegent/src/thegent/session/conversation_dumper.py:163]
**Acceptance Checklist:**

- [ ] Replace broad exception handling around dump directory creation with explicit OS/path failure branches.
- [ ] Preserve current fallback behavior while exposing actionable failure context.
- [ ] Add tests for successful directory creation and permission-denied setup paths.
      **Notes:** Current catch-all handling obscures whether dump setup failed due to permissions, path validity, or transient I/O issues.

### [WL-6721]

**Title:** Split JSON dump write errors into deterministic failure classes
**Source Path+Line:** [thegent/src/thegent/session/conversation_dumper.py:215]
**Acceptance Checklist:**

- [ ] Replace broad JSON dump exception handling with typed serialization and filesystem error paths.
- [ ] Keep caller-visible raising semantics stable while enriching diagnostics.
- [ ] Add tests for non-serializable payloads, unwritable targets, and successful writes.
      **Notes:** A generic catch-all currently hides root cause and weakens incident triage for failed dump persistence.

### [WL-6722]

**Title:** Harden markdown conversation ID parsing against malformed filenames
**Source Path+Line:** [thegent/src/thegent/session/conversation_dumper.py:342]
**Acceptance Checklist:**

- [ ] Replace broad parser exception swallowing with bounded validation and explicit malformed-name handling.
- [ ] Preserve compatibility for valid dump filenames while preventing index/split crashes.
- [ ] Add tests for valid filenames, malformed timestamp suffixes, and short-token edge cases.
      **Notes:** Filename parsing currently depends on structure assumptions that can fail silently under malformed artifacts.

### [WL-6723]

**Title:** Differentiate git invocation failures from truly empty commit windows
**Source Path+Line:** [thegent/src/thegent/summary.py:60]
**Acceptance Checklist:**

- [ ] Replace catch-all exception behavior in commit collection with explicit subprocess failure handling.
- [ ] Return structured failure context distinct from legitimate no-commit periods.
- [ ] Add tests covering non-git directories, empty histories, and failing git commands.
      **Notes:** Returning an empty commit list for all failures produces false no-change summaries.

### [WL-6724]

**Title:** Surface unreadable log file diagnostics during summary ingestion
**Source Path+Line:** [thegent/src/thegent/summary.py:93]
**Acceptance Checklist:**

- [ ] Replace silent read failure suppression with bounded diagnostics and skip accounting.
- [ ] Preserve partial ingestion semantics while reporting dropped files deterministically.
- [ ] Add tests with mixed valid and unreadable/corrupt log files.
      **Notes:** Silent failures reduce confidence in summary completeness and complicate auditability.

### [WL-6725]

**Title:** Report alias probe exceptions in shell doctor output
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:176]
**Acceptance Checklist:**

- [ ] Replace empty exception suppression around alias checks with a non-fatal diagnostic issue entry.
- [ ] Keep successful doctor execution unchanged while exposing probe reliability state.
- [ ] Add tests for probe timeout, command failure, and healthy probe cases.
      **Notes:** The current behavior can incorrectly present a healthy shell state when alias probing fails.

### [WL-6726]

**Title:** Preserve tmux fallback failure context in native session discovery
**Source Path+Line:** [thegent/src/thegent/native/discovery_native.py:59]
**Acceptance Checklist:**

- [ ] Replace blanket fallback exception handling with explicit failure metadata for discovery callers.
- [ ] Keep return-shape compatibility for consumers expecting session lists.
- [ ] Add tests for tmux absence, command errors, and successful fallback parsing.
      **Notes:** Collapsing discovery errors into empty results masks operational regressions.

### [WL-6727]

**Title:** Emit fallback diagnostics when Linux proc probing fails
**Source Path+Line:** [thegent/src/thegent/thegent_platform.py:40]
**Acceptance Checklist:**

- [ ] Replace silent `OSError` suppression with debug-level telemetry on fallback platform detection.
- [ ] Verify WSL detection behavior remains correct after proc-read failures.
- [ ] Add tests for readable `/proc/version`, unreadable proc files, and non-WSL Linux hosts.
      **Notes:** Silent fallback selection makes platform misclassification difficult to diagnose.

### [WL-6728]

**Title:** Enforce calibration payload schema before accepting stored bias map
**Source Path+Line:** [thegent/src/thegent/ux/calibration.py:42]
**Acceptance Checklist:**

- [ ] Replace broad load fallback with typed JSON decode and strict dict/float schema validation.
- [ ] Reject invalid payload types deterministically without silently resetting calibration.
- [ ] Add tests for missing files, invalid JSON, wrong types, and valid persisted calibration.
      **Notes:** Returning default calibration state on all errors hides data integrity problems.

### [WL-6729]

**Title:** Track dropped observability events on async queue saturation
**Source Path+Line:** [thegent/src/thegent/observability/async_logger.py:67]
**Acceptance Checklist:**

- [ ] Add bounded dropped-event counters when queue enqueue fails with `queue.Full`.
- [ ] Expose a lightweight read path for drop metrics to support runtime diagnostics.
- [ ] Add tests for normal enqueue flow and deterministic counter increments under saturation.
      **Notes:** Silent event loss under load undermines observability reliability.
