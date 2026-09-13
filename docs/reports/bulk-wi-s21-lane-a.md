### [WL-6570]

**Title:** Replace silent control-plane import fallback with explicit provider selection diagnostics
**Source Path+Line:** [thegent/src/thegent/config_provider.py:93]
**Acceptance Checklist:**

- [ ] Replace the bare `ImportError` swallow in `get_config_provider` with structured logging that records why control-plane provider initialization failed.
- [ ] Return a deterministic error or explicit env-provider fallback reason so callers can distinguish configuration intent from runtime failure.
- [ ] Add tests for configured control-plane URL with missing client module and for successful control-plane provider resolution.
      **Notes:** Current behavior silently falls back to `EnvConfigProvider`, which obscures broken control-plane wiring.

### [WL-6571]

**Title:** Enforce fail-fast worktree creation semantics instead of suppressing add failures
**Source Path+Line:** [thegent/src/thegent/mesh/worktree.py:60]
**Acceptance Checklist:**

- [ ] Remove silent `CalledProcessError` handling in `create_worktree` and surface actionable failure context (branch, stderr, return code).
- [ ] Prevent branch-registry updates when `git worktree add` fails.
- [ ] Add tests covering successful creation, duplicate-branch collision, and git command failure without stale registry writes.
      **Notes:** The current `pass` path can register ownership even when worktree creation did not succeed.

### [WL-6572]

**Title:** Harden cross-project registry loading with typed validation and corruption reporting
**Source Path+Line:** [thegent/src/thegent/cross_project/registry.py:33]
**Acceptance Checklist:**

- [ ] Replace broad exception swallowing in `_load_registry` with explicit JSON/IO error handling and structured diagnostics.
- [ ] Validate on-disk schema shape before assigning `self.registry` to avoid non-dict payload drift.
- [ ] Add tests for missing file, malformed JSON, and wrong top-level type inputs.
      **Notes:** Returning `{}` on any exception hides data corruption and silently drops persisted personas.

### [WL-6573]

**Title:** Surface CLIProxy model-discovery transport failures instead of returning partial-empty results
**Source Path+Line:** [thegent/src/thegent/provider_model_manager.py:507]
**Acceptance Checklist:**

- [ ] Replace the broad `except` in `discover_models` with classified network/parse failure handling.
- [ ] Emit deterministic error metadata (transport unavailable, invalid payload, timeout) alongside discovered model results.
- [ ] Add tests for reachable endpoint, non-200 response, timeout, and invalid JSON payloads.
      **Notes:** The current silent failure path makes provider discovery look successful while returning incomplete model inventory.

### [WL-6574]

**Title:** Replace hardcoded KPI placeholder values with metrics-derived calculations
**Source Path+Line:** [thegent/src/thegent/execution.py:1047]
**Acceptance Checklist:**

- [ ] Compute KPI fields (`routing_accuracy`, `accuracy`, `freshness`, `interruption_rate`, `cost_per_run`, `knowledge_coverage`, `rollback_sla`, `continuity_score`) from recorded telemetry instead of static constants.
- [ ] Preserve response schema while documenting fallback behavior when source metrics are insufficient.
- [ ] Add tests for populated telemetry and sparse-telemetry scenarios with deterministic outputs.
      **Notes:** Current fixed values mask real operational health and can mislead dashboard consumers.

### [WL-6575]

**Title:** Implement filesystem indicator scan in sitback gardening test-failure checks
**Source Path+Line:** [thegent/src/thegent/sitback/gardening.py:114]
**Acceptance Checklist:**

- [ ] Replace the no-op loop over indicator globs with actual existence checks and collected findings.
- [ ] Include indicator-derived context in `check_test_failures` output alongside pytest collect status.
- [ ] Add tests for repos with and without indicator directories to verify attention signaling behavior.
      **Notes:** The current `pass` leaves `_indicators` unused, reducing the reliability of backlog triage heuristics.

### [WL-6576]

**Title:** Differentiate unsupported-json-format vs command failure in zmx session listing
**Source Path+Line:** [thegent/src/thegent/session/zmx_backend.py:311]
**Acceptance Checklist:**

- [ ] Refine `_list_json` return contract to distinguish unsupported flag from runtime command failure.
- [ ] Ensure `_list_sessions` can report hard failures without silently degrading to empty lists.
- [ ] Add tests for unknown `--format` flag, zmx execution failure, and valid JSON listing paths.
      **Notes:** Returning `[]` on generic JSON command failure currently makes operational errors indistinguishable from “no sessions”.

### [WL-6577]

**Title:** Add per-method required-parameter validation in JSON-RPC request parsing
**Source Path+Line:** [thegent/src/thegent/protocols/jsonrpc_agent_server.py:108]
**Acceptance Checklist:**

- [ ] Extend request dispatch validation so methods with required params reject missing-param requests instead of defaulting to `{}`.
- [ ] Keep JSON-RPC error codes stable and include explicit reason strings for missing required keys.
- [ ] Add tests for valid parameterless methods, required-param methods without params, and non-object params.
      **Notes:** The current default `({}, None)` path allows missing-params requests to advance further than intended.

### [WL-6578]

**Title:** Normalize process-enumeration error reporting on macOS agent detection path
**Source Path+Line:** [thegent/src/thegent/mesh/process_detection.py:45]
**Acceptance Checklist:**

- [ ] Replace silent `CalledProcessError` handling with explicit diagnostic payloads for process-scan failures.
- [ ] Preserve successful process parsing while returning structured failure context when `ps` execution fails.
- [ ] Add tests for normal macOS parse flow and simulated `ps` command failure handling.
      **Notes:** The current `pass` returns an empty process set, which can be misinterpreted as “no agents running.”

### [WL-6579]

**Title:** Enforce handler-failure visibility contract in A2A router response flow
**Source Path+Line:** [thegent/src/thegent/protocols/a2a.py:166]
**Acceptance Checklist:**

- [ ] Define and implement explicit failure accounting for handler exceptions in `A2ARouter.route`.
- [ ] Return or emit structured error metadata per failed handler without breaking successful handler responses.
- [ ] Add tests for mixed success/failure handlers and total-handler-failure scenarios.
      **Notes:** Exceptions are logged today, but callers receive no machine-readable indication that handler execution failed.
