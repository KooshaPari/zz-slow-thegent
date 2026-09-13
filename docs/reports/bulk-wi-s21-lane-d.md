### [WL-6600]

**Title:** Make `shell reload` fail on unsuccessful `source ~/.zshrc` execution instead of always printing success.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:136]
**Acceptance Checklist:**

- [x] Capture `subprocess.run` result and gate success messaging on return code.
- [x] Print stderr-derived diagnostics when sourcing fails.
- [x] Add a CLI test that simulates non-zero exit and asserts failure output.
      **Evidence:** `shell_reload` now raises `typer.Exit(1)` on non-zero source result; validated by `tests/test_unit_shell_cli.py::test_shell_reload_exits_nonzero_on_source_failure`.
      **Notes:** Current `check=False` path reports success even when `.zshrc` sourcing fails.

### [WL-6601]

**Title:** Replace swallowed alias-detection failures in `shell doctor` with actionable diagnostics.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:176]
**Acceptance Checklist:**

- [x] Catch `TimeoutExpired` and subprocess errors explicitly in alias inspection.
- [x] Record a doctor issue entry when the alias probe itself fails.
- [x] Add coverage for timeout/error branches so failures are visible in doctor output.
      **Evidence:** Alias probe now classifies timeout/subprocess/os errors into issues/warnings; validated by `test_shell_doctor_records_alias_probe_timeout_issue` and `test_shell_doctor_records_alias_probe_oserror_issue`.
      **Notes:** Bare exception suppression can hide broken diagnostics and produce false "healthy" reports.

### [WL-6602]

**Title:** Harden git commit collection error reporting in summary generation.
**Source Path+Line:** [thegent/src/thegent/summary.py:60]
**Acceptance Checklist:**

- [x] Replace broad exception swallowing in `get_git_commits` with typed error handling.
- [x] Include command/context diagnostics in a structured warning path.
- [x] Add tests for git command failures and non-repo paths.
      **Evidence:** `get_git_commits` returns structured status/error and logs command/cwd diagnostics on failures; validated by `tests/test_unit_summary.py`.
      **Notes:** Silent `[]` fallback obscures whether there were no commits or command execution failed.

### [WL-6603]

**Title:** Expose malformed telemetry lines instead of silently suppressing all parse exceptions.
**Source Path+Line:** [thegent/src/thegent/contracts/telemetry.py:29]
**Acceptance Checklist:**

- [x] Replace `contextlib.suppress(Exception)` with explicit JSON decode handling.
- [x] Track malformed-line count or emit debug diagnostics during telemetry reads.
- [x] Add tests for mixed valid/invalid JSONL lines.
      **Evidence:** `_parse_event_line` now increments `malformed_line_count` and emits debug logs for malformed lines; validated by `test_get_fallback_kpis_corrupted_lines`.
      **Notes:** Full exception suppression makes telemetry corruption invisible during drift analysis.

### [WL-6604]

**Title:** Add structured parse-failure accounting in `ContractTelemetry.get_stats` event ingestion.
**Source Path+Line:** [thegent/src/thegent/contracts/telemetry.py:133]
**Acceptance Checklist:**

- [x] Separate parse failures from provider-filter skips while reading events.
- [x] Return parse-error counters alongside existing aggregate metrics.
- [x] Add regression tests for malformed events within otherwise valid telemetry streams.
      **Evidence:** `get_stats` now returns `parse_errors` and `provider_skips`; validated by `test_get_stats_corrupted_lines` and `test_get_stats_tracks_parse_errors_and_provider_skips`.
      **Notes:** Current `except ... continue` drops bad rows silently and can skew confidence/fallback metrics.

### [WL-6605]

**Title:** Make native parser extraction fallback observable when Rust extension invocation fails.
**Source Path+Line:** [thegent/src/thegent/contracts/parser.py:224]
**Acceptance Checklist:**

- [x] Catch and log native parser invocation failures with exception context.
- [x] Preserve Python parser fallback behavior without silent failure.
- [x] Add tests asserting fallback is triggered and diagnostics are emitted on native errors.
      **Evidence:** `extract_tags` now logs debug diagnostics on native parser exceptions and falls back to Python parser; validated by `test_extract_tags_falls_back_when_native_parser_raises`.
      **Notes:** The current silent pass masks native parser regressions and complicates troubleshooting.

### [WL-6606]

**Title:** Instrument native `<think>` stripping fallback path in output parser.
**Source Path+Line:** [thegent/src/thegent/output_parser.py:277]
**Acceptance Checklist:**

- [x] Replace silent native-strip failure handling with debug-level diagnostics.
- [x] Keep regex fallback result parity for normal text and nested think blocks.
- [x] Add tests for native failure simulation plus fallback correctness.
      **Evidence:** `_strip_think_blocks` now logs native failures before regex fallback; parity asserted against `_THINK_RE.sub(...).strip()` in `test_native_think_strip_failure_logs_and_uses_regex_fallback`.
      **Notes:** Observability gap prevents operators from detecting degraded parsing performance.

### [WL-6607]

**Title:** Remove silent scoring-path degradation when model quality/speed lookup imports fail.
**Source Path+Line:** [thegent/src/thegent/planning/selector.py:81]
**Acceptance Checklist:**

- [x] Replace broad import/lookup exception suppression with explicit diagnostics.
- [x] Define deterministic fallback scoring behavior when lookup modules are unavailable.
- [x] Add tests for successful lookup and forced-import-failure scenarios.
      **Evidence:** `_calculate_score` now logs explicit warnings for import/lookup failures and keeps metadata-based deterministic scoring; validated by two new selector fallback tests in `tests/test_unit_planning_learning.py`.
      **Notes:** Today the selector quietly reverts to metadata defaults with no signal that enrichment failed.

### [WL-6608]

**Title:** Validate calibration file schema instead of defaulting silently on load errors.
**Source Path+Line:** [thegent/src/thegent/ux/calibration.py:42]
**Acceptance Checklist:**

- [x] Distinguish JSON parse errors from wrong-shape payloads in `_load_calibration`.
- [x] Emit diagnostics before returning an empty bias map.
- [x] Add tests for corrupt JSON, non-dict payloads, and valid calibration maps.
      **Evidence:** `_load_calibration` now warns for JSON decode, I/O, and schema-shape errors; validated by `tests/test_unit_ux_calibration.py`.
      **Notes:** Returning `{}` on all errors can silently reset learned calibration behavior.

### [WL-6609]

**Title:** Prevent partial-state contamination when board artifact JSON loading fails.
**Source Path+Line:** [thegent/src/thegent/planning/board_artifact_loader.py:65]
**Acceptance Checklist:**

- [x] Ensure `load_all` rolls back or isolates partial `items/slices/metadata` mutations when `_load_json` raises.
- [x] Surface file-specific error details while preserving deterministic loader result schema.
- [x] Add tests for malformed JSON and mixed-artifact load sequences.
      **Evidence:** JSON/CSV parsing now happens via isolated parse helpers before assignment and errors include file + exception type; validated by two new malformed-JSON load tests in `tests/test_wl158_board_artifact_integration.py`.
      **Notes:** Failed JSON load currently records an error but may leave in-memory loader state inconsistent for subsequent steps.
