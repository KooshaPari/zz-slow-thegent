### [WL-11060]

**Title:** Preserve strict boolean extraction for turn/submit response id-path flag.
**Source:** `tests/protocols/test_wl11060_wl11069_lane_b11.py`
**Acceptance checklist:**

- [x] Reject non-boolean `request_has_id` values in response-phase extraction.

### [WL-11061]

**Title:** Preserve strict response turn payload extraction contract.
**Source:** `tests/protocols/test_wl11060_wl11069_lane_b11.py`
**Acceptance checklist:**

- [x] Reject non-dict `turn` payloads in response-phase extraction.

### [WL-11062]

**Title:** Preserve strict response approval payload extraction contract.
**Source:** `tests/protocols/test_wl11060_wl11069_lane_b11.py`
**Acceptance checklist:**

- [x] Reject non-dict, non-null `approval_payload` values.

### [WL-11063]

**Title:** Preserve approval-field tuple resolution for valid approval payloads.
**Source:** `tests/protocols/test_wl11060_wl11069_lane_b11.py`
**Acceptance checklist:**

- [x] Return `(id, status, diff)` unchanged for valid approval payloads.

### [WL-11064]

**Title:** Preserve strict approval id extraction guard in response helpers.
**Source:** `tests/protocols/test_wl11060_wl11069_lane_b11.py`
**Acceptance checklist:**

- [x] Reject empty or non-string approval ids.

### [WL-11065]

**Title:** Preserve strict approval status extraction guard in response helpers.
**Source:** `tests/protocols/test_wl11060_wl11069_lane_b11.py`
**Acceptance checklist:**

- [x] Reject empty or non-string approval status values.

### [WL-11066]

**Title:** Preserve optional approval diff nullability in response helpers.
**Source:** `tests/protocols/test_wl11060_wl11069_lane_b11.py`
**Acceptance checklist:**

- [x] Preserve `None` diff values without coercion.

### [WL-11067]

**Title:** Preserve notification-path response target resolution for turn/submit.
**Source:** `tests/protocols/test_wl11060_wl11069_lane_b11.py`
**Acceptance checklist:**

- [x] Resolve response-phase targets when `request_has_id` is false and request id is absent.

### [WL-11068]

**Title:** Preserve strict malformed-approval rejection in response target resolution.
**Source:** `tests/protocols/test_wl11060_wl11069_lane_b11.py`
**Acceptance checklist:**

- [x] Reject response-phase approval payloads with invalid field types.

### [WL-11069]

**Title:** Preserve success response result shape when no approval payload exists.
**Source:** `tests/protocols/test_wl11060_wl11069_lane_b11.py`
**Acceptance checklist:**

- [x] Omit `approval` key from success response when approval payload is absent.
