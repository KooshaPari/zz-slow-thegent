### [WL-6480]

**Title:** Harden hierarchy task execution result handling at executor dispatch
**Source:** [thegent/src/thegent/agents/hierarchy.py:413]
**Acceptance checklist:**

- [ ] Guard task executor return shape before mutating `result.task_id`.
- [ ] Add a targeted unit test for invalid executor return objects.
- [ ] Preserve current behavior for valid `task_executor` responses.
      **Notes:** Line 413 is the handoff point where executor output is assigned and immediately mutated.

### [WL-6481]

**Title:** Expand image-capable agent registry and enforce option parsing parity
**Source:** [thegent/src/thegent/agents/run_options.py:51]
**Acceptance checklist:**

- [ ] Add missing image-capable agents to `IMAGE_CAPABLE_AGENTS`.
- [ ] Ensure CLI option parsing rejects unsupported image payloads.
- [ ] Add regression coverage for at least one newly allowed and one rejected agent.
      **Notes:** The constant at line 51 controls capability gating for stream-json image flows.

### [WL-6482]

**Title:** Complete default payload scaffold for GitHub project sync write path
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:209]
**Acceptance checklist:**

- [ ] Fill all required default sync payload keys with explicit types.
- [ ] Validate serialization against downstream consumer expectations.
- [ ] Add a fixture-based test for empty-state sync bootstrap.
      **Notes:** The dict block ending at line 209 is part of sync state initialization.

### [WL-6483]

**Title:** Replace SAML bridge placeholder with validated assertion parsing flow
**Source:** [thegent/src/thegent/security/auth_bridge.py:74]
**Acceptance checklist:**

- [ ] Implement structured SAML assertion parsing with signature verification hook points.
- [ ] Fail closed on malformed or unsigned assertions.
- [ ] Add tests for valid, malformed, and replay-like SAML responses.
      **Notes:** Line 74 marks placeholder behavior currently logging-only instead of enforcing trust.

### [WL-6484]

**Title:** Replace static routing estimates with configurable cost/duration heuristics
**Source:** [thegent/src/thegent/routing/task_router.py:197]
**Acceptance checklist:**

- [ ] Externalize estimation factors by task category into config.
- [ ] Ensure estimates include deterministic fallback when config is missing.
- [ ] Add routing tests asserting estimate changes influence route decisions.
      **Notes:** The estimate map at line 197 is currently placeholder logic.

### [WL-6485]

**Title:** Inject sync auditor lifecycle hooks into CLI sync orchestration
**Source:** [thegent/src/thegent/cli/apps/sync.py:328]
**Acceptance checklist:**

- [ ] Wire `SyncAuditor` to pre-sync, per-step, and post-sync checkpoints.
- [ ] Emit actionable audit records on success and failure paths.
- [ ] Add an integration test covering CLI sync with audit output assertions.
      **Notes:** Line 328 instantiates `SyncAuditor`, making it the anchor for orchestration instrumentation.

### [WL-6486]

**Title:** Standardize exception wrapping and recovery signaling in autosync loop
**Source:** [thegent/src/thegent/integrations/workstream_autosync.py:436]
**Acceptance checklist:**

- [ ] Convert broad exception handling into categorized recoverable/non-recoverable paths.
- [ ] Preserve `last_operation` context in error reports.
- [ ] Add tests for retry behavior and terminal failure escalation.
      **Notes:** The exception branch starting after line 436 handles critical autosync failure control flow.

### [WL-6487]

**Title:** Strengthen Ollama provider doctor check with timeout and actionable diagnostics
**Source:** [thegent/src/thegent/doctor.py:1279]
**Acceptance checklist:**

- [ ] Add explicit timeout and endpoint override support for Ollama reachability check.
- [ ] Return remediation hints keyed to connection, auth, and version mismatch failures.
- [ ] Add doctor tests that mock healthy and unhealthy Ollama responses.
      **Notes:** Line 1279 begins the WL-118 provider reachability check used in runtime diagnostics.

### [WL-6488]

**Title:** Make SLO gate script enforceable in CI with explicit exit contract
**Source:** [thegent/scripts/check_slo_gate.py:10]
**Acceptance checklist:**

- [ ] Define documented non-zero exits for each SLO gate violation class.
- [ ] Add machine-readable output mode for CI parsing.
- [ ] Add script-level tests validating exit codes and report schema.
      **Notes:** The trace marker at line 10 anchors script ownership and is a stable insertion point for contract docs.

### [WL-6489]

**Title:** Promote extension metadata check output to structured pass/fail report
**Source:** [thegent/scripts/check_extension_package_metadata.py:162]
**Acceptance checklist:**

- [ ] Emit JSON summary with counts and failing package identifiers.
- [ ] Keep human-readable output while adding deterministic CI mode.
- [ ] Add coverage for missing metadata fields and malformed package manifests.
      **Notes:** Line 162 currently prints summary text and is the right anchor for report contract expansion.
