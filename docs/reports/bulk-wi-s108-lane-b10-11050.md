### [WL-11050]

**Title:** Preserve valid approval payload schema validation for turn/submit responses.
**Source:** `tests/protocols/test_wl11050_wl11059_lane_b10.py`
**Acceptance checklist:**

- [x] Accept payloads with valid `id`, `status`, and optional `diff`.

### [WL-11051]

**Title:** Preserve rejection of turn/submit approval payloads missing identifier.
**Source:** `tests/protocols/test_wl11050_wl11059_lane_b10.py`
**Acceptance checklist:**

- [x] Reject payloads without a truthy `id`.

### [WL-11052]

**Title:** Preserve rejection of turn/submit approval payloads missing status.
**Source:** `tests/protocols/test_wl11050_wl11059_lane_b10.py`
**Acceptance checklist:**

- [x] Reject payloads without a truthy `status`.

### [WL-11053]

**Title:** Preserve rejection of invalid approval diff types during turn/submit validation.
**Source:** `tests/protocols/test_wl11050_wl11059_lane_b10.py`
**Acceptance checklist:**

- [x] Reject non-string, non-null `diff` values.

### [WL-11054]

**Title:** Preserve request-id extraction for turn/submit response resolution when id is required.
**Source:** `tests/protocols/test_wl11050_wl11059_lane_b10.py`
**Acceptance checklist:**

- [x] Return the original request id when path requires response id.

### [WL-11055]

**Title:** Preserve optional request-id handling for notification-style turn/submit responses.
**Source:** `tests/protocols/test_wl11050_wl11059_lane_b10.py`
**Acceptance checklist:**

- [x] Preserve `None` request id when no response id is required.

### [WL-11056]

**Title:** Preserve request-id type rejection for required turn/submit response ids.
**Source:** `tests/protocols/test_wl11050_wl11059_lane_b10.py`
**Acceptance checklist:**

- [x] Reject non-primitive request-id values when a response id is required.

### [WL-11057]

**Title:** Preserve parse-failure pass-through behavior for turn/submit.
**Source:** `tests/protocols/test_wl11050_wl11059_lane_b10.py`
**Acceptance checklist:**

- [x] Return parse failure payload unchanged from parse-failure helper.

### [WL-11058]

**Title:** Preserve approval inclusion in turn/submit success response payloads.
**Source:** `tests/protocols/test_wl11050_wl11059_lane_b10.py`
**Acceptance checklist:**

- [x] Keep `approval` field in result payload when provided.

### [WL-11059]

**Title:** Preserve response-resolution payload extraction for full turn/approval tuples.
**Source:** `tests/protocols/test_wl11050_wl11059_lane_b10.py`
**Acceptance checklist:**

- [x] Resolve request-id, turn, and approval payload unchanged from response phase.
