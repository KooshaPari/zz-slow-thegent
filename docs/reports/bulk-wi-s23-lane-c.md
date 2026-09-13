### [WL-6690]

**Title:** Implement conflict-aware `sync_configs` merge flow in unified config manager
**Source:** [thegent/src/thegent/integration/unified_config.py:162]
**Acceptance checklist:**

- [ ] Detect key conflicts across managed config sources using explicit precedence rules.
- [ ] Apply a deterministic merge strategy and persist resolved values back to source files.
- [ ] Add tests for no-conflict sync, merge conflicts, and idempotent re-sync behavior.
      **Notes:** Line 162 marks `sync_configs` as a placeholder with only comments for conflict handling and merge strategy.

### [WL-6691]

**Title:** Replace mocked local-state collection with registry-backed sync payload construction
**Source:** [thegent/src/thegent/discovery/sync.py:70]
**Acceptance checklist:**

- [ ] Load `active_teams` and `recent_handoffs` from real local project data files instead of static empty lists.
- [ ] Validate generated sync payload shape before writing peer inbox JSON files.
- [ ] Add tests for valid state extraction and missing/corrupt source file handling.
      **Notes:** Line 69 states local state collection is mocking file reads and currently emits synthetic empty data.

### [WL-6692]

**Title:** Upgrade ZK verifier from response-length check to deterministic proof validation
**Source:** [thegent/src/thegent/verification/zkp.py:59]
**Acceptance checklist:**

- [ ] Replace `len(response) == 64` acceptance logic with deterministic challenge-response verification.
- [ ] Enforce freshness constraints for proof replay protection before accepting a proof.
- [ ] Add tests for valid proof, commitment mismatch, stale proof, and tampered response cases.
      **Notes:** Line 59 currently approves proofs with a fixed-length response regardless of cryptographic correctness.

### [WL-6693]

**Title:** Implement real remote transport in sync push path instead of stub-only reporting
**Source:** [thegent/src/thegent/commands/sync.py:654]
**Acceptance checklist:**

- [ ] Replace the `files_would_push` stub branch with actual remote upload/publish behavior.
- [ ] Return per-file transfer outcomes in `OperationResult.details` with actionable error metadata.
- [ ] Add tests for successful push, partial failures, and invalid/unreachable remote target handling.
      **Notes:** Line 654 labels push as a stub and only reports files that would be pushed.

### [WL-6694]

**Title:** Replace MCP gateway placeholder executor with real server tool invocation
**Source:** [thegent/src/thegent/mcp/gateway.py:98]
**Acceptance checklist:**

- [ ] Dispatch calls through registered MCP server configuration instead of returning synthetic success payloads.
- [ ] Preserve execution duration and normalize error mapping for unknown tools and transport failures.
- [ ] Add tests for successful invocation, unknown server IDs, and backend execution failures.
      **Notes:** Line 98 explicitly documents `execute` as a stub that returns a placeholder result.

### [WL-6695]

**Title:** Integrate dispatcher `_execute_task` with concrete runner infrastructure and HITL outcomes
**Source:** [thegent/src/thegent/orchestration/dispatcher.py:385]
**Acceptance checklist:**

- [ ] Replace placeholder output generation with real runner invocation based on selected `runner_name`.
- [ ] Enforce HITL approval outcomes as execution gates instead of log-and-continue semantics.
- [ ] Add tests for successful execution, runner failures, and approval-required blocking behavior.
      **Notes:** Line 385 marks `_execute_task` as a placeholder that currently returns synthetic success output.

### [WL-6696]

**Title:** Implement Rich style/token wiring in `apply_to_cli` for design language runtime
**Source:** [thegent/src/thegent/design/design_language.py:102]
**Acceptance checklist:**

- [ ] Map design tokens to concrete Rich theme/style configuration consumed by CLI render surfaces.
- [ ] Support platform-specific token overrides while preserving deterministic defaults.
- [ ] Add tests that assert style application and fallback behavior when tokens are missing.
      **Notes:** Line 101 states CLI design application is placeholder-only and does not configure Rich styles.

### [WL-6697]

**Title:** Replace KPI placeholder constants with telemetry-derived metric calculations
**Source:** [thegent/src/thegent/execution.py:1048]
**Acceptance checklist:**

- [ ] Compute KPI fields from run-registry and contract telemetry data rather than hardcoded constants.
- [ ] Define explicit behavior for sparse datasets, including confidence/data-availability indicators.
- [ ] Add tests validating KPI calculations across representative fixture datasets and edge cases.
      **Notes:** Line 1048 is inside a block of placeholder KPI values that can diverge from real runtime performance.

### [WL-6698]

**Title:** Implement persistent model-tier mutation in `ModelPromoter._update_model_tier`
**Source:** [thegent/src/thegent/learning/promotion.py:24]
**Acceptance checklist:**

- [ ] Implement catalog persistence for tier updates with validation that `model_id` exists.
- [ ] Record promotion metadata (old tier, new tier, trigger metrics, timestamp) for auditability.
- [ ] Add tests for successful promotion, unknown model IDs, and repeated idempotent updates.
      **Notes:** Line 24 is a no-op `pass`, so promotion decisions are logged but never persisted.

### [WL-6699]

**Title:** Add tier-2 worktree bind enforcement in Linux bubblewrap sandbox wrapper
**Source:** [thegent/src/thegent/security/sandboxing.py:36]
**Acceptance checklist:**

- [ ] Replace the tier-2 `pass` branch with explicit worktree-only bind mounts and required read/write scopes.
- [ ] Block unintended filesystem traversal outside allowed bind targets for worktree autonomy tier.
- [ ] Add tests for tier-specific wrapper arguments and regression coverage for tier-1/tier-5 behavior.
      **Notes:** Line 36 is an unimplemented tier-2 branch, leaving worktree isolation behavior undefined.
