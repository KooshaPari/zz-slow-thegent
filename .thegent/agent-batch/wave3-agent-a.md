# Wave 3 Agent A (2026-02-21)

## Completed slices

- WL-103
  - Integrated `ContextCompactor` into a real runner path in `CodexProxyRunner` LiteLLM API execution.
  - Added `_prepare_litellm_messages(...)` to build message turns, compact oversized context, and propagate context usage telemetry (`context_tokens_used`, `context_window_max`) into `RunResult`.
  - Added focused wiring test for compaction behavior with large activated-skill context.

- WL-105
  - Wired `DynamicToolRegistry` into one MCP session-turn path via `thegent_session_send` helper flow in `src/thegent/mcp/server/tools_sessions.py`.
  - Added session message types:
    - `dynamic_tool_register`
    - `dynamic_tool_list`
    - `dynamic_tool_invoke`
  - Added deterministic reset hook for tests and focused tests for register/list/invoke + input validation.

- WL-102
  - Expanded SDK with streaming API surface:
    - `ThegentClient.run_stream(...)` (line-delimited JSON stream events from `/v1/run`)
    - `StreamEvent` typed DTO + parser.
  - Added SDK unit tests for stream success, malformed stream line handling, and HTTP error behavior.
  - Updated SDK README API surface docs.

- WL-078
  - Added CI-friendly benchmark regression smoke command:
    - `task bench:smoke:ci`
  - Added CI workflow hook step to run benchmark smoke in `.github/workflows/ci.yml` quality job.
  - Added quality guide documentation hook for the smoke command.

- WL-101
  - Added CLI skill selection surface for execution paths:
    - `thegent run agent ... --skill <name>` (repeatable)
    - prompt-time skill instruction injection via `_inject_skill_instructions(...)` in CLI command layer.
  - Added `thegent skill select <name>` helper command for selection/usage alignment.
  - Updated README + docsite CLI docs to align list/selection usage.
  - Added focused tests for skill injection behavior and missing-skill failure path.

## Validation

- `uv run python -m py_compile src/thegent/agents/codex_proxy.py src/thegent/mcp/server/tools_sessions.py src/thegent/cli/commands/cli.py src/thegent/cli/apps/run.py src/thegent/cli/apps/skills.py packages/thegent-sdk/src/thegent_sdk/client.py packages/thegent-sdk/src/thegent_sdk/types.py scripts/check_python_benchmark_regression.py`
  - Passed.

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -q tests/test_wl103_context_compactor_wiring.py tests/mcp/test_tools_sessions_dynamic_registry.py tests/test_wl101_skill_selection_cli.py tests/performance/test_python_benchmark_regression.py packages/thegent-sdk/tests/test_client.py`
  - Passed: `22 passed`.

- `mkdir -p benchmarks/results/python && cp benchmarks/baseline.json benchmarks/results/python/ci-smoke.json && uv run python scripts/check_python_benchmark_regression.py --baseline benchmarks/baseline.json --current benchmarks/results/python/ci-smoke.json --max-regression-pct 15`
  - Passed: `{"ok": true, "max_regression_pct": 15.0}`.

## Blockers

- `task bench:smoke:ci` cannot currently be executed in this workspace due a pre-existing Task parser failure unrelated to this slice:
  - `Taskfile.yml:121:9 invalid keys in command`
  - This parser error occurs before task execution and predates this wave’s edits.

## Exact files touched

- `.thegent/agent-batch/wave3-agent-a.md`
- `.github/workflows/ci.yml`
- `Taskfile.yml`
- `README.md`
- `docs/guides/QUALITY_ASSURANCE.md`
- `docs/site/guide/cli-reference.md`
- `docs/site/guide/getting-started.md`
- `packages/thegent-sdk/README.md`
- `packages/thegent-sdk/src/thegent_sdk/__init__.py`
- `packages/thegent-sdk/src/thegent_sdk/client.py`
- `packages/thegent-sdk/src/thegent_sdk/types.py`
- `packages/thegent-sdk/tests/test_client.py`
- `src/thegent/agents/codex_proxy.py`
- `src/thegent/cli/apps/run.py`
- `src/thegent/cli/apps/skills.py`
- `src/thegent/cli/commands/cli.py`
- `src/thegent/mcp/server/tools_sessions.py`
- `tests/mcp/test_tools_sessions_dynamic_registry.py`
- `tests/test_wl101_skill_selection_cli.py`
- `tests/test_wl103_context_compactor_wiring.py`
