# Wave-2 Agent-B Execution Report (WL-107, WL-108, WL-109, WL-110, WL-114)

Date: 2026-02-21
Owner: agent-b

## Completed Slices

### WL-107 (Read-Only Review Structured Output)

- Added strict review output parser/validator module with fail-loud schema checks.
- Added focused tests for valid payload, invalid severity, and invalid JSON parse.
- Added top-level `thegent review` command surface that:
  - forces `mode="read-only"`
  - enforces structured JSON response contract
  - exits `1` when issues exist, else `0`

### WL-108 (Context Budget Indicator)

- Refactored context usage rendering into pure helper `compute_context_usage_display(...)`.
- Kept existing widget behavior while making threshold logic testable.
- Added tests for green/yellow/red thresholds and N/A behavior.

### WL-109 (MCP LSP Tools)

- Added `src/thegent/mcp/lsp_tools.py` adapter layer with deterministic payload shapes:
  - diagnostics
  - symbol lookup
  - hover
- Added strict validation for file existence and line/character coordinates.
- Registered MCP tool surfaces in `src/thegent/mcp/server.py`:
  - `thegent_lsp_diagnostics`
  - `thegent_lsp_symbol_lookup`
  - `thegent_lsp_hover`
- Added focused unit tests for success + invalid inputs.

### WL-110 (Stable Resume API)

- Added stable session state contract path helper and writer (`~/.thegent/sessions/<session_id>/state.json`).
- `bg_impl` now writes stable state contract for each new background session.
- Added `resume_impl(session_id=None, prompt=None)`:
  - resolves latest session when session id omitted
  - loads stable state contract
  - registers resume in run registry
  - optionally queues prompt via session input channel
- Updated CLI `resume_cmd` to use `resume_impl` and show state path/run id.
- Added `thegent run resume` command surface with optional `--prompt`.
- Added focused tests for state write, missing contract, and resume+prompt path.

### WL-114 (`--image` Background Support)

- Extended `bg_cmd` and `bg_impl` to accept repeatable image inputs.
- Added background path validation + codex-agent capability gating using existing WL-114 validators.
- Added forwarding of repeatable `--image` flags into spawned background command.
- Added focused test to verify `run agent --bg --image ...` forwards images to bg command.

## Validation

### Commands run

1. `python -m py_compile src/thegent/agents/review_output.py src/thegent/mcp/lsp_tools.py src/thegent/tui/widgets/statusbar.py src/thegent/cli/commands/impl.py src/thegent/cli/commands/cli.py src/thegent/cli/apps/run.py src/thegent/cli/apps/main.py tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py`

- Result: pass

2. `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py`

- Result: blocked by missing plugin import (`pytest_asyncio`) from repo conftest plugin declarations.

3. `python - <<'PY' ... targeted smoke checks for WL-107/108/109/110/114 helpers ... PY`

- Result: pass (`smoke-ok`)

## Blockers

- Test environment blocker: `pytest_asyncio` missing, causing pytest startup failure before focused test execution.
- WL-109 backend dependency blocker: adapter surfaces are registered and validated, but real diagnostics/symbol/hover execution still depends on configuring a concrete LSP backend adapter (currently explicit error path if unavailable).

## Exact Files Touched

- `src/thegent/agents/review_output.py`
- `src/thegent/mcp/lsp_tools.py`
- `src/thegent/tui/widgets/statusbar.py`
- `src/thegent/cli/commands/impl.py`
- `src/thegent/cli/commands/cli.py`
- `src/thegent/cli/apps/run.py`
- `src/thegent/cli/apps/main.py`
- `src/thegent/mcp/server.py`
- `tests/test_wl107_review_output.py`
- `tests/test_wl109_mcp_lsp_tools.py`
- `tests/test_wl110_resume_contract.py`
- `tests/test_wl108_wl114_slices.py`
- `.thegent/agent-batch/wave2-agent-b.md`
