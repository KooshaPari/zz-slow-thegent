### [WL-6620]

**Title:** Classify conversation dump write failures with deterministic error categories
**Source Path+Line:** [thegent/src/thegent/session/conversation_dumper.py:163]
**Acceptance Checklist:**

- [ ] Replace broad exception wrapping in `dump_conversation` with explicit handling for permission, missing-parent, and encoding/write failures.
- [ ] Preserve raised `OSError` semantics while attaching machine-readable failure context for callers.
- [ ] Add tests covering successful write, permission denial, and invalid output-path scenarios.
      **Notes:** Current generic catch-and-reraise obscures root cause classes needed for reliable retry behavior.

### [WL-6621]

**Title:** Unify markdown and JSON dump listing contract for conversation-scoped queries
**Source Path+Line:** [thegent/src/thegent/session/conversation_dumper.py:232]
**Acceptance Checklist:**

- [ ] Update `list_dumps`/`list_dumps_json` behavior so callers can request both formats without duplicating selection logic.
- [ ] Keep conversation-id filtering and sort-by-mtime behavior consistent across output formats.
- [ ] Add tests for mixed `.md` and `.json` dump directories with and without conversation-id filters.
      **Notes:** The current markdown-only pattern in `list_dumps` creates fragmented listing semantics for downstream tooling.

### [WL-6622]

**Title:** Make Linux platform detection resilient to `/proc/version` read anomalies
**Source Path+Line:** [thegent/src/thegent/thegent_platform.py:41]
**Acceptance Checklist:**

- [ ] Replace silent `OSError` suppression with debug-level diagnostics that record detection fallback path.
- [ ] Preserve WSL detection correctness when `/proc/version` is unreadable but WSL env vars are present.
- [ ] Add tests for readable proc data, unreadable proc file, and non-WSL Linux environments.
      **Notes:** Silent fallback hides platform-probing faults that can later affect runtime/IPC defaults.

### [WL-6623]

**Title:** Add observability and fallback reason reporting for Linux `sendfile` copy path
**Source Path+Line:** [thegent/src/thegent/infra/fast_file_ops.py:63]
**Acceptance Checklist:**

- [ ] Instrument the `sendfile` failure branch with reason metadata before falling back to `shutil` copy.
- [ ] Verify fallback preserves file contents and optional metadata semantics for large files.
- [ ] Add regression tests for successful `sendfile`, forced `sendfile` failure, and metadata-preserving fallback.
      **Notes:** The current silent fallback masks kernel/filesystem incompatibilities and impedes performance diagnostics.

### [WL-6624]

**Title:** Surface partial-size scan degradation when directory traversal errors occur
**Source Path+Line:** [thegent/src/thegent/infra/fast_file_ops.py:164]
**Acceptance Checklist:**

- [ ] Emit a structured indicator when `get_size` returns partial results due to `OSError`/`PermissionError`.
- [ ] Keep the function return type stable while exposing whether totals are complete or degraded.
- [ ] Add tests for full traversal success and permission-restricted subtrees.
      **Notes:** Returning a raw integer after swallowed traversal errors can mislead quota and cache planning logic.

### [WL-6625]

**Title:** Differentiate git-log command failures from empty commit history in summary generation
**Source Path+Line:** [thegent/src/thegent/summary.py:60]
**Acceptance Checklist:**

- [ ] Replace broad exception swallowing in `get_git_commits` with explicit subprocess failure handling.
- [ ] Return or log actionable failure context (command, return code, stderr) without changing caller-facing shape unexpectedly.
- [ ] Add tests for repo without commits, git command failure, and successful commit extraction.
      **Notes:** Current empty-list fallback conflates command failure with legitimate no-commit periods.

### [WL-6626]

**Title:** Preserve auditability when chat-log file reads fail during time-window collection
**Source Path+Line:** [thegent/src/thegent/summary.py:93]
**Acceptance Checklist:**

- [ ] Replace silent exception handling in `_read_log_file` with per-file diagnostics and bounded error reporting.
- [ ] Continue processing other files while clearly marking skipped/corrupt sources.
- [ ] Add tests for malformed JSONL lines, unreadable files, and mixed valid/invalid log sets.
      **Notes:** The current `pass` path can silently drop entire log files, weakening audit completeness guarantees.

### [WL-6627]

**Title:** Enforce lease-file schema validation before lock-state decisions
**Source Path+Line:** [thegent/src/thegent/coordination/file_coordination.py:53]
**Acceptance Checklist:**

- [ ] Replace permissive malformed-lease handling in `claim_lease` with explicit schema validation and repair policy.
- [ ] Ensure corrupted lease records do not incorrectly block or overwrite active locks.
- [ ] Add tests for valid lease, expired lease, malformed lease payload, and concurrent claim attempts.
      **Notes:** Swallowing `IndexError`/`ValueError` can produce ambiguous ownership transitions under contention.

### [WL-6628]

**Title:** Implement runtime-worker log/error forwarding instead of silent drops
**Source Path+Line:** [thegent/src/thegent/infra/multi_runtime_bridge.py:140]
**Acceptance Checklist:**

- [ ] Replace no-op branches in `_forward_logs` with structured stdout/stderr forwarding hooks.
- [ ] Tag forwarded records with runtime identity and severity to support cross-runtime debugging.
- [ ] Add tests for heartbeat-only streams, non-heartbeat stdout lines, and stderr emission paths.
      **Notes:** Ignoring worker output today blocks root-cause analysis for failover and dispatch instability.

### [WL-6629]

**Title:** Guard confidence calibration against corrupt on-disk payload types
**Source Path+Line:** [thegent/src/thegent/ux/calibration.py:42]
**Acceptance Checklist:**

- [ ] Replace broad error fallback in `_load_calibration` with typed JSON/decode/schema validation.
- [ ] Ensure non-dict payloads and non-float bias values are rejected or sanitized deterministically.
- [ ] Add tests for missing file, invalid JSON, wrong top-level type, and valid calibration payloads.
      **Notes:** Returning `{}` on any parse issue silently resets learned bias state and degrades calibration continuity.
