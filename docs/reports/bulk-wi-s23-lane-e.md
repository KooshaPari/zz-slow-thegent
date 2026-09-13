### [WL-6710]

**Title:** Expose alias-audit probe failures in `shell doctor` instead of suppressing them
**Source:** [thegent/src/thegent/shell_cli.py:178]
**Acceptance checklist:**

- [x] Replace blanket exception suppression around the alias probe with targeted handling for timeout and command-launch errors.
- [x] Emit a warning entry in doctor output when alias checks are skipped due to probe failure.
- [x] Add tests that assert normal alias detection still works and failure paths remain non-fatal but visible.
      **Notes:**
- The current `except Exception: pass` can hide shell-level regressions and produce false "healthy" output.
  **Evidence:** `src/thegent/shell_cli.py` now classifies alias-probe failures and records visible diagnostics; covered by `tests/test_wl6700_shell_cli.py` and lane-level WL-6900 coverage.

### [WL-6711]

**Title:** Differentiate zsh absence from execution failure in platform reporting
**Source:** [thegent/src/thegent/shell_cli.py:479]
**Acceptance checklist:**

- [x] Split error handling so missing `zsh`, timeout, and malformed version output are reported as distinct platform statuses.
- [x] Keep command execution non-blocking while preserving actionable diagnostics for each failure class.
- [x] Add CLI tests for success and each fallback status row in the platform table.
      **Notes:**
- Collapsing all exceptions into "Not available" reduces operator visibility during environment triage.
  **Evidence:** Status-specific platform rows implemented in `src/thegent/shell_cli.py`; covered by `tests/test_wl6900_wl6909_lane_e.py`.

### [WL-6712]

**Title:** Harden Nix version detection fallback to avoid incorrect success states
**Source:** [thegent/src/thegent/doctor_shell_nix.py:148]
**Acceptance checklist:**

- [x] Narrow exception handling around `nix --version` and preserve error details for non-timeout failures.
- [x] Distinguish "binary exists but invocation failed" from true positive detection in check results.
- [x] Add tests for timeout, permission, and execution-error cases covering expected status/message transitions.
      **Notes:**
- The current fallback may report Nix as found even when command execution is broken.
  **Evidence:** Categorized `nix --version` failures implemented in `src/thegent/doctor_shell_nix.py`; tested in `tests/test_unit_doctor_shell_nix_wl6712.py`.

### [WL-6713]

**Title:** Report MCP health-check failure causes in `_check_mcp_tools`
**Source:** [thegent/src/thegent/doctor.py:1501]
**Acceptance checklist:**

- [x] Capture exception category and bounded message context when MCP `/health` probing fails.
- [x] Preserve warning semantics but include failure reason in `r.details` for diagnostics tooling.
- [x] Add tests for connection refused, timeout, and malformed response scenarios.
      **Notes:**
- A generic "not reachable" message obscures the remediation path for different outage modes.
  **Evidence:** Detailed probe-failure reason fields added in `src/thegent/doctor.py`; tested in `tests/test_unit_doctor_mcp_tools_wl6713.py`.

### [WL-6714]

**Title:** Preserve git-log invocation errors in `get_git_commits` with structured outcomes
**Source:** [thegent/src/thegent/summary.py:61]
**Acceptance checklist:**

- [x] Replace bare `return []` on exception with a typed result that distinguishes "no commits" from "query failure".
- [x] Include command stderr/exit-code metadata (bounded) for failed git-log calls.
- [x] Update summary callers/tests to handle failure metadata without breaking existing output generation.
      **Notes:**
- Silent fallback to empty commits can under-report work activity and mislead audit consumers.
  **Evidence:** Structured git-log failure metadata added in `src/thegent/summary.py`; tested in `tests/test_unit_summary_wl6714_wl6715.py`.

### [WL-6715]

**Title:** Surface JSONL parse failures in `_parse_log_entry` without aborting log ingestion
**Source:** [thegent/src/thegent/summary.py:79]
**Acceptance checklist:**

- [x] Track parse-error counters and optionally sample malformed lines for diagnostics.
- [x] Keep per-line fault tolerance while exposing aggregate parse quality to callers.
- [x] Add tests for invalid JSON, bad timestamps, and mixed valid/invalid log files.
      **Notes:**
- Current suppression (`except Exception: pass`) hides data-quality drift in session audit logs.
  **Evidence:** Parse-quality counters/samples added in `src/thegent/summary.py`; tested in `tests/test_unit_summary_wl6714_wl6715.py`.

### [WL-6716]

**Title:** Add observable fallback telemetry for Linux `sendfile` copy path
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:65]
**Acceptance checklist:**

- [x] Log or meter when `sendfile` fails and the code falls back to standard copy.
- [x] Preserve existing functional fallback while recording failure reason categories.
- [x] Add tests that force `sendfile` failure and assert fallback correctness plus telemetry emission.
      **Notes:**
- Silent fallback makes performance regressions difficult to detect in large-file workflows.
  **Evidence:** Sendfile fallback telemetry fields/counters added in `src/thegent/infra/fast_file_ops.py`; tested in `tests/test_unit_fast_file_ops_wl6716.py`.

### [WL-6717]

**Title:** Return explicit discovery failure metadata in `discover_models`
**Source:** [thegent/src/thegent/provider_model_manager.py:507]
**Acceptance checklist:**

- [x] Replace silent exception swallowing around CLIProxy model discovery with warning-level diagnostics.
- [x] Return provider discovery status metadata alongside model list so callers can distinguish empty results from probe failures.
- [x] Add tests for connection failure and invalid payload schema.
      **Notes:**
- The current behavior conflates "no models" with "discovery failed," weakening provider onboarding UX.
  **Evidence:** `discover_models(..., include_status=True)` now emits structured `discovery` metadata and warning logs; tests added in `tests/test_unit_provider_model_manager_discovery.py`.

### [WL-6718]

**Title:** Emit recoverable diagnostics when subagent enumeration fails in session TUI
**Source:** [thegent/src/thegent/ux/session_tui.py:103]
**Acceptance checklist:**

- [x] Replace broad exception-to-empty-list fallback with structured warning context tied to session ID.
- [x] Keep UI rendering resilient while displaying a degraded-state indicator in the session view.
- [x] Add tests covering psutil errors and unexpected process-tree failures.
      **Notes:**
- Returning `[]` silently can misrepresent active subagents as absent.
  **Evidence:** `SessionTUI` now records `diagnostics` + `degraded` metadata for subagent/log-path failures and renders a `DEGRADED` badge; tests in `tests/test_unit_session_tui.py`.

### [WL-6719]

**Title:** Distinguish interface-query errors from zero-interface state in `list_interfaces`
**Source:** [thegent/src/thegent/resources/network.py:159]
**Acceptance checklist:**

- [x] Return a result shape that separates "no interfaces" from psutil query failure.
- [x] Preserve existing exception logging while exposing machine-readable error context to callers.
- [x] Add unit tests for psutil exceptions and empty-interface hosts.
      **Notes:**
- Returning a bare empty list for both paths can mask runtime telemetry pipeline failures.
  **Evidence:** `list_interfaces(include_diagnostics=True)` now returns `status/error/interfaces`; tests extended in `tests/resources/test_network.py`.
