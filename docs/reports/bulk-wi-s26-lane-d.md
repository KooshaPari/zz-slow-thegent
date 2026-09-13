### [WL-6850]

**Title:** Replace silent alias-probe exception handling with observable doctor diagnostics.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:179]
**Acceptance Checklist:**

- [x] Replace broad alias-probe exception swallowing with typed failure handling.
- [x] Emit a non-fatal doctor warning entry when alias probing fails.
- [x] Add tests for successful probe and degraded probe execution branches.
      **Evidence:**
- `src/thegent/shell_cli.py` classifies probe exceptions and reports non-fatal `issues`/`warnings` with bounded reason text.
- Tests: `tests/test_wl6900_wl6909_lane_e.py::test_wl6900_shell_doctor_alias_probe_success_branch`, `tests/test_wl6900_wl6909_lane_e.py::test_wl6900_shell_doctor_records_probe_timeout`, `tests/test_unit_shell_cli.py::test_shell_doctor_records_alias_probe_timeout_issue`.
  **Notes:** Silent alias-probe failure can create misleading healthy shell diagnostics.

### [WL-6851]

**Title:** Preserve zsh-version probe failure reason in environment table output.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:480]
**Acceptance Checklist:**

- [x] Differentiate timeout, missing binary, and subprocess errors when checking zsh version.
- [x] Keep doctor execution non-fatal while exposing cause-specific status text.
- [x] Add tests for success and degraded zsh-detection branches.
      **Evidence:**
- `src/thegent/shell_cli.py` reports `Not installed`, `Probe timed out`, and `Probe failed (<type>)` separately in platform table output.
- Tests: `tests/test_wl6900_wl6909_lane_e.py::test_wl6901_shell_platform_reports_success_version`, `tests/test_wl6900_wl6909_lane_e.py::test_wl6901_shell_platform_reports_degraded_causes`.
  **Notes:** Collapsing all exceptions to `Not available` removes actionable triage context.

### [WL-6852]

**Title:** Prevent Nix status false-positives after generic invocation exceptions.
**Source Path+Line:** [thegent/src/thegent/doctor_shell_nix.py:149]
**Acceptance Checklist:**

- [x] Replace broad fallback exception handling with explicit failure classification.
- [x] Avoid reporting `ok` status without validated command output.
- [x] Add tests covering timeout, execution error, and successful version checks.
      **Evidence:**
- `src/thegent/doctor_shell_nix.py` marks timeout as `warn`, non-executable/invocation errors as `fail`, and only marks `ok` when return code is `0` with non-empty stdout.
- Tests: `tests/test_unit_doctor_shell_nix_wl6712.py::test_check_nix_timeout_is_warn`, `tests/test_unit_doctor_shell_nix_wl6712.py::test_check_nix_nonzero_exit_is_fail`, `tests/test_unit_doctor_shell_nix_wl6712.py::test_check_nix_success_reports_ok`.
  **Notes:** Current generic exception path can misclassify unhealthy Nix installs as healthy.

### [WL-6853]

**Title:** Include bounded MCP probe error details in doctor warning output.
**Source Path+Line:** [thegent/src/thegent/doctor.py:1502]
**Acceptance Checklist:**

- [x] Capture and classify health-check probe failures with bounded error context.
- [x] Preserve warning semantics while adding actionable remediation detail.
- [x] Add tests for timeout and connection-refused MCP probe outcomes.
      **Evidence:**
- `src/thegent/doctor.py` classifies timeout/connect/http failures, stores bounded `details`, and retains `warn` status with `thegent mcp up` fix hint.
- Tests: `tests/test_unit_doctor_mcp_tools_wl6713.py::test_check_mcp_tools_timeout_has_details`, `tests/test_unit_doctor_mcp_tools_wl6713.py::test_check_mcp_tools_connection_refused_has_details`.
  **Notes:** A generic not-reachable message slows incident triage for MCP tooling.

### [WL-6854]

**Title:** Distinguish git-log execution failures from true zero-commit windows.
**Source Path+Line:** [thegent/src/thegent/summary.py:62]
**Acceptance Checklist:**

- [x] Replace blanket exception-to-empty behavior with structured failure signaling.
- [x] Preserve empty-list return only for actual no-commit ranges.
- [x] Add tests for command failure, non-repository paths, and real empty ranges.
      **Evidence:**
- `src/thegent/summary.py` returns `GitCommitsResult(status=not_repo|error|empty|ok)` plus machine-readable `error` payload.
- Tests: `tests/test_unit_summary.py::test_get_git_commits_non_repo_returns_diagnostic_status`, `tests/test_unit_summary.py::test_get_git_commits_git_command_failure_logs_context`, `tests/test_wl6900_wl6909_lane_e.py::test_wl6902_get_git_commits_empty_window_keeps_empty_status`.
  **Notes:** Returning `[]` for both outcomes can under-report development activity.

### [WL-6855]

**Title:** Track malformed JSON entry counts during summary log parsing.
**Source Path+Line:** [thegent/src/thegent/summary.py:80]
**Acceptance Checklist:**

- [x] Record parse-failure counts while preserving line-by-line ingestion.
- [x] Optionally capture bounded sample context for malformed entries.
- [x] Add tests for mixed valid and malformed JSONL records.
      **Evidence:**
- `src/thegent/summary.py` tracks `parse_counts` (`malformed_json` and related counters) and bounded `sampled_errors`.
- Tests: `tests/test_wl6900_wl6909_lane_e.py::test_wl6903_read_log_file_tracks_malformed_json_and_out_of_window`, `tests/test_unit_summary_wl6714_wl6715.py::test_read_log_file_tracks_invalid_timestamp_and_json_sample`.
  **Notes:** Silent parse failures hide data-quality regressions in summary outputs.

### [WL-6856]

**Title:** Emit diagnostics when `sendfile` branch degrades to copy fallback.
**Source Path+Line:** [thegent/src/thegent/infra/fast_file_ops.py:66]
**Acceptance Checklist:**

- [x] Capture fallback activation reason when optimized sendfile copy fails.
- [x] Preserve functional copy behavior and metadata semantics in fallback mode.
- [x] Add tests that force sendfile failure and assert diagnostic emission.
      **Evidence:**
- `src/thegent/infra/fast_file_ops.py` records per-reason fallback counters and warning logs while preserving functional `shutil` copy fallback.
- Test: `tests/test_unit_fast_file_ops_wl6716.py::test_sendfile_failure_falls_back_and_emits_telemetry`.
  **Notes:** Silent fallback obscures performance regressions for large file operations.

### [WL-6857]

**Title:** Surface provider-model discovery errors instead of suppressing exceptions.
**Source Path+Line:** [thegent/src/thegent/provider_model_manager.py:508]
**Acceptance Checklist:**

- [x] Replace broad exception swallowing with warning-level diagnostics.
- [x] Differentiate discovery failure from legitimately empty provider model lists.
- [x] Add tests for transport failure and malformed model payload handling.
      **Evidence:**
- `src/thegent/provider_model_manager.py` returns structured discovery status (`ok`/`error`/`invalid_payload`) and warning-level logs for timeout/http/payload faults.
- Tests: `tests/test_unit_provider_model_manager_discovery.py::test_discover_models_timeout_returns_status_metadata`, `tests/test_unit_provider_model_manager_discovery.py::test_discover_models_invalid_payload_schema`.
  **Notes:** Hidden discovery errors can be misread as valid empty provider catalogs.

### [WL-6858]

**Title:** Preserve subagent enumeration failure signals in session view resolution.
**Source Path+Line:** [thegent/src/thegent/ux/session_tui.py:105]
**Acceptance Checklist:**

- [x] Replace catch-all empty-list fallback with structured degraded-state signaling.
- [x] Keep UI resilience while surfacing explicit subagent collection warnings.
- [x] Add tests for process-tree enumeration exceptions and normal success.
      **Evidence:**
- `src/thegent/ux/session_tui.py` stores explicit subagent diagnostics (`component`, `error_type`, `error_message`) and marks session view `degraded` without crashing UI.
- Tests: `tests/test_unit_session_tui.py::test_subagent_probe_failure_sets_degraded_diagnostics`, `tests/test_unit_session_tui.py::test_subagent_probe_success_returns_entries_without_degraded_state`.
  **Notes:** Silent fallback to empty subagent lists can misrepresent runtime state.

### [WL-6859]

**Title:** Differentiate network interface query failures from genuine empty inventories.
**Source Path+Line:** [thegent/src/thegent/resources/network.py:160]
**Acceptance Checklist:**

- [x] Return machine-readable error context when interface enumeration fails.
- [x] Preserve existing logging while exposing failure-vs-empty distinction.
- [x] Add tests for psutil exceptions and true no-interface scenarios.
      **Evidence:**
- `src/thegent/resources/network.py` supports `include_diagnostics=True` payload with distinct `status` values (`empty` vs `error` vs `unavailable`) and error metadata.
- Tests: `tests/resources/test_network.py::TestListInterfaces::test_include_diagnostics_distinguishes_empty_from_error`, `tests/resources/test_network.py::TestListInterfaces::test_empty_when_no_interfaces_found`.
  **Notes:** Shared empty-list behavior masks telemetry failures during diagnostics.
