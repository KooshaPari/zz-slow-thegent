### [WL-6580]

**Title:** Replace `sync push` stub response with real remote write execution and result accounting
**Source:** [thegent/src/thegent/commands/sync.py:662]
**Acceptance checklist:**

- [ ] Implement actual push transport that uploads discovered agent and hook files to the configured remote.
- [ ] Populate `OperationResult.details` with real transferred/failed file lists instead of `stub` markers.
- [ ] Add command tests covering successful push, partial failure, and unreachable-remote behavior.
      **Notes:** Line 662 emits a placeholder message and marks the operation as stubbed without performing remote writes.

### [WL-6581]

**Title:** Implement endpoint probe logic in startup validation instead of unconditional reachable status
**Source:** [thegent/src/thegent/integrations/startup_validation.py:47]
**Acceptance checklist:**

- [ ] Replace always-true reachability mapping with per-endpoint network probes and timeout handling.
- [ ] Classify probe outcomes into reachable, timeout, and transport-error states for downstream diagnostics.
- [ ] Add tests for mixed endpoint outcomes so warnings reflect only truly unreachable targets.
      **Notes:** Line 46 documents the current stub behavior that reports every endpoint as reachable.

### [WL-6582]

**Title:** Remove stub-only fork wiring by enforcing persisted snapshot integrity for session forks
**Source:** [thegent/src/thegent/cli/apps/run.py:346]
**Acceptance checklist:**

- [ ] Validate that fork operations persist a new session artifact containing the expected turn cutoff.
- [ ] Surface deterministic CLI errors when source session IDs or turn indices are invalid.
- [ ] Add integration coverage that asserts forked-session replay continuity from the selected turn boundary.
      **Notes:** Line 346 still labels `run fork` as stub wiring, signaling incomplete lifecycle guarantees in the command contract.

### [WL-6583]

**Title:** Harden rollback command path with transactional turn deletion and recovery-safe metadata updates
**Source:** [thegent/src/thegent/cli/apps/run.py:363]
**Acceptance checklist:**

- [ ] Ensure rollback mutates conversation state atomically so partial truncation cannot leave corrupted history.
- [ ] Update session metadata indexes/cursors after rollback and verify they remain consistent.
- [ ] Add tests for rollback by one turn, full rollback-to-empty, and rollback failure recovery.
      **Notes:** Line 363 exposes rollback as stub wiring and should be upgraded to a fully validated state-transition operation.

### [WL-6584]

**Title:** Replace mock synthesizer code generation with provider-backed LLM invocation and structured failure handling
**Source:** [thegent/src/thegent/agents/synthesis.py:69]
**Acceptance checklist:**

- [ ] Swap `_mock_llm_generation` for configurable model-provider calls with prompt and optional spec inputs.
- [ ] Capture generation errors as typed synthesis failures instead of returning synthetic placeholder code.
- [ ] Add tests for successful generation and provider-error fallback behavior in `synthesize`.
      **Notes:** Line 69 currently returns deterministic fake code, which bypasses the actual synthesis pipeline intent.

### [WL-6585]

**Title:** Upgrade agent signing from deterministic mock hash to asymmetric key-based signatures
**Source:** [thegent/src/thegent/agents/identity.py:57]
**Acceptance checklist:**

- [ ] Replace hash-based `sign` implementation with asymmetric signing tied to persisted agent key material.
- [ ] Update `verify` to validate signatures using public keys without access to private-key-derived state.
- [ ] Add tests for valid signatures, tampered payloads, and key mismatch failures.
      **Notes:** Line 57 marks a mocked signer that derives signatures from synthetic key strings rather than cryptographic primitives.

### [WL-6586]

**Title:** Decode captured PNG frames into canonical RGBA buffers for Linux virtual desktop streaming
**Source:** [thegent/src/thegent/automation/providers/linux_virtual_desktop.py:251]
**Acceptance checklist:**

- [ ] Implement PNG decode and pixel-format normalization instead of truncating raw subprocess stdout.
- [ ] Validate decoded dimensions against expected desktop geometry before emitting `ScreenFrame`.
- [ ] Add tests for successful decode, malformed image data, and fallback frame generation paths.
      **Notes:** Line 251 explicitly flags placeholder behavior where PNG bytes are treated as frame bytes without decoding.

### [WL-6587]

**Title:** Implement native DXGI capture path for Windows provider to replace placeholder fallback branch
**Source:** [thegent/src/thegent/automation/providers/windows_virtual_desktop.py:217]
**Acceptance checklist:**

- [ ] Add a real DXGI capture implementation and use it when `_dxgi_available` is true.
- [ ] Emit structured telemetry comparing DXGI and GDI latency/failure rates.
- [ ] Add provider tests that verify DXGI success path and deterministic fallback to GDI on capture errors.
      **Notes:** Line 217 marks the placeholder in `_capture_dxgi`, which currently delegates immediately to slower fallback logic.

### [WL-6588]

**Title:** Implement config synchronization conflict detection and merge-strategy execution
**Source:** [thegent/src/thegent/integration/unified_config.py:162]
**Acceptance checklist:**

- [ ] Build conflict detection across loaded config sources with per-key provenance details.
- [ ] Apply explicit merge strategies (for example precedence or interactive/manual) and persist resolved output.
- [ ] Add tests that validate conflict reporting and deterministic resolution outcomes.
      **Notes:** Line 162 is currently a no-op placeholder in `sync_configs` despite documented merge responsibilities.

### [WL-6589]

**Title:** Replace sitback harness placeholder status with concrete probe states and remediation hints
**Source:** [thegent/src/thegent/sitback_plugins.py:137]
**Acceptance checklist:**

- [ ] Return explicit status variants (`available`, `missing_binary`, `misconfigured`, `probe_error`) from harness checks.
- [ ] Include actionable remediation guidance in status payloads for failed harness activation.
- [ ] Add tests for plugin-load exceptions, missing harness binaries, and enabled-harness success cases.
      **Notes:** Line 136 anchors `_harness_status_placeholder`, which currently collapses several failure modes into generic placeholder output.
