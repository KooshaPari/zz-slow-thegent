### [WL-7620]

**Title:** Replace broad replay parse failure handling with typed JSON/schema classification
**Source:** [thegent/src/thegent/output_parser.py:279]
**Acceptance checklist:**

- [ ] Split decode errors from schema-shape errors in the line parser path at this call site.
- [ ] Preserve current successful parse output shape for valid replay lines.
- [ ] Add focused tests for malformed JSON, missing keys, and valid objects.
      **Notes:** The current broad exception path obscures the boundary between bad input and code-level parser defects.

### [WL-7621]

**Title:** Remove silent suppression in partial output parsing and emit explicit invalid-line outcomes
**Source:** [thegent/src/thegent/output_parser.py:552]
**Acceptance checklist:**

- [ ] Replace blanket `except Exception` suppression with explicit decode/validation branches.
- [ ] Keep parser iteration resilient so one bad line does not abort the full stream.
- [ ] Add tests that assert observable handling for malformed lines and clean passthrough for valid lines.
      **Notes:** Silent suppression at this site reduces debuggability and can hide recurring upstream format regressions.

### [WL-7622]

**Title:** Harden cache entry hydration around ISO timestamp parsing invariants
**Source:** [thegent/src/thegent/cache/frecency.py:313]
**Acceptance checklist:**

- [ ] Validate required timestamp fields before `fromisoformat` conversion during cache load.
- [ ] Preserve current behavior for valid persisted entries and ordering calculations.
- [ ] Add tests for missing fields, non-string timestamp values, and valid persisted payloads.
      **Notes:** This conversion currently assumes strict payload shape and can fail noisily on corrupted cache records.

### [WL-7623]

**Title:** Enforce explicit environment file decoding and error context in secrets CLI loader
**Source:** [thegent/src/thegent/secrets/cli.py:88]
**Acceptance checklist:**

- [ ] Open env files with explicit encoding and emit actionable error context on parse failure.
- [ ] Preserve existing secret discovery and listing semantics.
- [ ] Add tests for valid env files, invalid encodings, and malformed key-value lines.
      **Notes:** The loader currently relies on implicit defaults and limited failure diagnostics.

### [WL-7624]

**Title:** Centralize provider model I/O file operations with atomic write semantics
**Source:** [thegent/src/thegent/provider_model_manager_io.py:30]
**Acceptance checklist:**

- [ ] Introduce atomic write behavior for persisted model-manager state to avoid partial file corruption.
- [ ] Preserve current JSON schema and read compatibility for existing files.
- [ ] Add tests for normal writes and interrupted/failed write simulation.
      **Notes:** Direct writes at this location can leave truncated files if process interruption happens mid-write.

### [WL-7625]

**Title:** Validate mesh claim payload schema before lock state transitions
**Source:** [thegent/src/thegent/mesh/coordination.py:85]
**Acceptance checklist:**

- [ ] Enforce minimal required claim fields and types when loading claim files.
- [ ] Preserve existing lock-acquisition semantics for well-formed claims.
- [ ] Add tests for malformed claim files, stale claims, and valid claim progression.
      **Notes:** Unvalidated claim payloads can create inconsistent lock lifecycle behavior across agents.

### [WL-7626]

**Title:** Strengthen pre-warming worker error taxonomy for deterministic retry decisions
**Source:** [thegent/src/thegent/cache/pre_warmer.py:170]
**Acceptance checklist:**

- [ ] Classify transient vs non-transient failures instead of collapsing into one generic exception path.
- [ ] Preserve current scheduling cadence and successful warm completion behavior.
- [ ] Add tests proving retry behavior only occurs for explicitly transient failures.
      **Notes:** Broad exception handling here makes retry policy opaque and harder to tune safely.

### [WL-7627]

**Title:** Replace generic adapter exception wrapping with typed contract adaptation failures
**Source:** [thegent/src/thegent/contracts/adapters.py:233]
**Acceptance checklist:**

- [ ] Convert generic exception wrapping into typed adaptation errors with source-context details.
- [ ] Preserve successful adapter transformations and output schema guarantees.
- [ ] Add tests for invalid input payloads and valid adaptation paths.
      **Notes:** Generic exception handling currently weakens observability for contract migration defects.

### [WL-7628]

**Title:** Tighten helios bridge initialization error signaling around dependency and transport setup
**Source:** [thegent/src/thegent/mesh/helios_bridge.py:26]
**Acceptance checklist:**

- [ ] Separate dependency import/setup failures from runtime transport failures.
- [ ] Preserve normal bridge startup flow and existing happy-path behavior.
- [ ] Add tests for missing dependencies and transport handshake failures.
      **Notes:** Coarse exception handling at initialization time makes operator triage slower during startup incidents.

### [WL-7629]

**Title:** Eliminate silent config ingestion bypass in unified config builder
**Source:** [thegent/src/thegent/integration/unified_config.py:104]
**Acceptance checklist:**

- [ ] Replace bare `pass` behavior with explicit validation outcome or typed error path.
- [ ] Preserve merged config behavior for valid provider inputs.
- [ ] Add tests for invalid provider fragments and full valid merge flow.
      **Notes:** Silent bypass here can mask missing configuration and lead to delayed runtime failures.
