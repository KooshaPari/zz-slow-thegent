### [WL-6910]

**Title:** Surface alias-probe failures in shell health checks instead of suppressing diagnostics
**Source:** [thegent/src/thegent/shell_cli.py:179]
**Acceptance checklist:**

- [x] Replace blanket exception swallowing around alias probe subprocess execution with typed failure handling.
- [x] Preserve non-fatal behavior while recording bounded diagnostics when alias inspection cannot run.
- [x] Add tests for successful alias probe, subprocess failure, and timeout paths.
      **Notes:** Line 176 currently drops all alias-probe failures, masking shell environment inspection regressions.
      **Evidence:** `src/thegent/shell_cli.py` now classifies alias probe errors and surfaces bounded `Alias probe failed` diagnostics without aborting doctor flow; covered by `tests/test_wl6910_wl6919_lane_f.py` (`test_wl6910_*`).

### [WL-6911]

**Title:** Preserve parse and timestamp validation failures in `_parse_log_entry`
**Source:** [thegent/src/thegent/summary.py:81]
**Acceptance checklist:**

- [x] Replace broad exception suppression with structured handling for JSON decode, key, and timestamp errors.
- [x] Keep `None` return contract for unusable rows while surfacing failure categories for observability.
- [x] Add tests for valid entries, malformed JSON lines, and invalid timestamp formats.
      **Notes:** Line 79 suppresses all parsing failures and makes dropped-log behavior opaque.
      **Evidence:** `src/thegent/summary.py` uses `LogParseStats` categories (`malformed_json`, `missing_required_key`, `invalid_timestamp`) while returning `None` for unusable rows; covered by `tests/test_wl6910_wl6919_lane_f.py` (`test_wl6911_*`).

### [WL-6912]

**Title:** Report log-file read failures in `_read_log_file` without aborting summary collection
**Source:** [thegent/src/thegent/summary.py:94]
**Acceptance checklist:**

- [x] Replace blanket read-loop exception swallowing with typed IO/error diagnostics.
- [x] Continue best-effort aggregation for readable files while surfacing unreadable-path failures.
- [x] Add tests for readable files, missing files, and permission-denied paths.
      **Notes:** Line 93 currently hides file access and decode failures, returning partial results without signal.
      **Evidence:** `_read_log_file(..., include_diagnostics=True)` now reports typed statuses (`missing`, `permission_denied`, `decode_error`, `io_error`) while preserving readable entries; covered by `tests/test_wl6910_wl6919_lane_f.py` (`test_wl6912_*`).

### [WL-6913]

**Title:** Differentiate import resolution failure from missing packaged assets in `_get_thegent_root`
**Source:** [thegent/src/thegent/install.py:108]
**Acceptance checklist:**

- [x] Replace broad exception suppression around package import/path resolution with typed failure handling.
- [x] Emit bounded diagnostics indicating whether import or path checks failed before dev-root fallback.
- [x] Add tests for installed-package discovery success and import/path failure fallback behavior.
      **Notes:** Line 108 swallows all exceptions, obscuring why packaged hook/skill discovery failed.
      **Evidence:** `src/thegent/install.py:_get_thegent_root` now separates `import_error` vs `path_resolution_error` diagnostics (bounded) before dev-root fallback; covered by `tests/test_wl6910_wl6919_lane_f.py` (`test_wl6913_*`).

### [WL-6914]

**Title:** Make lockfile cleanup errors explicit during shared MCP lock recovery
**Source:** [thegent/src/thegent/shared_mcp_manager.py:66]
**Acceptance checklist:**

- [x] Replace broad exception fallback in lockfile parse/recovery flow with typed handling and explicit cleanup outcomes.
- [x] Differentiate corrupt lockfile JSON, stale PID state, and unlink permission failures.
- [x] Add tests for stale lockfile cleanup success, invalid lockfile content, and unlink failure handling.
      **Notes:** Line 64 can call `lockfile.unlink()` inside a blanket exception path, hiding root-cause failure modes.
      **Evidence:** `src/thegent/shared_mcp_manager.py` now centralizes cleanup via `_remove_lockfile(...)`, differentiates stale/corrupt/invalid lockfile cases, and returns explicit unlink-failure messages; covered by `tests/test_wl6910_wl6919_lane_f.py` (`test_wl6914_*`).

### [WL-6915]

**Title:** Expose argv parsing failures in `extract_dex_command_args`
**Source:** [thegent/src/thegent/dex_cli_helpers.py:75]
**Acceptance checklist:**

- [x] Replace blanket exception suppression in dex token scanning with typed validation and diagnostics.
- [x] Preserve empty-list fallback when command token is absent while distinguishing malformed argv inputs.
- [x] Add tests for normal dex invocation, no dex token, and non-string/invalid argv entries.
      **Notes:** Line 75 drops parsing failures and can silently return empty args for malformed command vectors.
      **Evidence:** `src/thegent/dex_cli_helpers.py:extract_dex_command_args` now validates argv container/entry types and emits typed warnings while keeping empty-list fallback; covered by `tests/test_wl6910_wl6919_lane_f.py` (`test_wl6915_*`).

### [WL-6916]

**Title:** Surface model-list filtering failures in provider model manager
**Source:** [thegent/src/thegent/provider_model_manager.py:508]
**Acceptance checklist:**

- [x] Replace broad exception swallowing in model normalization/filtering with typed parse/shape diagnostics.
- [x] Preserve partial-result behavior for recoverable record-level errors while signaling hard payload failures.
- [x] Add tests for valid provider filtering, malformed model entries, and invalid top-level payloads.
      **Notes:** Line 507 suppresses exceptions and can return incomplete results without any operator-visible signal.
      **Evidence:** `discover_models` now tracks `malformed_count`, classifies payload failures, and keeps recoverable partial rows; tests in `tests/test_unit_provider_model_manager_discovery.py`.

### [WL-6917]

**Title:** Record session metadata/log-path resolution failures in TUI session details
**Source:** [thegent/src/thegent/ux/session_tui.py:123]
**Acceptance checklist:**

- [x] Replace broad exception suppression around meta-path lookup with typed diagnostics.
- [x] Preserve session rendering by degrading gracefully while indicating unavailable log-path metadata.
- [x] Add tests for valid meta lookup, missing metadata file, and path resolution errors.
      **Notes:** Line 123 suppresses all failures while populating `log_paths`, making broken session metadata invisible.
      **Evidence:** `src/thegent/ux/session_tui.py` now sets `failure_type` (`meta_missing` / `path_resolution_error`) in degraded diagnostics and preserves rendering; covered by `tests/test_wl6910_wl6919_lane_f.py` (`test_wl6917_*`).

### [WL-6918]

**Title:** Distinguish development-mode path detection failures in `get_resource_path`
**Source:** [thegent/src/thegent/resources/__init__.py:64]
**Acceptance checklist:**

- [x] Replace blanket exception suppression in dev-mode detection with typed error handling.
- [x] Preserve package-resource fallback while emitting bounded diagnostics for path-resolution failures.
- [x] Add tests for dev-tree discovery, non-dev installation paths, and unexpected path inspection errors.
      **Notes:** Line 64 silently suppresses exceptions, conflating genuine detection failures with non-dev environments.
      **Evidence:** `src/thegent/resources/__init__.py:get_resource_path` now emits typed diagnostics for dev-mode config/path inspection and keeps package/fallback behavior; covered by `tests/test_wl6910_wl6919_lane_f.py` (`test_wl6918_*`).

### [WL-6919]

**Title:** Surface terminal pane cleanup failures when terminating child shell process
**Source:** [thegent/src/thegent/compositor/terminal_pane.py:132]
**Acceptance checklist:**

- [x] Replace broad cleanup exception swallowing with typed handling for terminate/wait/kill failures.
- [x] Preserve pane teardown resiliency while recording bounded failure diagnostics.
- [x] Add tests for graceful termination, timeout-triggered kill path, and cleanup exception handling.
      **Notes:** Line 132 currently suppresses all cleanup errors and can hide terminal subprocess lifecycle issues.
      **Evidence:** `src/thegent/compositor/terminal_pane.py:cleanup` now records `last_cleanup_diagnostic` for terminate/wait/kill failure types while always tearing down pane state; covered by `tests/test_wl6910_wl6919_lane_f.py` (`test_wl6919_*`).
