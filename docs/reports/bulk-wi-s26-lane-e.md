### [WL-6860]

**Title:** Preserve control-plane provider import failures as explicit diagnostics in `get_config_provider`
**Source:** [thegent/src/thegent/config_provider.py:93]
**Acceptance checklist:**

- [x] Replace `except ImportError: pass` with explicit degraded-state reporting when control-plane provider import fails.
- [x] Distinguish "control plane not configured" from "configured but dependency missing" in returned provider metadata.
- [x] Add tests for successful control-plane provider load and ImportError fallback diagnostics.
      **Notes:** Line 93 currently swallows import failure and silently falls back to `EnvConfigProvider`.
      **Evidence:** `tests/test_wl6860_wl6869_lane_f.py::test_wl6860_control_plane_not_configured_metadata`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6860_control_plane_import_failure_records_metadata`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6860_control_plane_success_metadata`

### [WL-6861]

**Title:** Expose `/proc/version` read failures during WSL2 detection in `detect_platform`
**Source:** [thegent/src/thegent/thegent_platform.py:41]
**Acceptance checklist:**

- [x] Replace silent `except OSError: pass` branch with bounded warning telemetry for `/proc/version` read failures.
- [x] Keep platform detection non-fatal while preserving error category for troubleshooting.
- [x] Add tests for readable `/proc/version`, unreadable file, and environment-variable fallback paths.
      **Notes:** Line 41 drops filesystem read errors, which can hide platform detection regressions.
      **Evidence:** `tests/test_wl6860_wl6869_lane_f.py::test_wl6861_detect_platform_reads_proc_version`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6861_detect_platform_proc_read_failure_uses_env_fallback`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6861_detect_platform_proc_read_failure_linux_path`

### [WL-6862]

**Title:** Surface JSON parse/copy failures when cloning global Claude settings into isolated config
**Source:** [thegent/src/thegent/clode_config_isolation.py:28]
**Acceptance checklist:**

- [x] Replace broad exception suppression with explicit handling for malformed JSON and write failures.
- [x] Emit structured diagnostics indicating whether parse or write failed during `settings.json` copy.
- [x] Add tests for valid settings copy, malformed source JSON, and unwritable target directory.
      **Notes:** Line 28 silently ignores any failure while copying global `settings.json` into isolated config.
      **Evidence:** `tests/test_wl6860_wl6869_lane_f.py::test_wl6862_settings_copy_success`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6862_settings_copy_malformed_source`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6862_settings_copy_unwritable_target`

### [WL-6863]

**Title:** Report target cleanup failures before relinking global Claude state in isolation setup
**Source:** [thegent/src/thegent/clode_config_isolation.py:42]
**Acceptance checklist:**

- [x] Replace silent `except OSError: pass` in target removal path with bounded cleanup diagnostics.
- [x] Differentiate unlink/rmtree permission failures from non-existent target behavior.
- [x] Add tests for file target removal, directory target removal, and permission-denied cleanup failures.
      **Notes:** Line 42 suppresses cleanup errors and can leave stale non-symlink targets without visibility.
      **Evidence:** `tests/test_wl6860_wl6869_lane_f.py::test_wl6863_cleanup_removes_file_target`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6863_cleanup_removes_directory_target`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6863_cleanup_permission_denied_records_diagnostics`

### [WL-6864]

**Title:** Preserve model-transform parse/type failure context in `transform_models`
**Source:** [thegent/src/thegent/cliproxy_models_transform.py:131]
**Acceptance checklist:**

- [x] Replace bare parse/type suppression with structured error metadata for invalid upstream payloads.
- [x] Keep `None` return contract while exposing failure reason to callers and logs.
- [x] Add tests for malformed JSON, wrong-shape payloads, and successful transformed responses.
      **Notes:** Line 131 currently swallows decode/type errors and returns `None` without diagnostics.
      **Evidence:** `tests/test_wl6860_wl6869_lane_f.py::test_wl6864_transform_success_payload`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6864_transform_malformed_json_records_diagnostics`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6864_transform_wrong_shape_records_diagnostics`

### [WL-6865]

**Title:** Make optional load-based-limit import failure visible in lane-admission flow
**Source:** [thegent/src/thegent/execution.py:343]
**Acceptance checklist:**

- [x] Replace `except ImportError: pass` with explicit degraded-mode signaling when advanced resource gates are unavailable.
- [x] Emit a one-time diagnostic indicating which optional module is missing and what behavior is skipped.
- [x] Add tests for import-available and import-missing admission behavior.
      **Notes:** Line 343 currently hides advanced-gate unavailability and silently falls back to basic slot limits.
      **Evidence:** `tests/test_wl6860_wl6869_lane_f.py::test_wl6865_optional_module_present`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6865_optional_module_missing_logs_once`

### [WL-6866]

**Title:** Surface deadline monitor unregister failures in `ResourceCoordinator.release`
**Source:** [thegent/src/thegent/execution.py:449]
**Acceptance checklist:**

- [x] Replace broad exception swallowing around `get_deadline_monitor().unregister(...)` with typed failure handling.
- [x] Preserve release-path resiliency while recording bounded failure diagnostics.
- [x] Add tests for successful unregister, monitor import failure, and unregister runtime exception.
      **Notes:** Line 449 suppresses all unregister errors, masking potential deadline-monitor drift.
      **Evidence:** `tests/test_wl6860_wl6869_lane_f.py::test_wl6866_release_unregister_success`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6866_release_import_failure_records_diagnostics`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6866_release_runtime_failure_records_diagnostics`

### [WL-6867]

**Title:** Record low-confidence handoff events in `HandoffRegistry.confirm_handoff`
**Source:** [thegent/src/thegent/execution.py:586]
**Acceptance checklist:**

- [x] Replace the no-op low-confidence branch with persisted event details and explicit confidence-state tagging.
- [x] Enforce configurable thresholds for warnings/escalation before confirming handoff.
- [x] Add tests for high-confidence confirmation, low-confidence logging/escalation, and invalid snapshot handling.
      **Notes:** Line 586 is currently a `pass`, so low-confidence handoffs are not recorded before confirmation continues.
      **Evidence:** `tests/test_wl6860_wl6869_lane_f.py::test_wl6867_handoff_high_confidence_confirmation`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6867_handoff_low_confidence_logs_escalation`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6867_invalid_snapshot_handling`

### [WL-6868]

**Title:** Track malformed pending-message records instead of dropping them silently
**Source:** [thegent/src/thegent/execution.py:1399]
**Acceptance checklist:**

- [x] Replace bare parse suppression in `_parse_message_line` with counters or sampled diagnostics for invalid records.
- [x] Preserve `None` return for non-pending/invalid rows while surfacing parse-quality degradation.
- [x] Add tests for valid pending records, malformed JSON lines, and non-pending records.
      **Notes:** Line 1399 silently suppresses parse/validation errors, hiding message-registry data issues.
      **Evidence:** `tests/test_wl6860_wl6869_lane_f.py::test_wl6868_parse_message_valid_pending`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6868_parse_message_malformed_records_diagnostics`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6868_parse_message_non_pending_records_counter`

### [WL-6869]

**Title:** Differentiate hash-chain read failure from empty registry in `RunRegistry._get_last_hash`
**Source:** [thegent/src/thegent/execution.py:1462]
**Acceptance checklist:**

- [x] Replace broad exception suppression in `_get_last_hash` with typed error handling and bounded diagnostics.
- [x] Return structured status metadata so callers can distinguish an unreadable/corrupt registry from a truly empty chain.
- [x] Add tests for empty registry, valid last-hash read, malformed trailing record, and IO failure.
      **Notes:** Line 1462 currently swallows all read/parse failures and returns `None`, conflating failure with empty state.
      **Evidence:** `tests/test_wl6860_wl6869_lane_f.py::test_wl6869_get_last_hash_empty_registry_status`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6869_get_last_hash_valid_hash_status`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6869_get_last_hash_malformed_record_status`, `tests/test_wl6860_wl6869_lane_f.py::test_wl6869_get_last_hash_io_failure_status`
