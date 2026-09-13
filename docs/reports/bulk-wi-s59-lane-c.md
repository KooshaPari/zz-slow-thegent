### [WL-8490]

**Title:** Preserve data import by separating CSV parse and schema normalize
**Source:** [thegent/src/thegent/data/importer.py:468]
**Acceptance checklist:**

- [ ] Separate CSV parsing failures from schema normalization failures.
- [ ] Keep schema-normalized fallback path on parse failures.
- [ ] Add tests for parser and normalization branches.
      **Notes:** Preserves import throughput under intermittent CSV formatting issues.

### [WL-8491]

**Title:** Preserve background jobs by separating queue polling and handler dispatch
**Source:** [thegent/src/thegent/jobs/background.py:333]
**Acceptance checklist:**

- [ ] Separate queue poll failures from handler dispatch failures.
- [ ] Preserve handler dispatch on poll branch recoveries.
- [ ] Add tests for polling and dispatch branch failures.
      **Notes:** Helps background processing recover from intermittent transport issues.

### [WL-8492]

**Title:** Preserve API client resilience by separating identity extraction and client construction
**Source:** [thegent/src/thegent/clients/api_client.py:422]
**Acceptance checklist:**

- [ ] Separate identity extraction failures from client construction failures.
- [ ] Preserve default client behavior during identity extraction issues.
- [ ] Add tests for extraction and construction branches.
      **Notes:** Prevents client instantiation issues from cascading failures.

### [WL-8493]

**Title:** Preserve policy snapshots by separating snapshot compression and index mapping
**Source:** [thegent/src/thegent/policies/snapshot.py:389]
**Acceptance checklist:**

- [ ] Separate snapshot compression failures from index mapping failures.
- [ ] Preserve mapping state on compression failures.
- [ ] Add tests for compression and mapping branches.
      **Notes:** Improves policy rollback reliability.

### [WL-8494]

**Title:** Preserve event sink registration by separating endpoint discovery and sink attach
**Source:** [thegent/src/thegent/events/sink.py:401]
**Acceptance checklist:**

- [ ] Separate endpoint discovery failures from sink attachment failures.
- [ ] Keep sink attachment retry active with discovered endpoints.
- [ ] Add tests for discovery and attachment failures.
      **Notes:** Supports resilient event pipeline setup.

### [WL-8495]

**Title:** Preserve user state sync by separating token fetch and local persistence
**Source:** [thegent/src/thegent/user/state_sync.py:523]
**Acceptance checklist:**

- [ ] Separate remote token fetch failures from local persistence failures.
- [ ] Preserve local user state on remote token failures.
- [ ] Add tests for token fetch and persistence branches.
      **Notes:** Maintains state continuity during token provider outages.

### [WL-8496]

**Title:** Preserve command audit by separating command metadata parse and audit sink write
**Source:** [thegent/src/thegent/audit/command_audit.py:334]
**Acceptance checklist:**

- [ ] Separate command metadata parse failures from audit sink writes.
- [ ] Keep audit trail with metadata fallback.
- [ ] Add tests for metadata and sink branch failures.
      **Notes:** Ensures command audit remains meaningful under payload drift.

### [WL-8497]

**Title:** Preserve repository sync by separating diff patching and workspace validation
**Source:** [thegent/src/thegent/repo/sync.py:486]
**Acceptance checklist:**

- [ ] Separate patch application failures from workspace validation failures.
- [ ] Preserve workspace rollback on patch failures.
- [ ] Add tests for patch and validation branches.
      **Notes:** Prevents partial sync corruption in large repos.

### [WL-8498]

**Title:** Preserve artifact search indexing by separating tokenization and index commit
**Source:** [thegent/src/thegent/artifacts/search_index.py:431]
**Acceptance checklist:**

- [ ] Separate tokenization failures from index commit failures.
- [ ] Preserve index write queue on tokenization failures.
- [ ] Add tests for tokenization and commit branch issues.
      **Notes:** Keeps searchability during indexing component failures.

### [WL-8499]

**Title:** Preserve health data retention by separating TTL parse and retention execution
**Source:** [thegent/src/thegent/health/retention.py:352]
**Acceptance checklist:**

- [ ] Separate TTL configuration parse failures from retention execution failures.
- [ ] Preserve retention baseline when TTL parse fails.
- [ ] Add tests for TTL parse and retention branches.
      **Notes:** Helps avoid accidental data loss under malformed TTL configs.
