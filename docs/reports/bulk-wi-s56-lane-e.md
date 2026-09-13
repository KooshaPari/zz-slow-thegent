### [WL-8360]

**Title:** Preserve notification delivery by separating payload validation and transport retries
**Source:** [thegent/src/thegent/notifications/dispatcher.py:411]
**Acceptance checklist:**

- [ ] Separate payload schema failures from retry scheduler failures.
- [ ] Keep retry scheduling unchanged for valid payloads.
- [ ] Add tests for schema and retry branches.
      **Notes:** Reduces notification drops during schema transitions.

### [WL-8361]

**Title:** Preserve build manifest handling by separating manifest schema parse and dependency resolution
**Source:** [thegent/src/thegent/build/manifest.py:338]
**Acceptance checklist:**

- [ ] Separate manifest parse failures from dependency resolution failures.
- [ ] Preserve build scheduling when only dependency resolution degrades.
- [ ] Add tests for parse and dependency branches.
      **Notes:** Keeps builds resilient when manifests are partially invalid.

### [WL-8362]

**Title:** Preserve prompt history by separating cursor state load and persistence
**Source:** [thegent/src/thegent/prompt/history.py:267]
**Acceptance checklist:**

- [ ] Separate history state load failures from persistence failures.
- [ ] Preserve UX with read-only history fallback on load issues.
- [ ] Add tests for load and persist failure modes.
      **Notes:** Helps avoid prompt history corruption under transient storage faults.

### [WL-8363]

**Title:** Preserve API key rotation by separating policy lookup and signing key fetch
**Source:** [thegent/src/thegent/security/keys.py:455]
**Acceptance checklist:**

- [ ] Split policy lookup failures from signing key retrieval failures.
- [ ] Keep stale keys available under non-critical policy lookup issues.
- [ ] Add tests for policy and signing branches.
      **Notes:** Prevents key rotation delays from one policy backend flake.

### [WL-8364]

**Title:** Preserve task export by separating serialization and archive compression
**Source:** [thegent/src/thegent/tasks/exporter.py:522]
**Acceptance checklist:**

- [ ] Separate task serialization failures from archive compression failures.
- [ ] Preserve uncompressed export fallback on compression failures.
- [ ] Add tests for both export branches.
      **Notes:** Keeps data recovery functional when one pipeline branch is down.

### [WL-8365]

**Title:** Preserve API response caching by separating key derivation and cache backend write
**Source:** [thegent/src/thegent/http/cache.py:349]
**Acceptance checklist:**

- [ ] Distinguish cache key derivation failures from write failures.
- [ ] Preserve response serving when cache derivation fails.
- [ ] Add tests for key and write branch behavior.
      **Notes:** Improves response delivery under key format drift.

### [WL-8366]

**Title:** Preserve config migration checks by separating checksum validation and migration plan
**Source:** [thegent/src/thegent/config/migration.py:412]
**Acceptance checklist:**

- [ ] Separate checksum validation failures from plan generation failures.
- [ ] Preserve migration dry-run path when checksum validation is unavailable.
- [ ] Add tests for checksum and plan branches.
      **Notes:** Helps identify config drift without halting safe checks.

### [WL-8367]

**Title:** Preserve search indexing by separating query parse and scorer warming
**Source:** [thegent/src/thegent/search/index.py:592]
**Acceptance checklist:**

- [ ] Split query parse failures from scorer warmup failures.
- [ ] Keep fallback query handling for parse recovery.
- [ ] Add tests for parse and scorer warmup branches.
      **Notes:** Keeps search usable when ranking warmup is unstable.

### [WL-8368]

**Title:** Preserve artifact purge behavior by separating retention policy parse and execution window
**Source:** [thegent/src/thegent/artifacts/purge.py:477]
**Acceptance checklist:**

- [ ] Separate retention policy parse failures from purge window scheduling failures.
- [ ] Preserve safe purge defaults when scheduling branches degrade.
- [ ] Add tests for parse and scheduling faults.
      **Notes:** Prevents accidental over-retention due to one policy bug.

### [WL-8369]

**Title:** Preserve CLI streaming behavior by separating stream parsing and frame rendering
**Source:** [thegent/src/thegent/cli/stream.py:611]
**Acceptance checklist:**

- [ ] Separate stream message parsing failures from frame rendering failures.
- [ ] Keep streaming fallback path active on parser recovery.
- [ ] Add tests for parser and renderer branches.
      **Notes:** Improves CLI responsiveness during high-volume stream changes.
