### [WL-7540]

**Title:** Surface Codex thread-metadata query failure classes during session listing
**Source:** [thegent/src/thegent/prompts.py:115]
**Acceptance checklist:**

- [ ] Replace broad session metadata exception handling with explicit sqlite-open, query, and row-shape failure branches.
- [ ] Preserve session listing behavior when metadata lookup fails for individual records.
- [ ] Add tests for valid metadata lookup, missing table schema, and inaccessible state DB.
      **Notes:** Current handling at line 115 collapses distinct metadata failure modes into one generic branch.

### [WL-7541]

**Title:** Differentiate filesystem read failures from absent-file outcomes in project path probing
**Source:** [thegent/src/thegent/prompts.py:148]
**Acceptance checklist:**

- [ ] Replace catch-all safe-read exception handling with explicit permission, missing-file, and decode-error branches.
- [ ] Preserve `None` return behavior when candidate project files are genuinely absent.
- [ ] Add tests for readable files, unreadable files, and invalid-encoding content.
      **Notes:** The broad catch at line 148 hides root cause when project discovery returns no path.

### [WL-7542]

**Title:** Preserve per-transcript diagnostics during cursor session transcript enumeration
**Source:** [thegent/src/thegent/prompts.py:205]
**Acceptance checklist:**

- [ ] Replace broad per-file transcript exception handling with bounded diagnostics keyed by transcript file.
- [ ] Preserve continued iteration so one malformed transcript does not abort enumeration.
- [ ] Add tests for valid JSONL transcripts, malformed rows, and unreadable transcript files.
      **Notes:** The generic suppression at line 205 silently drops failing transcript files from summaries.

### [WL-7543]

**Title:** Classify idea-seed extraction failures instead of returning null records silently
**Source:** [thegent/src/thegent/prompts.py:321]
**Acceptance checklist:**

- [ ] Replace broad extraction exception handling with explicit frontmatter parse, file-read, and decode failure branches.
- [ ] Preserve successful extraction for well-formed seed files.
- [ ] Add tests for valid seeds, malformed frontmatter, and truncated content.
      **Notes:** Line 321 currently erases failure provenance when seed extraction falls back to `None`.

### [WL-7544]

**Title:** Surface Codex history DB lookup failures in prompt exploration filters
**Source:** [thegent/src/thegent/prompts.py:425]
**Acceptance checklist:**

- [ ] Replace broad DB lookup exception handling with typed sqlite connection, query, and schema failure reporting.
- [ ] Preserve exploration flow when thread metadata is unavailable.
- [ ] Add tests for successful lookup, missing `threads` table, and unreadable DB path.
      **Notes:** The catch-all at line 425 weakens provenance for project-scoped prompt filtering.

### [WL-7545]

**Title:** Preserve benchmark probe failure taxonomy in shell timing runs
**Source:** [thegent/src/thegent/shell_cli.py:262]
**Acceptance checklist:**

- [ ] Replace broad benchmark exception handling with explicit subprocess launch, timeout, and parse-failure branches.
- [ ] Preserve per-iteration continuation so one failed probe does not abort the benchmark loop.
- [ ] Add tests for successful timing capture, timeout failure, and malformed benchmark output.
      **Notes:** At line 262, one generic exception path obscures whether execution or parsing failed.

### [WL-7546]

**Title:** Differentiate metrics file read, parse, and coercion failures in shell reports
**Source:** [thegent/src/thegent/shell_cli.py:341]
**Acceptance checklist:**

- [ ] Replace catch-all metrics exception handling with explicit file-open, row-parse, and integer-coercion branches.
- [ ] Preserve command behavior when metrics are unavailable or malformed.
- [ ] Add tests for valid metrics rows, malformed rows, and non-integer metric values.
      **Notes:** The broad catch at line 341 collapses distinct metrics failure classes.

### [WL-7547]

**Title:** Surface job-registry parse failures separately from PID status probe issues
**Source:** [thegent/src/thegent/shell_cli.py:388]
**Acceptance checklist:**

- [ ] Replace broad job-registry exception handling with explicit unreadable-file, malformed-line, and PID-parse diagnostics.
- [ ] Preserve best-effort status probing for valid registry records.
- [ ] Add tests for valid registry entries, malformed rows, and unreadable registry files.
      **Notes:** Current handling at line 388 makes file-shape and process-probe failures indistinguishable.

### [WL-7548]

**Title:** Classify provider score hydration failures before defaulting to empty score maps
**Source:** [thegent/src/thegent/execution.py:1100]
**Acceptance checklist:**

- [ ] Replace broad provider-score exception handling with explicit file-read, JSON-decode, and schema-shape failure branches.
- [ ] Preserve safe fallback behavior when persisted score data is unavailable.
- [ ] Add tests for valid score payloads, invalid JSON, and structurally invalid score documents.
      **Notes:** The generic catch at line 1100 can mask score-registry corruption as a normal empty-state fallback.

### [WL-7549]

**Title:** Differentiate non-JSON REST payload handling from malformed JSON decode failures
**Source:** [thegent/src/thegent/mcp/rest_to_mcp.py:126]
**Acceptance checklist:**

- [ ] Replace broad response parse exception handling with explicit JSON-decode and text-fallback branches.
- [ ] Preserve text passthrough behavior for intentionally non-JSON endpoints.
- [ ] Add tests for valid JSON responses, plain-text responses, and malformed JSON payloads.
      **Notes:** The catch-all at line 126 hides whether payloads are non-JSON by design or syntactically invalid.
