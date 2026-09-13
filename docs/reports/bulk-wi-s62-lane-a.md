### [WL-8620]

**Title:** Preserve command queue handoff by separating command metadata parse and queue assignment
**Source:** [thegent/src/thegent/commands/queueing.py:512]
**Acceptance checklist:**

- [ ] Separate command metadata parsing failures from queue assignment failures.
- [ ] Preserve queue assignment with metadata fallback values.
- [ ] Add tests for parse and assignment branch failures.
      **Notes:** Prevents command dispatch stoppage when one metadata format changes.

### [WL-8621]

**Title:** Preserve sync event tracking by separating event envelope parse and tracking state updates
**Source:** [thegent/src/thegent/sync/event_tracker.py:398]
**Acceptance checklist:**

- [ ] Separate event envelope parsing failures from state update failures.
- [ ] Preserve in-memory sync state when envelope parsing fails.
- [ ] Add tests for parse and state update branches.
      **Notes:** Improves sync observability under partially malformed events.

### [WL-8622]

**Title:** Preserve artifact manifest validation by separating manifest schema and manifest reference checks
**Source:** [thegent/src/thegent/artifacts/manifest_validator.py:457]
**Acceptance checklist:**

- [ ] Separate manifest schema failures from reference validation failures.
- [ ] Preserve manifest acceptance with conservative reference checks.
- [ ] Add tests for schema and reference validation branches.
      **Notes:** Reduces unnecessary artifact rejections during schema drift.

### [WL-8623]

**Title:** Preserve queue metrics export by separating metric filter parse and export serialization
**Source:** [thegent/src/thegent/queue/metrics_export.py:338]
**Acceptance checklist:**

- [ ] Separate metrics filter parse failures from export serialization failures.
- [ ] Keep export operational with default filtering.
- [ ] Add tests for parse and serialization branch coverage.
      **Notes:** Improves debugging signal continuity under filter parser drift.

### [WL-8624]

**Title:** Preserve policy engine resilience by separating policy expression parse and evaluator bootstrap
**Source:** [thegent/src/thegent/policies/executor.py:522]
**Acceptance checklist:**

- [ ] Separate policy expression parse failures from evaluator bootstrap failures.
- [ ] Keep fallback evaluator path active on parse failures.
- [ ] Add tests for expression parse and bootstrap branch handling.
      **Notes:** Prevents full evaluator outages from one expression syntax issue.

### [WL-8625]

**Title:** Preserve session startup by separating startup flag parsing and session registry loading
**Source:** [thegent/src/thegent/session/boot.py:377]
**Acceptance checklist:**

- [ ] Separate startup flag parsing failures from registry loading failures.
- [ ] Preserve startup flow with fallback registry state.
- [ ] Add tests for flag parse and registry load branches.
      **Notes:** Improves startup success in mixed CLI invocation environments.

### [WL-8626]

**Title:** Preserve data export tooling by separating row extraction and export serializer
**Source:** [thegent/src/thegent/export/rows.py:498]
**Acceptance checklist:**

- [ ] Separate row extraction failures from export serializer failures.
- [ ] Preserve partially extracted export data on serializer failures.
- [ ] Add tests for extraction and serializer branches.
      **Notes:** Reduces failed exports from one serializer regression.

### [WL-8627]

**Title:** Preserve plugin runtime status by separating plugin status parse and status cache writes
**Source:** [thegent/src/thegent/plugins/status.py:446]
**Acceptance checklist:**

- [ ] Separate plugin status parse failures from cache write failures.
- [ ] Preserve status cache with parse fallback.
- [ ] Add tests for status parse and cache write branches.
      **Notes:** Maintains accurate status reporting under plugin message drift.

### [WL-8628]

**Title:** Preserve CLI environment checks by separating shell detection and capability probe
**Source:** [thegent/src/thegent/cli/envcheck.py:441]
**Acceptance checklist:**

- [ ] Separate shell type detection failures from capability probe failures.
- [ ] Preserve CLI checks with conservative capability defaults.
- [ ] Add tests for detection and capability probe branches.
      **Notes:** Improves setup guidance under mixed shell environments.

### [WL-8629]

**Title:** Preserve artifact upload by separating upload manifest creation and background upload dispatch
**Source:** [thegent/src/thegent/artifacts/uploader_v2.py:612]
**Acceptance checklist:**

- [ ] Separate upload manifest creation failures from background upload dispatch failures.
- [ ] Preserve dispatch behavior on manifest fallback.
- [ ] Add tests for manifest and dispatch branches.
      **Notes:** Keeps upload throughput under partial manifest generation issues.
