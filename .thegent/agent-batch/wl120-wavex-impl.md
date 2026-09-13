# WL-120 Extraction Wave X (impl.py)

## Scope

Focused file: `src/thegent/cli/commands/impl.py`.

Cohesive slice extracted: explicit Ollama provider validation helper.

- Moved full `_validate_explicit_ollama_provider` logic out of `impl.py` into `src/thegent/cli/services/run_model_helpers.py` as:
  - `validate_explicit_ollama_provider(*, provider, model)`
- Kept `impl.py` compatibility surface intact by converting `_validate_explicit_ollama_provider` to a thin wrapper that delegates to the service helper.
- Preserved call sites in `run_impl` and `bg_impl` (behavior unchanged by interface).

## Files Changed

- `src/thegent/cli/commands/impl.py`
- `src/thegent/cli/services/run_model_helpers.py`
- `tests/test_wl125_run_model_helpers_parity.py`

## Parity Tests Added

Added wrapper delegation parity test:

- `test_wl120_wavex_validate_explicit_ollama_provider_wrapper_delegates`
  - Verifies `impl._validate_explicit_ollama_provider(...)` delegates to `run_model_helpers.validate_explicit_ollama_provider(...)` with unchanged arguments and return passthrough.

## LOC Delta (slice-level)

Measured slice size after extraction:

- Helper body in service: 44 LOC (`run_model_helpers.py:41-84`)
- Wrapper in impl: 4 LOC (`impl.py:602-605`)
- New parity test: 15 LOC (`tests/test_wl125_run_model_helpers_parity.py:29-43`)

Net for this extraction slice:

- `impl.py`: -40 LOC (44 moved out, 4-line wrapper retained)
- Service + tests: +59 LOC
- Overall changed surface for this slice: +19 LOC

## Validation

Initial direct pytest invocation failed due environment plugin mismatch:

- `pytest -q ...` -> `ImportError: No module named 'pytest_asyncio'`

Project-managed validation (successful):

1. `uv run pytest -q tests/test_wl125_run_model_helpers_parity.py`
   - Result: `2 passed`
2. `uv run pytest -q tests/test_wl118_ollama_run_cmd.py`
   - Result: `4 passed`

## Behavior Preservation Notes

- Error messages and decision branches for explicit Ollama checks are unchanged; logic was relocated verbatim into the service helper.
- `impl.py` public helper name and call signatures remain available for existing imports and tests.
