### [WL-7770]

**Title:** Strengthen clode profile resolution by rejecting ambiguous default aliases
**Source:** [thegent/src/thegent/clode_profiles.py:39]
**Acceptance checklist:**

- [ ] Add explicit validation that a default alias maps to exactly one profile entry.
- [ ] Preserve current profile selection behavior when aliases are unambiguous.
- [ ] Add tests for valid alias resolution, missing alias, and duplicate alias collision.
      **Notes:** Line 39 is in the profile lookup flow where ambiguous alias resolution should fail fast.

### [WL-7771]

**Title:** Keep execution mode normalization strict for mixed shorthand and longform flags
**Source:** [thegent/src/thegent/clode_args.py:68]
**Acceptance checklist:**

- [ ] Normalize shorthand and longform execution flags through a single canonical parser path.
- [ ] Preserve current defaults when no explicit execution mode is provided.
- [ ] Add tests for shorthand-only, longform-only, and mixed conflicting flag inputs.
      **Notes:** Line 68 is in argument normalization where mode parsing contracts should stay deterministic.

### [WL-7772]

**Title:** Enforce deterministic shell detection ordering before runner bootstrap
**Source:** [thegent/src/thegent/shell_detect.py:51]
**Acceptance checklist:**

- [ ] Refactor shell detection to use a single ordered probe sequence with explicit precedence.
- [ ] Preserve successful detection behavior for zsh, bash, and fish environments.
- [ ] Add tests for recognized shells, missing shell metadata, and unsupported shell values.
      **Notes:** Line 51 is in the probe branch that sets the shell runtime used by command execution.

### [WL-7773]

**Title:** Validate session metadata schema before writing lifecycle snapshots
**Source:** [thegent/src/thegent/session_store.py:92]
**Acceptance checklist:**

- [ ] Add required-field and type validation for session metadata prior to persistence.
- [ ] Preserve successful write behavior for schema-compliant lifecycle snapshots.
- [ ] Add tests for valid metadata, missing required keys, and invalid value types.
      **Notes:** Line 92 is in snapshot persistence where malformed session state should be rejected loudly.

### [WL-7774]

**Title:** Separate process table parse errors from empty process discovery results
**Source:** [thegent/src/thegent/process_registry.py:117]
**Acceptance checklist:**

- [ ] Split parse-failure handling from legitimate empty discovery outcomes in process reads.
- [ ] Preserve existing behavior when process enumeration returns valid rows.
- [ ] Add tests for populated process tables, empty results, and malformed row parse failures.
      **Notes:** Line 117 sits in process enumeration where empty-state and parse-state semantics diverge.

### [WL-7775]

**Title:** Require explicit trust-level tagging for memory ingestion events
**Source:** [thegent/src/thegent/memory/manager.py:141]
**Acceptance checklist:**

- [ ] Add validation that each ingestion event includes a supported trust-level tag.
- [ ] Preserve current ingestion flow for events with valid trust-level values.
- [ ] Add tests for valid tags, missing tags, and unsupported trust-level inputs.
      **Notes:** Line 141 is in memory ingestion where trust metadata gates downstream retrieval policy.

### [WL-7776]

**Title:** Keep native bridge handshake errors typed across startup boundaries
**Source:** [thegent/src/thegent/native/bridge.py:74]
**Acceptance checklist:**

- [ ] Replace broad startup exception handling with explicit handshake error categories.
- [ ] Preserve successful native bridge initialization behavior on healthy startup.
- [ ] Add tests for successful handshake, transport timeout, and invalid handshake payload.
      **Notes:** Line 74 is in native bridge startup where error typing should remain precise for diagnostics.

### [WL-7777]

**Title:** Gate watcher event fanout on validated event envelope fields
**Source:** [thegent/src/thegent/native/watcher_daemon.py:162]
**Acceptance checklist:**

- [ ] Validate required event envelope fields before watcher events are fanned out.
- [ ] Preserve current fanout behavior for events that satisfy envelope schema requirements.
- [ ] Add tests for valid events, missing envelope fields, and invalid field type cases.
      **Notes:** Line 162 is in watcher dispatch where malformed events should be blocked before propagation.

### [WL-7778]

**Title:** Enforce stable cache promotion ordering when lower-tier hits race
**Source:** [thegent/src/thegent/cache/multi_level.py:176]
**Acceptance checklist:**

- [ ] Add deterministic ordering for promotion writes when multiple lower-tier hits are observed.
- [ ] Preserve current promotion behavior for single lower-tier cache hits.
- [ ] Add tests for single-hit promotion, dual-hit race ordering, and promotion write conflicts.
      **Notes:** Line 176 is in promotion flow where non-deterministic ordering can cause cache state drift.

### [WL-7779]

**Title:** Require explicit capability checks before enabling native discovery acceleration
**Source:** [thegent/src/thegent/native/discovery_native.py:83]
**Acceptance checklist:**

- [ ] Add a capability guard that must pass before native acceleration paths are invoked.
- [ ] Preserve existing discovery behavior when native acceleration is supported.
- [ ] Add tests for capability-available, capability-missing, and native invocation failure paths.
      **Notes:** Line 83 is at the acceleration branch where capability gating prevents invalid native calls.
