### [WL-7170]

**Title:** Preserve Node version probe failure classes in dependency diagnostics
**Source:** [thegent/src/thegent/doctor_dependencies.py:27]
**Acceptance checklist:**

- [ ] Replace broad Node version probe exception handling with typed subprocess-launch, timeout, and decode failure branches.
- [ ] Preserve current dependency status semantics when Node is missing versus present-but-unreadable.
- [ ] Add tests for successful version probe, command execution failure, and malformed output decode paths.
      **Notes:** Line 27 currently collapses all Node version probe failures into one warning path, reducing triage precision.

### [WL-7171]

**Title:** Remove no-op Claude dependency try/except and make availability checks deterministic
**Source:** [thegent/src/thegent/doctor_dependencies.py:42]
**Acceptance checklist:**

- [ ] Eliminate redundant broad exception handling that returns the same status/message in both branches.
- [ ] Preserve current behavior for discovered Claude binaries while clarifying control flow.
- [ ] Add tests that assert deterministic output when Claude is present and when it is missing.
      **Notes:** Line 42 is part of a no-op exception branch that obscures intent without changing runtime outcomes.

### [WL-7172]

**Title:** Classify `mise doctor` execution faults without masking actionable failure causes
**Source:** [thegent/src/thegent/doctor_dependencies.py:157]
**Acceptance checklist:**

- [ ] Replace catch-all `mise doctor` exception handling with explicit timeout, subprocess, and decode-failure paths.
- [ ] Preserve warn-level contract while adding bounded diagnostics for each failure class.
- [ ] Add tests for successful execution, non-zero exit handling, and runtime invocation exceptions.
      **Notes:** Line 157 currently funnels all invocation failures into one message, limiting operator remediation speed.

### [WL-7173]

**Title:** Differentiate `brew bundle check` runtime failures from dependency drift results
**Source:** [thegent/src/thegent/doctor_dependencies.py:181]
**Acceptance checklist:**

- [ ] Replace broad exception handling around `brew bundle check` with typed command-launch and output-parse error branches.
- [ ] Preserve current warn semantics for missing packages versus command execution failures.
- [ ] Add tests for clean bundle checks, drift reports, and subprocess invocation exceptions.
      **Notes:** Line 181 currently merges execution faults and actionable bundle drift into the same warning shape.

### [WL-7174]

**Title:** Surface control-plane provider import failures with bounded fallback diagnostics
**Source:** [thegent/src/thegent/config_provider.py:88]
**Acceptance checklist:**

- [ ] Replace silent `ImportError` fallback with explicit diagnostic capture while preserving EnvConfigProvider fallback behavior.
- [ ] Preserve non-fatal startup behavior when control-plane provider modules are unavailable.
- [ ] Add tests for successful control-plane provider loading and import-fallback diagnostics.
      **Notes:** Line 88 currently suppresses control-plane import failure context, making degraded mode entry opaque.

### [WL-7175]

**Title:** Classify policy federation write failures per peer without collapsing filesystem and permission errors
**Source:** [thegent/src/thegent/discovery/federation.py:50]
**Acceptance checklist:**

- [ ] Replace broad peer policy sync exception handling with typed directory-creation, file-write, and permission failure branches.
- [ ] Preserve best-effort federation across peers when one destination fails.
- [ ] Add tests for successful peer sync, unwritable destination paths, and missing parent-directory behavior.
      **Notes:** Line 50 currently collapses distinct write-time failures into one generic error message.

### [WL-7176]

**Title:** Preserve identity federation failure specificity for append and serialization paths
**Source:** [thegent/src/thegent/discovery/federation.py:76]
**Acceptance checklist:**

- [ ] Replace broad identity append exception handling with explicit JSON serialization versus filesystem append failure branches.
- [ ] Preserve current per-peer continuation behavior when one write fails.
- [ ] Add tests for successful identity federation, malformed payload serialization, and append permission failures.
      **Notes:** Line 76 currently masks whether federation failures come from payload encoding or storage I/O.

### [WL-7177]

**Title:** Differentiate shell reload command failures from shell availability issues
**Source:** [thegent/src/thegent/shell_cli.py:138]
**Acceptance checklist:**

- [ ] Replace broad shell reload exception handling with typed executable-not-found and subprocess runtime failure branches.
- [ ] Preserve existing user guidance while surfacing concrete failure causes.
- [ ] Add tests for successful reload invocation, missing `zsh`, and subprocess execution errors.
      **Notes:** Line 138 currently reports a generic reload error that obscures root-cause class.

### [WL-7178]

**Title:** Preserve benchmark iteration failure taxonomy instead of generic per-iteration errors
**Source:** [thegent/src/thegent/shell_cli.py:220]
**Acceptance checklist:**

- [ ] Replace broad benchmark exception handling with explicit timeout, parse, and subprocess-invocation failure classes.
- [ ] Preserve partial-results behavior for completed iterations while reporting skipped iteration counts by cause.
- [ ] Add tests for successful timing parse, malformed timing output, and timeout/error iteration paths.
      **Notes:** Line 220 currently collapses all iteration failures into a single error print, reducing benchmark reliability diagnostics.

### [WL-7179]

**Title:** Classify shell metrics parsing failures without conflating read and value-conversion errors
**Source:** [thegent/src/thegent/shell_cli.py:299]
**Acceptance checklist:**

- [ ] Replace broad metrics-read exception handling with typed file-access and integer-conversion failure branches.
- [ ] Preserve command behavior for missing/empty metrics files while surfacing malformed metric line counts.
- [ ] Add tests for valid metrics files, malformed counter values, and unreadable metrics paths.
      **Notes:** Line 299 currently maps read-time and parse-time failures to one opaque error path.
