# Wave 12 Agent A Report

## Objective

Deliver one additional reliability/integration slice per item: `WL-102`, `WL-103`, `WL-105`, `WL-101`, `WL-078`, with focused tests/docs.

## Completed slices

### WL-102: SDK error detail extraction for `errors` payloads

- Extended HTTP error detail extraction to inspect top-level `errors` alongside existing `detail/error/message` keys.
- Added a focused SDK test for payloads like `{"errors": [{"msg": "..."}]}` to ensure first useful message is surfaced as `ThegentRequestError.detail`.

Files:

- `packages/thegent-sdk/src/thegent_sdk/client.py`
- `packages/thegent-sdk/tests/test_client.py`

### WL-103: Context usage ratio clamp in shared payload builder

- Hardened `build_context_usage_payload` to only accept override ratios in `[0.0, 1.0]`.
- Out-of-range override ratios now fall back to computed ratio from `used/max_tokens`.
- Added focused test for ratio `> 1.0` fallback behavior.

Files:

- `src/thegent/cli/services/run_input_helpers.py`
- `tests/test_wl108_wl114_slices.py`

### WL-105: Fail-loud string contract for dynamic tool registry identifiers

- Hardened registry normalization helper to reject non-string identifier inputs with explicit `ValueError`.
- Prevents accidental `AttributeError` from `.strip()` on non-string runtime payloads.
- Added focused test for non-string `session_id` in `list_dynamic_tools`.

Files:

- `src/thegent/mcp/dynamic_tools.py`
- `tests/mcp/test_dynamic_tools.py`

### WL-101: Broader control-character rejection for `skill select`

- Strengthened `thegent skill select` validation to reject all ASCII control characters (`0x00-0x1F`, `0x7F`) in skill names.
- Added focused test for unit-separator (`\x1f`) rejection.

Files:

- `src/thegent/cli/apps/skills.py`
- `tests/test_wl101_skill_selection_cli.py`

### WL-078: Benchmark label type contract hardening

- Tightened benchmark row validation to require `label` values be actual strings (not implicit coercions).
- Added focused regression test for numeric labels being rejected.

Files:

- `scripts/check_python_benchmark_regression.py`
- `tests/performance/test_python_benchmark_regression.py`

## Validation

- `uv run python -m py_compile packages/thegent-sdk/src/thegent_sdk/client.py src/thegent/cli/services/run_input_helpers.py src/thegent/mcp/dynamic_tools.py src/thegent/cli/apps/skills.py scripts/check_python_benchmark_regression.py`
  - Result: success
- `uv run pytest -q packages/thegent-sdk/tests/test_client.py tests/test_wl108_wl114_slices.py tests/mcp/test_dynamic_tools.py tests/test_wl101_skill_selection_cli.py tests/performance/test_python_benchmark_regression.py`
  - Result: `117 passed in 27.55s`

## Constraints check

- Did not edit `docs/reference/WORK_STREAM.md`.
