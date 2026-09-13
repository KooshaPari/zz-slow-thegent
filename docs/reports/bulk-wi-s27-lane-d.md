### [WL-6900]

**Title:** Expose alias-probe subprocess failures in shell doctor output.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:178]
**Acceptance Checklist:**

- [x] Replace broad alias-probe exception swallowing with typed failure handling.
- [x] Record a non-fatal diagnostic entry when probe execution fails.
- [x] Add tests for successful alias probe and failure-report branches.
      **Notes:** Silent alias-probe failure can hide shell misconfiguration during environment checks.
      **Evidence:** `src/thegent/shell_cli.py` (`shell_doctor`, `_classify_subprocess_probe_error`), `tests/test_wl6900_wl6909_lane_e.py::test_wl6900_shell_doctor_alias_probe_success_branch`, `tests/test_wl6900_wl6909_lane_e.py::test_wl6900_shell_doctor_records_probe_timeout`

### [WL-6901]

**Title:** Preserve zsh-version probe failure cause in platform diagnostics.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:480]
**Acceptance Checklist:**

- [x] Differentiate timeout, missing executable, and subprocess errors for zsh version lookup.
- [x] Keep command execution non-fatal while surfacing cause-specific status.
- [x] Add tests for successful and degraded zsh-version detection paths.
      **Notes:** Mapping all failures to `Not available` removes actionable debugging context.
      **Evidence:** `src/thegent/shell_cli.py` (`shell_platform`), `tests/test_wl6900_wl6909_lane_e.py::test_wl6901_shell_platform_reports_success_version`, `tests/test_wl6900_wl6909_lane_e.py::test_wl6901_shell_platform_reports_degraded_causes`

### [WL-6902]

**Title:** Separate git-log command failures from true empty commit windows.
**Source Path+Line:** [thegent/src/thegent/summary.py:62]
**Acceptance Checklist:**

- [x] Replace blanket exception-to-empty behavior with structured error signaling.
- [x] Preserve empty-list return only for genuinely empty commit ranges.
- [x] Add tests for non-repo path, command failure, and real zero-commit windows.
      **Notes:** Returning `[]` for both failure and empty history can under-report activity.
      **Evidence:** `src/thegent/summary.py` (`GitCommitsResult`, `get_git_commits`), `tests/test_wl6900_wl6909_lane_e.py::test_wl6902_get_git_commits_non_repo_reports_not_repo`, `tests/test_wl6900_wl6909_lane_e.py::test_wl6902_get_git_commits_command_failure_reports_error`, `tests/test_wl6900_wl6909_lane_e.py::test_wl6902_get_git_commits_empty_window_keeps_empty_status`

### [WL-6903]

**Title:** Track malformed JSONL parse failures in log entry parsing.
**Source Path+Line:** [thegent/src/thegent/summary.py:80]
**Acceptance Checklist:**

- [x] Capture parse-failure counts instead of silently dropping malformed rows.
- [x] Keep ingestion resilient for valid records in mixed-quality files.
- [x] Add tests for valid entries, malformed JSON, and out-of-window timestamps.
      **Notes:** Silent parse drops hide data-quality regressions in summary generation.
      **Evidence:** `src/thegent/summary.py` (`LogParseStats`, `_parse_log_entry`, `_read_log_file`), `tests/test_wl6900_wl6909_lane_e.py::test_wl6903_read_log_file_tracks_malformed_json_and_out_of_window`

### [WL-6904]

**Title:** Surface chat-log file read failures as explicit degraded-state signals.
**Source Path+Line:** [thegent/src/thegent/summary.py:93]
**Acceptance Checklist:**

- [x] Replace catch-all read suppression with explicit file/IO error reporting.
- [x] Distinguish unreadable log files from legitimately empty log sets.
- [x] Add tests for readable files, missing files, and permission-denied cases.
      **Notes:** Suppressing read errors can make incomplete audits look complete.
      **Evidence:** `src/thegent/summary.py` (`_read_log_file`, `get_chat_logs`), `tests/test_wl6900_wl6909_lane_e.py::test_wl6904_read_log_file_missing_file_reports_explicit_status`, `tests/test_wl6900_wl6909_lane_e.py::test_wl6904_read_log_file_permission_denied_reports_status`

### [WL-6905]

**Title:** Preserve initial MCP health-check transport errors before auto-start.
**Source Path+Line:** [thegent/src/thegent/doctor_setup_checks.py:106]
**Acceptance Checklist:**

- [x] Replace silent preflight suppression with typed connectivity diagnostics.
- [x] Retain auto-start flow while recording why the initial check failed.
- [x] Add tests for healthy endpoint, timeout, and connection-refused preflight states.
      **Notes:** Hidden preflight failures reduce observability during doctor-driven startup.
      **Evidence:** `src/thegent/doctor_setup_checks.py` (`ensure_mcp_running`, `_classify_httpx_error`), `tests/test_wl6900_wl6909_lane_e.py::test_wl6905_ensure_mcp_running_healthy_preflight_short_circuits`, `tests/test_wl6900_wl6909_lane_e.py::test_wl6905_ensure_mcp_running_records_timeout_preflight`

### [WL-6906]

**Title:** Add bounded diagnostics for retry-loop MCP health probe failures.
**Source Path+Line:** [thegent/src/thegent/doctor_setup_checks.py:122]
**Acceptance Checklist:**

- [x] Record failure reason classes inside the startup wait loop without spamming output.
- [x] Preserve retry behavior and timeout semantics.
- [x] Add tests covering transient failures followed by success and persistent failure.
      **Notes:** Repeated silent retries obscure whether startup is progressing or stuck.
      **Evidence:** `src/thegent/doctor_setup_checks.py` (`ensure_mcp_running` retry diagnostics), `tests/test_wl6900_wl6909_lane_e.py::test_wl6906_ensure_mcp_running_retry_diagnostics_transient_then_success`, `tests/test_wl6900_wl6909_lane_e.py::test_wl6906_ensure_mcp_running_retry_diagnostics_persistent_failure`

### [WL-6907]

**Title:** Differentiate CLIProxy transport errors from service-unavailable status.
**Source Path+Line:** [thegent/src/thegent/doctor_setup_checks.py:181]
**Acceptance Checklist:**

- [x] Replace generic exception handling with categorized warning messages.
- [x] Preserve warn-level outcome while exposing actionable remediation detail.
- [x] Add tests for timeout, connection refusal, and non-200 responses.
      **Notes:** A single generic warning message slows down proxy incident triage.
      **Evidence:** `src/thegent/doctor_setup_checks.py` (`check_connectivity` CLIProxy branch), `tests/test_wl6900_wl6909_lane_e.py::test_wl6907_check_connectivity_cliproxy_categorizes_failures`

### [WL-6908]

**Title:** Avoid deleting lockfiles after unclassified parsing/read failures.
**Source Path+Line:** [thegent/src/thegent/shared_mcp_manager.py:65]
**Acceptance Checklist:**

- [x] Replace broad exception handling with explicit JSON and IO failure branches.
- [x] Prevent destructive lockfile cleanup on uncertain error conditions.
- [x] Add tests for stale lockfile cleanup, malformed JSON, and transient read errors.
      **Notes:** Blind lockfile deletion can break active shared MCP sessions.
      **Evidence:** `src/thegent/shared_mcp_manager.py` (`ensure_shared_mcp_server` JSON/IO branches), `tests/test_wl6900_wl6909_lane_e.py::test_wl6908_shared_mcp_cleans_only_stale_lockfile`, `tests/test_wl6900_wl6909_lane_e.py::test_wl6908_shared_mcp_malformed_json_does_not_delete_lockfile`, `tests/test_wl6900_wl6909_lane_e.py::test_wl6908_shared_mcp_read_error_does_not_delete_lockfile`

### [WL-6909]

**Title:** Distinguish interface-enumeration failure from true no-interface state.
**Source Path+Line:** [thegent/src/thegent/resources/network.py:160]
**Acceptance Checklist:**

- [x] Return machine-readable failure context when interface listing throws.
- [x] Preserve empty-interface behavior only for legitimate zero-interface scenarios.
- [x] Add tests for psutil exceptions and healthy interface enumeration.
      **Notes:** Shared empty-list behavior currently masks telemetry acquisition failures.
      **Evidence:** `src/thegent/resources/network.py` (`list_interfaces(include_diagnostics=True)`), `tests/resources/test_network.py::TestListInterfaces::test_include_diagnostics_distinguishes_empty_from_error`, `tests/resources/test_network.py::TestListInterfaces::test_lists_all_interfaces`, `tests/test_wl6900_wl6909_lane_e.py::test_wl6909_network_interface_diagnostics_distinguish_error_from_empty`

### Validation Command

`.venv/bin/python -m pytest -q tests/test_wl6900_wl6909_lane_e.py tests/resources/test_network.py -k 'wl6900 or wl6901 or wl6902 or wl6903 or wl6904 or wl6905 or wl6906 or wl6907 or wl6908 or wl6909 or list_interfaces' -p no:tach`
