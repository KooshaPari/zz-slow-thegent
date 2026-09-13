### [WL-7240]

**Title:** Preserve proxy reachability probe failure classes instead of collapsing all transport faults to unreachable
**Source:** [thegent/src/thegent/mgmt_manage.py:34]
**Acceptance checklist:**

- [ ] Replace catch-all reachability suppression with typed timeout, connection, and HTTP protocol failure handling.
- [ ] Preserve boolean reachability contract for healthy proxy responses.
- [ ] Add tests for successful probe, connection refusal, and timeout failure classes.
      **Notes:** Generic reachability fallback hides why Codex+CLIProxy verification fails.

### [WL-7241]

**Title:** Surface Codex thread-metadata query failures during session listing
**Source:** [thegent/src/thegent/prompts.py:115]
**Acceptance checklist:**

- [ ] Replace broad state-db query suppression with typed sqlite open, query, and row-shape handling.
- [ ] Preserve session listing continuity when thread metadata is partially unavailable.
- [ ] Add tests for readable state DB, malformed schema, and inaccessible database paths.
      **Notes:** Silent metadata query drops reduce confidence in project-to-session mapping.

### [WL-7242]

**Title:** Differentiate safe-read filesystem failures from empty-content outcomes in cursor project discovery
**Source:** [thegent/src/thegent/prompts.py:148]
**Acceptance checklist:**

- [ ] Replace catch-all file-read suppression with explicit permission, missing-file, and decode-error branches.
- [ ] Preserve `None` return behavior when candidate files are genuinely absent.
- [ ] Add tests for readable files, unreadable files, and invalid encoding cases.
      **Notes:** Collapsing all read failures to `None` obscures root causes in project-path inference.

### [WL-7243]

**Title:** Preserve per-transcript parse diagnostics during cursor session enumeration
**Source:** [thegent/src/thegent/prompts.py:205]
**Acceptance checklist:**

- [ ] Replace broad transcript-iteration suppression with bounded file-specific diagnostics.
- [ ] Preserve continued enumeration for sibling transcripts after one file fails.
- [ ] Add tests for valid transcript files, malformed JSONL rows, and unreadable transcript files.
      **Notes:** Silent transcript drops can undercount prompt volumes per session.

### [WL-7244]

**Title:** Classify idea-seed extraction failure causes instead of returning null seed records silently
**Source:** [thegent/src/thegent/prompts.py:321]
**Acceptance checklist:**

- [ ] Replace catch-all extraction suppression with explicit frontmatter parse, read, and decode error handling.
- [ ] Preserve successful extraction for well-formed seed files.
- [ ] Add tests for valid seed files, malformed frontmatter, and truncated file content.
      **Notes:** Opaque extraction failures reduce visibility into missing seed inventory.

### [WL-7245]

**Title:** Surface Codex history DB lookup failures during prompt exploration filters
**Source:** [thegent/src/thegent/prompts.py:425]
**Acceptance checklist:**

- [ ] Replace broad `CODEX_STATE_DB` query suppression with typed sqlite connection and query failure branches.
- [ ] Preserve prompt exploration behavior when thread cwd metadata is unavailable.
- [ ] Add tests for successful DB lookup, missing `threads` table, and inaccessible state DB.
      **Notes:** Silent DB lookup failures weaken provenance for project-scoped prompt exploration.

### [WL-7246]

**Title:** Differentiate invalid-JSON detection errors from legacy-format detection in task parser heuristics
**Source:** [thegent/src/thegent/task/parser.py:67]
**Acceptance checklist:**

- [ ] Replace catch-all JSON parse suppression with typed decode error handling in format detection.
- [ ] Preserve legacy and YAML frontmatter detection precedence.
- [ ] Add tests for valid JSON payloads, invalid JSON content, and mixed legacy markers.
      **Notes:** Generic parse suppression can misclassify files and route them to wrong parsers.

### [WL-7247]

**Title:** Preserve task parse failure taxonomy when wrapping parser exceptions
**Source:** [thegent/src/thegent/task/parser.py:114]
**Acceptance checklist:**

- [ ] Replace broad wrapper exception handling with typed propagation for `TaskParseError` versus decode/validation failures.
- [ ] Preserve current user-facing `TaskParseError` contract at call sites.
- [ ] Add tests for YAML errors, JSON decode failures, and unknown format branches.
      **Notes:** Blanket wrapping can flatten actionable parse context needed for remediation.

### [WL-7248]

**Title:** Surface list-command task parse failures as bounded diagnostics instead of silent row omission
**Source:** [thegent/src/thegent/task/cli.py:139]
**Acceptance checklist:**

- [ ] Replace per-file catch-all suppression in task listing with bounded warnings that include filename and failure class.
- [ ] Preserve list output for parseable task files even when some files are malformed.
- [ ] Add tests for all-valid task directories, mixed valid/invalid files, and unreadable task files.
      **Notes:** Silent omission can make backlog views appear healthy while hiding parse regressions.

### [WL-7249]

**Title:** Record per-task sync parse failures when rebuilding WORK_STREAM backlog rows
**Source:** [thegent/src/thegent/task/sync.py:48]
**Acceptance checklist:**

- [ ] Replace per-item catch-all suppression with bounded sync diagnostics keyed by task filename.
- [ ] Preserve successful backlog reconstruction for parseable tasks.
- [ ] Add tests for full sync success, mixed parse failures, and malformed task metadata.
      **Notes:** Suppressed parse failures can silently desynchronize WORK_STREAM from task files.
