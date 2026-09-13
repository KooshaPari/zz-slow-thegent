### [WL-7690]

**Title:** Preserve prompt metadata diagnostics by separating sqlite-open, query, and row-shape failures
**Source:** [thegent/src/thegent/prompts.py:115]
**Acceptance checklist:**

- [ ] Replace broad metadata exception handling with explicit sqlite-open, query, and row-shape branches.
- [ ] Preserve session listing behavior when one metadata record fails.
- [ ] Add tests for valid metadata, missing schema, and unreadable DB paths.
      **Notes:** Line 115 currently collapses distinct metadata failure modes into a single fallback path.

### [WL-7691]

**Title:** Differentiate project file discovery failures from expected missing-file outcomes
**Source:** [thegent/src/thegent/prompts.py:148]
**Acceptance checklist:**

- [ ] Replace catch-all safe-read handling with explicit permission, missing-file, and decode-error branches.
- [ ] Preserve `None` returns for legitimately absent project markers.
- [ ] Add tests for readable files, unreadable files, and invalid encoding.
      **Notes:** The broad catch at line 148 hides root cause when project probing returns no match.

### [WL-7692]

**Title:** Keep per-transcript error provenance during session transcript enumeration
**Source:** [thegent/src/thegent/prompts.py:205]
**Acceptance checklist:**

- [ ] Replace generic per-file suppression with bounded diagnostics tagged by transcript filename.
- [ ] Preserve iteration so one malformed transcript does not stop enumeration.
- [ ] Add tests for valid JSONL, malformed rows, and unreadable transcript files.
      **Notes:** Line 205 silently drops failing transcript files without preserving why they failed.

### [WL-7693]

**Title:** Classify idea-seed extraction failures instead of returning null records silently
**Source:** [thegent/src/thegent/prompts.py:321]
**Acceptance checklist:**

- [ ] Replace broad extraction exception handling with explicit read, frontmatter-parse, and decode branches.
- [ ] Preserve successful extraction for well-formed idea seed files.
- [ ] Add tests for valid seeds, malformed frontmatter, and truncated files.
      **Notes:** The catch at line 321 erases failure provenance when extraction falls back to `None`.

### [WL-7694]

**Title:** Surface history DB lookup failures in prompt exploration filters
**Source:** [thegent/src/thegent/prompts.py:425]
**Acceptance checklist:**

- [ ] Replace broad DB lookup exception handling with explicit sqlite-open, query, and schema-shape branches.
- [ ] Preserve exploration flow when thread metadata is unavailable.
- [ ] Add tests for successful lookup, missing `threads` table, and unreadable DB paths.
      **Notes:** The catch-all at line 425 weakens provenance for project-scoped prompt filtering.

### [WL-7695]

**Title:** Differentiate benchmark subprocess launch, timeout, and parse failures in shell timing runs
**Source:** [thegent/src/thegent/shell_cli.py:262]
**Acceptance checklist:**

- [ ] Replace broad benchmark exception handling with explicit launch, timeout, and parse-failure branches.
- [ ] Preserve per-iteration continuation when one probe fails.
- [ ] Add tests for successful capture, timeout failure, and malformed timing output.
      **Notes:** Current handling at line 262 conflates execution and parsing failure classes.

### [WL-7696]

**Title:** Split metrics read, row-parse, and integer-coercion failures in shell reporting
**Source:** [thegent/src/thegent/shell_cli.py:341]
**Acceptance checklist:**

- [ ] Replace catch-all metrics handling with explicit file-open, row-parse, and value-coercion branches.
- [ ] Preserve command behavior when metrics are missing or malformed.
- [ ] Add tests for valid metrics rows, malformed rows, and non-integer values.
      **Notes:** Line 341 currently hides which stage of metrics ingestion failed.

### [WL-7697]

**Title:** Surface job-registry parse failures separately from PID status probe errors
**Source:** [thegent/src/thegent/shell_cli.py:388]
**Acceptance checklist:**

- [ ] Replace broad registry exception handling with explicit unreadable-file, malformed-line, and PID-parse diagnostics.
- [ ] Preserve best-effort status probing for valid registry entries.
- [ ] Add tests for valid rows, malformed rows, and unreadable registry files.
      **Notes:** The generic catch at line 388 makes file-shape and process-probe failures indistinguishable.

### [WL-7698]

**Title:** Expose stale-task escalation dependency failures apart from queue submission failures
**Source:** [thegent/src/thegent/execution.py:878]
**Acceptance checklist:**

- [ ] Replace broad escalation exception handling with dependency-load, queue-init, and enqueue failure branches.
- [ ] Preserve stale-task scan continuity if escalation cannot complete.
- [ ] Add tests for successful escalation, missing escalation module, and queue write failure.
      **Notes:** Line 878 currently routes multiple escalation failure types through one warning path.

### [WL-7699]

**Title:** Preserve provider score hydration diagnostics before defaulting to empty score maps
**Source:** [thegent/src/thegent/execution.py:1079]
**Acceptance checklist:**

- [ ] Replace broad provider-score handling with explicit file-read, JSON-decode, and schema-shape branches.
- [ ] Preserve safe fallback behavior when score data is unavailable.
- [ ] Add tests for valid score payloads, invalid JSON, and invalid score schema.
      **Notes:** The catch-all at line 1079 can mask score-registry corruption as a normal empty fallback.
