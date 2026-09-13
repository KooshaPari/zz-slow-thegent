### [WL-6530]

**Title:** Validate `task_executor` contract before mutating task result fields
**Source:** [thegent/src/thegent/agents/hierarchy.py:413]
**Acceptance checklist:**

- [ ] Add explicit shape/type checks for `task_executor` return values before assigning `task_id`/`agent_id`.
- [ ] Raise a deterministic error when executor output is missing required `TaskResult` fields.
- [ ] Add targeted unit coverage for valid and invalid executor return objects.
      **Notes:** Line 413 is the executor handoff where the returned object is assumed mutable and well-formed.

### [WL-6531]

**Title:** Centralize image-capability gating so CLI and stream-json paths cannot drift
**Source:** [thegent/src/thegent/agents/run_options.py:52]
**Acceptance checklist:**

- [ ] Move agent image capability rules into a single source used by all input-format paths.
- [ ] Reject image payloads with a clear error for agents not in the supported set.
- [ ] Add regression tests that cover one supported and one unsupported image-capable agent.
      **Notes:** Line 52 defines `IMAGE_CAPABLE_AGENTS`, which is the contract anchor for image-input eligibility.

### [WL-6532]

**Title:** Implement real GitHub CSV import path instead of mock import response
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:359]
**Acceptance checklist:**

- [ ] Replace TODO/mock response with actual `gh` project item creation/update behavior from CSV rows.
- [ ] Surface row-level validation failures with actionable error payloads.
- [ ] Add integration-style tests that verify imported item counts and error handling.
      **Notes:** Line 359 marks the current TODO that short-circuits import behavior with a zero-result stub.

### [WL-6533]

**Title:** Replace SAML bridge placeholder with verified assertion parsing and claim mapping
**Source:** [thegent/src/thegent/security/auth_bridge.py:74]
**Acceptance checklist:**

- [ ] Implement SAML response parsing that validates required assertion structure and issuer fields.
- [ ] Fail closed on malformed or unverifiable assertions instead of returning static claims.
- [ ] Add tests for valid assertions and representative malformed/replay-like responses.
      **Notes:** Line 74 explicitly documents placeholder SAML handling and currently returns hardcoded claims.

### [WL-6534]

**Title:** Replace placeholder routing estimates with configurable scoring inputs
**Source:** [thegent/src/thegent/routing/task_router.py:197]
**Acceptance checklist:**

- [ ] Move duration/cost estimate constants to typed configuration inputs.
- [ ] Preserve deterministic category assignment when config is incomplete.
- [ ] Add routing tests showing estimate changes alter route selection outcomes.
      **Notes:** Line 197 starts the hardcoded estimate map used for duration and cost predictions.

### [WL-6535]

**Title:** Wire `sync audit` to real config sources instead of empty stub values
**Source:** [thegent/src/thegent/cli/apps/sync.py:330]
**Acceptance checklist:**

- [ ] Load enabled connectors, quotas, and policy modes from runtime settings/env-backed config.
- [ ] Keep `json` and `table` output modes behaviorally consistent with loaded values.
- [ ] Add command tests that assert populated audit output from non-empty config.
      **Notes:** Line 330 begins a stub block that currently forces empty connector/quota/policy data.

### [WL-6536]

**Title:** Implement Linear read-back status reconciliation in autosync runner
**Source:** [thegent/src/thegent/integrations/workstream_autosync.py:495]
**Acceptance checklist:**

- [ ] Replace read-path stub with actual Linear status fetch and mapping into local workstream items.
- [ ] Update `items_successful`/`items_failed` counters based on per-item reconciliation outcomes.
- [ ] Add tests for successful reconciliation and error escalation behavior.
      **Notes:** Line 495 marks the placeholder branch that logs a stub message without applying remote updates.

### [WL-6537]

**Title:** Make Ollama doctor probe endpoint and timeout configurable with structured failure codes
**Source:** [thegent/src/thegent/doctor.py:1301]
**Acceptance checklist:**

- [ ] Add environment/config support for Ollama base URL and probe timeout.
- [ ] Normalize connection/timeout/HTTP failures into stable diagnostic categories.
- [ ] Add doctor tests for healthy endpoint, timeout, and unreachable-host scenarios.
      **Notes:** Line 1301 hardcodes the probe endpoint and timeout, limiting deployment portability.

### [WL-6538]

**Title:** Remove implicit sample-metrics fallback from dashboard renderer for CI reliability
**Source:** [thegent/scripts/render_slo_dashboard.py:47]
**Acceptance checklist:**

- [ ] Replace auto-sample fallback with explicit `--allow-sample` opt-in behavior.
- [ ] Fail with a clear non-zero exit when metrics input is missing in strict/CI mode.
- [ ] Add script tests for strict failure mode and opt-in sample generation mode.
      **Notes:** Line 47 currently returns synthetic metrics, which can mask missing telemetry during automated runs.

### [WL-6539]

**Title:** Surface parse/read failures when collecting oversized functions instead of silently dropping files
**Source:** [thegent/scripts/collect_loc_metrics.py:47]
**Acceptance checklist:**

- [ ] Track file-level parse/read failures in the output report with filename and error type.
- [ ] Keep oversized-function collection running for valid files while reporting partial failure.
- [ ] Add tests covering syntax-error files and read-error paths in metrics output.
      **Notes:** Line 47 currently swallows `OSError`/`SyntaxError` and returns an empty result, hiding data-quality issues.
