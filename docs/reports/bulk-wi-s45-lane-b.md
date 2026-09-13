### [WL-7780]

**Title:** Classify provider registry load failures by config parse versus provider construction stages
**Source:** [thegent/src/thegent/providers/registry.py:47]
**Acceptance checklist:**

- [ ] Replace broad registry load exception handling with explicit config-parse and provider-construction branches.
- [ ] Preserve successful provider registration order and existing key normalization behavior.
- [ ] Add tests for malformed config input, constructor failure, and successful registry load.
      **Notes:** Current registry errors do not indicate whether failures originate from input parsing or runtime construction.

### [WL-7781]

**Title:** Split tool invocation pipeline failures between argument validation and executor dispatch
**Source:** [thegent/src/thegent/tools/invocation_pipeline.py:132]
**Acceptance checklist:**

- [ ] Replace catch-all invocation pipeline errors with explicit argument-validation and executor-dispatch branches.
- [ ] Preserve successful tool invocation payload shape and response passthrough semantics.
- [ ] Add tests for invalid argument schema, executor dispatch failure, and successful tool execution.
      **Notes:** Consolidated errors obscure whether inputs are invalid or execution routing failed.

### [WL-7782]

**Title:** Differentiate config bootstrap faults across env hydration and required key enforcement
**Source:** [thegent/src/thegent/config/bootstrap.py:59]
**Acceptance checklist:**

- [ ] Replace generic bootstrap exception handling with explicit env-hydration and required-key enforcement branches.
- [ ] Preserve existing default resolution behavior for valid configuration states.
- [ ] Add tests for missing required environment values, malformed overrides, and successful bootstrap.
      **Notes:** Bootstrap diagnostics should identify whether source material is absent or semantically invalid.

### [WL-7783]

**Title:** Separate session recorder failures between event serialization and append-write operations
**Source:** [thegent/src/thegent/session/recorder.py:101]
**Acceptance checklist:**

- [ ] Replace broad recorder exception handling with explicit event-serialization and append-write branches.
- [ ] Preserve successful event ordering and persisted record structure.
- [ ] Add tests for serialization failure, append I/O failure, and successful event persistence.
      **Notes:** A single recorder failure path slows triage for storage versus payload issues.

### [WL-7784]

**Title:** Keep auth token resolution errors typed for cache lookup and signature verification
**Source:** [thegent/src/thegent/auth/token_resolver.py:88]
**Acceptance checklist:**

- [ ] Replace catch-all token resolution exceptions with explicit cache-lookup and signature-verification branches.
- [ ] Preserve successful token resolution contract and downstream identity payload fields.
- [ ] Add tests for cache miss corruption, signature verification failure, and successful token resolution.
      **Notes:** Error collapse currently hides whether failures are retrieval-related or cryptographic.

### [WL-7785]

**Title:** Split CLI command parse failures between flag schema decode and positional argument binding
**Source:** [thegent/src/thegent/cli/command_parser.py:73]
**Acceptance checklist:**

- [ ] Replace generic command parse error handling with explicit flag-schema decode and positional-binding branches.
- [ ] Preserve successful parse output field names and command routing behavior.
- [ ] Add tests for invalid flag values, positional binding mismatch, and successful parse.
      **Notes:** Parse failures should expose whether flags or positional tokens caused the breakdown.

### [WL-7786]

**Title:** Differentiate rate limiter failures across bucket state fetch and quota commit update
**Source:** [thegent/src/thegent/runtime/rate_limiter.py:141]
**Acceptance checklist:**

- [ ] Replace broad rate limiter exception handling with explicit bucket-state fetch and quota-commit branches.
- [ ] Preserve successful allow/deny decisions and current quota math semantics.
- [ ] Add tests for bucket fetch failure, quota commit failure, and successful quota evaluation.
      **Notes:** Unified failures make it difficult to isolate read-side versus write-side limiter regressions.

### [WL-7787]

**Title:** Separate artifact sync failures between manifest generation and object upload stages
**Source:** [thegent/src/thegent/artifacts/sync.py:166]
**Acceptance checklist:**

- [ ] Replace catch-all artifact sync exception handling with explicit manifest-generation and object-upload branches.
- [ ] Preserve successful sync manifest schema and object key naming conventions.
- [ ] Add tests for manifest build failure, upload transport failure, and successful sync.
      **Notes:** Current error grouping masks whether failures occur before or during remote transfer.

### [WL-7788]

**Title:** Classify MCP bridge request failures by envelope decoding versus downstream forward errors
**Source:** [thegent/src/thegent/mcp/bridge.py:94]
**Acceptance checklist:**

- [ ] Replace generic bridge request exception handling with explicit envelope-decoding and downstream-forward branches.
- [ ] Preserve successful request forwarding payload contract and response relay behavior.
- [ ] Add tests for malformed request envelope, forwarder failure, and successful bridge round-trip.
      **Notes:** Bridge observability should distinguish bad inbound payloads from downstream transport issues.

### [WL-7789]

**Title:** Split metrics flush faults between snapshot collection and emitter transport submission
**Source:** [thegent/src/thegent/monitoring/metrics_flush.py:52]
**Acceptance checklist:**

- [ ] Replace broad metrics flush exception handling with explicit snapshot-collection and emitter-submission branches.
- [ ] Preserve successful metric field set and flush cadence behavior.
- [ ] Add tests for snapshot collection failure, emitter transport failure, and successful flush.
      **Notes:** Current metrics failures do not make clear whether collection or emission is at fault.
