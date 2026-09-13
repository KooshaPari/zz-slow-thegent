### [WL-10960]

**Title:** Preserve request-id behavior for response-id extraction when no id is required
**Source:** `tests/protocols/test_wl10960_wl10969_lane_c4.py`
**Acceptance checklist:**

- [x] Add regression for `request_has_id=False` returning `None`.
- [x] Confirm helper does not require response id in this mode.
- [x] Keep behavior stable for response-id optional path.
      **Notes:** Covered by `test_wl10960_*`.

### [WL-10961]

**Title:** Preserve numeric request-id passthrough during response target extraction
**Source:** `tests/protocols/test_wl10960_wl10969_lane_c4.py`
**Acceptance checklist:**

- [x] Add regression for floating-point request id extraction.
- [x] Confirm no coercion of id types.
- [x] Keep stable on valid numeric input.
      **Notes:** Covered by `test_wl10961_*`.

### [WL-10962]

**Title:** Preserve boolean rejection for request-id resolution in response target parsing
**Source:** `tests/protocols/test_wl10960_wl10969_lane_c4.py`
**Acceptance checklist:**

- [x] Add regression that boolean ids raise target resolution errors.
- [x] Keep fail-fast behavior for invalid request id values.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10962_*`.

### [WL-10963]

**Title:** Preserve invalid approval payload-shape guard in response target resolution
**Source:** `tests/protocols/test_wl10960_wl10969_lane_c4.py`
**Acceptance checklist:**

- [x] Add regression for non-dict approval payload failure.
- [x] Keep resolver fail-fast on malformed response-phase shape.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10963_*`.

### [WL-10964]

**Title:** Preserve structured return contract for response-resolution phase build
**Source:** `tests/protocols/test_wl10960_wl10969_lane_c4.py`
**Acceptance checklist:**

- [x] Add regression that phase build outputs expected tuple values.
- [x] Ensure no mutation through build/resolve path.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10964_*`.

### [WL-10965]

**Title:** Preserve notification-first behavior for approval-required turn submission
**Source:** `tests/protocols/test_wl10960_wl10969_lane_c4.py`
**Acceptance checklist:**

- [x] Add regression for in-band approval state and notifications when no request id.
- [x] Preserve suppression of synchronous result response in this path.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10965_*`.

### [WL-10966]

**Title:** Preserve approval payload echo when request id is present
**Source:** `tests/protocols/test_wl10960_wl10969_lane_c4.py`
**Acceptance checklist:**

- [x] Add regression for approval payload in synchronous response.
- [x] Verify `turn/started` notification is emitted in approval path.
- [x] Keep response payload shape stable.
      **Notes:** Covered by `test_wl10966_*`.

### [WL-10967]

**Title:** Preserve whitespace rejection for approval diff input
**Source:** `tests/protocols/test_wl10960_wl10969_lane_c4.py`
**Acceptance checklist:**

- [x] Add regression for whitespace-only diff validation rejection.
- [x] Keep parse error reason stable.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10967_*`.

### [WL-10968]

**Title:** Preserve completed-turn path when no approval is required
**Source:** `tests/protocols/test_wl10960_wl10969_lane_c4.py`
**Acceptance checklist:**

- [x] Add regression for completed turn result shape without approvals.
- [x] Verify terminal `status` and `tool_call_id` values are populated.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10968_*`.

### [WL-10969]

**Title:** Preserve non-mutating payload shape for turn submit success response
**Source:** `tests/protocols/test_wl10960_wl10969_lane_c4.py`
**Acceptance checklist:**

- [x] Add regression asserting exact response payload shape.
- [x] Confirm no in-place mutation via builder function.
- [x] Add focused regression coverage.
      **Notes:** Covered by `test_wl10969_*`.
