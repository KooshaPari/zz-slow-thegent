### [WL-6920]

**Title:** Replace markdown dump write catch-all with typed filesystem failure handling
**Source:** [thegent/src/thegent/session/conversation_dumper.py:163]
**Acceptance checklist:**

- [ ] Replace broad exception handling in markdown dump writes with explicit path/permission/I-O failure branches.
- [ ] Preserve current successful dump behavior while exposing actionable write-failure diagnostics.
- [ ] Add tests covering successful writes, unwritable destinations, and invalid dump roots.
      **Notes:** Catch-all write failure handling obscures whether markdown dump persistence failed due to serialization or filesystem state.

### [WL-6921]

**Title:** Classify JSON dump persistence failures into serialization and write error paths
**Source:** [thegent/src/thegent/session/conversation_dumper.py:215]
**Acceptance checklist:**

- [ ] Replace catch-all JSON dump write handling with explicit serialization versus filesystem failure branches.
- [ ] Preserve caller-visible failure contract while adding deterministic root-cause context.
- [ ] Add tests for successful dump, non-serializable payloads, and permission-denied write targets.
      **Notes:** Generic exception wrapping in JSON dump persistence weakens triage when dumps fail in production.

### [WL-6922]

**Title:** Harden markdown model-header extraction against malformed split assumptions
**Source:** [thegent/src/thegent/session/conversation_dumper.py:332]
**Acceptance checklist:**

- [ ] Replace brittle `split(":**")[1]` parsing with a defensive model-header parser.
- [ ] Preserve current behavior for valid dump headers while handling malformed or missing model lines explicitly.
- [ ] Add tests for valid headers, malformed delimiters, and dumps without `**Model:**` entries.
      **Notes:** Current parser assumptions can trigger index errors that are later hidden by broad exception handling.

### [WL-6923]

**Title:** Distinguish git-log execution failures from true empty commit windows in summaries
**Source:** [thegent/src/thegent/summary.py:60]
**Acceptance checklist:**

- [ ] Replace catch-all exception handling in commit collection with explicit subprocess failure classification.
- [ ] Keep no-commit windows distinct from command-execution failures in return semantics.
- [ ] Add tests for non-repository paths, empty histories, and failing git invocations.
      **Notes:** Returning empty commit lists for all failures produces false no-change summary output.

### [WL-6924]

**Title:** Surface malformed log-entry parse failures with bounded diagnostics
**Source:** [thegent/src/thegent/summary.py:79]
**Acceptance checklist:**

- [ ] Replace `_parse_log_entry` silent parse suppression with explicit malformed-record diagnostics.
- [ ] Preserve line-by-line ingestion flow while exposing deterministic skipped-record counts.
- [ ] Add tests for mixed valid and malformed JSON log lines.
      **Notes:** Silent parse failures reduce trust in summary completeness and make data-loss triage harder.

### [WL-6925]

**Title:** Report unreadable chat-log file failures instead of silently dropping them
**Source:** [thegent/src/thegent/summary.py:93]
**Acceptance checklist:**

- [ ] Replace silent `_read_log_file` exception swallowing with bounded unreadable-file diagnostics.
- [ ] Preserve partial ingestion behavior while surfacing skipped-file accounting.
- [ ] Add tests for readable, missing, and permission-denied log file scenarios.
      **Notes:** Hidden file-read failures can undercount activity without any operator-visible signal.

### [WL-6926]

**Title:** Replace shell doctor alias-probe exception suppression with explicit degraded-state output
**Source:** [thegent/src/thegent/shell_cli.py:176]
**Acceptance checklist:**

- [ ] Replace broad alias-probe exception suppression with timeout and command-failure classification.
- [ ] Preserve healthy doctor output while emitting non-fatal diagnostics when probing fails.
- [ ] Add tests for successful probe, timeout path, and subprocess failure path.
      **Notes:** Silent alias-probe failure can incorrectly report healthy shell diagnostics.

### [WL-6927]

**Title:** Preserve tmux fallback discovery failures as explicit diagnostics
**Source:** [thegent/src/thegent/native/discovery_native.py:59]
**Acceptance checklist:**

- [ ] Replace blanket discovery fallback exception swallowing with structured failure metadata.
- [ ] Distinguish true zero-session state from command/runtime failure state.
- [ ] Add tests for successful parsing, missing tmux binary, and tmux command errors.
      **Notes:** Returning empty results on all fallback failures masks discovery regressions.

### [WL-6928]

**Title:** Emit deterministic diagnostics when Linux proc-version probe fails
**Source:** [thegent/src/thegent/thegent_platform.py:40]
**Acceptance checklist:**

- [ ] Replace silent `OSError` suppression in platform probing with explicit debug diagnostics.
- [ ] Preserve correct WSL-vs-Linux detection behavior after proc-read failures.
- [ ] Add tests for readable proc content, unreadable proc path, and non-WSL Linux hosts.
      **Notes:** Silent probe fallback makes platform misclassification difficult to investigate.

### [WL-6929]

**Title:** Track dropped async observability events during queue saturation
**Source:** [thegent/src/thegent/observability/async_logger.py:67]
**Acceptance checklist:**

- [ ] Replace silent `queue.Full` drop behavior with bounded dropped-event accounting.
- [ ] Expose a lightweight mechanism to read drop counters for runtime diagnostics.
- [ ] Add tests for normal enqueue behavior and deterministic counter increments under saturation.
      **Notes:** Silent event loss under load undermines observability accuracy and incident triage confidence.
