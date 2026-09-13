### [WL-6780]

**Title:** Classify config normalization failures in unified sync bootstrap instead of silent fallback
**Source:** [thegent/src/thegent/integration/unified_config.py:162]
**Acceptance checklist:**

- [ ] Replace broad exception fallback in config normalization with typed failure categories exposed to callers.
- [ ] Preserve successful normalization behavior while surfacing actionable diagnostics for invalid payloads.
- [ ] Add tests for valid config, malformed config blobs, and schema-mismatch inputs.
      **Notes:** Current fallback handling can mask bootstrap configuration defects and delay remediation.

### [WL-6781]

**Title:** Preserve sync discovery retrieval errors as explicit outcomes rather than empty-result success
**Source:** [thegent/src/thegent/discovery/sync.py:70]
**Acceptance checklist:**

- [ ] Replace generic exception suppression in sync discovery with structured error reporting.
- [ ] Distinguish command/transport failures from legitimate no-discovery states.
- [ ] Add tests for healthy retrieval, execution failure, and parse failure branches.
      **Notes:** Collapsing failures into empty outputs obscures runtime regressions in discovery paths.

### [WL-6782]

**Title:** Surface ZKP verification parsing failures with bounded diagnostics
**Source:** [thegent/src/thegent/verification/zkp.py:59]
**Acceptance checklist:**

- [ ] Replace catch-all parse fallback in verification flow with explicit decode/validation error classes.
- [ ] Preserve normal verification behavior for valid payloads while returning failure context for invalid proofs.
- [ ] Add tests for valid proofs, malformed payloads, and missing required fields.
      **Notes:** Silent parse fallback reduces trust in verification outcomes and weakens incident triage.

### [WL-6783]

**Title:** Differentiate sync command execution failures from no-op completion states
**Source:** [thegent/src/thegent/commands/sync.py:654]
**Acceptance checklist:**

- [ ] Replace broad command-level exception handling with typed execution failure results.
- [ ] Preserve caller-facing success behavior for true no-op runs while exposing failed command context.
- [ ] Add tests for successful sync, command subprocess failure, and timeout behavior.
      **Notes:** Current handling can report benign completion where actual execution failed.

### [WL-6784]

**Title:** Report MCP gateway dispatch failures with deterministic error contracts
**Source:** [thegent/src/thegent/mcp/gateway.py:98]
**Acceptance checklist:**

- [ ] Replace blanket dispatch exception suppression with structured failure objects.
- [ ] Include bounded execution context (tool, return code/status, error type) for failed dispatches.
- [ ] Add tests for successful tool dispatch, unknown-tool paths, and transport/runtime failures.
      **Notes:** Hidden gateway failures make MCP health appear better than actual runtime behavior.

### [WL-6785]

**Title:** Track orchestration task-runner failures as first-class execution outcomes
**Source:** [thegent/src/thegent/orchestration/dispatcher.py:385]
**Acceptance checklist:**

- [ ] Replace synthetic-success fallback in task dispatch execution with explicit runner failure propagation.
- [ ] Distinguish blocked/approval-required tasks from hard execution failures.
- [ ] Add tests for runner success, runner exception, and approval-gated blocking.
      **Notes:** Placeholder success behavior can misclassify failed orchestration tasks as completed.

### [WL-6786]

**Title:** Enforce design-language config schema validation before rule application
**Source:** [thegent/src/thegent/design/design_language.py:102]
**Acceptance checklist:**

- [ ] Replace permissive fallback in design-language config loading with strict typed schema checks.
- [ ] Preserve compatibility for valid config files while rejecting malformed entries deterministically.
- [ ] Add tests for valid configs, unknown keys, and invalid value types.
      **Notes:** Implicit fallback semantics can hide invalid rule definitions and cause drift in outputs.

### [WL-6787]

**Title:** Propagate execution pipeline stage failures with stage-level diagnostics
**Source:** [thegent/src/thegent/execution.py:1048]
**Acceptance checklist:**

- [ ] Replace broad stage exception swallowing with explicit stage failure records.
- [ ] Preserve pipeline continuation policy where configured while exposing per-stage error metadata.
- [ ] Add tests for successful runs, recoverable stage failures, and terminal failure behavior.
      **Notes:** Stage failures currently risk being flattened into generic pipeline outcomes.

### [WL-6788]

**Title:** Distinguish learning promotion validation failures from unsupported candidate states
**Source:** [thegent/src/thegent/learning/promotion.py:24]
**Acceptance checklist:**

- [ ] Replace generic failure fallback in promotion checks with explicit validation vs unsupported-state outcomes.
- [ ] Preserve current success behavior while returning deterministic reasons for rejected promotions.
- [ ] Add tests for promotable candidates, invalid metadata, and unsupported-state candidates.
      **Notes:** Failure-mode ambiguity complicates promotion governance and rollback planning.

### [WL-6789]

**Title:** Surface sandbox policy resolution failures instead of permissive ambiguity
**Source:** [thegent/src/thegent/security/sandboxing.py:36]
**Acceptance checklist:**

- [ ] Replace catch-all sandbox policy fallback with typed policy-load and policy-parse errors.
- [ ] Ensure denied/unknown policy states are represented distinctly for callers and telemetry.
- [ ] Add tests for valid policy evaluation, unreadable policy input, and malformed policy definitions.
      **Notes:** Ambiguous fallback behavior can conceal policy misconfiguration in security-critical paths.
