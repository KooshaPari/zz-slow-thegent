# Wave 13 Agent A Report

## Objective

Deliver one additional reliability/integration slice per item: `WL-102`, `WL-103`, `WL-105`, `WL-101`, `WL-078`, with focused tests/docs.

## Completed slices

### WL-102: SDK nested error-title extraction for `errors` payloads

- Extended SDK HTTP error detail extraction to accept nested `title` fields in structured error payloads.
- Added focused test for payload shape like `{"errors": [{"title": "..."}]}` to ensure `ThegentRequestError.detail` remains actionable.

Files:

- `packages/thegent-sdk/src/thegent_sdk/client.py`
- `packages/thegent-sdk/tests/test_client.py`

### WL-103: Litellm context usage ratio saturation in proxy runner

- Hardened `CodexProxyRunner` litellm path to normalize context usage ratio into `[0.0, 1.0]` before emitting run metrics.
- Ensures `context_tokens_used` stays bounded by configured context window in output contracts.
- Added focused wiring test for over-limit compaction ratios.

Files:

- `src/thegent/agents/codex_proxy.py`
- `tests/test_wl103_context_compactor_wiring.py`

### WL-105: Dynamic tool description non-empty contract

- Hardened dynamic tool registration to require non-empty string descriptions (same fail-loud semantics as session/tool name validation).
- Added focused registry test for blank description rejection.

Files:

- `src/thegent/mcp/dynamic_tools.py`
- `tests/mcp/test_dynamic_tools.py`

### WL-101: Explicit blank-skill rejection in `skill select`

- Added explicit `thegent skill select` validation for post-trim empty names with deterministic error text.
- Added focused CLI test covering whitespace-only input.

Files:

- `src/thegent/cli/apps/skills.py`
- `tests/test_wl101_skill_selection_cli.py`

### WL-078: Benchmark boolean-average input rejection

- Hardened benchmark regression parser to reject boolean `avg_microseconds` values (avoid Python bool→float coercion ambiguity).
- Added focused regression test for boolean average payloads.

Files:

- `scripts/check_python_benchmark_regression.py`
- `tests/performance/test_python_benchmark_regression.py`

## Validation

- `uv run python -m py_compile packages/thegent-sdk/src/thegent_sdk/client.py src/thegent/agents/codex_proxy.py src/thegent/mcp/dynamic_tools.py src/thegent/cli/apps/skills.py scripts/check_python_benchmark_regression.py`
  - Result: success
- `uv run pytest -q packages/thegent-sdk/tests/test_client.py tests/test_wl103_context_compactor_wiring.py tests/mcp/test_dynamic_tools.py tests/test_wl101_skill_selection_cli.py tests/performance/test_python_benchmark_regression.py`
  - Result: `93 passed in 6.67s`

## Constraints check

- Did not edit `docs/reference/WORK_STREAM.md`.
