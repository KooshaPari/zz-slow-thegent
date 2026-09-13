### [WL-6670]

**Title:** Classify JSON conversation dump write failures into actionable error categories
**Source Path+Line:** [thegent/src/thegent/session/conversation_dumper.py:215]
**Acceptance Checklist:**

- [ ] Replace broad exception handling in `dump_conversation_json` with explicit handling for permission, path, and serialization/write failures.
- [ ] Preserve `OSError` raising semantics while attaching structured context for caller diagnostics.
- [ ] Add tests for successful JSON dump, unwritable destination, and non-serializable metadata payloads.
      **Notes:** Generic exception wrapping currently obscures the underlying failure mode during dump persistence.

### [WL-6671]

**Title:** Harden markdown dump model-header parsing to avoid malformed split crashes
**Source Path+Line:** [thegent/src/thegent/session/conversation_dumper.py:332]
**Acceptance Checklist:**

- [ ] Replace brittle `line.split(":**")[1]` parsing with a defensive parser that tolerates missing or malformed `**Model:**` headers.
- [ ] Define deterministic fallback behavior when model metadata is absent in markdown dumps.
- [ ] Add tests for well-formed headers, malformed headers, and dumps without model lines.
      **Notes:** The current split logic can throw index errors that are later hidden by outer broad exception handling.

### [WL-6672]

**Title:** Differentiate git command failures from genuine empty commit windows
**Source Path+Line:** [thegent/src/thegent/summary.py:60]
**Acceptance Checklist:**

- [ ] Replace catch-all exception swallowing in `get_git_commits` with explicit subprocess failure handling.
- [ ] Surface command failure context (exit code/stderr) separately from legitimate no-commit results.
- [ ] Add tests for non-git paths, empty histories, and failing git invocations.
      **Notes:** Returning `[]` for all failures collapses operational errors into false no-change summaries.

### [WL-6673]

**Title:** Preserve per-file ingestion diagnostics when chat log reads fail
**Source Path+Line:** [thegent/src/thegent/summary.py:93]
**Acceptance Checklist:**

- [ ] Replace silent exception swallowing in `_read_log_file` with bounded diagnostics that identify unreadable/corrupt files.
- [ ] Continue partial ingestion while exposing skipped-file counts in a stable return contract.
- [ ] Add tests for mixed valid and unreadable `.jsonl` files.
      **Notes:** Silent failures reduce audit-log completeness without any operator-visible signal.

### [WL-6674]

**Title:** Report alias-probe execution errors in `shell doctor` instead of suppressing them
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:176]
**Acceptance Checklist:**

- [ ] Replace empty `except` behavior around alias probing with a non-fatal issue entry that includes probe failure reason.
- [ ] Keep doctor command success path intact while surfacing probe reliability status.
- [ ] Add tests for timeout, command execution failure, and successful probe scenarios.
      **Notes:** Current suppression can report a healthy shell state even when the alias check never ran correctly.

### [WL-6675]

**Title:** Distinguish tmux session discovery failures from true zero-session states
**Source Path+Line:** [thegent/src/thegent/native/discovery_native.py:59]
**Acceptance Checklist:**

- [ ] Replace blanket `return []` on `_fallback_sessions` exceptions with structured failure metadata.
- [ ] Preserve existing return compatibility while exposing whether output is empty-by-state or empty-by-error.
- [ ] Add tests for tmux missing, tmux command failure, and successful session parsing.
      **Notes:** Collapsing errors into empty output hides discovery regressions and weakens operator trust in scan results.

### [WL-6676]

**Title:** Add explicit fallback telemetry when `/proc/version` probing fails on Linux
**Source Path+Line:** [thegent/src/thegent/thegent_platform.py:41]
**Acceptance Checklist:**

- [ ] Replace silent `OSError` suppression in `detect_platform` with debug diagnostics that record fallback path selection.
- [ ] Ensure WSL detection still correctly checks environment variables after proc-read failure.
- [ ] Add tests for readable proc content, proc-read failure, and non-WSL Linux environments.
      **Notes:** Silent probing failures make platform misclassification difficult to root-cause in mixed Linux/WSL environments.

### [WL-6677]

**Title:** Enforce schema validation when loading confidence calibration state
**Source Path+Line:** [thegent/src/thegent/ux/calibration.py:42]
**Acceptance Checklist:**

- [ ] Replace broad `_load_calibration` fallback with typed JSON decode and dict/float schema checks.
- [ ] Reject or sanitize non-dict payloads and non-numeric bias values deterministically.
- [ ] Add tests for missing file, invalid JSON, wrong payload type, and valid calibration maps.
      **Notes:** Returning `{}` on any load failure silently resets learned calibration behavior.

### [WL-6678]

**Title:** Track and expose dropped observability events when async queue is saturated
**Source Path+Line:** [thegent/src/thegent/observability/async_logger.py:68]
**Acceptance Checklist:**

- [ ] Replace silent drop behavior in `log()` with bounded counters/metrics for queue-full event loss.
- [ ] Provide a lightweight API to retrieve dropped-event counts for health diagnostics.
- [ ] Add tests validating enqueue behavior under saturation and counter increments on drops.
      **Notes:** Silent event loss prevents accurate interpretation of observability coverage during load spikes.

### [WL-6679]

**Title:** Replace randomized DAG audit issue IDs with deterministic stable identifiers
**Source Path+Line:** [thegent/src/thegent/sync/audit_framework.py:322]
**Acceptance Checklist:**

- [ ] Replace `hash(e)` usage with a deterministic ID strategy (for example stable digest of normalized error text).
- [ ] Guarantee issue IDs remain stable across interpreter restarts and process boundaries.
- [ ] Add tests verifying identical DAG validation errors produce identical IDs across runs.
      **Notes:** Python hash randomization currently makes issue IDs unstable and breaks deduplication/audit continuity.
