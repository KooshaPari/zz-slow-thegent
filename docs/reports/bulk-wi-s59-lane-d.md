### [WL-8500]

**Title:** Preserve sync metrics by separating event decode and metric aggregation
**Source:** [thegent/src/thegent/sync/metrics.py:377]
**Acceptance checklist:**

- [ ] Separate event decode failures from metric aggregation failures.
- [ ] Preserve metrics with decode fallback data.
- [ ] Add tests for decode and aggregation branches.
      **Notes:** Keeps sync observability intact across event format changes.

### [WL-8501]

**Title:** Preserve artifact diff tooling by separating manifest read and diff algorithm
**Source:** [thegent/src/thegent/artifacts/diff_tool.py:417]
**Acceptance checklist:**

- [ ] Separate manifest read failures from diff algorithm failures.
- [ ] Keep diff tooling usable with fallback algorithm.
- [ ] Add tests for manifest and algorithm branches.
      **Notes:** Helps prevent review blockers from one algorithm regression.

### [WL-8502]

**Title:** Preserve config fallback handling by separating schema defaults and environment overrides
**Source:** [thegent/src/thegent/config/fallback.py:288]
**Acceptance checklist:**

- [ ] Separate schema default generation failures from env override failures.
- [ ] Preserve configured env overrides with fallback defaults.
- [ ] Add tests for defaults and override branches.
      **Notes:** Improves startup robustness under config mismatch.

### [WL-8503]

**Title:** Preserve prompt router behavior by separating route inference and context binding
**Source:** [thegent/src/thegent/prompt/router.py:447]
**Acceptance checklist:**

- [ ] Separate route inference failures from context binding failures.
- [ ] Keep context binding fallback on route inference errors.
- [ ] Add tests for inference and binding failures.
      **Notes:** Reduces prompt dispatch errors in dynamic routing setups.

### [WL-8504]

**Title:** Preserve event store indexing by separating key extraction and index write
**Source:** [thegent/src/thegent/events/store_index.py:531]
**Acceptance checklist:**

- [ ] Separate event key extraction failures from index write failures.
- [ ] Preserve event storage with key extraction fallback.
- [ ] Add tests for extraction and index write branches.
      **Notes:** Preserves event retention when keys are partially malformed.

### [WL-8505]

**Title:** Preserve migration safety by separating plan simulation and execution approval
**Source:** [thegent/src/thegent/migrations/safety.py:349]
**Acceptance checklist:**

- [ ] Separate migration plan simulation failures from execution approval failures.
- [ ] Preserve execution safeguards when simulation branch fails.
- [ ] Add tests for simulation and approval failures.
      **Notes:** Reduces risky application of unverified migration plans.

### [WL-8506]

**Title:** Preserve command line plugin loader by separating plugin discovery and command registration
**Source:** [thegent/src/thegent/cli/plugin_registry.py:489]
**Acceptance checklist:**

- [ ] Separate plugin discovery failures from command registration failures.
- [ ] Keep known plugins available when discovery fails.
- [ ] Add tests for discovery and registration branch failures.
      **Notes:** Maintains CLI capabilities despite discovery endpoint blips.

### [WL-8507]

**Title:** Preserve telemetry export by separating file rotate and upload orchestration
**Source:** [thegent/src/thegent/telemetry/export.py:501]
**Acceptance checklist:**

- [ ] Separate telemetry file rotation failures from upload orchestration failures.
- [ ] Preserve upload orchestration with in-memory rotation fallback.
- [ ] Add tests for rotate and upload branches.
      **Notes:** Prevents telemetry backlog growth under rotation defects.

### [WL-8508]

**Title:** Preserve session command aliases by separating alias parse and alias resolution
**Source:** [thegent/src/thegent/commands/aliases.py:356]
**Acceptance checklist:**

- [ ] Separate alias parse failures from alias resolution failures.
- [ ] Preserve default aliases during parser fallback.
- [ ] Add tests for parse and resolution branches.
      **Notes:** Helps users retain familiar command workflows under parser drift.

### [WL-8509]

**Title:** Preserve API request retries by separating retry window calc and actual retry dispatch
**Source:** [thegent/src/thegent/api/retry_policy.py:612]
**Acceptance checklist:**

- [ ] Separate retry window calculation failures from retry dispatch failures.
- [ ] Preserve dispatch fallback with default retry windows.
- [ ] Add tests for window and dispatch branch failures.
      **Notes:** Improves stability of outbound request behavior.
