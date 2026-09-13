### [WL-7370]

**Title:** Classify shell benchmark iteration failures without suppressing root-cause diagnostics
**Source:** [thegent/src/thegent/shell_cli.py:263]
**Acceptance checklist:**

- [ ] Replace broad benchmark-loop exception handling with explicit subprocess timeout and parse failure branches.
- [ ] Preserve benchmark continuation semantics across per-iteration failures.
- [ ] Add tests for successful iteration, timeout failure, and malformed stderr timing output.
      **Notes:** The handler at line 262 currently merges distinct benchmark iteration failure causes into one generic error path.

### [WL-7371]

**Title:** Preserve typed metrics parsing failures during shell metrics aggregation
**Source:** [thegent/src/thegent/shell_cli.py:342]
**Acceptance checklist:**

- [ ] Replace broad metrics file-read exception handling with explicit file I/O and integer conversion failure branches.
- [ ] Preserve current metrics aggregation behavior for valid records.
- [ ] Add tests for valid metrics parsing, malformed value conversion, and unreadable metrics file paths.
      **Notes:** Line 341 currently collapses parsing and I/O failures, reducing diagnostics for metrics ingestion regressions.

### [WL-7372]

**Title:** Separate job registry read faults from per-process status resolution errors
**Source:** [thegent/src/thegent/shell_cli.py:389]
**Acceptance checklist:**

- [ ] Replace broad registry parsing exception handling with explicit registry file-read and PID-state evaluation failure categories.
- [ ] Preserve successful job table rendering for valid registry entries.
- [ ] Add tests for healthy registry parsing, malformed PID entries, and registry read failures.
      **Notes:** The catch-all at line 388 obscures whether failures occur during registry ingestion or process-status probing.

### [WL-7373]

**Title:** Surface markdown conversation dump write failures with bounded error classes
**Source:** [thegent/src/thegent/session/conversation_dumper.py:163]
**Acceptance checklist:**

- [ ] Replace broad markdown dump write exception handling with explicit serialization and filesystem write failure branches.
- [ ] Preserve successful markdown dump output contract for valid records.
- [ ] Add tests for successful markdown dump writes, serialization failures, and write permission errors.
      **Notes:** Line 163 currently handles all markdown dump failures uniformly, limiting operational diagnosis.

### [WL-7374]

**Title:** Distinguish JSON dump encoding failures from filesystem output faults
**Source:** [thegent/src/thegent/session/conversation_dumper.py:215]
**Acceptance checklist:**

- [ ] Replace broad JSON dump exception handling with explicit JSON encoding and path write failure categories.
- [ ] Preserve existing filename and output location behavior when writes succeed.
- [ ] Add tests for valid JSON dump writes, non-serializable metadata, and invalid output directory states.
      **Notes:** The branch at line 215 currently merges encoding and persistence failures into one recovery path.

### [WL-7375]

**Title:** Classify conversation dump read-path failures before returning empty records
**Source:** [thegent/src/thegent/session/conversation_dumper.py:342]
**Acceptance checklist:**

- [ ] Replace broad dump read exception handling with explicit JSON decode, markdown parse, and timestamp extraction failure branches.
- [ ] Preserve current successful dump reconstruction behavior for valid markdown and JSON dumps.
- [ ] Add tests for valid dump reads, malformed JSON payloads, and malformed markdown metadata.
      **Notes:** Line 342 currently suppresses read-stage failure taxonomy by funneling divergent faults through one handler.

### [WL-7376]

**Title:** Preserve watcher start diagnostics by separating observer bootstrap failure categories
**Source:** [thegent/src/thegent/native/watcher_daemon.py:289]
**Acceptance checklist:**

- [ ] Replace broad observer start exception handling with explicit thread-start and observer-runtime initialization branches.
- [ ] Preserve daemon running-state guarantees when startup succeeds.
- [ ] Add tests for successful startup, observer start failure, and cleanup-thread bootstrap failure.
      **Notes:** The broad branch at line 289 currently hides whether startup failure is observer-related or cleanup-thread related.

### [WL-7377]

**Title:** Differentiate watcher stop transport errors from join-time shutdown anomalies
**Source:** [thegent/src/thegent/native/watcher_daemon.py:321]
**Acceptance checklist:**

- [ ] Replace broad join exception handling with explicit observer-stop and observer-join failure categories.
- [ ] Preserve idempotent stop semantics when shutdown steps complete.
- [ ] Add tests for clean stop, observer stop exceptions, and join timeout/error handling.
      **Notes:** Line 321 currently collapses stop-stage and join-stage failures into generic shutdown warnings.

### [WL-7378]

**Title:** Bound native SHM bootstrap faults with explicit initialization diagnostics
**Source:** [thegent/src/thegent/native/state_shm.py:212]
**Acceptance checklist:**

- [ ] Replace broad native SHM init exception handling with explicit directory-creation, interface-construction, and permission failure branches.
- [ ] Preserve deterministic fallback activation semantics after native initialization failure.
- [ ] Add tests for successful native initialization, missing native module behavior, and unwritable SHM path handling.
      **Notes:** The warning path at line 212 currently flattens heterogeneous initialization failures into one message.

### [WL-7379]

**Title:** Classify native discovery command invocation failures before fallback dispatch
**Source:** [thegent/src/thegent/native/discovery_native.py:143]
**Acceptance checklist:**

- [ ] Replace broad native command exception handling with explicit timeout, process-launch, and transport error branches.
- [ ] Preserve current fallback discovery behavior when native command execution fails.
- [ ] Add tests for successful native command execution, timeout fallback, and non-timeout invocation failure handling.
      **Notes:** Line 143 currently reduces distinct native discovery invocation failures to an undifferentiated fallback path.
