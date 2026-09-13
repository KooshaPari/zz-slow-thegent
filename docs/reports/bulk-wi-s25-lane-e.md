### [WL-6810]

**Title:** Implement conflict-aware `sync_configs` merge flow in unified config manager
**Source:** [thegent/src/thegent/integration/unified_config.py:163]
**Acceptance checklist:**

- [x] Detect key conflicts across managed config sources using explicit precedence rules.
- [x] Apply deterministic merge logic and persist reconciled values to source files.
- [x] Add tests for no-conflict sync, merge conflicts, and idempotent re-sync behavior.
      **Notes:** Implemented precedence merge + persisted YAML/frontmatter reconciliation with explicit `last_sync_conflicts` tracking. Covered by `tests/test_wl681x_lane_d.py::test_wl6810_sync_configs_merges_conflicts_and_persists`.

### [WL-6811]

**Title:** Replace mocked local-state collection with registry-backed sync payload construction
**Source:** [thegent/src/thegent/discovery/sync.py:69]
**Acceptance checklist:**

- [x] Load `active_teams` and `recent_handoffs` from real project state files instead of static empty lists.
- [x] Validate generated sync payload schema before writing peer inbox artifacts.
- [x] Add tests for successful extraction and malformed source-file handling.
      **Notes:** Replaced mock state builder with file-backed loaders (`team_registry.json`, `handoff_registry.jsonl`) and `SyncPayload` schema validation before write. Covered by `tests/test_wl681x_lane_d.py::test_wl6811_sync_loop_collects_real_state_and_validates_payload` and malformed-file case.

### [WL-6812]

**Title:** Upgrade ZK verifier from mock response checks to deterministic proof validation
**Source:** [thegent/src/thegent/verification/zkp.py:60]
**Acceptance checklist:**

- [x] Replace response-shape-only logic with deterministic challenge-response proof verification.
- [x] Enforce freshness and replay constraints before accepting proofs.
- [x] Add tests for valid proof, stale proof, commitment mismatch, and tampered response cases.
      **Notes:** Added deterministic challenge-response verification against registered commitments, freshness window enforcement, and replay key tracking. Covered by `tests/test_wl681x_lane_d.py::test_wl6812_zk_verify_valid_stale_mismatch_and_tamper`.

### [WL-6813]

**Title:** Implement real remote transport in sync push path instead of stub-only reporting
**Source:** [thegent/src/thegent/commands/sync.py:655]
**Acceptance checklist:**

- [x] Replace `files_would_push` stub behavior with concrete upload/publish execution.
- [x] Return per-file transfer outcomes in `OperationResult.details` with actionable error metadata.
- [x] Add tests for successful push, partial failure, and unreachable target handling.
      **Notes:** Implemented real filesystem-backed push transport under `<target>/.thegent/sync_push/` with per-file outcome records and partial-failure handling. Covered by `tests/test_wl681x_lane_d.py::test_wl6813_push_success_partial_failure_and_unreachable`.

### [WL-6814]

**Title:** Replace MCP gateway placeholder executor with real server tool invocation
**Source:** [thegent/src/thegent/mcp/gateway.py:100]
**Acceptance checklist:**

- [x] Dispatch calls through registered MCP server configuration rather than synthetic results.
- [x] Preserve duration and normalize errors for unknown servers/tools and transport failures.
- [x] Add tests for successful invocation, unknown server ID, and downstream execution failure.
      **Notes:** Replaced placeholder return path with command execution (`subprocess.run`) + JSON-RPC response parsing and normalized unknown-tool/transport errors. Covered by `tests/mcp/test_gateway.py` and `tests/test_wl681x_lane_d.py::test_wl6814_gateway_exec_success_unknown_server_tool_and_transport_failure`.

### [WL-6815]

**Title:** Integrate dispatcher `_execute_task` with concrete runner execution path
**Source:** [thegent/src/thegent/orchestration/dispatcher.py:386]
**Acceptance checklist:**

- [x] Replace placeholder output generation with real runner invocation from selected `runner_name`.
- [x] Propagate non-success execution state and captured error details to callers.
- [x] Add tests for success, runner failure propagation, and approval-blocked execution.
      **Notes:** `_execute_task` now resolves runners via registry, executes in thread, and propagates exit/error state. HITL gate now blocks when approval is required but not granted. Covered by `tests/test_wl681x_lane_d.py::test_wl6815_dispatcher_execute_task_success_failure_and_approval_block`.

### [WL-6816]

**Title:** Implement Rich style/token wiring in `apply_to_cli` for runtime design language
**Source:** [thegent/src/thegent/design/design_language.py:101]
**Acceptance checklist:**

- [x] Map design tokens to concrete Rich theme/style configuration consumed by CLI surfaces.
- [x] Support platform-specific token overrides while preserving deterministic defaults.
- [x] Add tests asserting style application and missing-token fallback behavior.
      **Notes:** `apply_to_cli` now creates/stores `Rich Theme` styles from design tokens and stores typography metadata with deterministic platform fallback logic. Covered by `tests/test_wl681x_lane_d.py::test_wl6816_design_language_apply_to_cli_and_fallback`.

### [WL-6817]

**Title:** Replace KPI placeholder constants with telemetry-derived calculations
**Source:** [thegent/src/thegent/execution.py:1047]
**Acceptance checklist:**

- [x] Compute KPI fields from run registry and contract telemetry instead of hardcoded constants.
- [x] Define explicit behavior for sparse datasets, including confidence/data-availability indicators.
- [x] Add deterministic tests for populated and empty telemetry fixtures.
      **Notes:** Replaced hardcoded KPI constants with derived run/telemetry/interruption metrics and added `data_availability`, `kpi_confidence`, `coverage_points`. Covered by `tests/test_wl681x_lane_d.py::test_wl6817_kpis_from_telemetry_and_sparse_behavior`.

### [WL-6818]

**Title:** Implement persistent model-tier mutation in `ModelPromoter._update_model_tier`
**Source:** [thegent/src/thegent/learning/promotion.py:23]
**Acceptance checklist:**

- [x] Implement catalog persistence for tier updates with validation that `model_id` exists.
- [x] Record promotion metadata (old tier, new tier, trigger metrics, timestamp) for auditability.
- [x] Add tests for successful promotion, unknown IDs, and idempotent repeated updates.
      **Notes:** Implemented tier persistence to `custom_models.yaml` with catalog validation and audit trail in `model_promotion_audit.jsonl`; repeated same-tier updates are idempotent. Covered by `tests/test_wl681x_lane_d.py::test_wl6818_model_promotion_persists_with_audit_and_idempotency`.

### [WL-6819]

**Title:** Add tier-2 bind-mount enforcement in Linux sandbox wrapper
**Source:** [thegent/src/thegent/security/sandboxing.py:39]
**Acceptance checklist:**

- [x] Replace the tier-2 `pass` branch with explicit worktree-only bind mounts and allowed scopes.
- [x] Block unintended filesystem traversal outside permitted bind targets.
- [x] Add tests for tier-2 wrapper arguments and regression coverage for other tiers.
      **Notes:** Tier-2 Linux bwrap now binds only configured worktree + explicit allowed read scopes (plus tmpfs scratch), preventing root-wide bind at this tier. Covered by `tests/test_wl681x_lane_d.py::test_wl6819_tier2_bwrap_has_worktree_bind_and_no_root_bind`.
