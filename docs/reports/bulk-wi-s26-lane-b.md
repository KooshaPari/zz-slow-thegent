### [WL-6830]

**Title:** Replace silent alias-probe exception handling with observable doctor diagnostics.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:176]
**Acceptance Checklist:**

- [ ] Replace broad alias-probe exception swallowing with typed failure handling.
- [ ] Emit a non-fatal doctor warning entry when alias probing fails.
- [ ] Add tests for successful probe and degraded probe execution branches.
      **Notes:** Silent alias-probe failure can create misleading healthy shell diagnostics.

### [WL-6831]

**Title:** Preserve zsh-version probe failure reason in environment table output.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:479]
**Acceptance Checklist:**

- [ ] Differentiate timeout, missing binary, and subprocess errors when checking zsh version.
- [ ] Keep doctor execution non-fatal while exposing cause-specific status text.
- [ ] Add tests for success and degraded zsh-detection branches.
      **Notes:** Collapsing all exceptions to `Not available` removes actionable triage context.

### [WL-6832]

**Title:** Prevent Nix status false-positives after generic invocation exceptions.
**Source Path+Line:** [thegent/src/thegent/doctor_shell_nix.py:148]
**Acceptance Checklist:**

- [ ] Replace broad fallback exception handling with explicit failure classification.
- [ ] Avoid reporting `ok` status without validated command output.
- [ ] Add tests covering timeout, execution error, and successful version checks.
      **Notes:** Current generic exception path can misclassify unhealthy Nix installs as healthy.

### [WL-6833]

**Title:** Include bounded MCP probe error details in doctor warning output.
**Source Path+Line:** [thegent/src/thegent/doctor.py:1501]
**Acceptance Checklist:**

- [ ] Capture and classify health-check probe failures with bounded error context.
- [ ] Preserve warning semantics while adding actionable remediation detail.
- [ ] Add tests for timeout and connection-refused MCP probe outcomes.
      **Notes:** A generic not-reachable message slows incident triage for MCP tooling.

### [WL-6834]

**Title:** Distinguish git-log execution failures from true zero-commit windows.
**Source Path+Line:** [thegent/src/thegent/summary.py:60]
**Acceptance Checklist:**

- [ ] Replace blanket exception-to-empty behavior with structured failure signaling.
- [ ] Preserve empty-list return only for actual no-commit ranges.
- [ ] Add tests for command failure, non-repository paths, and real empty ranges.
      **Notes:** Returning `[]` for both outcomes can under-report development activity.

### [WL-6835]

**Title:** Track malformed JSON entry counts during summary log parsing.
**Source Path+Line:** [thegent/src/thegent/summary.py:79]
**Acceptance Checklist:**

- [ ] Record parse-failure counts while preserving line-by-line ingestion.
- [ ] Optionally capture bounded sample context for malformed entries.
- [ ] Add tests for mixed valid and malformed JSONL records.
      **Notes:** Silent parse failures hide data-quality regressions in summary outputs.

### [WL-6836]

**Title:** Emit diagnostics when `sendfile` branch degrades to copy fallback.
**Source Path+Line:** [thegent/src/thegent/infra/fast_file_ops.py:64]
**Acceptance Checklist:**

- [ ] Capture fallback activation reason when optimized sendfile copy fails.
- [ ] Preserve functional copy behavior and metadata semantics in fallback mode.
- [ ] Add tests that force sendfile failure and assert diagnostic emission.
      **Notes:** Silent fallback obscures performance regressions for large file operations.

### [WL-6837]

**Title:** Surface provider-model discovery errors instead of suppressing exceptions.
**Source Path+Line:** [thegent/src/thegent/provider_model_manager.py:507]
**Acceptance Checklist:**

- [ ] Replace broad exception swallowing with warning-level diagnostics.
- [ ] Differentiate discovery failure from legitimately empty provider model lists.
- [ ] Add tests for transport failure and malformed model payload handling.
      **Notes:** Hidden discovery errors can be misread as valid empty provider catalogs.

### [WL-6838]

**Title:** Preserve subagent enumeration failure signals in session view resolution.
**Source Path+Line:** [thegent/src/thegent/ux/session_tui.py:103]
**Acceptance Checklist:**

- [ ] Replace catch-all empty-list fallback with structured degraded-state signaling.
- [ ] Keep UI resilience while surfacing explicit subagent collection warnings.
- [ ] Add tests for process-tree enumeration exceptions and normal success.
      **Notes:** Silent fallback to empty subagent lists can misrepresent runtime state.

### [WL-6839]

**Title:** Differentiate network interface query failures from genuine empty inventories.
**Source Path+Line:** [thegent/src/thegent/resources/network.py:159]
**Acceptance Checklist:**

- [ ] Return machine-readable error context when interface enumeration fails.
- [ ] Preserve existing logging while exposing failure-vs-empty distinction.
- [ ] Add tests for psutil exceptions and true no-interface scenarios.
      **Notes:** Shared empty-list behavior masks telemetry failures during diagnostics.
