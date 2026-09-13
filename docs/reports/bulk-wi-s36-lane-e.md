### [WL-7360]

**Title:** Preserve Codex thread lookup failure visibility during session discovery
**Source:** [thegent/src/thegent/prompts.py:110]
**Acceptance checklist:**

- [ ] Replace broad DB query suppression in `_list_codex_sessions` with typed sqlite connection/query handling.
- [ ] Preserve session enumeration behavior when metadata lookup is unavailable.
- [ ] Add tests for healthy DB reads, missing `threads` table, and inaccessible DB paths.
      **Notes:** Current catch-all handling can hide state-database regressions and silently degrade project mapping.

### [WL-7361]

**Title:** Differentiate safe-read file errors from absent-content outcomes in prompt utilities
**Source:** [thegent/src/thegent/prompts.py:147]
**Acceptance checklist:**

- [ ] Replace catch-all suppression in `_read_file_safe` with explicit file-not-found, permission, and decode branches.
- [ ] Preserve `None` contract for unrecoverable read paths.
- [ ] Add tests for readable files, permission failures, and malformed text payloads.
      **Notes:** Returning `None` for every exception obscures whether data is missing or unreadable.

### [WL-7362]

**Title:** Surface transcript read failures without aborting Cursor session enumeration
**Source:** [thegent/src/thegent/prompts.py:195]
**Acceptance checklist:**

- [ ] Replace broad exception suppression around transcript iteration with bounded per-file diagnostics.
- [ ] Preserve continued processing for sibling transcript files.
- [ ] Add tests for valid transcript parsing, unreadable files, and malformed lines.
      **Notes:** Silent transcript failures reduce confidence in session-level prompt counts.

### [WL-7363]

**Title:** Narrow JSON detection exception handling in task format auto-detection
**Source:** [thegent/src/thegent/task/parser.py:65]
**Acceptance checklist:**

- [ ] Replace blanket `except` in `detect_task_format` with typed JSON decode handling.
- [ ] Preserve existing precedence for YAML frontmatter and legacy detection.
- [ ] Add tests for valid JSON, invalid JSON, and mixed-format content.
      **Notes:** Generic suppression can misclassify files and route them into the wrong parser branch.

### [WL-7364]

**Title:** Preserve parse failure taxonomy when wrapping task parser errors
**Source:** [thegent/src/thegent/task/parser.py:115]
**Acceptance checklist:**

- [ ] Replace broad parse wrapper handling in `parse_task_file` with typed propagation for `TaskParseError` and decode/validation faults.
- [ ] Preserve user-facing `TaskParseError` contract at call sites.
- [ ] Add tests for YAML parse errors, JSON decode failures, and unknown format handling.
      **Notes:** Flattening all parser exceptions reduces remediation precision for malformed task files.

### [WL-7365]

**Title:** Make task list command report per-file parse failures instead of silent omission
**Source:** [thegent/src/thegent/task/cli.py:140]
**Acceptance checklist:**

- [ ] Replace catch-all per-file suppression in task listing with bounded warnings containing filename and failure class.
- [ ] Preserve listing continuity for parseable task files.
- [ ] Add tests for mixed valid/invalid task directories and unreadable files.
      **Notes:** Silent row drops can make backlog views appear healthy while parse errors accumulate.

### [WL-7366]

**Title:** Record sync-stage parse diagnostics while rebuilding task backlog entries
**Source:** [thegent/src/thegent/task/sync.py:49]
**Acceptance checklist:**

- [ ] Replace per-item catch-all suppression in sync reconstruction with structured diagnostics keyed by file.
- [ ] Preserve successful sync for parseable tasks in mixed-quality directories.
- [ ] Add tests for full sync success, partial parse failure, and malformed metadata.
      **Notes:** Hidden parse failures can desynchronize generated backlog artifacts from on-disk tasks.

### [WL-7367]

**Title:** Surface WORK_STREAM detail-extraction failures during migration bootstrap
**Source:** [thegent/src/thegent/task/migrate.py:59]
**Acceptance checklist:**

- [ ] Replace broad suppression around optional WORK_STREAM reads with typed file-not-found, permission, and decode handling.
- [ ] Preserve migration output when enrichment data is unavailable.
- [ ] Add tests for readable WORK_STREAM input, unreadable file paths, and malformed content handling.
      **Notes:** Current catch-all handling can silently drop enrichment context and mask migration environment faults.

### [WL-7368]

**Title:** Differentiate task validation schema errors from runtime evaluation faults
**Source:** [thegent/src/thegent/task/validator.py:72]
**Acceptance checklist:**

- [ ] Replace blanket validation exception suppression with typed schema and coercion error handling.
- [ ] Preserve current pass/fail validation output contract.
- [ ] Add tests for valid tasks, schema violations, and unexpected runtime exceptions.
      **Notes:** Collapsed validation failures reduce operator clarity when triaging invalid task definitions.

### [WL-7369]

**Title:** Preserve unexpected validator failure diagnostics during task file validation
**Source:** [thegent/src/thegent/task/validator.py:130]
**Acceptance checklist:**

- [ ] Replace broad unexpected-error handling in `validate_file` with typed runtime classification and bounded logging context.
- [ ] Preserve `ValidationResult` return contract for parse and non-parse failures.
- [ ] Add tests for parser failures, validator runtime exceptions, and stable error-code mapping.
      **Notes:** Generic unexpected-error wrapping can obscure root cause categories during CI and CLI validation runs.
