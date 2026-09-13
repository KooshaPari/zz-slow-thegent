### [WL-7880]

**Title:** Separate workspace scan failures between root discovery and ignore-rule evaluation
**Source:** [thegent/src/thegent/workspace/scanner.py:67]
**Acceptance checklist:**

- [ ] Replace broad workspace scan exception handling with explicit root-discovery and ignore-rule evaluation branches.
- [ ] Preserve successful scan output ordering and path normalization behavior.
- [ ] Add tests for missing workspace roots, invalid ignore patterns, and successful scan results.
      **Notes:** Scan failures should show whether root resolution or filtering logic failed first.

### [WL-7881]

**Title:** Split command registry load errors between module import and signature binding stages
**Source:** [thegent/src/thegent/commands/registry_loader.py:109]
**Acceptance checklist:**

- [ ] Replace catch-all registry load handling with explicit module-import and signature-binding branches.
- [ ] Preserve successful command registration names and invocation metadata fields.
- [ ] Add tests for import-time failures, binding mismatch failures, and successful registry load.
      **Notes:** Current load failures obscure whether the issue is importability or callable contract shape.

### [WL-7882]

**Title:** Differentiate config merge faults across defaults expansion and user override application
**Source:** [thegent/src/thegent/config/merge.py:82]
**Acceptance checklist:**

- [ ] Replace generic config merge exception handling with explicit defaults-expansion and override-application branches.
- [ ] Preserve successful merged config key precedence and canonical key casing.
- [ ] Add tests for malformed defaults payload, invalid override values, and successful merge output.
      **Notes:** Merged-config errors should identify whether baseline defaults or overrides caused the break.

### [WL-7883]

**Title:** Classify session restore failures by transcript decode versus state rehydration steps
**Source:** [thegent/src/thegent/session/restore.py:144]
**Acceptance checklist:**

- [ ] Replace broad restore exception handling with explicit transcript-decode and state-rehydration branches.
- [ ] Preserve successful restored session identifiers and cursor position semantics.
- [ ] Add tests for malformed transcript data, rehydration contract failures, and successful restore.
      **Notes:** Restore diagnostics should separate bad serialized data from rehydration logic regressions.

### [WL-7884]

**Title:** Split provider selection errors between capability filtering and priority tie-break resolution
**Source:** [thegent/src/thegent/providers/selector.py:58]
**Acceptance checklist:**

- [ ] Replace catch-all provider selection failures with explicit capability-filter and tie-break-resolution branches.
- [ ] Preserve successful provider choice determinism and existing ranking semantics.
- [ ] Add tests for empty capability matches, invalid tie-break inputs, and successful selection.
      **Notes:** Provider routing failures need to distinguish no-match conditions from ranking logic defects.

### [WL-7885]

**Title:** Separate artifact manifest build faults between metadata extraction and checksum computation
**Source:** [thegent/src/thegent/artifacts/manifest_builder.py:121]
**Acceptance checklist:**

- [ ] Replace generic manifest build exception handling with explicit metadata-extraction and checksum-computation branches.
- [ ] Preserve successful manifest schema fields and artifact key naming behavior.
- [ ] Add tests for unreadable metadata sources, checksum calculation failures, and successful manifest generation.
      **Notes:** Manifest failures should indicate whether input metadata or digest calculation is failing.

### [WL-7886]

**Title:** Differentiate MCP bridge response failures across envelope encoding and stream write dispatch
**Source:** [thegent/src/thegent/mcp/response_bridge.py:93]
**Acceptance checklist:**

- [ ] Replace broad response bridge exception handling with explicit envelope-encoding and stream-write-dispatch branches.
- [ ] Preserve successful response envelope fields and downstream delivery contract.
- [ ] Add tests for encoding serialization failures, write dispatch failures, and successful response relay.
      **Notes:** Response-path failures should isolate payload shaping issues from transport emission issues.

### [WL-7887]

**Title:** Classify queue scheduler errors between lease acquisition and runnable task materialization
**Source:** [thegent/src/thegent/queue/scheduler.py:156]
**Acceptance checklist:**

- [ ] Replace catch-all scheduler exception handling with explicit lease-acquisition and task-materialization branches.
- [ ] Preserve successful scheduling order and current fairness semantics.
- [ ] Add tests for lease contention failures, task materialization failures, and successful scheduling cycles.
      **Notes:** Scheduler reliability improves when lock/lease problems are separated from task shaping failures.

### [WL-7888]

**Title:** Split report exporter failures between template render and destination write commit phases
**Source:** [thegent/src/thegent/reports/exporter.py:72]
**Acceptance checklist:**

- [ ] Replace generic exporter exception handling with explicit template-render and destination-write branches.
- [ ] Preserve successful exported report naming and output format invariants.
- [ ] Add tests for render-stage failures, write-stage failures, and successful export completion.
      **Notes:** Export errors should make clear whether content generation or persistence failed.

### [WL-7889]

**Title:** Keep telemetry flush diagnostics typed for batch assembly and transport submission outcomes
**Source:** [thegent/src/thegent/monitoring/telemetry_flush.py:47]
**Acceptance checklist:**

- [ ] Replace broad telemetry flush exception handling with explicit batch-assembly and transport-submission branches.
- [ ] Preserve successful metric batching boundaries and flush interval behavior.
- [ ] Add tests for batch assembly failures, transport submission failures, and successful flush runs.
      **Notes:** Flush diagnostics are more actionable when batch construction and network submission failures are distinct.
