### [WL-8690]

**Title:** Preserve API rate-limiting by separating limiter config parse and limiter state updates
**Source:** [thegent/src/thegent/http/rate_limiter.py:412]
**Acceptance checklist:**

- [ ] Separate rate-limit config parse failures from limiter state update failures.
- [ ] Preserve limiter state with fallback defaults.
- [ ] Add tests for config parse and state update branches.
      **Notes:** Keeps rate-limiting responsive under config volatility.

### [WL-8691]

**Title:** Preserve artifact transport by separating transport metadata parse and transport request submit
**Source:** [thegent/src/thegent/artifacts/transport.py:478]
**Acceptance checklist:**

- [ ] Separate transport metadata parse failures from submit request failures.
- [ ] Preserve transport submit with metadata fallback.
- [ ] Add tests for metadata parse and request submit branches.
      **Notes:** Improves artifact flow under transport metadata drift.

### [WL-8692]

**Title:** Preserve command history sync by separating history diff parse and history sync apply
**Source:** [thegent/src/thegent/commands/history_sync.py:333]
**Acceptance checklist:**

- [ ] Separate history diff parse failures from sync apply failures.
- [ ] Preserve sync app for partial diff success cases.
- [ ] Add tests for parse and apply branches.
      **Notes:** Reduces history corruption risk with mixed history diff formats.

### [WL-8693]

**Title:** Preserve policy compliance checks by separating compliance rule parse and compliance action
**Source:** [thegent/src/thegent/compliance/checks.py:589]
**Acceptance checklist:**

- [ ] Separate compliance rule parse failures from compliance action failures.
- [ ] Preserve action fallback under parse failures.
- [ ] Add tests for parse and action branch failures.
      **Notes:** Helps compliance checks remain functional during policy updates.

### [WL-8694]

**Title:** Preserve artifact index integrity by separating index tokenization and index write
**Source:** [thegent/src/thegent/artifacts/index_writer.py:357]
**Acceptance checklist:**

- [ ] Separate artifact tokenization failures from index write failures.
- [ ] Preserve index writes with tokenization fallback.
- [ ] Add tests for tokenization and write branches.
      **Notes:** Keeps artifact lookup available with partial input issues.

### [WL-8695]

**Title:** Preserve queue reconciliation by separating reconciliation diff parse and reconciliation apply
**Source:** [thegent/src/thegent/queue/reconcile.py:522]
**Acceptance checklist:**

- [ ] Separate reconciliation diff parse failures from reconciliation apply failures.
- [ ] Preserve apply path with conservative reconciliation defaults.
- [ ] Add tests for parse and apply branches.
      **Notes:** Improves queue accuracy during reconciliation schema shifts.

### [WL-8696]

**Title:** Preserve API payload handling by separating payload schema parse and payload routing
**Source:** [thegent/src/thegent/api/payload_router.py:423]
**Acceptance checklist:**

- [ ] Separate payload schema parse failures from payload routing failures.
- [ ] Preserve routing with fallback paths.
- [ ] Add tests for parse and routing branches.
      **Notes:** Keeps API dispatch alive when payloads vary.

### [WL-8697]

**Title:** Preserve dashboard updates by separating dashboard payload parse and dashboard render
**Source:** [thegent/src/thegent/ui/dashboard.py:531]
**Acceptance checklist:**

- [ ] Separate dashboard payload parse failures from dashboard render failures.
- [ ] Preserve render with fallback payloads.
- [ ] Add tests for parse and render branch failures.
      **Notes:** Helps UI reliability when dashboard schemas evolve.

### [WL-8698]

**Title:** Preserve queue worker scale by separating scale policy parse and scale action
**Source:** [thegent/src/thegent/queue/scale.py:477]
**Acceptance checklist:**

- [ ] Separate scale policy parse failures from scale action failures.
- [ ] Preserve scale action defaults on parse failures.
- [ ] Add tests for scale policy parse and scale actions.
      **Notes:** Avoids worker instability during policy config updates.

### [WL-8699]

**Title:** Preserve artifact migration scheduling by separating migration schedule parse and migration enqueue
**Source:** [thegent/src/thegent/artifacts/migration_scheduler.py:333]
**Acceptance checklist:**

- [ ] Separate migration schedule parse failures from migration enqueue failures.
- [ ] Preserve migration enqueue with schedule fallback.
- [ ] Add tests for schedule parse and enqueue branches.
      **Notes:** Improves artifact migration timing resilience.
