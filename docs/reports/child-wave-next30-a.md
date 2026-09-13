# Child Wave Next30 - Lane A

- Assigned: `CLIP-BUG-01`, `CLIP-BUG-02`, `CLIP-BUG-03`, `CLIP-BUG-04`, `CLIP-BUG-05`
- Status: complete

## Changes

- `src/thegent/routing/harness_model_mapping.py`
- `src/thegent/cliproxy_request_transform.py`
- `src/thegent/routing/litellm_responses_handler.py`
- `tests/test_unit_cliproxy_adapter.py`
- `tests/routing/test_litellm_responses_handler.py`

## Validation

- `.venv/bin/python -m pytest -q -p no:tach tests/test_integration_cliproxy_adapter.py tests/test_unit_cliproxy_adapter.py tests/routing/test_litellm_responses_handler.py tests/test_unit_cliproxy_manager.py` (124 passed)
