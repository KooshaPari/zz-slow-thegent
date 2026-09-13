### [WL-8530]

**Title:** Preserve prompt runtime by separating template variable resolution and runtime validation
**Source:** [thegent/src/thegent/prompt/runtime.py:442]
**Acceptance checklist:**

- [ ] Separate template variable resolution failures from runtime validation failures.
- [ ] Preserve runtime defaults on template resolution failures.
- [ ] Add tests for resolution and runtime validation branches.
      **Notes:** Helps maintain output quality under variable schema drift.

### [WL-8531]

**Title:** Preserve sync plan diagnostics by separating plan parse and diagnostics emission
**Source:** [thegent/src/thegent/sync/diagnostics.py:401]
**Acceptance checklist:**

- [ ] Separate sync plan parse failures from diagnostics emission failures.
- [ ] Preserve diagnostics output with parse fallback.
- [ ] Add tests for plan parse and diagnostics branches.
      **Notes:** Improves operator insight during plan migration.

### [WL-8532]

**Title:** Preserve API key cache by separating key lookup and key decrypt
**Source:** [thegent/src/thegent/security/key_cache.py:366]
**Acceptance checklist:**

- [ ] Separate key lookup failures from key decryption failures.
- [ ] Preserve non-crypto cache path when decryption is unavailable.
- [ ] Add tests for lookup and decryption branches.
      **Notes:** Prevents authentication instability under partial cache failures.

### [WL-8533]

**Title:** Preserve routing health by separating route config parse and route registration
**Source:** [thegent/src/thegent/routing/health.py:332]
**Acceptance checklist:**

- [ ] Separate route config parse failures from route registration failures.
- [ ] Keep existing registrations active on parse errors.
- [ ] Add tests for config and registration branches.
      **Notes:** Keeps routing health checks operational during config transitions.

### [WL-8534]

**Title:** Preserve task state transitions by separating transition validation and state persistence
**Source:** [thegent/src/thegent/tasks/state.py:522]
**Acceptance checklist:**

- [ ] Separate task transition validation failures from state persistence failures.
- [ ] Preserve in-memory transition state if persistence fails.
- [ ] Add tests for validation and persistence branch failures.
      **Notes:** Reduces dropped state changes under persistence pressure.

### [WL-8535]

**Title:** Preserve CLI error visibility by separating internal error aggregation and presentation layer
**Source:** [thegent/src/thegent/cli/errors.py:278]
**Acceptance checklist:**

- [ ] Separate internal error aggregation from presentation rendering.
- [ ] Preserve human-readable errors when render paths fail.
- [ ] Add tests for aggregation and rendering branches.
      **Notes:** Improves operator debugging on rare rendering regressions.

### [WL-8536]

**Title:** Preserve event subscription by separating subscription map parse and subscribe loop
**Source:** [thegent/src/thegent/events/subscription.py:491]
**Acceptance checklist:**

- [ ] Separate subscription map parse failures from subscribe loop failures.
- [ ] Keep active subscriptions available with parse fallback.
- [ ] Add tests for parse and subscribe loop branches.
      **Notes:** Helps event delivery remain stable during schema drift.

### [WL-8537]

**Title:** Preserve artifact validation by separating schema check and semantic validation
**Source:** [thegent/src/thegent/artifacts/validator.py:351]
**Acceptance checklist:**

- [ ] Separate schema validation failures from semantic validation failures.
- [ ] Preserve artifact acceptance with semantic fallback heuristics.
- [ ] Add tests for schema and semantic branches.
      **Notes:** Improves validation resilience on edge-case artifacts.

### [WL-8538]

**Title:** Preserve sync backoff by separating backoff policy parse and scheduler queue
**Source:** [thegent/src/thegent/sync/backoff.py:523]
**Acceptance checklist:**

- [ ] Separate sync backoff policy parse failures from scheduler queue failures.
- [ ] Keep queue scheduling with fallback policy when parse fails.
- [ ] Add tests for policy parse and scheduler queue branches.
      **Notes:** Reduces retry storms under config parsing issues.

### [WL-8539]

**Title:** Preserve metrics export by separating metric filter and sink write
**Source:** [thegent/src/thegent/metrics/export_writer.py:414]
**Acceptance checklist:**

- [ ] Separate metric filter failures from sink write failures.
- [ ] Preserve export payload in filtered-fallback mode.
- [ ] Add tests for filter and sink branch failures.
      **Notes:** Keeps metrics exports useful when one filtering rule is broken.
