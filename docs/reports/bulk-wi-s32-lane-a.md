### [WL-7120]

**Title:** Replace markdown dump write catch-all with typed filesystem failure handling
**Source:** [thegent/src/thegent/session/conversation_dumper.py:163]
**Acceptance checklist:**

- [ ] Replace broad exception handling in markdown dump writes with explicit path/permission/I-O failure branches.
- [ ] Preserve current successful dump behavior while exposing actionable write-failure diagnostics.
- [ ] Add tests covering successful writes, unwritable destinations, and invalid dump roots.
      **Notes:** Line 163 currently collapses all write-time failures into one path, obscuring root-cause classes during dump persistence failures.

### [WL-7121]

**Title:** Classify JSON dump persistence failures into serialization and write error paths
**Source:** [thegent/src/thegent/session/conversation_dumper.py:215]
**Acceptance checklist:**

- [ ] Replace catch-all JSON dump write handling with explicit serialization versus filesystem failure branches.
- [ ] Preserve caller-visible failure contract while adding deterministic root-cause context.
- [ ] Add tests for successful dump, non-serializable payloads, and permission-denied write targets.
      **Notes:** Line 215 currently treats serialization and disk failures as one class, reducing operator-level triage precision.

### [WL-7122]

**Title:** Harden markdown dump parsing by separating malformed content from file-read failures
**Source:** [thegent/src/thegent/session/conversation_dumper.py:342]
**Acceptance checklist:**

- [ ] Replace broad dump-read exception handling with typed malformed-content and filesystem failure branches.
- [ ] Preserve successful parse behavior while returning deterministic diagnostics for malformed dump bodies.
- [ ] Add tests for valid dumps, malformed model headers, and unreadable dump files.
      **Notes:** Line 342 currently swallows parse and I/O error classes into one fallback path that returns `None`.

### [WL-7123]

**Title:** Distinguish git-log execution failures from legitimate empty commit windows
**Source:** [thegent/src/thegent/summary.py:60]
**Acceptance checklist:**

- [ ] Replace broad exception swallowing in commit collection with explicit subprocess-failure classification.
- [ ] Preserve no-commit behavior for true empty ranges while surfacing command-execution failures separately.
- [ ] Add tests for empty history windows, non-repository paths, and failing git invocations.
      **Notes:** Line 60 currently returns empty commits for all exceptions, which can produce false no-change summaries.

### [WL-7124]

**Title:** Surface malformed log-entry parse failures with bounded diagnostics
**Source:** [thegent/src/thegent/summary.py:79]
**Acceptance checklist:**

- [ ] Replace silent log-entry parse suppression with explicit malformed-record accounting.
- [ ] Preserve line-by-line ingestion flow while exposing deterministic skipped-record metadata.
- [ ] Add tests for mixed valid/malformed JSON lines and invalid timestamp payloads.
      **Notes:** Line 79 currently suppresses parse-time faults, making ingestion completeness hard to verify.

### [WL-7125]

**Title:** Report unreadable chat-log files instead of silently dropping them
**Source:** [thegent/src/thegent/summary.py:93]
**Acceptance checklist:**

- [ ] Replace silent `_read_log_file` exception swallowing with bounded unreadable-file diagnostics.
- [ ] Preserve partial ingestion behavior while surfacing skipped-file counts and file identity.
- [ ] Add tests for readable, missing, and permission-denied log file scenarios.
      **Notes:** Line 93 currently hides file-read failures, which can undercount activity without any operator-visible signal.

### [WL-7126]

**Title:** Preserve shell doctor alias-probe failures as non-fatal diagnostics
**Source:** [thegent/src/thegent/shell_cli.py:176]
**Acceptance checklist:**

- [ ] Replace empty exception suppression around alias probing with explicit timeout and subprocess-failure reporting.
- [ ] Preserve doctor command continuity while surfacing probe reliability state.
- [ ] Add tests for successful probe, timeout path, and subprocess execution failure.
      **Notes:** Line 176 currently suppresses all probe exceptions, which can mask invalid shell-health conclusions.

### [WL-7127]

**Title:** Differentiate zsh-version probe failures from unavailable-shell scenarios in platform reporting
**Source:** [thegent/src/thegent/shell_cli.py:479]
**Acceptance checklist:**

- [ ] Replace blanket version-probe exception handling with typed executable-not-found and command-failure branches.
- [ ] Preserve platform table rendering while emitting deterministic failure context for zsh detection.
- [ ] Add tests for successful version retrieval, missing zsh binary, and probe-time exceptions.
      **Notes:** Line 479 currently merges all probe exceptions into "Not available", reducing observability for platform diagnostics.

### [WL-7128]

**Title:** Classify checker-agent execution failures without collapsing transport and parse errors
**Source:** [thegent/src/thegent/agents/checker.py:120]
**Acceptance checklist:**

- [ ] Replace broad checker exception handling with typed runner-execution, response-shape, and JSON-parse failure branches.
- [ ] Preserve current kill-on-failure semantics while attaching deterministic failure reasons.
- [ ] Add tests for runner failure, malformed checker output, and successful checker decisions.
      **Notes:** Line 120 currently funnels all checker failures into one generic exception reason, reducing debugging fidelity.

### [WL-7129]

**Title:** Separate watcher SHM import/config failures from runtime initialization errors
**Source:** [thegent/src/thegent/native/watcher_daemon.py:100]
**Acceptance checklist:**

- [ ] Replace broad fallback handling in `_try_get_breaker` with explicit import, settings, and initialization failure branches.
- [ ] Preserve current non-fatal fallback behavior while exposing bounded degraded-state diagnostics.
- [ ] Add tests for healthy SHM initialization, missing SHM dependency, and invalid SHM configuration paths.
      **Notes:** Line 100 currently collapses distinct dependency and runtime initialization faults into one debug message.
