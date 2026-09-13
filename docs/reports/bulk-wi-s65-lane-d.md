### [WL-8800]

**Title:** Preserve telemetry storage by separating storage config parse and storage write
**Source:** [thegent/src/thegent/telemetry/storage.py:531]
**Acceptance checklist:**

- [ ] Separate telemetry storage config parse failures from storage write failures.
- [ ] Preserve writes with default storage config.
- [ ] Add tests for parse and write branch failures.
      **Notes:** Helps retain telemetry data during storage config drift.

### [WL-8801]

**Title:** Preserve command queue replay by separating replay payload parse and replay executor
**Source:** [thegent/src/thegent/commands/replay.py:333]
**Acceptance checklist:**

- [ ] Separate command replay payload parse failures from replay executor failures.
- [ ] Preserve replay with payload fallback.
- [ ] Add tests for replay parse and executor branches.
      **Notes:** Prevents replay dead-ends from one payload schema regression.

### [WL-8802]

**Title:** Preserve API gateway routing by separating gateway route parse and gateway route activation
**Source:** [thegent/src/thegent/api/gateway_router.py:477]
**Acceptance checklist:**

- [ ] Separate gateway route parse failures from route activation failures.
- [ ] Preserve activation using fallback route configuration.
- [ ] Add tests for parse and activation branch failures.
      **Notes:** Keeps API traffic flowing when route definitions change.

### [WL-8803]

**Title:** Preserve artifact annotation export by separating annotation parse and export pipeline
**Source:** [thegent/src/thegent/artifacts/annotation_export.py:401]
**Acceptance checklist:**

- [ ] Separate annotation parse failures from export pipeline failures.
- [ ] Preserve pipeline with annotation fallback.
- [ ] Add tests for parse and pipeline branch behavior.
      **Notes:** Keeps annotation exports functional during annotation format updates.

### [WL-8804]

**Title:** Preserve sync integrity by separating integrity token parse and integrity enforcement
**Source:** [thegent/src/thegent/sync/integrity.py:531]
**Acceptance checklist:**

- [ ] Separate integrity token parse failures from enforcement failures.
- [ ] Preserve integrity enforcement with token fallback.
- [ ] Add tests for parse and enforcement branches.
      **Notes:** Improves sync safety without full pipeline outages.

### [WL-8805]

**Title:** Preserve session event replay by separating replay marker parse and replay execution
**Source:** [thegent/src/thegent/session/replay_executor.py:333]
**Acceptance checklist:**

- [ ] Separate replay marker parse failures from replay execution failures.
- [ ] Preserve replay progress with fallback markers.
- [ ] Add tests for marker parse and execution branches.
      **Notes:** Improves session recovery under partial marker inconsistencies.

### [WL-8806]

**Title:** Preserve artifact queue integrity by separating queue payload parse and queue commit
**Source:** [thegent/src/thegent/artifacts/queue_integrity.py:589]
**Acceptance checklist:**

- [ ] Separate queue payload parse failures from queue commit failures.
- [ ] Preserve queue commit with payload fallback.
- [ ] Add tests for parse and commit branches.
      **Notes:** Maintains queue consistency under payload format changes.

### [WL-8807]

**Title:** Preserve policy context by separating context token parse and context application
**Source:** [thegent/src/thegent/policies/context.py:412]
**Acceptance checklist:**

- [ ] Separate policy context token parse failures from context application failures.
- [ ] Preserve context application with fallback tokens.
- [ ] Add tests for parse and context branches.
      **Notes:** Reduces policy behavior surprises under token format drift.

### [WL-8808]

**Title:** Preserve CLI diagnostics emission by separating diagnostic schema parse and emission transport
**Source:** [thegent/src/thegent/cli/diagnostics_transport.py:523]
**Acceptance checklist:**

- [ ] Separate diagnostic schema parse failures from emission transport failures.
- [ ] Preserve diagnostic emissions with transport fallback.
- [ ] Add tests for schema and transport branch failures.
      **Notes:** Improves operator visibility under schema changes.

### [WL-8809]

**Title:** Preserve sync connector auth by separating connector auth parse and connector auth attach
**Source:** [thegent/src/thegent/integrations/connector_auth.py:378]
**Acceptance checklist:**

- [ ] Separate connector auth parse failures from auth attach failures.
- [ ] Preserve auth attach with fallback auth metadata.
- [ ] Add tests for parse and attach branches.
      **Notes:** Keeps connector sync functional when auth metadata varies.
