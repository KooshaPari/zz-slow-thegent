### [WL-8220]

**Title:** Separate Playwright recorder startup exception branches by phase
**Source:** [thegent/src/thegent/doc_tools/playwright_recorder.py:250]
**Acceptance checklist:**

- [ ] Split browser startup, context creation, and page opening failures.
- [ ] Preserve existing fallback messaging when startup succeeds.
- [ ] Add tests for each phase failure.
      **Notes:** Improves failure precision in developer recordings.

### [WL-8221]

**Title:** Preserve shell command completion on parse failures
**Source:** [thegent/src/thegent/shell_cli.py:720]
**Acceptance checklist:**

- [ ] Separate argument parse failures from command dispatch failures.
- [ ] Keep completion generation path for parse exceptions.
- [ ] Add tests for parse error and dispatch error inputs.
      **Notes:** Keeps usability when completion logic receives invalid input.

### [WL-8222]

**Title:** Separate clipboard sync failures by read vs write path
**Source:** [thegent/src/thegent/clipboard/history.py:338]
**Acceptance checklist:**

- [ ] Distinguish read failures from write failures during history sync.
- [ ] Preserve sync retries on write failures.
- [ ] Add tests for permission and read errors.
      **Notes:** Improves recovery behavior for mixed IO states.

### [WL-8223]

**Title:** Preserve prompt template handling by splitting parse and apply phases
**Source:** [thegent/src/thegent/prompts.py:275]
**Acceptance checklist:**

- [ ] Separate template parsing and variable interpolation exceptions.
- [ ] Keep fallback prompt when interpolation fails.
- [ ] Add tests for parse and interpolation errors.
      **Notes:** Better attribution for prompt generation issues.

### [WL-8224]

**Title:** Keep borrower telemetry robust while separating serialization and transport failures
**Source:** [thegent/src/thegent/tools/borrow.py:591]
**Acceptance checklist:**

- [ ] Add branches for metrics payload serialization failures and transport failures.
- [ ] Preserve call outcome reporting despite telemetry failures.
- [ ] Add tests for serialization vs transport errors.
      **Notes:** Prevents telemetry issues from masking functional failures.

### [WL-8225]

**Title:** Split queue state fetch decode from metric persistence failures
**Source:** [thegent/src/thegent/queue/state.py:202]
**Acceptance checklist:**

- [ ] Distinguish malformed queue state payloads from persistence layer failures.
- [ ] Preserve polling loop behavior for persistence exceptions.
- [ ] Add tests for each failure class.
      **Notes:** Reduces cascading failures in queue orchestration.

### [WL-8226]

**Title:** Preserve retry engine behavior while splitting strategy parse and runtime backoff failures
**Source:** [thegent/src/thegent/retry/strategy.py:202]
**Acceptance checklist:**

- [ ] Separate strategy config parse exceptions from backoff runtime exceptions.
- [ ] Preserve fallback delay behavior in runtime backoff failures.
- [ ] Add tests for invalid config and runtime timeout failures.
      **Notes:** Keeps retrying deterministic under mixed error conditions.

### [WL-8227]

**Title:** Preserve plugin loader startup by separating manifest and runtime import failures
**Source:** [thegent/src/thegent/ui/plugin_loader.py:372]
**Acceptance checklist:**

- [ ] Split manifest decode failures from runtime plugin import failures.
- [ ] Preserve UI startup fallback when one branch fails.
- [ ] Add tests for decode and import branches.
      **Notes:** Improves plugin onboarding diagnostics.

### [WL-8228]

**Title:** Preserve health endpoint behavior by separating input validation and payload encoding
**Source:** [thegent/src/thegent/health/endpoint.py:271]
**Acceptance checklist:**

- [ ] Isolate request validation errors from output encoding failures.
- [ ] Preserve status responses and headers under encoding errors.
- [ ] Add tests for invalid payload and encoding failures.
      **Notes:** Keeps monitoring stable with clearer failure attribution.

### [WL-8229]

**Title:** Preserve summary collection while separating parse and persistence errors
**Source:** [thegent/src/thegent/summary.py:395]
**Acceptance checklist:**

- [ ] Differentiate JSON parse failures from persistence save failures.
- [ ] Keep summary write contract on parse issues.
- [ ] Add tests for malformed summaries and save failures.
      **Notes:** Maintains resilience when summary payloads are partially invalid.
