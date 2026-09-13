### [WL-11080]

**Title:** Preserve notification-path response id extraction behavior for turn/submit.
**Source:** `tests/protocols/test_wl11080_wl11089_lane_b12.py`
**Acceptance checklist:**

- [x] Allow absent request id when `request_has_id` is false.

### [WL-11081]

**Title:** Preserve strict required request-id enforcement in response extraction.
**Source:** `tests/protocols/test_wl11080_wl11089_lane_b12.py`
**Acceptance checklist:**

- [x] Reject `None` request id when `request_has_id` is true.

### [WL-11082]

**Title:** Preserve JSON-RPC id contract rejecting boolean request ids.
**Source:** `tests/protocols/test_wl11080_wl11089_lane_b12.py`
**Acceptance checklist:**

- [x] Reject boolean request id values on response id-required path.

### [WL-11083]

**Title:** Preserve nullable response approval payload extraction contract.
**Source:** `tests/protocols/test_wl11080_wl11089_lane_b12.py`
**Acceptance checklist:**

- [x] Keep `approval_payload` optional and return `None` unchanged.

### [WL-11084]

**Title:** Preserve approval diff passthrough for valid string payloads.
**Source:** `tests/protocols/test_wl11080_wl11089_lane_b12.py`
**Acceptance checklist:**

- [x] Return string `diff` values unchanged from approval payload extraction.

### [WL-11085]

**Title:** Preserve approval payload validation acceptance for valid shape.
**Source:** `tests/protocols/test_wl11080_wl11089_lane_b12.py`
**Acceptance checklist:**

- [x] Accept `{id, status, diff}` payloads without raising validation errors.

### [WL-11086]

**Title:** Preserve strict approval payload id requirement.
**Source:** `tests/protocols/test_wl11080_wl11089_lane_b12.py`
**Acceptance checklist:**

- [x] Reject approval payloads missing a non-empty string `id`.

### [WL-11087]

**Title:** Preserve strict approval payload status requirement.
**Source:** `tests/protocols/test_wl11080_wl11089_lane_b12.py`
**Acceptance checklist:**

- [x] Reject approval payloads missing a non-empty string `status`.

### [WL-11088]

**Title:** Preserve result payload shape with approval inclusion when present.
**Source:** `tests/protocols/test_wl11080_wl11089_lane_b12.py`
**Acceptance checklist:**

- [x] Include serialized turn and `approval` payload in turn/submit result payload.

### [WL-11089]

**Title:** Preserve success response shape with approval inclusion when present.
**Source:** `tests/protocols/test_wl11080_wl11089_lane_b12.py`
**Acceptance checklist:**

- [x] Include `result.approval` in success response when approval payload exists.
