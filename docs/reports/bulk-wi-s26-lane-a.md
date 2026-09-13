### [WL-6820]

**Title:** Make alias probe failures visible in shell doctor diagnostics
**Source:** [thegent/src/thegent/shell_cli.py:177]
**Acceptance checklist:**

- [ ] Replace blanket alias-probe exception swallowing with targeted timeout/launch handling.
- [ ] Emit a non-fatal doctor issue when probing fails, including actionable failure reason.
- [ ] Add tests for successful probe, timeout, and command-execution failure branches.
      **Notes:** Line 177 currently suppresses all alias-probe failures and can misreport shell health.

### [WL-6821]

**Title:** Distinguish git-log execution failure from true no-commit windows in summary generation
**Source:** [thegent/src/thegent/summary.py:61]
**Acceptance checklist:**

- [ ] Replace catch-all exception-to-empty behavior in commit collection with structured failure metadata.
- [ ] Preserve explicit no-commit output for legitimate empty windows.
- [ ] Add tests for non-repository paths, empty history, and failing git invocation.
      **Notes:** Line 61 returns `[]` for both command failure and legitimate empty results.

### [WL-6822]

**Title:** Preserve malformed log-entry diagnostics during summary parsing
**Source:** [thegent/src/thegent/summary.py:78]
**Acceptance checklist:**

- [ ] Replace generic parse exception swallowing with bounded decode/validation diagnostics.
- [ ] Continue line-by-line ingestion while tracking malformed record counts.
- [ ] Add tests for mixed valid/invalid JSONL records and malformed timestamps.
      **Notes:** Line 79 currently hides parse failures and reduces confidence in summary completeness.

### [WL-6823]

**Title:** Differentiate fallback discovery failure from true empty native session sets
**Source:** [thegent/src/thegent/native/discovery_native.py:60]
**Acceptance checklist:**

- [ ] Replace fallback exception-to-empty behavior with explicit failure context for callers.
- [ ] Preserve return-shape compatibility while distinguishing degraded discovery state.
- [ ] Add tests for tmux absence, execution failure, and successful fallback parsing.
      **Notes:** Line 60 collapses discovery failures into empty results, masking operational regressions.

### [WL-6824]

**Title:** Emit diagnostics when fast file copy degrades from `sendfile` to fallback path
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:65]
**Acceptance checklist:**

- [ ] Capture fallback reason when optimized `sendfile` transfer fails.
- [ ] Preserve existing copy correctness and metadata behavior across fallback.
- [ ] Add tests forcing `sendfile` failure and asserting diagnostic emission.
      **Notes:** Line 65 silently swallows optimization failures and obscures performance regressions.

### [WL-6825]

**Title:** Surface provider model-discovery probe failures as explicit degraded outcomes
**Source:** [thegent/src/thegent/provider_model_manager.py:506]
**Acceptance checklist:**

- [ ] Replace broad exception swallowing with warning-level diagnostics and bounded failure context.
- [ ] Distinguish probe failure from legitimate empty provider catalogs.
- [ ] Add tests for transport failure, malformed payloads, and successful discovery.
      **Notes:** Line 507 suppresses probe errors and can misclassify outages as empty model lists.

### [WL-6826]

**Title:** Preserve subagent-enumeration failure signals in session TUI details
**Source:** [thegent/src/thegent/ux/session_tui.py:104]
**Acceptance checklist:**

- [ ] Replace `except Exception: return []` with explicit degraded-state signaling.
- [ ] Keep UI resilient while surfacing non-fatal warning context.
- [ ] Add tests for process-enumeration failures and successful subagent discovery.
      **Notes:** Line 104 hides enumeration failures and can misrepresent active subagent state.

### [WL-6827]

**Title:** Differentiate network-interface query failures from truly empty interface state
**Source:** [thegent/src/thegent/resources/network.py:158]
**Acceptance checklist:**

- [ ] Replace generic exception-to-empty behavior with machine-readable error context.
- [ ] Preserve logging while exposing deterministic failure shape for callers.
- [ ] Add tests for psutil query exceptions and genuine zero-interface hosts.
      **Notes:** Line 159 collapses telemetry failure and real empty state into identical `[]` output.

### [WL-6828]

**Title:** Attach bounded failure cause to MCP health-check reachability warnings
**Source:** [thegent/src/thegent/doctor.py:1503]
**Acceptance checklist:**

- [ ] Capture error category/details on MCP `/health` probe failures before warning fallback.
- [ ] Preserve warning semantics and remediation hint while improving diagnosability.
- [ ] Add tests for timeout, connection-refused, and non-200 responses.
      **Notes:** Line 1501 currently maps all probe failures to a generic unreachable warning.

### [WL-6829]

**Title:** Replace hash-randomized SID mapping with deterministic cross-process UID derivation
**Source:** [thegent/src/thegent/infra/wsl_interop.py:118]
**Acceptance checklist:**

- [ ] Replace Python `hash()` based SID mapping with stable deterministic digest-based mapping.
- [ ] Define collision handling semantics for SID-to-UID assignment.
- [ ] Add reproducibility tests verifying stable mappings across interpreter restarts.
      **Notes:** Line 119 uses process-randomized hashing and can produce nondeterministic UID mappings.
