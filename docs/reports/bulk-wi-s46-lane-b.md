### [WL-7830]

**Title:** Split run-context bootstrap faults between workspace detection and config hydration stages
**Source:** [thegent/src/thegent/runtime/run_context.py:58]
**Acceptance checklist:**

- [ ] Replace broad bootstrap exception handling with explicit workspace-detection and config-hydration branches.
- [ ] Preserve successful run-context output fields and downstream caller contract.
- [ ] Add tests for missing workspace roots, invalid config payloads, and successful bootstrap.
      **Notes:** Current startup failures do not reveal whether path discovery or configuration hydration failed.

### [WL-7831]

**Title:** Classify command graph build errors by node decode versus edge validation failures
**Source:** [thegent/src/thegent/commands/graph_builder.py:91]
**Acceptance checklist:**

- [ ] Replace catch-all graph build errors with explicit node-decode and edge-validation branches.
- [ ] Preserve successful DAG construction order and node identity semantics.
- [ ] Add tests for malformed node entries, invalid edge references, and successful graph build.
      **Notes:** Combined graph errors obscure whether inputs are malformed or dependency links are invalid.

### [WL-7832]

**Title:** Separate MCP request auth failures between token extraction and policy authorization checks
**Source:** [thegent/src/thegent/mcp/request_auth.py:74]
**Acceptance checklist:**

- [ ] Replace generic auth failure handling with explicit token-extraction and policy-authorization branches.
- [ ] Preserve successful authenticated request context fields.
- [ ] Add tests for missing auth headers, policy deny outcomes, and successful authorization.
      **Notes:** Unified auth errors slow diagnosis by hiding whether credentials were absent or rejected.

### [WL-7833]

**Title:** Differentiate template compilation faults across variable resolution and markdown rendering stages
**Source:** [thegent/src/thegent/reports/template_compiler.py:133]
**Acceptance checklist:**

- [ ] Replace broad compile exception handling with explicit variable-resolution and markdown-render branches.
- [ ] Preserve successful report template output format and metadata blocks.
- [ ] Add tests for unresolved variables, renderer exceptions, and successful compilation.
      **Notes:** Single compile failure paths make template debugging noisy and non-actionable.

### [WL-7834]

**Title:** Keep provider health probe errors typed for transport timeout and payload decode outcomes
**Source:** [thegent/src/thegent/providers/health_probe.py:49]
**Acceptance checklist:**

- [ ] Replace catch-all probe errors with explicit transport-timeout and payload-decode branches.
- [ ] Preserve current healthy-provider fast path and status mapping behavior.
- [ ] Add tests for timeout probes, malformed health payloads, and successful probe responses.
      **Notes:** Probe failures currently collapse network and data-shape errors into one generic message.

### [WL-7835]

**Title:** Split event bus publish failures between topic resolution and subscriber dispatch stages
**Source:** [thegent/src/thegent/events/bus.py:118]
**Acceptance checklist:**

- [ ] Replace generic publish exception handling with explicit topic-resolution and subscriber-dispatch branches.
- [ ] Preserve successful publish ordering and subscriber invocation semantics.
- [ ] Add tests for unknown topics, subscriber handler exceptions, and successful publish flows.
      **Notes:** Current publish errors do not isolate routing problems from downstream handler failures.

### [WL-7836]

**Title:** Classify session attach faults across socket connect and handshake negotiation steps
**Source:** [thegent/src/thegent/sessions/attach.py:86]
**Acceptance checklist:**

- [ ] Replace broad session attach exceptions with explicit socket-connect and handshake-negotiation branches.
- [ ] Preserve successful attach response payload and negotiated capabilities.
- [ ] Add tests for refused socket connections, handshake mismatch failures, and successful attach.
      **Notes:** Attachment failures should indicate whether transport or protocol negotiation is at fault.

### [WL-7837]

**Title:** Separate queue drain errors between dequeue fetch and ack persistence operations
**Source:** [thegent/src/thegent/queue/drain.py:157]
**Acceptance checklist:**

- [ ] Replace catch-all drain exception handling with explicit dequeue-fetch and ack-persistence branches.
- [ ] Preserve successful queue drain ordering and idempotent ack behavior.
- [ ] Add tests for dequeue source failure, ack write failure, and successful drain cycles.
      **Notes:** A single drain error shape hides whether reads or acknowledgements are failing.

### [WL-7838]

**Title:** Differentiate policy evaluation failures for rule parsing versus rule execution phases
**Source:** [thegent/src/thegent/policy/evaluator.py:102]
**Acceptance checklist:**

- [ ] Replace broad evaluator exceptions with explicit rule-parsing and rule-execution branches.
- [ ] Preserve successful policy decision payload schema and rule ordering.
- [ ] Add tests for invalid rule definitions, runtime rule exceptions, and successful evaluations.
      **Notes:** Collapsed evaluator failures make remediation unclear for malformed policies versus runtime defects.

### [WL-7839]

**Title:** Split transcript index rebuild faults between file scan and index write-back stages
**Source:** [thegent/src/thegent/session/transcript_index.py:65]
**Acceptance checklist:**

- [ ] Replace generic rebuild exception handling with explicit file-scan and index-write branches.
- [ ] Preserve successful index key structure and lookup behavior.
- [ ] Add tests for unreadable transcript files, write-back failures, and successful rebuild runs.
      **Notes:** Index rebuild diagnostics should identify read-path versus persistence-path failures.
