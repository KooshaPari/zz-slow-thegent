### [WL-8390]

**Title:** Preserve API schema migration by separating rule generation and migration commit
**Source:** [thegent/src/thegent/schemas/migration.py:417]
**Acceptance checklist:**

- [ ] Separate migration rule generation failures from migration commit failures.
- [ ] Preserve validation state on commit path failures.
- [ ] Add tests for generation and commit branches.
      **Notes:** Prevents schema updates from becoming all-or-nothing.

### [WL-8391]

**Title:** Preserve log archive retention by separating archive listing and cleanup
**Source:** [thegent/src/thegent/logging/archive.py:364]
**Acceptance checklist:**

- [ ] Separate archive listing failures from cleanup failures.
- [ ] Keep cleanup metrics intact when listing is partial.
- [ ] Add tests for listing and cleanup branches.
      **Notes:** Reduces retention backlog when index listing regresses.

### [WL-8392]

**Title:** Preserve event correlation by separating correlation-id parse and timeline build
**Source:** [thegent/src/thegent/events/correlation.py:478]
**Acceptance checklist:**

- [ ] Separate correlation-id parsing failures from timeline construction failures.
- [ ] Preserve event storage while timeline fallback is active.
- [ ] Add tests for id parse and timeline branches.
      **Notes:** Maintains event traceability under partial parsing noise.

### [WL-8393]

**Title:** Preserve config sync by separating remote snapshot fetch and local apply
**Source:** [thegent/src/thegent/config/sync.py:542]
**Acceptance checklist:**

- [ ] Split remote fetch failures from local apply failures.
- [ ] Preserve local config on remote failure with stale-aware warning.
- [ ] Add tests for fetch and apply branch behavior.
      **Notes:** Helps prevent accidental drift when one sync leg fails.

### [WL-8394]

**Title:** Preserve auth context extraction by separating token parse and identity claim merge
**Source:** [thegent/src/thegent/auth/context.py:412]
**Acceptance checklist:**

- [ ] Separate token parse failures from identity claim merge failures.
- [ ] Preserve claims map on merge fallback behavior.
- [ ] Add tests for parse and merge branch failures.
      **Notes:** Enhances resilience to mixed token formats.

### [WL-8395]

**Title:** Preserve queue diagnostics by separating metric extraction and serialization
**Source:** [thegent/src/thegent/queue/diagnostics.py:381]
**Acceptance checklist:**

- [ ] Separate queue metric extraction failures from JSON serialization failures.
- [ ] Preserve diagnostics endpoint for extraction-only failures.
- [ ] Add tests for extraction and serialization behavior.
      **Notes:** Improves diagnostics utility under serializer churn.

### [WL-8396]

**Title:** Preserve artifact download routing by separating URL normalization and stream negotiation
**Source:** [thegent/src/thegent/artifacts/download.py:466]
**Acceptance checklist:**

- [ ] Separate URL normalization failures from stream negotiation failures.
- [ ] Preserve download attempts with normalized fallback URLs.
- [ ] Add tests for each branch.
      **Notes:** Helps keep artifact distribution stable across URL format changes.

### [WL-8397]

**Title:** Preserve command response timeouts by separating timeout config and timer callback
**Source:** [thegent/src/thegent/commands/timeout.py:333]
**Acceptance checklist:**

- [ ] Separate timeout configuration parse failures from timer callback registration failures.
- [ ] Keep default timeout path active on parser failures.
- [ ] Add tests for config and callback branches.
      **Notes:** Improves command stability when config drift appears.

### [WL-8398]

**Title:** Preserve artifact encryption by separating key derivation and cipher initialization
**Source:** [thegent/src/thegent/security/encryption.py:551]
**Acceptance checklist:**

- [ ] Separate key derivation failures from cipher initialization failures.
- [ ] Preserve storage encryption with fallback key material when possible.
- [ ] Add tests for derivation and cipher initialization branches.
      **Notes:** Increases data safety for encryption pipeline regressions.

### [WL-8399]

**Title:** Preserve data merge job by separating key normalization and conflict resolution
**Source:** [thegent/src/thegent/data/merge.py:610]
**Acceptance checklist:**

- [ ] Separate key normalization failures from conflict resolution failures.
- [ ] Preserve merged output with normalized fallback keys.
- [ ] Add tests for normalization and conflict branches.
      **Notes:** Reduces merge corruption from metadata inconsistencies.
