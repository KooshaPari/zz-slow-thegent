### [WL-7010]

**Title:** Expose development-mode detection failures in resource path resolution
**Source:** [thegent/src/thegent/resources/__init__.py:64]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression in `get_resource_path` dev-mode detection with typed diagnostics.
- [ ] Preserve non-fatal fallback behavior while distinguishing config import failures from path probing failures.
- [ ] Add tests for dev-mode success, config import failure, and git-root probe failure paths.
      **Notes:** Line 64 currently suppresses all exceptions, obscuring why dev-mode detection was skipped.

### [WL-7011]

**Title:** Preserve installed-resource fallback failure causes in package resource lookup
**Source:** [thegent/src/thegent/resources/__init__.py:98]
**Acceptance checklist:**

- [ ] Replace broad outer exception handling in package resource lookup with typed import/path diagnostics.
- [ ] Keep final filesystem fallback behavior while surfacing whether package lookup or resource access failed.
- [ ] Add tests for package resource success, missing subpackage fallback, and package lookup failure reporting.
      **Notes:** Line 98 catches all exceptions and collapses distinct packaging/resource errors into one silent fallback.

### [WL-7012]

**Title:** Differentiate parent-process introspection failures in current agent ID detection
**Source:** [thegent/src/thegent/discovery/__init__.py:93]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression around parent-process inspection with typed psutil failure handling.
- [ ] Preserve fallback ID generation while recording bounded diagnostics for process-tree probe failures.
- [ ] Add tests for successful parent-agent detection, AccessDenied handling, and no-parent fallback.
      **Notes:** Line 93 suppresses all process-introspection exceptions, making agent-ID provenance opaque.

### [WL-7013]

**Title:** Surface malformed discovery file handling outcomes during discovered-agent listing
**Source:** [thegent/src/thegent/discovery/__init__.py:203]
**Acceptance checklist:**

- [ ] Replace broad parse/IO suppression in `_parse_agent_discovery_file` with typed handling and bounded diagnostics.
- [ ] Preserve stale-file cleanup behavior while distinguishing malformed JSON from unreadable file failures.
- [ ] Add tests for valid discovery records, malformed files, and stale-file cleanup error paths.
      **Notes:** Line 203 currently swallows all parsing and file errors, hiding discovery registry data quality issues.

### [WL-7014]

**Title:** Report session log-path resolution failures in TUI session details
**Source:** [thegent/src/thegent/ux/session_tui.py:123]
**Acceptance checklist:**

- [ ] Replace broad exception suppression around session log-path population with typed diagnostics.
- [ ] Preserve session detail rendering while explicitly marking missing or unresolved log-path metadata.
- [ ] Add tests for valid metadata lookup, missing session metadata, and path resolution failures.
      **Notes:** Line 123 suppresses all exceptions and can silently omit log path metadata in session detail views.

### [WL-7015]

**Title:** Surface native checkpoint parser fallback triggers in JSONL parsing helper
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:38]
**Acceptance checklist:**

- [ ] Replace blanket native parser exception suppression in `parse_checkpoint_by_id` with typed fallback diagnostics.
- [ ] Preserve Python parser fallback behavior while exposing native parser failure categories.
- [ ] Add tests for native parse success, native failure fallback, and malformed checkpoint lines.
      **Notes:** Line 38 catches all native parser exceptions and hides why parsing fell back to Python.

### [WL-7016]

**Title:** Distinguish timestamp decode faults from schema mismatches in circuit failure parsing
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:74]
**Acceptance checklist:**

- [ ] Replace broad JSON/timestamp parse suppression in `parse_circuit_failure` with typed failure classification.
- [ ] Preserve `(0, None)` fallback contract for non-matching rows while surfacing malformed record categories.
- [ ] Add tests for matching failure rows, invalid timestamp values, and malformed JSON lines.
      **Notes:** Line 74 suppresses all parse failures, conflating broken records with legitimate non-matches.

### [WL-7017]

**Title:** Preserve DLQ native parser failure visibility before Python fallback
**Source:** [thegent/src/thegent/execution_jsonl_parsers.py:133]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression around native `parse_dlq_item` calls with typed diagnostics.
- [ ] Preserve Python fallback and `None` semantics while emitting bounded native failure context.
- [ ] Add tests for native parser success, native parser exception fallback, and malformed DLQ input.
      **Notes:** Line 133 currently catches every native parser exception and obscures DLQ fallback causes.

### [WL-7018]

**Title:** Make XML partial-state parse failures observable in validated condensed output
**Source:** [thegent/src/thegent/output_parser.py:550]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression around `IncrementalXMLParser` usage with typed parse/import diagnostics.
- [ ] Preserve validated output behavior while clearly indicating when truncation analysis could not run.
- [ ] Add tests for successful partial-state extraction, parser import failure, and malformed XML handling.
      **Notes:** Line 550 swallows all exceptions and can hide broken truncation classification in validated parsing.

### [WL-7019]

**Title:** Surface run-registry read failures in daily cost rollup calculations
**Source:** [thegent/src/thegent/cost/aggregator.py:115]
**Acceptance checklist:**

- [ ] Replace broad outer exception suppression in `daily_total` with typed file/read diagnostics.
- [ ] Preserve best-effort aggregation while differentiating unreadable registry files from empty datasets.
- [ ] Add tests for valid aggregation, unreadable registry files, and malformed line handling outcomes.
      **Notes:** Line 115 catches all exceptions and can silently return partial or zero totals when registry reads fail.
