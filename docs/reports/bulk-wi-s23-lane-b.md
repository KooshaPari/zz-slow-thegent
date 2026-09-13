### [WL-6680]

**Title:** Implement `get_tenant_config` control-plane retrieval with fallback parity to `resolve`
**Source:** [thegent/src/thegent/control_plane/client.py:75]
**Acceptance checklist:**

- [ ] Implement tenant config fetch against the control-plane endpoint with timeout and error handling.
- [ ] Reuse circuit-breaker and local fallback semantics so failures degrade predictably.
- [ ] Add tests for success, timeout/circuit-open fallback, and malformed response payloads.
      **Notes:** Line 75 currently returns `None` with a "Phase 2: not implemented" marker.

### [WL-6681]

**Title:** Wire forensic post-run snapshots to a real git diff provider
**Source:** [thegent/src/thegent/forensics/snapshot.py:70]
**Acceptance checklist:**

- [ ] Replace the empty diff placeholder with an actual diff retrieval path from `thegent_git` or a vetted fallback command.
- [ ] Bound captured diff size and include truncation metadata to keep snapshot artifacts stable.
- [ ] Add tests for clean tree, changed tree, and diff-provider failure handling.
      **Notes:** Line 70 documents that diff retrieval is not implemented and currently returns an empty string.

### [WL-6682]

**Title:** Replace KPI placeholder constants with telemetry-derived metrics in `KPIManager`
**Source:** [thegent/src/thegent/execution.py:1047]
**Acceptance checklist:**

- [ ] Compute routing/accuracy/freshness and continuity metrics from persisted run and contract telemetry instead of literals.
- [ ] Define denominator/empty-dataset behavior explicitly to avoid divide-by-zero and misleading defaults.
- [ ] Add deterministic tests for populated and empty session directories.
      **Notes:** Line 1047 is one of several hardcoded KPI values currently marked as placeholders.

### [WL-6683]

**Title:** Add signed-baseline policy drift checks to `DriftDetector.detect_drift`
**Source:** [thegent/src/thegent/governance/drift.py:42]
**Acceptance checklist:**

- [ ] Implement contract/policy baseline hashing and compare current state against signed baseline artifacts.
- [ ] Emit structured mismatch records under `policy_mismatches` with policy key, expected hash, and observed hash.
- [ ] Add tests for no-drift, single-policy mismatch, and baseline-missing behavior.
      **Notes:** Line 42 is a placeholder comment for future hash-based policy drift detection.

### [WL-6684]

**Title:** Replace mocked local-state collection in SyncLoop with real project registry reads
**Source:** [thegent/src/thegent/discovery/sync.py:69]
**Acceptance checklist:**

- [ ] Read concrete local sync inputs (team registry, handoff logs, and recent run summaries) from project state.
- [ ] Normalize and validate payload schema before writing peer inbox files.
- [ ] Add tests covering valid state extraction, missing optional files, and malformed source data.
      **Notes:** Line 69 currently marks local-state collection as a mocked file-read placeholder.

### [WL-6685]

**Title:** Implement `thegent mcp-stdio` command to launch stdio transport end-to-end
**Source:** [thegent/src/thegent/cli/apps/mcp.py:218]
**Acceptance checklist:**

- [ ] Add stdio transport bootstrap that starts MCP service with a stable lifecycle and exit codes.
- [ ] Support essential runtime flags/env passthrough required for local and CI invocation.
- [ ] Add command tests for successful startup, invalid config, and controlled shutdown.
      **Notes:** Line 218 defines `mcp-stdio` as not yet implemented and only prints guidance text.

### [WL-6686]

**Title:** Implement design-token application pipeline for CLI Rich console styling
**Source:** [thegent/src/thegent/design/design_language.py:101]
**Acceptance checklist:**

- [ ] Translate design tokens into concrete Rich theme/style registrations used by CLI renderers.
- [ ] Apply platform-specific overrides consistently through token lookup and style binding.
- [ ] Add tests asserting token-to-style mapping and fallback behavior for missing tokens.
      **Notes:** Line 101 marks `apply_to_cli` as placeholder-only with no style configuration execution.

### [WL-6687]

**Title:** Replace process-random SID mapping with stable persisted SID-to-UID mapping in WSL interop
**Source:** [thegent/src/thegent/infra/wsl_interop.py:117]
**Acceptance checklist:**

- [ ] Implement deterministic mapping that is stable across interpreter restarts and hosts (no raw `hash()` dependence).
- [ ] Persist and reuse mappings to avoid UID churn for previously-seen SIDs.
- [ ] Add tests for deterministic repeat mapping, collision handling, and invalid SID input.
      **Notes:** Line 117 labels the SID mapping as a placeholder and currently derives UIDs from Python hash output.

### [WL-6688]

**Title:** Convert `sync reset` from preview-only stub into transactional reset execution
**Source:** [thegent/src/thegent/commands/sync.py:741]
**Acceptance checklist:**

- [ ] Implement real reset behavior with explicit target set, safety checks, and optional dry-run mode.
- [ ] Record applied changes and failures in `OperationResult.details` instead of `files_would_reset` only.
- [ ] Add command tests for successful reset, permission-denied failure, and no-op behavior.
      **Notes:** Line 741 emits a stub message and intentionally avoids making destructive changes.

### [WL-6689]

**Title:** Implement critical-path and float computation in PERT forward pass
**Source:** [thegent/src/thegent/planning/simulation.py:38]
**Acceptance checklist:**

- [ ] Build topological scheduling to compute earliest/latest times and task-level total float.
- [ ] Mark critical-path tasks based on computed float thresholds rather than defaulting to `False`.
- [ ] Add tests for linear, branching, and disconnected dependency graphs.
      **Notes:** Line 38 identifies `pert_forward_pass` as a D1 stub and currently omits true path analysis.
