### [WL-6870]

**Title:** Make alias probe failure modes explicit in shell doctor output
**Source:** [thegent/src/thegent/shell_cli.py:177]
**Acceptance checklist:**

- [x] Replace broad alias-probe exception swallowing with typed failure handling.
- [x] Emit a non-fatal doctor issue including actionable failure cause.
- [x] Add tests for success, timeout, and subprocess-failure probe branches.
      **Notes:** Current probe handling at this line can suppress useful diagnostics during shell validation.
- **Evidence:** `tests/test_unit_shell_cli.py`

### [WL-6871]

**Title:** Preserve zsh version probe failure reason in environment diagnostics
**Source:** [thegent/src/thegent/shell_cli.py:481]
**Acceptance checklist:**

- [x] Differentiate timeout, missing binary, and invocation failure for zsh detection.
- [x] Keep doctor execution non-fatal while exposing cause-specific status text.
- [x] Add tests covering successful and degraded zsh detection paths.
      **Notes:** Collapsing all failures into a single unavailable state reduces triage quality.
- **Evidence:** `tests/test_unit_shell_cli.py`

### [WL-6872]

**Title:** Distinguish git-log command errors from legitimate zero-commit windows
**Source:** [thegent/src/thegent/summary.py:61]
**Acceptance checklist:**

- [x] Replace catch-all exception-to-empty behavior with structured failure metadata.
- [x] Preserve explicit empty output semantics for true no-commit ranges.
- [x] Add tests for command failure, non-repo paths, and real empty history.
      **Notes:** This location currently risks under-reporting activity by treating failures as empty results.
- **Evidence:** `thegent/tests/test_wl6872_summary_commits.py`

### [WL-6873]

**Title:** Track malformed summary entry parsing outcomes with bounded diagnostics
**Source:** [thegent/src/thegent/summary.py:78]
**Acceptance checklist:**

- [x] Record malformed-entry counts while continuing line-by-line ingestion.
- [x] Capture bounded sample context for invalid records without noisy logs.
- [x] Add tests with mixed valid and malformed JSONL records.
      **Notes:** Silent parse failure at this path weakens confidence in summary completeness.
- **Evidence:** `tests/test_unit_summary.py`

### [WL-6874]

**Title:** Differentiate native fallback discovery errors from true empty results
**Source:** [thegent/src/thegent/native/discovery_native.py:60]
**Acceptance checklist:**

- [x] Replace generic fallback exception swallowing with explicit degraded-state context.
- [x] Preserve return-shape compatibility while exposing failure classification.
- [x] Add tests for tmux missing, execution errors, and successful fallback parsing.
      **Notes:** Mapping discovery failures to empty sets can mask runtime regressions.
- **Evidence:** `tests/test_unit_native_discovery.py`

### [WL-6875]

**Title:** Emit explicit diagnostics when optimized sendfile copy degrades
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:65]
**Acceptance checklist:**

- [x] Capture fallback activation reason when sendfile transfer fails.
- [x] Preserve copy correctness and metadata behavior across fallback paths.
- [x] Add tests forcing sendfile failure and asserting diagnostic emission.
      **Notes:** Silent optimization fallback obscures performance regressions in file operations.
- **Evidence:** `tests/test_unit_fast_file_ops_wl6716.py`

### [WL-6876]

**Title:** Surface provider discovery probe failures as degraded outcomes
**Source:** [thegent/src/thegent/provider_model_manager.py:506]
**Acceptance checklist:**

- [x] Replace broad exception swallowing with warning-level diagnostic context.
- [x] Distinguish probe failure from legitimately empty provider model catalogs.
- [x] Add tests for transport failures and malformed provider payloads.
      **Notes:** Hidden probe failures can be misread as healthy empty-provider states.
- **Evidence:** `tests/test_unit_provider_model_manager_discovery.py`

### [WL-6877]

**Title:** Preserve subagent enumeration failure signals in session UI data
**Source:** [thegent/src/thegent/ux/session_tui.py:104]
**Acceptance checklist:**

- [x] Replace `except Exception: return []` style handling with explicit degraded signaling.
- [x] Keep UI resilient while surfacing non-fatal warning context.
- [x] Add tests for process-tree enumeration failure and successful enumeration.
      **Notes:** Empty-list fallback at this line can misrepresent active runtime state.
- **Evidence:** `tests/test_unit_session_tui.py`

### [WL-6878]

**Title:** Attach bounded MCP health probe failure context to doctor warnings
**Source:** [thegent/src/thegent/doctor.py:1503]
**Acceptance checklist:**

- [x] Capture categorized error context for timeout, refusal, and HTTP failure outcomes.
- [x] Preserve warning semantics while improving remediation guidance.
- [x] Add tests for timeout, connection-refused, and non-200 health responses.
      **Notes:** Generic unreachable warnings slow diagnosis of MCP availability issues.
- **Evidence:** `thegent/tests/test_unit_doctor_mcp_tools_wl6713.py`

### [WL-6879]

**Title:** Replace randomized SID-to-UID hashing with deterministic mapping
**Source:** [thegent/src/thegent/infra/wsl_interop.py:118]
**Acceptance checklist:**

- [x] Replace process-randomized `hash()` mapping with stable deterministic derivation.
- [x] Define collision handling semantics for SID-to-UID assignment.
- [x] Add reproducibility tests verifying stable mappings across interpreter restarts.
      **Notes:** Current mapping behavior can vary across runs and break deterministic identity translation.
- **Evidence:** `tests/infra/test_wsl_interop.py`
