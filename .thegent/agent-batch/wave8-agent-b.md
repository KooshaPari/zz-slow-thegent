# Wave 8 Agent B Report (WL-107, WL-108, WL-109, WL-110, WL-114)

Date: 2026-02-21

## Scope Completed

### Do-next objective: harden schema/contracts + fix one flaky path

- Implemented contract hardening in WL-110 resume state handling.
- Fixed a deterministic-selection flake in WL-110 latest-session resolution.

### WL-110: state contract hardening

- Updated `resume_impl(...)` in `src/thegent/cli/commands/impl.py` to validate state contract payload shape before resume side effects:
  - fail fast on invalid JSON state payloads
  - require state payload to be an object
  - require non-empty `session_id`
  - require `session_id` in payload to match requested session
  - preserve existing strict `run_id` requirement

### Flaky path fix (WL-110)

- Updated `_resolve_latest_session_id(...)` in `src/thegent/cli/commands/impl.py` to remove glob-order nondeterminism:
  - iterate `state.json` and fallback meta files in sorted order
  - compare parsed ISO timestamps + `session_id` tuple for deterministic tie-breaking
- Updated `_find_session_meta(...)` to sort glob matches before selecting.

### Tests added

- `tests/test_wl110_resume.py`
  - added deterministic tie-break test when `updated_at_utc` timestamps are equal
- `tests/test_wl110_resume_contract.py`
  - added invalid-JSON state contract rejection test
  - added payload/request `session_id` mismatch rejection test

## Files Changed

- `src/thegent/cli/commands/impl.py`
- `tests/test_wl110_resume.py`
- `tests/test_wl110_resume_contract.py`
- `.thegent/agent-batch/wave8-agent-b.md`

## Focused Validation

- `UV_NO_SYNC=1 uv run pytest -q tests/test_wl110_resume.py tests/test_wl110_resume_contract.py`
  - Result: `36 passed`
- Earlier WL slice checks in this session before patching:
  - `UV_NO_SYNC=1 uv run pytest -q tests/test_wl107_review_cmd.py tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py`
    - Result: `57 passed`
  - `UV_NO_SYNC=1 uv run pytest -q tests/test_wl109_lsp_tools.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume.py tests/test_wl110_resume_contract.py tests/test_wl114_image_flag.py`
    - Result: `101 passed`

## Constraints Check

- Did not edit `docs/reference/WORK_STREAM.md`.
- Kept edits scoped to WL-110 contract and flake hardening within wave scope and report output path.
