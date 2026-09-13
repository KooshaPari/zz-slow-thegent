### [WL-8600]

**Title:** Preserve command execution audit by separating execution metadata and execution logger
**Source:** [thegent/src/thegent/commands/exec_audit.py:377]
**Acceptance checklist:**

- [ ] Separate execution metadata parse failures from execution logger failures.
- [ ] Preserve audit stream with metadata fallback.
- [ ] Add tests for metadata and logger branch failures.
      **Notes:** Improves audit continuity for high-volume command runs.

### [WL-8601]

**Title:** Preserve artifact manifest generation by separating manifest build and manifest checksum
**Source:** [thegent/src/thegent/artifacts/manifest_builder.py:599]
**Acceptance checklist:**

- [ ] Separate manifest build failures from manifest checksum failures.
- [ ] Preserve manifest output with checksum fallback.
- [ ] Add tests for build and checksum branches.
      **Notes:** Reduces artifact packaging risk under checksum mismatches.

### [WL-8602]

**Title:** Preserve queue orchestration by separating queue heartbeat parse and heartbeat dispatch
**Source:** [thegent/src/thegent/queue/heartbeat.py:447]
**Acceptance checklist:**

- [ ] Separate queue heartbeat parse failures from heartbeat dispatch failures.
- [ ] Preserve dispatch behavior on parse errors.
- [ ] Add tests for parse and dispatch branch failures.
      **Notes:** Keeps orchestration stable during heartbeat signal drift.

### [WL-8603]

**Title:** Preserve user session cleanup by separating cleanup policy parse and cleanup execution
**Source:** [thegent/src/thegent/session/cleanup.py:331]
**Acceptance checklist:**

- [ ] Separate cleanup policy parse failures from cleanup execution failures.
- [ ] Preserve baseline cleanup with policy fallback.
- [ ] Add tests for policy and execution branches.
      **Notes:** Prevents session buildup when policy parsing is flaky.

### [WL-8604]

**Title:** Preserve artifact version resolution by separating version index parse and version fetch
**Source:** [thegent/src/thegent/artifacts/version_resolver.py:489]
**Acceptance checklist:**

- [ ] Separate artifact version index parse failures from version fetch failures.
- [ ] Preserve version fetch fallback list when index parse fails.
- [ ] Add tests for index parse and fetch branches.
      **Notes:** Improves versioned artifact retrieval reliability.

### [WL-8605]

**Title:** Preserve API token routing by separating token issuer parse and route assignment
**Source:** [thegent/src/thegent/auth/token_router.py:423]
**Acceptance checklist:**

- [ ] Separate issuer parse failures from route assignment failures.
- [ ] Preserve route assignment fallback for unknown issuers.
- [ ] Add tests for issuer parse and assignment branches.
      **Notes:** Avoids authentication misroutes under token format changes.

### [WL-8606]

**Title:** Preserve CLI plugin execution by separating plugin invocation parse and sandbox invocation
**Source:** [thegent/src/thegent/cli/plugin_exec.py:356]
**Acceptance checklist:**

- [ ] Separate plugin invocation parse failures from sandbox invocation failures.
- [ ] Preserve direct invocation fallback.
- [ ] Add tests for invocation parse and sandbox branches.
      **Notes:** Keeps plugin features usable when one invocation mode regresses.

### [WL-8607]

**Title:** Preserve sync request signing by separating request canonicalization and signing key derivation
**Source:** [thegent/src/thegent/sync/request_signer.py:451]
**Acceptance checklist:**

- [ ] Separate request canonicalization failures from key derivation failures.
- [ ] Preserve signing retries with canonicalization fallback.
- [ ] Add tests for canonicalization and derivation branches.
      **Notes:** Improves request pipeline resilience under signer drift.

### [WL-8608]

**Title:** Preserve alert templating by separating template render and notification target resolution
**Source:** [thegent/src/thegent/alerts/template.py:501]
**Acceptance checklist:**

- [ ] Separate alert template render failures from target resolution failures.
- [ ] Preserve alert target fallback on render failures.
- [ ] Add tests for render and target resolution branches.
      **Notes:** Maintains alert delivery under template syntax issues.

### [WL-8609]

**Title:** Preserve event history by separating history query parse and history store reads
**Source:** [thegent/src/thegent/events/history.py:412]
**Acceptance checklist:**

- [ ] Separate event history query parse failures from history store read failures.
- [ ] Preserve partial history on query parse failures.
- [ ] Add tests for parse and store read branch handling.
      **Notes:** Helps operators view usable history under query format mismatch.
