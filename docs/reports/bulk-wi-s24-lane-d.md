### [WL-6750]

**Title:** Convert alias-probe exception swallowing in `shell doctor` into visible diagnostics.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:177]
**Acceptance Checklist:**

- [x] Replace blanket exception suppression in the alias probe with targeted handling for subprocess timeout and launch failures.
- [x] Add a doctor issue or warning entry when alias probing fails so output does not appear falsely healthy.
- [x] Add tests covering both successful alias detection and probe-failure visibility.
      **Evidence:** `src/thegent/shell_cli.py` catches typed probe failures and records issue+warning; covered by `tests/test_wl6750_wl6759_lane_a.py::test_wl6750_shell_doctor_alias_probe_success_and_probe_failure_visibility` (`17 passed` lane run).
      **Notes:** The current bare `except` path drops probe failures and can mask shell-environment regressions.

### [WL-6751]

**Title:** Split zsh-version detection failures into actionable platform statuses.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:479]
**Acceptance Checklist:**

- [x] Distinguish missing binary, timeout, and execution failure when collecting zsh version.
- [x] Preserve non-fatal behavior while surfacing failure cause in platform output.
- [x] Add tests for success and each degraded status path.
      **Evidence:** `src/thegent/shell_cli.py` emits distinct statuses (`Not installed`, `Probe timed out`, `Probe failed (...)`); covered by `tests/test_wl6750_wl6759_lane_a.py::test_wl6751_shell_platform_reports_actionable_statuses`.
      **Notes:** Collapsing all errors into `Not available` removes useful environment-triage detail.

### [WL-6752]

**Title:** Prevent incorrect Nix success fallback when version command fails unexpectedly.
**Source Path+Line:** [thegent/src/thegent/doctor_shell_nix.py:148]
**Acceptance Checklist:**

- [x] Replace broad fallback handling with typed exception branches for timeout, execution errors, and missing binary.
- [x] Avoid marking status `ok` on generic invocation errors without evidence of a healthy binary.
- [x] Add tests covering timeout, permission, and non-zero invocation outcomes.
      **Evidence:** `src/thegent/doctor_shell_nix.py` uses typed branches for timeout/permission/subprocess execution outcomes; covered by `tests/test_wl6750_wl6759_lane_a.py::test_wl6752_check_nix_typed_failure_branches`.
      **Notes:** Current fallback logic can report Nix as found even when command execution is broken.

### [WL-6753]

**Title:** Attach failure cause context to MCP health-check warnings.
**Source Path+Line:** [thegent/src/thegent/doctor.py:1501]
**Acceptance Checklist:**

- [x] Capture bounded error category/message when MCP `/health` probing fails.
- [x] Preserve warning semantics but include reason context in result details.
- [x] Add tests for connection-refused and timeout scenarios.
      **Evidence:** `src/thegent/doctor.py` sets warning details for timeout/connect/http failures; covered by `tests/test_wl6750_wl6759_lane_a.py::test_wl6753_mcp_health_warnings_include_failure_cause`.
      **Notes:** Generic `not reachable` messaging obscures remediation for different outage modes.

### [WL-6754]

**Title:** Differentiate git-log command failure from true zero-commit windows.
**Source Path+Line:** [thegent/src/thegent/summary.py:61]
**Acceptance Checklist:**

- [x] Replace blanket exception-to-empty-list fallback with structured failure metadata.
- [x] Include bounded stderr/exit code context for failed git invocation.
- [x] Update callers/tests to handle `no commits` versus `query failed` as distinct states.
      **Evidence:** `src/thegent/summary.py` returns `GitCommitsResult(status/error)` with exit-code+stderr context and keeps `empty` distinct from `error`; covered by `tests/test_wl6750_wl6759_lane_a.py::test_wl6754_git_commit_query_failure_is_distinct_from_empty_window`.
      **Notes:** Returning `[]` for all failures can under-report activity in generated summaries.

### [WL-6755]

**Title:** Track malformed JSONL lines during session log parsing.
**Source Path+Line:** [thegent/src/thegent/summary.py:79]
**Acceptance Checklist:**

- [x] Record parse-failure counts and optionally sampled line context while continuing ingestion.
- [x] Keep per-line fault tolerance without silent data-quality loss.
- [x] Add tests for mixed valid/invalid log files and malformed timestamps.
      **Evidence:** `src/thegent/summary.py` tracks `parse_counts` and sampled errors via `LogParseStats`; covered by `tests/test_wl6750_wl6759_lane_a.py::test_wl6755_read_log_file_tracks_malformed_json_and_timestamp_errors`.
      **Notes:** The current `except ... pass` path hides parsing drift and makes audit confidence weaker.

### [WL-6756]

**Title:** Emit telemetry when `sendfile` optimization falls back to standard copy.
**Source Path+Line:** [thegent/src/thegent/infra/fast_file_ops.py:66]
**Acceptance Checklist:**

- [x] Capture fallback reason category when the `sendfile` branch fails.
- [x] Preserve existing copy correctness and metadata behavior across fallback.
- [x] Add tests that force `sendfile` failure and assert fallback plus diagnostic emission.
      **Evidence:** `src/thegent/infra/fast_file_ops.py` records categorized fallback counts and warning logs; covered by `tests/test_wl6750_wl6759_lane_a.py::test_wl6756_sendfile_fallback_emits_telemetry`.
      **Notes:** Silent fallback obscures performance regressions in large file copy workflows.

### [WL-6757]

**Title:** Surface provider-discovery probe failures in model listing.
**Source Path+Line:** [thegent/src/thegent/provider_model_manager.py:507]
**Acceptance Checklist:**

- [x] Replace broad exception swallowing with warning-level diagnostics including provider context.
- [x] Return discovery status metadata so callers can distinguish `no models` from probe failure.
- [x] Add tests for transport failure and malformed model payload handling.
      **Evidence:** `src/thegent/provider_model_manager.py` now includes `provider` in discovery metadata and warning extras for probe failures; covered by `tests/test_wl6750_wl6759_lane_a.py::test_wl6757_discover_models_transport_failure_and_provider_context` and `tests/test_wl6750_wl6759_lane_a.py::test_wl6757_discover_models_invalid_payload_status` (`4 passed` in `tests/test_unit_provider_model_manager_discovery.py`).
      **Notes:** Silent failure conflates connectivity issues with legitimately empty model catalogs.

### [WL-6758]

**Title:** Preserve subagent enumeration failure signals in session TUI.
**Source Path+Line:** [thegent/src/thegent/ux/session_tui.py:103]
**Acceptance Checklist:**

- [x] Replace `except Exception: return []` with structured degraded-state signaling.
- [x] Keep UI resilient while exposing an explicit warning for enumeration errors.
- [x] Add tests for psutil/process-tree failure paths.
      **Evidence:** `src/thegent/ux/session_tui.py` captures structured `_last_diag`, logs warning, and marks session details `degraded`; covered by `tests/test_wl6750_wl6759_lane_a.py::test_wl6758_session_tui_surfaces_subagent_enumeration_failures`.
      **Notes:** Returning an empty list silently can misrepresent active subagents as absent.

### [WL-6759]

**Title:** Separate network-interface query errors from true empty-interface state.
**Source Path+Line:** [thegent/src/thegent/resources/network.py:159]
**Acceptance Checklist:**

- [x] Return a result shape that distinguishes psutil query failure from zero discovered interfaces.
- [x] Preserve exception logging while exposing machine-readable error context.
- [x] Add tests for psutil exceptions and empty-interface hosts.
      **Evidence:** `src/thegent/resources/network.py` returns diagnostic payload with `status=empty|error|unavailable` and typed errors when requested; covered by `tests/test_wl6750_wl6759_lane_a.py::test_wl6759_network_interfaces_distinguish_empty_from_error`.
      **Notes:** A bare `[]` on both paths masks telemetry failures during runtime diagnostics.
