### [WL-7550]

**Title:** Preserve markdown fragment read failures in sync discovery instead of silently dropping files
**Source:** [thegent/src/thegent/commands/sync.py:833]
**Acceptance checklist:**

- [ ] Replace silent `OSError` suppression in `_extract_fragments_from_file` with structured warning metadata that includes file path and errno context.
- [ ] Continue scanning remaining files after a read failure so one bad file does not abort fragment discovery.
- [ ] Add tests covering unreadable markdown files and mixed readable/unreadable scan sets.
      **Notes:** Line 833 currently swallows file read failures via `pass`, which hides why fragments are missing.

### [WL-7551]

**Title:** Differentiate invalid sync-target inputs from filesystem creation failures in target resolution
**Source:** [thegent/src/thegent/commands/sync.py:882]
**Acceptance checklist:**

- [ ] Replace broad exception fallback in `_resolve_sync_target` with explicit path-parse, permission, and mkdir failure branches.
- [ ] Preserve `None` return semantics for invalid targets while emitting actionable diagnostics.
- [ ] Add tests for invalid target strings, permission-denied directories, and successful directory creation.
      **Notes:** Line 882 collapses all resolution failures into a generic `None`, obscuring root cause.

### [WL-7552]

**Title:** Split YAML dependency absence from malformed hook-config parsing fallback behavior
**Source:** [thegent/src/thegent/commands/sync.py:901]
**Acceptance checklist:**

- [ ] Replace catch-all hook-config parse fallback with typed handling for missing `yaml` module, YAML parse errors, and schema-shape mismatches.
- [ ] Preserve line-based fallback parsing only for dependency-unavailable paths.
- [ ] Add tests for valid YAML hooks, malformed YAML payloads, and no-PyYAML runtime behavior.
      **Notes:** Line 901 currently routes all errors through fallback parsing, masking malformed config states.

### [WL-7553]

**Title:** Surface `sync_board` failure classes instead of single generic board-sync exception path
**Source:** [thegent/src/thegent/commands/sync.py:1012]
**Acceptance checklist:**

- [ ] Replace broad `sync_board` exception handling with explicit configuration-load, parse, and transport/sync failure branches.
- [ ] Preserve current `OperationResult` contract while adding failure-type metadata in `details`.
- [ ] Add tests for missing board config, malformed work-stream input, and remote sync failures.
      **Notes:** Line 1012 catches all exceptions and returns a flat failure message, reducing observability.

### [WL-7554]

**Title:** Report WORK_STREAM parse read errors instead of silently returning empty item set
**Source:** [thegent/src/thegent/commands/sync.py:1050]
**Acceptance checklist:**

- [ ] Replace silent `OSError` suppression in `_parse_work_stream_items` with structured warning output and context.
- [ ] Preserve non-crashing behavior by returning an empty list on unreadable files while exposing failure metadata.
- [ ] Add tests for missing file, unreadable file, and valid parse scenarios.
      **Notes:** Line 1050 currently swallows read errors, making "no items" indistinguishable from parse failure.

### [WL-7555]

**Title:** Replace board sync API stub contract with concrete GitHub/Linear synchronization path
**Source:** [thegent/src/thegent/commands/sync.py:1059]
**Acceptance checklist:**

- [ ] Implement real `_perform_board_sync` integrations for configured source platforms instead of stub behavior.
- [ ] Return per-item update outcomes with partial-failure accounting in `failed` and `updated_items`.
- [ ] Add integration-style tests for successful sync, auth/config errors, and mixed update results.
      **Notes:** Line 1059 explicitly documents that board sync is currently a stub and not a live API path.

### [WL-7556]

**Title:** Remove hardcoded stub marker from board-sync result payload once real sync is implemented
**Source:** [thegent/src/thegent/commands/sync.py:1076]
**Acceptance checklist:**

- [ ] Drop static `"stub": True` from `_perform_board_sync` output and replace with real execution metadata.
- [ ] Ensure result schema remains backward compatible for callers that consume sync counters.
- [ ] Add tests verifying payload shape for success, partial failure, and platform-not-supported cases.
      **Notes:** Line 1076 hardcodes stub state, preventing consumers from trusting sync completion semantics.

### [WL-7557]

**Title:** Expose plan markdown load failures when hydrating phase/task registry
**Source:** [thegent/src/thegent/integration/plan_system.py:107]
**Acceptance checklist:**

- [ ] Replace silent `OSError` suppression in `_load_plan` with diagnostics that include plan file path and failure class.
- [ ] Preserve empty-plan fallback behavior while recording load failure context for troubleshooting.
- [ ] Add tests for unreadable PLAN file and successful parse of phases/tasks.
      **Notes:** Line 107 currently suppresses load failures and leaves empty in-memory state without diagnostics.

### [WL-7558]

**Title:** Differentiate PLAN_STATUS table parse failures from absent status rows during load
**Source:** [thegent/src/thegent/integration/plan_system.py:149]
**Acceptance checklist:**

- [ ] Replace broad `OSError` suppression in `_load_plan_status` with explicit file-read and table-parse diagnostics.
- [ ] Preserve fallback behavior for missing files while distinguishing malformed status content.
- [ ] Add tests for valid status tables, unreadable files, and malformed markdown table rows.
      **Notes:** Line 149 currently swallows status-load failures, making malformed status docs appear as empty status sets.

### [WL-7559]

**Title:** Preserve WORK_STREAM loader diagnostics when source file cannot be read
**Source:** [thegent/src/thegent/integration/work_stream.py:73]
**Acceptance checklist:**

- [ ] Replace silent `OSError` suppression in `_load_work_stream` with actionable warning output and source path context.
- [ ] Keep existing empty-dataset fallback so workflows continue when file access fails.
- [ ] Add tests for unreadable work-stream files and successful extraction of BACKLOG/CLAIMED/COMPLETED sections.
      **Notes:** Line 73 currently uses `pass` on loader failure, obscuring data-source issues.
