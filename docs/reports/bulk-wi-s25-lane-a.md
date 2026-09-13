### [WL-6770]

**Title:** Replace markdown dump directory setup catch-all with typed filesystem failures
**Source Path+Line:** [thegent/src/thegent/session/conversation_dumper.py:163]
**Acceptance Checklist:**

- [ ] Replace broad exception handling in dump directory creation with explicit path/permission/I-O branches.
- [ ] Preserve existing success behavior while surfacing actionable failure diagnostics.
- [ ] Add tests covering writable paths, permission-denied paths, and invalid target roots.
      **Notes:** Current catch-all handling masks root cause when conversation dump directory initialization fails.

### [WL-6771]

**Title:** Split JSON dump persistence errors into serialization and write failure classes
**Source Path+Line:** [thegent/src/thegent/session/conversation_dumper.py:215]
**Acceptance Checklist:**

- [ ] Replace broad exception handling in JSON dump writes with explicit serialization and filesystem failure paths.
- [ ] Preserve caller-visible failure semantics while adding deterministic error context.
- [ ] Add tests for successful writes, non-serializable payloads, and unwritable destinations.
      **Notes:** Generic exception wrapping obscures whether failures come from payload shape or disk operations.

### [WL-6772]

**Title:** Harden markdown filename parsing for malformed conversation dump artifacts
**Source Path+Line:** [thegent/src/thegent/session/conversation_dumper.py:342]
**Acceptance Checklist:**

- [ ] Replace parser catch-all behavior with bounded filename validation and explicit malformed-artifact handling.
- [ ] Preserve valid filename parsing behavior and deterministic output contracts.
- [ ] Add tests for valid dumps, malformed timestamp tokens, and short-token filename edge cases.
      **Notes:** Parsing assumptions can fail on malformed filenames and are currently hidden behind broad exception paths.

### [WL-6773]

**Title:** Distinguish git command failures from legitimate empty commit windows in summary generation
**Source Path+Line:** [thegent/src/thegent/summary.py:60]
**Acceptance Checklist:**

- [ ] Replace catch-all exception handling in commit collection with explicit subprocess failure reporting.
- [ ] Return failure context distinct from true no-commit time windows.
- [ ] Add tests for non-git directories, empty histories, and git invocation failures.
      **Notes:** Returning empty commit lists for all failures creates false no-change reports.

### [WL-6774]

**Title:** Surface unreadable file diagnostics during summary chat-log ingestion
**Source Path+Line:** [thegent/src/thegent/summary.py:93]
**Acceptance Checklist:**

- [ ] Replace silent read-failure suppression with bounded diagnostics for unreadable/corrupt files.
- [ ] Preserve partial-ingestion behavior while exposing deterministic skipped-file accounting.
- [ ] Add tests with mixed readable and unreadable log files.
      **Notes:** Silent failures hide data loss and reduce confidence in summary completeness.

### [WL-6775]

**Title:** Report alias-probe execution failures in shell doctor issue output
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:176]
**Acceptance Checklist:**

- [ ] Replace empty exception suppression around alias probing with non-fatal diagnostic issue entries.
- [ ] Keep healthy doctor execution unchanged while exposing probe reliability state.
- [ ] Add tests for probe timeout, probe command failure, and successful probe scenarios.
      **Notes:** Suppressed exceptions can incorrectly present a healthy shell state when probing fails.

### [WL-6776]

**Title:** Preserve tmux fallback discovery failure context for native session scans
**Source Path+Line:** [thegent/src/thegent/native/discovery_native.py:59]
**Acceptance Checklist:**

- [ ] Replace blanket exception collapse in fallback session discovery with explicit failure metadata.
- [ ] Preserve return-shape compatibility for existing session discovery consumers.
- [ ] Add tests for tmux unavailable, tmux command failure, and successful fallback parsing.
      **Notes:** Collapsing discovery failures into empty results masks operational regressions.

### [WL-6777]

**Title:** Emit deterministic diagnostics when Linux proc-based platform probes fail
**Source Path+Line:** [thegent/src/thegent/thegent_platform.py:40]
**Acceptance Checklist:**

- [ ] Replace silent `OSError` suppression with debug-visible fallback diagnostics.
- [ ] Verify WSL detection behavior remains correct after proc-read failures.
- [ ] Add tests for readable proc content, unreadable proc paths, and non-WSL Linux hosts.
      **Notes:** Silent probe failures make platform misclassification difficult to debug.

### [WL-6778]

**Title:** Enforce schema checks when loading persisted UX calibration payloads
**Source Path+Line:** [thegent/src/thegent/ux/calibration.py:42]
**Acceptance Checklist:**

- [ ] Replace broad calibration-load fallback with typed JSON decode and strict dict/float schema validation.
- [ ] Reject invalid payload types deterministically instead of silently resetting calibration.
- [ ] Add tests for missing files, invalid JSON, wrong payload types, and valid calibration maps.
      **Notes:** Returning defaults on all errors can hide data-integrity issues in persisted calibration state.

### [WL-6779]

**Title:** Track dropped async observability events on queue saturation
**Source Path+Line:** [thegent/src/thegent/observability/async_logger.py:67]
**Acceptance Checklist:**

- [ ] Add bounded dropped-event accounting when enqueue attempts fail due to `queue.Full`.
- [ ] Expose a lightweight read path for drop metrics to support runtime diagnostics.
- [ ] Add tests for normal enqueue flow and deterministic counter increments under saturation.
      **Notes:** Silent event loss under load weakens observability reliability and triage confidence.
