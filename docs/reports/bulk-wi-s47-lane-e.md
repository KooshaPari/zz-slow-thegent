### [WL-7910]

**Title:** Add explicit config origin tracing in `thegent doctor` output for faster setup debugging
**Source:** [thegent/src/thegent/commands/doctor.py:73]
**Acceptance checklist:**

- [ ] Print effective config value and origin source (default, env, workspace, user file) for key runtime settings.
- [ ] Preserve concise doctor output mode when verbose flags are not enabled.
- [ ] Add tests for origin precedence display, redaction of secret-like values, and no-origin regressions in non-verbose mode.
      **Notes:** New users lose time guessing where a surprising runtime value came from.

### [WL-7911]

**Title:** Fail fast with actionable message when workspace root cannot be resolved from current cwd
**Source:** [thegent/src/thegent/workspace/discovery.py:58]
**Acceptance checklist:**

- [ ] Raise a clear error naming attempted markers and current working directory when workspace discovery fails.
- [ ] Preserve successful discovery behavior for valid repo and nested project paths.
- [ ] Add tests for marker-found success, marker-missing failure messaging, and symlinked path resolution parity.
      **Notes:** Current failures are ambiguous and look like random command breakage.

### [WL-7912]

**Title:** Add bounded wait with progress ticks for stuck background session attach operations
**Source:** [thegent/src/thegent/commands/bg.py:141]
**Acceptance checklist:**

- [ ] Add an attach timeout with periodic progress ticks that report elapsed wait and pending readiness checks.
- [ ] Preserve immediate attach behavior when session readiness completes quickly.
- [ ] Add tests for fast attach success, timeout path with non-zero exit, and deterministic tick cadence.
      **Notes:** Hanging attach calls degrade trust because users cannot tell if the command is alive.

### [WL-7913]

**Title:** Stabilize JSON output contract by sorting map keys for machine-readable CLI modes
**Source:** [thegent/src/thegent/output/json_printer.py:39]
**Acceptance checklist:**

- [ ] Emit deterministic key ordering for JSON map objects in machine-readable output mode.
- [ ] Preserve semantic output content and existing field names across all JSON-capable commands.
- [ ] Add tests for stable ordering across repeated runs, nested map ordering, and unchanged scalar serialization.
      **Notes:** Non-deterministic JSON key order creates noisy diffs in automation pipelines.

### [WL-7914]

**Title:** Improve plugin load diagnostics with per-plugin duration and first-failure short summary
**Source:** [thegent/src/thegent/plugins/loader.py:126]
**Acceptance checklist:**

- [ ] Capture and report plugin load duration per plugin when diagnostics mode is enabled.
- [ ] Surface a one-line first-failure summary while preserving full traceback in debug mode.
- [ ] Add tests for all-success load reporting, single-plugin failure reporting, and stable plugin ordering in diagnostics.
      **Notes:** Plugin startup slowness and failures are hard to isolate without timing and concise failure context.

### [WL-7915]

**Title:** Reject invalid enum values in CLI flags with nearest-match suggestions
**Source:** [thegent/src/thegent/cli/args.py:212]
**Acceptance checklist:**

- [ ] Validate enum-like CLI flags and emit nearest valid choices on mismatch.
- [ ] Preserve existing parser behavior for valid flag values and required/optional semantics.
- [ ] Add tests for exact-match acceptance, invalid-value suggestion output, and multiple-close-match ranking determinism.
      **Notes:** Mistyped flag values currently trigger generic errors that slow down command retries.

### [WL-7916]

**Title:** Add atomic write guard and backup-on-parse-fail for user config save flow
**Source:** [thegent/src/thegent/config/writer.py:84]
**Acceptance checklist:**

- [ ] Write config updates using temp-file plus atomic rename semantics to prevent partial-file corruption.
- [ ] Create a timestamped backup when an on-disk config is unreadable before overwrite attempt.
- [ ] Add tests for successful atomic write, interrupted write simulation, and unreadable-config backup creation.
      **Notes:** Manual config edits can leave partially valid files that are currently easy to clobber without recovery.

### [WL-7917]

**Title:** Surface command deprecation warnings once per invocation with migration hint links
**Source:** [thegent/src/thegent/cli/deprecations.py:52]
**Acceptance checklist:**

- [ ] Emit each deprecation warning at most once per command invocation even when multiple code paths hit it.
- [ ] Include a migration hint link or command replacement snippet in warning text.
- [ ] Add tests for single-warning emission, multiple-hit dedupe, and no-warning behavior for non-deprecated commands.
      **Notes:** Repeated warnings create noise and hide the actual migration action users need.

### [WL-7918]

**Title:** Add clear exit-code taxonomy table to `--help` for automation-friendly error handling
**Source:** [thegent/src/thegent/cli/help_formatter.py:97]
**Acceptance checklist:**

- [ ] Include a compact standardized exit-code table in top-level help output.
- [ ] Preserve existing help sections, command listings, and wrapping behavior.
- [ ] Add tests for table presence in top-level help, stable ordering of codes, and unchanged subcommand help output.
      **Notes:** CI and shell wrappers currently rely on undocumented exit-code assumptions.

### [WL-7919]

**Title:** Add lightweight self-check command for env prerequisites before running long workflows
**Source:** [thegent/src/thegent/commands/selfcheck.py:31]
**Acceptance checklist:**

- [ ] Implement a fast prerequisite check command covering required binaries, writable dirs, and critical env vars.
- [ ] Preserve non-interactive output mode suitable for preflight checks in scripts.
- [ ] Add tests for all-pass self-check, single-failure reporting, and multi-failure grouped summary ordering.
      **Notes:** Developers often discover missing prerequisites only after expensive workflow startup.
