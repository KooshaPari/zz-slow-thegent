### [WL-6800]

**Title:** Make alias-probe failures visible in `shell doctor` output.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:177]
**Acceptance Checklist:**

- [x] Replace blanket alias-probe exception swallowing with targeted timeout/launch handling.
- [x] Emit a doctor warning or issue entry when probing fails.
- [x] Add tests for successful probe and failure visibility paths.
      **Notes:** Silent probe failure can produce a false healthy shell diagnosis.
      **Evidence:** `shell_doctor` now classifies probe exceptions and surfaces `Alias probe failed` as both issue and warning (`src/thegent/shell_cli.py`).
      **Evidence:** `.venv/bin/python -m pytest -q -p no:tach tests/test_unit_shell_cli.py::test_shell_doctor_records_alias_probe_timeout_issue tests/test_unit_shell_cli.py::test_shell_doctor_records_alias_probe_oserror_issue tests/test_wl6900_wl6909_lane_e.py::test_wl6900_shell_doctor_alias_probe_success_branch` -> `3 passed`.

### [WL-6801]

**Title:** Report actionable zsh-version detection degradation states.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:479]
**Acceptance Checklist:**

- [x] Distinguish missing binary, timeout, and execution failure when checking zsh version.
- [x] Preserve non-fatal doctor flow while surfacing failure cause.
- [x] Add tests for success and each degraded status path.
      **Notes:** Collapsing all failures to `Not available` removes triage detail.
      **Evidence:** `shell_platform` reports `Not installed`, `Probe timed out`, and `Probe failed (SubprocessError)` in separate branches (`src/thegent/shell_cli.py`).
      **Evidence:** `.venv/bin/python -m pytest -q -p no:tach tests/test_wl6900_wl6909_lane_e.py::test_wl6901_shell_platform_reports_success_version 'tests/test_wl6900_wl6909_lane_e.py::test_wl6901_shell_platform_reports_degraded_causes[side_effect0-Probe timed out]' 'tests/test_wl6900_wl6909_lane_e.py::test_wl6901_shell_platform_reports_degraded_causes[side_effect1-Not installed]' 'tests/test_wl6900_wl6909_lane_e.py::test_wl6901_shell_platform_reports_degraded_causes[side_effect2-Probe failed (SubprocessError)]'` -> `4 passed`.

### [WL-6802]

**Title:** Prevent optimistic Nix health on failed version invocations.
**Source Path+Line:** [thegent/src/thegent/doctor_shell_nix.py:148]
**Acceptance Checklist:**

- [x] Replace broad fallback handling with typed exception branches.
- [x] Avoid `ok` status on generic invocation failure without verified output.
- [x] Add tests for timeout, execution failure, and non-zero outcomes.
      **Notes:** Current fallback can misclassify broken Nix setups as healthy.
      **Evidence:** `check_nix` now uses explicit timeout/permission/subprocess branches and only returns `ok` on verified version stdout (`src/thegent/doctor_shell_nix.py`).
      **Evidence:** `.venv/bin/python -m pytest -q -p no:tach tests/test_unit_doctor_shell_nix_wl6712.py` -> `3 passed`.

### [WL-6803]

**Title:** Include MCP health-check failure cause in warning details.
**Source Path+Line:** [thegent/src/thegent/doctor.py:1501]
**Acceptance Checklist:**

- [x] Capture bounded error category/message when `/health` probe fails.
- [x] Preserve warning semantics while adding remediation context.
- [x] Add tests for timeout and connection-refused scenarios.
      **Notes:** Generic `not reachable` warnings are insufficient for rapid diagnosis.
      **Evidence:** `_check_mcp_tools` now sets warning details for timeout/connect/http/json failures while keeping non-fatal semantics (`src/thegent/doctor.py`).
      **Evidence:** `.venv/bin/python -m pytest -q -p no:tach tests/test_unit_doctor_mcp_tools_wl6713.py` -> `3 passed`.

### [WL-6804]

**Title:** Separate git-log execution failure from true no-commit windows.
**Source Path+Line:** [thegent/src/thegent/summary.py:61]
**Acceptance Checklist:**

- [x] Replace blanket exception-to-empty fallback with structured failure metadata.
- [x] Capture bounded stderr/exit code context for failed git invocations.
- [x] Update callers/tests to distinguish query failure from no-commit results.
      **Notes:** Returning `[]` for both paths can under-report activity in summaries.
      **Evidence:** `get_git_commits` returns `GitCommitsResult(status,error)` with separated `not_repo`, `error`, and `empty` states plus bounded stderr/returncode (`src/thegent/summary.py`).
      **Evidence:** `.venv/bin/python -m pytest -q -p no:tach tests/test_unit_summary.py tests/test_unit_summary_wl6714_wl6715.py::test_get_git_commits_reports_error_metadata tests/test_wl6900_wl6909_lane_e.py::test_wl6902_get_git_commits_empty_window_keeps_empty_status` -> `5 passed`.

### [WL-6805]

**Title:** Track malformed JSONL records during summary ingestion.
**Source Path+Line:** [thegent/src/thegent/summary.py:79]
**Acceptance Checklist:**

- [x] Record parse-failure counts while continuing line-by-line ingestion.
- [x] Optionally retain bounded sampled context for bad lines.
- [x] Add tests for mixed valid/invalid JSONL and malformed timestamps.
      **Notes:** Silent parse skips hide data-quality degradation.
      **Evidence:** `LogParseStats` and `_read_log_file(..., include_diagnostics=True)` now track parse counters and sampled malformed lines while continuing ingestion (`src/thegent/summary.py`).
      **Evidence:** `.venv/bin/python -m pytest -q -p no:tach tests/test_unit_summary_wl6714_wl6715.py::test_read_log_file_tracks_invalid_timestamp_and_json_sample tests/test_wl6900_wl6909_lane_e.py::test_wl6903_read_log_file_tracks_malformed_json_and_out_of_window` -> `2 passed`.

### [WL-6806]

**Title:** Emit diagnostics when `sendfile` path degrades to copy fallback.
**Source Path+Line:** [thegent/src/thegent/infra/fast_file_ops.py:66]
**Acceptance Checklist:**

- [x] Capture fallback reason when `sendfile` branch fails.
- [x] Preserve correctness and metadata behavior across fallback.
- [x] Add tests forcing `sendfile` failure and asserting diagnostic emission.
      **Notes:** Silent fallback obscures large-file performance regressions.
      **Evidence:** fallback path now records categorized reason counters and warning logs via `_record_sendfile_fallback` (`src/thegent/infra/fast_file_ops.py`).
      **Evidence:** `.venv/bin/python -m pytest -q -p no:tach tests/test_unit_fast_file_ops_wl6716.py` -> `1 passed`.

### [WL-6807]

**Title:** Surface provider discovery probe failures in model listing.
**Source Path+Line:** [thegent/src/thegent/provider_model_manager.py:507]
**Acceptance Checklist:**

- [x] Replace broad exception swallowing with warning-level diagnostics.
- [x] Return status metadata to distinguish probe failure from empty model catalogs.
- [x] Add tests for transport failure and malformed payload handling.
      **Notes:** Silent failure conflates outages with legitimate empty results.
      **Evidence:** `discover_models(include_status=True)` now returns `discovery` metadata (`status/failure_type/error_message/malformed_count`) and logs warning-level probe failures (`src/thegent/provider_model_manager.py`).
      **Evidence:** `.venv/bin/python -m pytest -q -p no:tach tests/test_unit_provider_model_manager_discovery.py` -> `4 passed`.

### [WL-6808]

**Title:** Preserve subagent enumeration failure signals in session TUI.
**Source Path+Line:** [thegent/src/thegent/ux/session_tui.py:103]
**Acceptance Checklist:**

- [x] Replace `except Exception: return []` with structured degraded-state signaling.
- [x] Keep UI resilient while surfacing explicit warnings.
- [x] Add tests for process-tree enumeration failure paths.
      **Notes:** Returning empty lists silently can misrepresent active subagents.
      **Evidence:** subagent/log-path failures now populate `diagnostics` and set `degraded=True` while preserving UI rendering (`src/thegent/ux/session_tui.py`).
      **Evidence:** `.venv/bin/python -m pytest -q -p no:tach tests/test_unit_session_tui.py` -> `3 passed`.

### [WL-6809]

**Title:** Distinguish network-interface query errors from true empty state.
**Source Path+Line:** [thegent/src/thegent/resources/network.py:159]
**Acceptance Checklist:**

- [x] Return a shape that differentiates psutil query failure from zero interfaces.
- [x] Preserve logging while exposing machine-readable error context.
- [x] Add tests for psutil exceptions and genuine empty-interface hosts.
      **Notes:** Shared `[]` output masks telemetry failure during diagnostics.
      **Evidence:** `list_interfaces(include_diagnostics=True)` now returns `{interfaces,status,error}` with distinct `empty` and `error` states while retaining exception logging (`src/thegent/resources/network.py`).
      **Evidence:** `.venv/bin/python -m pytest -q -p no:tach tests/resources/test_network.py::TestListInterfaces::test_include_diagnostics_distinguishes_empty_from_error tests/resources/test_network.py::TestListInterfaces::test_include_diagnostics_reports_psutil_unavailable` -> `2 passed`.
