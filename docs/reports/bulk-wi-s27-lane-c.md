### [WL-6890]

**Title:** Replace alias-probe blanket exception swallowing with typed degraded diagnostics
**Source:** [thegent/src/thegent/shell_cli.py:180]
**Acceptance checklist:**

- [x] Replace broad alias-probe exception swallowing with timeout and subprocess-error classification.
- [x] Emit non-fatal doctor output with explicit failure reason and suggested remediation.
- [x] Add tests for successful probe, timeout path, and execution-failure path.
- **Evidence:** `src/thegent/shell_cli.py`, `tests/test_unit_shell_cli.py` (`test_shell_doctor_alias_probe_success`, `test_shell_doctor_records_alias_probe_timeout`, `test_shell_doctor_records_alias_probe_execution_failure`)
  **Notes:** Silent alias-probe failures can produce false healthy shell diagnostics.

### [WL-6891]

**Title:** Distinguish git log execution failures from true empty commit windows
**Source:** [thegent/src/thegent/summary.py:64]
**Acceptance checklist:**

- [x] Replace catch-all git-log failure fallback with structured subprocess error handling.
- [x] Preserve explicit zero-commit semantics separately from command-execution failures.
- [x] Add tests for non-repository paths, empty ranges, and failing git invocations.
- **Evidence:** `src/thegent/summary.py`, `tests/test_unit_summary.py` (`test_get_git_commits_non_repo_returns_diagnostic_status`, `test_get_git_commits_git_command_failure_logs_context`, `test_get_git_commits_git_command_timeout_reports_error`), `tests/test_wl6872_summary_commits.py`
  **Notes:** Returning empty commit lists for all failures hides operational issues in summaries.

### [WL-6892]

**Title:** Surface malformed summary JSON entries instead of silently dropping parse failures
**Source:** [thegent/src/thegent/summary.py:84]
**Acceptance checklist:**

- [x] Replace parse exception swallowing with bounded malformed-entry diagnostics.
- [x] Continue line-by-line ingestion while exposing skipped malformed record counts.
- [x] Add tests for mixed valid and malformed `.jsonl` records.
- **Evidence:** `src/thegent/summary.py`, `tests/test_wl6910_wl6919_lane_f.py` (`test_wl6911_parse_log_entry_malformed_json`, `test_wl6912_read_log_file_with_malformed_and_valid_records`)
  **Notes:** Hidden parse failures reduce trust in generated activity summaries.

### [WL-6893]

**Title:** Preserve tmux fallback discovery failures as degraded-state diagnostics
**Source:** [thegent/src/thegent/native/discovery_native.py:61]
**Acceptance checklist:**

- [x] Capture fallback discovery command failures with structured metadata.
- [x] Differentiate discovery failure from legitimate empty session results.
- [x] Add tests for successful parse, missing dependency, and command failure paths.
- **Evidence:** `src/thegent/native/discovery_native.py`, `tests/native/test_discovery_native.py` (`test_all_falls_back_on_tmux_probe_failure`, `test_handles_subprocess_exception`, `test_returns_error_on_nonzero_exit`)
  **Notes:** Empty-list fallthrough on failure obscures runtime discovery health.

### [WL-6894]

**Title:** Emit observable diagnostics when optimized sendfile copy falls back
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:63]
**Acceptance checklist:**

- [x] Record fallback reason when optimized `sendfile` transfer fails.
- [x] Preserve correctness and metadata behavior across fallback copy paths.
- [x] Add tests that force `sendfile` failure and assert diagnostics plus successful copy.
      **Notes:** Silent fallback behavior can hide performance regressions under load.
- **Evidence:** `src/thegent/infra/fast_file_ops.py`, `tests/test_unit_fast_file_ops_wl6716.py` (`test_sendfile_failure_falls_back_and_emits_telemetry`, `test_sendfile_unexpected_failure_falls_back_and_records_exception_name`)

### [WL-6895]

**Title:** Replace startup endpoint reachability stub with deterministic network probes
**Source:** [thegent/src/thegent/integrations/startup_validation.py:46]
**Acceptance checklist:**

- [x] Implement real endpoint checks with explicit timeout and connection-failure handling.
- [x] Return structured reachability outcomes consumed by startup validation reporting.
- [x] Add tests for reachable, unreachable, and timeout scenarios.
      **Notes:** Stubbed reachability logic can over-report healthy startup state.
- **Evidence:** `src/thegent/integrations/startup_validation.py` (`StartupValidator`), `tests/test_wl192_startup_validation.py` (`test_check_endpoint_reachability_returns_dict`, `test_check_endpoint_reachability_reflects_status_code`, `test_check_endpoint_reachability_handles_errors`, `test_check_endpoint_reachability_empty_list`, `test_validate_all_with_endpoints`, `test_validate_all_with_unreachable_endpoint`)

### [WL-6896]

**Title:** Replace GitHub Project sync mock write response with real item upsert flow
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:202]
**Acceptance checklist:**

- [x] Replace placeholder write response with real project item create and update behavior.
- [x] Validate required outbound field mappings before write attempts.
- [x] Add tests for created-versus-updated counts and API failure propagation.
      **Notes:** Mock success paths hide whether synchronization actually occurred.
- **Evidence:** `src/thegent/integrations/gh_project_sync.py`, `tests/test_wl157_gh_project_sync.py` (`test_create_and_update_counts_reflect_upsert_path`, `test_missing_status_options_fails_before_item_mutations`, `test_api_failure_during_upsert_is_propagated_in_strict_mode`), `tests/integrations/test_wl178_github_sync_integration.py`

### [WL-6897]

**Title:** Replace MCP gateway stub executor with transport-backed tool execution
**Source:** [thegent/src/thegent/mcp/gateway.py:98]
**Acceptance checklist:**

- [ ] Route tool execution through configured server transport rather than synthetic payloads.
- [ ] Preserve explicit error contracts for unknown tools, transport failures, and execution exceptions.
- [ ] Add tests for successful execution and representative failure branches.
      **Notes:** Stub executor behavior undermines confidence in end-to-end MCP integration health.

### [WL-6898]

**Title:** Replace dispatcher placeholder task execution with runner-backed invocation
**Source:** [thegent/src/thegent/orchestration/dispatcher.py:385]
**Acceptance checklist:**

- [ ] Route `_execute_task` through real runner resolution and invocation.
- [ ] Enforce HITL approval gates as deterministic execution preconditions.
- [ ] Add tests for success, runner failure propagation, and approval-required blocking.
      **Notes:** Placeholder execution can incorrectly mark blocked tasks as completed.

### [WL-6899]

**Title:** Replace hash-randomized SID mapping with deterministic UID derivation
**Source:** [thegent/src/thegent/infra/wsl_interop.py:119]
**Acceptance checklist:**

- [ ] Replace Python `hash()` SID mapping with stable deterministic digest-based derivation.
- [ ] Define explicit collision handling semantics for SID-to-UID assignments.
- [ ] Add reproducibility tests ensuring stable mappings across interpreter restarts.
      **Notes:** Hash randomization can produce nondeterministic identities across process boundaries.
