### [WL-8350]

**Title:** Preserve workflow orchestration by separating context hydration and validation
**Source:** [thegent/src/thegent/orchestration/workflow.py:688]
**Acceptance checklist:**

- [ ] Separate context hydration failures from workflow validation failures.
- [ ] Preserve partial execution for recoverable validation branch.
- [ ] Add tests for hydration and validation branch behavior.
      **Notes:** Improves stability when workflow context is partially stale.

### [WL-8351]

**Title:** Preserve CLI report generation by separating template load and row serialization
**Source:** [thegent/src/thegent/cli/report.py:247]
**Acceptance checklist:**

- [ ] Split template loading failures from row serialization failures.
- [ ] Keep report generation operational on transient row serialization failures.
- [ ] Add tests for both report error branches.
      **Notes:** Keeps reporting useful even with mixed quality data.

### [WL-8352]

**Title:** Preserve policy engine by separating YAML parse and constraint evaluation
**Source:** [thegent/src/thegent/policies/evaluator.py:333]
**Acceptance checklist:**

- [ ] Separate malformed policy YAML from constraint evaluation failures.
- [ ] Preserve rule application defaults when YAML parse fails.
- [ ] Add tests for parse and evaluation branches.
      **Notes:** Prevents policy engines from failing hard on syntax-only drift.

### [WL-8353]

**Title:** Preserve API request tracing by separating token redaction and context enrichment
**Source:** [thegent/src/thegent/tracing/request.py:428]
**Acceptance checklist:**

- [ ] Separate redaction failures from enrichment failures.
- [ ] Preserve trace IDs even when enrichment errors occur.
- [ ] Add tests for redaction and enrichment branch handling.
      **Notes:** Keeps privacy and tracing behavior independently reliable.

### [WL-8354]

**Title:** Preserve dataset import by separating schema migration and row transform
**Source:** [thegent/src/thegent/datasets/importer.py:566]
**Acceptance checklist:**

- [ ] Isolate schema migration failures from row transformation failures.
- [ ] Preserve imported row progress despite schema warnings.
- [ ] Add tests for schema and transform error branches.
      **Notes:** Helps imports proceed safely in mixed-quality payloads.

### [WL-8355]

**Title:** Preserve websocket client handling by separating connect negotiation and subscription registration
**Source:** [thegent/src/thegent/clients/ws_client.py:491]
**Acceptance checklist:**

- [ ] Separate handshake negotiation failures from subscription registration failures.
- [ ] Preserve subscription attempts after transient negotiation success.
- [ ] Add tests for negotiation and registration failures.
      **Notes:** Reduces silent disconnects during partial websocket issues.

### [WL-8356]

**Title:** Preserve cache warming by separating manifest filtering and fetch scheduling
**Source:** [thegent/src/thegent/cache/warmup.py:367]
**Acceptance checklist:**

- [ ] Distinguish manifest filter failures from fetch scheduler failures.
- [ ] Keep warmup progress on filter errors with fallback set.
- [ ] Add tests for filtered and scheduled branches.
      **Notes:** Prevents long warmup stalls on one bad filter entry.

### [WL-8357]

**Title:** Preserve secrets handling by separating key parsing and secret materialization
**Source:** [thegent/src/thegent/secrets/loader.py:301]
**Acceptance checklist:**

- [ ] Separate key parse failures from secret materialization failures.
- [ ] Preserve operational keys while surfacing non-critical parse issues.
- [ ] Add tests for parse and materialization fault conditions.
      **Notes:** Improves startup resilience under mixed provider secret configs.

### [WL-8358]

**Title:** Preserve deployment trigger by separating branch resolution and executor selection
**Source:** [thegent/src/thegent/deploy/triggers.py:522]
**Acceptance checklist:**

- [ ] Separate branch resolution failures from executor selection failures.
- [ ] Preserve existing executor behavior when branch resolution regresses.
- [ ] Add tests for branch and executor fallback conditions.
      **Notes:** Reduces pipeline stalls from naming or path resolution glitches.

### [WL-8359]

**Title:** Preserve artifact checksum verification by separating algorithm negotiation and hash write
**Source:** [thegent/src/thegent/artifacts/checksum.py:388]
**Acceptance checklist:**

- [ ] Separate checksum algorithm negotiation failures from checksum persistence failures.
- [ ] Preserve verification results when algorithm negotiation is incompatible.
- [ ] Add tests for negotiation and persistence failures.
      **Notes:** Improves evidence integrity workflows under algorithm drift.
