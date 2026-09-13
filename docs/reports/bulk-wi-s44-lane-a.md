### [WL-7720]

**Title:** Tighten CLI argument validation for mutually exclusive execution modes
**Source:** [thegent/src/thegent/clode_args.py:42]
**Acceptance checklist:**

- [ ] Add explicit validation for mutually exclusive mode flags with a clear error path.
- [ ] Preserve current defaults when no mode flags are provided.
- [ ] Add tests for valid single-mode, invalid dual-mode, and default-mode parsing.
      **Notes:** Line 42 is in the primary argument assembly flow where conflicting flags should fail fast.

### [WL-7721]

**Title:** Normalize platform detection branches to keep OS-specific path logic deterministic
**Source:** [thegent/src/thegent/thegent_platform.py:57]
**Acceptance checklist:**

- [ ] Refactor platform matching to a single deterministic branch order for supported OS values.
- [ ] Preserve existing output for macOS, Linux, and Windows platforms.
- [ ] Add tests for known platforms and one unsupported platform failure case.
      **Notes:** Line 57 sits at the OS dispatch branch that influences downstream path and binary selection.

### [WL-7722]

**Title:** Enforce typed cache-key construction for frecency lookups
**Source:** [thegent/src/thegent/cache/frecency.py:88]
**Acceptance checklist:**

- [ ] Add strict cache-key normalization for nullable and non-string input components.
- [ ] Preserve cache hit behavior for existing valid key shapes.
- [ ] Add tests for normalized keys, invalid key inputs, and stable hit/miss behavior.
      **Notes:** Line 88 generates composite keys used by frecency scoring and retrieval.

### [WL-7723]

**Title:** Separate multi-level cache read miss handling from backend transport failures
**Source:** [thegent/src/thegent/cache/multi_level.py:131]
**Acceptance checklist:**

- [ ] Split logical cache misses from backend I/O or transport exceptions in read flow.
- [ ] Preserve current promotion behavior when a lower-tier cache returns a valid value.
- [ ] Add tests for L1 miss/L2 hit, full miss, and backend failure scenarios.
      **Notes:** Line 131 is in the cache read path where miss and failure states are currently easy to conflate.

### [WL-7724]

**Title:** Keep pre-warm batch boundaries explicit to avoid silent overrun of configured limits
**Source:** [thegent/src/thegent/cache/pre_warmer.py:74]
**Acceptance checklist:**

- [ ] Enforce configured batch-size ceilings before dispatching pre-warm jobs.
- [ ] Preserve existing pre-warm ordering semantics for eligible entries.
- [ ] Add tests for exact-boundary, under-boundary, and over-boundary batch cases.
      **Notes:** Line 74 is where batch slicing is computed before pre-warm execution starts.

### [WL-7725]

**Title:** Harden memory manager seed selection against ambiguous source precedence
**Source:** [thegent/src/thegent/memory/manager.py:112]
**Acceptance checklist:**

- [ ] Define explicit precedence when multiple seed sources are present in one request.
- [ ] Preserve current behavior for single-source seed selection.
- [ ] Add tests for single-source, multi-source conflict, and no-seed request paths.
      **Notes:** Line 112 is in seed selection logic that determines which memory signal is promoted.

### [WL-7726]

**Title:** Validate seed storage writes with explicit schema checks before persistence
**Source:** [thegent/src/thegent/memory/seed_storage.py:67]
**Acceptance checklist:**

- [ ] Add required-field and type validation before writing seed records.
- [ ] Preserve successful persistence behavior for schema-compliant records.
- [ ] Add tests for valid records, missing required fields, and invalid field types.
      **Notes:** Line 67 is in the persistence entrypoint where malformed seed payloads should be rejected.

### [WL-7727]

**Title:** Keep native JSONL parser return contracts strict across event parsing paths
**Source:** [thegent/src/thegent/native/jsonl_parser.py:103]
**Acceptance checklist:**

- [ ] Add explicit return-shape validation for parsed event objects before handoff.
- [ ] Preserve successful parse behavior for valid JSONL event lines.
- [ ] Add tests for valid events, malformed JSON lines, and invalid return shapes.
      **Notes:** Line 103 is in event parsing where native output must match Python-side expectations.

### [WL-7728]

**Title:** Preserve watcher daemon startup determinism by typing SHM initialization failures
**Source:** [thegent/src/thegent/native/watcher_daemon.py:119]
**Acceptance checklist:**

- [ ] Replace broad SHM init failure handling with explicit filesystem, permission, and config categories.
- [ ] Preserve watcher startup behavior when SHM initializes successfully.
- [ ] Add tests for successful init, permission-denied SHM path, and invalid config values.
      **Notes:** Line 119 is in watcher startup where SHM setup outcomes drive runtime monitoring readiness.

### [WL-7729]

**Title:** Require explicit discovery-native capability checks before invoking accelerated scans
**Source:** [thegent/src/thegent/native/discovery_native.py:54]
**Acceptance checklist:**

- [ ] Add explicit capability guards before calling native accelerated discovery paths.
- [ ] Preserve current scan behavior when native capabilities are available.
- [ ] Add tests for capability-available, capability-missing, and native-call failure cases.
      **Notes:** Line 54 is at the native discovery entrypoint where capability gating should occur.
