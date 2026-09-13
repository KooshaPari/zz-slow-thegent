### [WL-6880]

**Title:** Replace blanket alias-probe exception swallowing with actionable shell diagnostics.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:176]
**Acceptance Checklist:**

- [x] Replace broad alias-probe `except Exception` handling with classified timeout/process failure outcomes.
- [x] Emit a non-fatal doctor warning entry that preserves probe failure reason.
- [x] Add tests for successful probe, timeout, and subprocess failure branches.
      **Notes:** Silent alias probe failures can misreport shell health as fully operational.

### [WL-6881]

**Title:** Preserve zsh-version probe failure cause in doctor environment reporting.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:479]
**Acceptance Checklist:**

- [x] Differentiate timeout, missing binary, and subprocess errors during zsh version checks.
- [x] Keep doctor execution non-fatal while exposing cause-specific status text.
- [x] Add tests for successful detection and degraded probe scenarios.
      **Notes:** Collapsing all failures to `Not available` hides remediation direction.

### [WL-6882]

**Title:** Distinguish git-log invocation failure from true empty commit windows.
**Source Path+Line:** [thegent/src/thegent/summary.py:60]
**Acceptance Checklist:**

- [x] Replace blanket exception fallback with structured command-failure signaling.
- [x] Preserve empty-list output only for legitimate no-commit ranges.
- [x] Add tests for non-repo paths, git command failures, and valid empty windows.
      **Notes:** Returning `[]` for both failure and empty windows under-reports activity issues.

### [WL-6883]

**Title:** Track malformed summary JSONL records instead of silently skipping parse failures.
**Source Path+Line:** [thegent/src/thegent/summary.py:79]
**Acceptance Checklist:**

- [x] Record parse-failure counts while maintaining line-by-line ingestion.
- [x] Include bounded malformed-record context for diagnostics.
- [x] Add tests for mixed valid and malformed summary lines.
      **Notes:** Silent JSON parse drops reduce confidence in generated summary completeness.

### [WL-6884]

**Title:** Preserve fallback session discovery failure context instead of returning empty lists.
**Source Path+Line:** [thegent/src/thegent/native/discovery_native.py:59]
**Acceptance Checklist:**

- [x] Replace catch-all empty-list fallback with typed subprocess failure reporting.
- [x] Differentiate true no-session states from discovery execution failures.
- [x] Add tests for successful fallback discovery, timeout, and command failure paths.
      **Notes:** Empty-list failure collapse masks runtime discovery regressions.

### [WL-6885]

**Title:** Emit diagnostics when optimized `sendfile` copy path degrades to fallback.
**Source Path+Line:** [thegent/src/thegent/infra/fast_file_ops.py:64]
**Acceptance Checklist:**

- [x] Capture and expose fallback activation reason when `sendfile` raises.
- [x] Preserve file-copy correctness and metadata behavior in fallback mode.
- [x] Add tests forcing `sendfile` failure and asserting diagnostic emission.
      **Notes:** Silent fallback obscures performance regressions in large file operations.

### [WL-6886]

**Title:** Surface provider model-discovery probe failures as explicit degraded outcomes.
**Source Path+Line:** [thegent/src/thegent/provider_model_manager.py:507]
**Acceptance Checklist:**

- [x] Replace broad exception swallowing with warning-level, bounded failure diagnostics.
- [x] Differentiate transport/protocol failures from legitimately empty provider catalogs.
- [x] Add tests for malformed payload, transport failure, and successful discovery branches.
      **Notes:** Hidden discovery errors can be misinterpreted as valid empty model sets.

### [WL-6887]

**Title:** Preserve subagent enumeration failure signals in session detail rendering.
**Source Path+Line:** [thegent/src/thegent/ux/session_tui.py:103]
**Acceptance Checklist:**

- [x] Replace catch-all empty-list fallback with explicit degraded-state signaling.
- [x] Keep UI resilient while surfacing non-fatal subagent collection warnings.
- [x] Add tests for successful enumeration and exception paths.
      **Notes:** Silent fallback to empty subagent lists can misrepresent active runtime state.

### [WL-6888]

**Title:** Distinguish network interface query failures from genuine empty-interface hosts.
**Source Path+Line:** [thegent/src/thegent/resources/network.py:159]
**Acceptance Checklist:**

- [x] Replace generic exception-to-empty behavior with machine-readable error context.
- [x] Preserve logging while exposing deterministic failure-vs-empty state.
- [x] Add tests for psutil query exceptions and true no-interface scenarios.
      **Notes:** Shared empty-list outputs hide telemetry acquisition failures.

### [WL-6889]

**Title:** Preserve pending-message poll failure details rather than returning silent empties.
**Source Path+Line:** [thegent/src/thegent/execution.py:1806]
**Acceptance Checklist:**

- [x] Replace broad `except Exception: return []` with structured degraded-result signaling.
- [x] Emit bounded diagnostics when session metadata lookup or registry loading fails.
- [x] Add tests for missing metadata, parser errors, and successful pending-message retrieval.
      **Notes:** Silent empty returns can mask failures in message-delivery control flow.
