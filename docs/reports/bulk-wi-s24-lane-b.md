### [WL-6730]

**Title:** Preserve Codex thread-db read failures instead of silently dropping `cwd_map`
**Source:** [thegent/src/thegent/prompts.py:115]
**Acceptance checklist:**

- [ ] Replace blanket exception swallowing around Codex state DB reads with explicit error capture and surfaced diagnostics.
- [ ] Return structured metadata indicating whether `cwd_map` population succeeded, failed, or was skipped.
- [ ] Add tests for valid DB, missing `threads` table, and unreadable DB file paths.
      **Notes:** Line 115 currently catches all exceptions and suppresses failures with `pass`.

### [WL-6731]

**Title:** Differentiate unreadable file errors in `_read_file_safe` from normal missing-content outcomes
**Source:** [thegent/src/thegent/prompts.py:148]
**Acceptance checklist:**

- [ ] Replace broad exception handling with typed read errors that preserve root cause and file path context.
- [ ] Ensure callers can distinguish "file missing", "permission denied", and "decode/read failure".
- [ ] Add tests for each failure class and for successful UTF-8 and non-UTF-8 reads.
      **Notes:** Line 148 currently returns `None` for any exception, collapsing all failure modes.

### [WL-6732]

**Title:** Surface Cursor transcript parse/read failures in `_list_cursor_sessions`
**Source:** [thegent/src/thegent/prompts.py:205]
**Acceptance checklist:**

- [ ] Capture per-transcript ingestion errors with bounded details instead of suppressing them.
- [ ] Keep session discovery resilient while exposing degraded transcript counts to callers.
- [ ] Add tests for malformed JSONL, I/O errors, and mixed healthy/failing transcripts.
      **Notes:** Line 205 currently suppresses all errors and continues with potentially incomplete counts.

### [WL-6733]

**Title:** Add observable extraction failure reporting for `list_idea_seeds`
**Source:** [thegent/src/thegent/prompts.py:321]
**Acceptance checklist:**

- [ ] Replace silent exception fallback in `_extract_seed` with structured error metadata attached to extraction results.
- [ ] Preserve successful seed listing while tracking failed seed files and reason categories.
- [ ] Add tests for malformed frontmatter, unreadable files, and partial-directory success.
      **Notes:** Line 321 currently converts every extraction exception into `None` with no diagnostics.

### [WL-6734]

**Title:** Preserve Codex state DB lookup failures during prompt exploration
**Source:** [thegent/src/thegent/prompts.py:425]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression around `_explore_codex_prompts` DB lookup with explicit failure reporting.
- [ ] Ensure prompt exploration output includes a machine-readable indicator when cwd enrichment fails.
- [ ] Add tests for valid DB enrichment, schema mismatch, and inaccessible DB.
      **Notes:** Line 425 currently drops DB failures silently via `except Exception: pass`.

### [WL-6735]

**Title:** Distinguish tmux fallback probe failures from "no sessions" in discovery
**Source:** [thegent/src/thegent/native/discovery_native.py:60]
**Acceptance checklist:**

- [ ] Replace broad exception-to-empty-list fallback in `_fallback_sessions` with explicit failure-state results.
- [ ] Preserve compatibility for healthy tmux probing while exposing command-exec and parse failure causes.
- [ ] Add tests for tmux unavailable, timeout/exec failure, malformed output, and true empty-session state.
      **Notes:** Line 59 currently returns `[]` on any exception, conflating probe failure with empty state.

### [WL-6736]

**Title:** Report `psutil` import failures in process fallback discovery
**Source:** [thegent/src/thegent/native/discovery_native.py:77]
**Acceptance checklist:**

- [ ] Return typed discovery status when `psutil` import fails instead of silently returning an empty process list.
- [ ] Expose dependency-missing diagnostics to callers for operator remediation.
- [ ] Add tests for successful import, ImportError path, and behavior when pattern filtering is requested.
      **Notes:** Line 77 currently maps all import exceptions to `[]`, hiding dependency state.

### [WL-6737]

**Title:** Preserve native discovery command execution errors in `DiscoveryClient._run`
**Source:** [thegent/src/thegent/native/discovery_native.py:144]
**Acceptance checklist:**

- [ ] Replace blanket exception handling in `_run` with structured error outcomes that capture failure class.
- [ ] Include bounded stderr/return-code context for failed native discovery invocations.
- [ ] Add tests for timeout, OSError, invalid JSON payload, and non-zero exit behavior.
      **Notes:** Line 143 currently returns `None` for all exceptions, obscuring root causes.

### [WL-6738]

**Title:** Differentiate zmx text-list command failure from legitimate empty session set
**Source:** [thegent/src/thegent/session/zmx_backend.py:299]
**Acceptance checklist:**

- [ ] Split `_list_sessions` fallback handling so command execution failures and empty stdout are reported distinctly.
- [ ] Preserve current parsing behavior for successful plain-text output.
- [ ] Add tests for command failure, blank output, and valid single/multi-session text rows.
      **Notes:** Line 299 currently returns `[]` for both command failure and true empty results.

### [WL-6739]

**Title:** Surface non-flag zmx JSON mode failures instead of returning empty results
**Source:** [thegent/src/thegent/session/zmx_backend.py:311]
**Acceptance checklist:**

- [ ] Replace `_list_json` non-unknown-flag fallback with explicit error signaling for execution failures.
- [ ] Keep unsupported-flag behavior (`return None`) for intended text-mode fallback only.
- [ ] Add tests for unknown-flag fallback, execution failure, and successful JSON parsing.
      **Notes:** Line 311 currently returns `[]` for non-flag errors, masking zmx command/runtime failures.
