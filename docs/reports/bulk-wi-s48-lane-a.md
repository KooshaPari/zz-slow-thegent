### [WL-7920]

**Title:** Add explicit startup phase labels to MCP boot diagnostics
**Source:** [thegent/src/thegent/mcp/launcher.py:128]
**Acceptance checklist:**

- [ ] Emit stable startup phase labels for each MCP boot stage in diagnostics mode.
- [ ] Preserve existing non-diagnostics output and failure exit behavior.
- [ ] Add tests for successful boot labeling, timeout labeling, and early-failure labeling.
      **Notes:** Phase labels should make MCP startup stalls identifiable without extra tracing.

### [WL-7921]

**Title:** Validate profile override keys before config merge
**Source:** [thegent/src/thegent/config/merge.py:117]
**Acceptance checklist:**

- [ ] Reject unknown profile override keys with actionable validation errors.
- [ ] Preserve merge behavior for valid keys and documented precedence rules.
- [ ] Add tests for unknown-key rejection, valid override merge, and empty-override no-op.
      **Notes:** Pre-merge validation prevents ambiguous runtime behavior caused by misspelled keys.

### [WL-7922]

**Title:** Include session command origin in lifecycle audit logs
**Source:** [thegent/src/thegent/cli/session.py:96]
**Acceptance checklist:**

- [ ] Attach origin metadata for start, stop, and restart lifecycle commands.
- [ ] Preserve current lifecycle command semantics and return codes.
- [ ] Add tests for origin field presence, origin value mapping, and missing-origin defaults.
      **Notes:** Origin metadata is required for deterministic auditability across concurrent session actions.

### [WL-7923]

**Title:** Gate task dispatch when worker pool reports draining state
**Source:** [thegent/src/thegent/workers/pool.py:182]
**Acceptance checklist:**

- [ ] Block new task dispatch while the worker pool is explicitly marked draining.
- [ ] Preserve in-flight task completion behavior during draining.
- [ ] Add tests for active dispatch, draining-state rejection, and post-drain resume behavior.
      **Notes:** Dispatch gating avoids race conditions between shutdown and new work admission.

### [WL-7924]

**Title:** Emit normalized workspace path in file-guard rejection errors
**Source:** [thegent/src/thegent/fs/workspace_guard.py:74]
**Acceptance checklist:**

- [ ] Include the normalized candidate path in out-of-scope write rejection messages.
- [ ] Preserve existing allowlist enforcement and successful in-scope writes.
- [ ] Add tests for outside-root rejection detail, inside-root success, and traversal normalization.
      **Notes:** Normalized-path visibility shortens triage for path-rejection incidents.

### [WL-7925]

**Title:** Add deterministic ordering to tool alias registration output
**Source:** [thegent/src/thegent/tools/registry.py:149]
**Acceptance checklist:**

- [ ] Produce alias registration output in deterministic sorted order.
- [ ] Preserve alias conflict detection and hard-fail behavior.
- [ ] Add tests for sorted output stability, duplicate alias failure, and lookup parity.
      **Notes:** Stable ordering prevents noisy diffs in diagnostics and snapshot-based tests.

### [WL-7926]

**Title:** Capture cumulative retry wait in network backoff summaries
**Source:** [thegent/src/thegent/net/backoff.py:103]
**Acceptance checklist:**

- [ ] Include cumulative waited duration in terminal retry summary records.
- [ ] Preserve per-attempt backoff intervals and max-attempt controls.
- [ ] Add tests for immediate success, eventual success, and retry exhaustion summaries.
      **Notes:** Cumulative wait context is needed to quantify latency impact of retry storms.

### [WL-7927]

**Title:** Surface active cache namespace in index rebuild logs
**Source:** [thegent/src/thegent/cache/index.py:196]
**Acceptance checklist:**

- [ ] Emit the resolved cache namespace whenever a rebuild is triggered.
- [ ] Preserve current rebuild trigger conditions and rebuild completion flow.
- [ ] Add tests for namespace logging on mismatch rebuild, missing-index rebuild, and no-rebuild paths.
      **Notes:** Namespace visibility is required when multiple cache scopes coexist in shared environments.

### [WL-7928]

**Title:** Print grouped flaky-test retries in final test runner recap
**Source:** [thegent/src/thegent/test/runner.py:224]
**Acceptance checklist:**

- [ ] Add a final grouped recap for flaky-test retries by test identifier.
- [ ] Preserve existing full test output detail and final exit code behavior.
- [ ] Add tests for zero-retry runs, single-test retries, and multi-test deterministic grouping.
      **Notes:** Retry grouping keeps flaky behavior visible without scanning interleaved logs.

### [WL-7929]

**Title:** Record artifact provenance id in verification failure messages
**Source:** [thegent/src/thegent/artifacts/verify.py:161]
**Acceptance checklist:**

- [ ] Include artifact provenance id in integrity verification failure output.
- [ ] Preserve successful verification behavior and current pass/fail thresholds.
- [ ] Add tests for provenance field presence on mismatch, successful verification silence, and missing-provenance handling.
      **Notes:** Provenance identifiers are required to map integrity failures back to producing pipelines.
