### [WL-11040]

**Title:** Preserve approval payload id extraction for turn/submit responses.
**Source:** `tests/protocols/test_wl11040_wl11049_lane_b9.py`
**Acceptance checklist:**

- [x] Return approval payload id when valid payload is provided.

### [WL-11041]

**Title:** Reject empty approval payload id in turn/submit response parsing.
**Source:** `tests/protocols/test_wl11040_wl11049_lane_b9.py`
**Acceptance checklist:**

- [x] Raise a validation error when approval id is empty.

### [WL-11042]

**Title:** Preserve approval payload status extraction for turn/submit response helpers.
**Source:** `tests/protocols/test_wl11040_wl11049_lane_b9.py`
**Acceptance checklist:**

- [x] Return status when payload status is a valid string.

### [WL-11043]

**Title:** Reject non-string approval payload status in turn/submit response parsing.
**Source:** `tests/protocols/test_wl11040_wl11049_lane_b9.py`
**Acceptance checklist:**

- [x] Raise a validation error for non-string status values.

### [WL-11044]

**Title:** Preserve strict validation for malformed approval payload in response resolution.
**Source:** `tests/protocols/test_wl11040_wl11049_lane_b9.py`
**Acceptance checklist:**

- [x] Reject malformed approval payload entries with empty identifiers/values.

### [WL-11045]

**Title:** Preserve approval payload diff handling for explicit null.
**Source:** `tests/protocols/test_wl11040_wl11049_lane_b9.py`
**Acceptance checklist:**

- [x] Resolve approval payload `(id, status, diff)` with `diff=None`.

### [WL-11046]

**Title:** Preserve request metadata when building turn/submit response phase for notification path.
**Source:** `tests/protocols/test_wl11040_wl11049_lane_b9.py`
**Acceptance checklist:**

- [x] Preserve `request_has_id=False` and `request_id=None` in response phase.

### [WL-11047]

**Title:** Preserve notification-path behavior for `turn/submit` requests.
**Source:** `tests/protocols/test_wl11040_wl11049_lane_b9.py`
**Acceptance checklist:**

- [x] Return no JSON-RPC result for requests without `id`.
- [x] Emit turn lifecycle notifications when processing successfully.

### [WL-11048]

**Title:** Preserve session resolution failure behavior for `turn/submit` without request id.
**Source:** `tests/protocols/test_wl11040_wl11049_lane_b9.py`
**Acceptance checklist:**

- [x] Return parse error response with `Session not found` for missing sessions.
- [x] Return no notifications when session cannot be resolved.

### [WL-11049]

**Title:** Preserve request-id extraction failure handling in turn/submit response resolution.
**Source:** `tests/protocols/test_wl11040_wl11049_lane_b9.py`
**Acceptance checklist:**

- [x] Reject missing request id when a response id is required.
