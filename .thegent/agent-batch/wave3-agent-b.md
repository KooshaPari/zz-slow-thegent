# Wave-3 Agent-B Execution Report (WL-107, WL-108, WL-109, WL-110, WL-114)

Date: 2026-02-21
Owner: agent-b

## Scope Completed

### WL-107: Harden structured review output path and CLI exit semantics

- Hardened `thegent review` in `src/thegent/cli/apps/main.py`:
  - catches structured-output parse/validation failures from `parse_review_output`
  - prints explicit validation error instead of surfacing traceback paths
  - returns explicit exit semantics:
    - `0` when parsed payload has no issues
    - `1` when parsed payload includes issues
    - `2` when output violates structured JSON contract
  - preserves underlying run exit code when `run_impl` fails.
- Added focused tests in `tests/test_wl107_review_output.py` for exit semantics (0/1/2).

### WL-108: Wire context budget display helper into an end-user rendering path

- Added `_format_context_usage_line(...)` in `src/thegent/cli/commands/cli.py`.
- Wired this helper into `run_cmd(...)` so foreground CLI output now surfaces context usage (when available) using `compute_context_usage_display(...)` from the statusbar helper.
- Added focused assertion in `tests/test_wl108_wl114_slices.py`.

### WL-109: Concrete LSP backend adapter path + guarded fallback

- Implemented concrete Python backend adapter in `src/thegent/mcp/lsp_tools.py`:
  - `_PythonAstAdapter.diagnostics(...)` uses Python compile checks for syntax diagnostics
  - `_PythonAstAdapter.symbol_lookup(...)` uses AST symbol discovery
  - `_PythonAstAdapter.hover(...)` computes token-at-position and resolves local definition metadata
- Added guarded adapter resolution via `_resolve_default_adapter(...)`:
  - default concrete path for `.py` files
  - explicit guarded failure (`_UnavailableAdapter`) for unsupported/unconfigured paths
  - supports explicit env override `THGENT_LSP_ADAPTER=python-ast`.
- Added focused integration-style tests in `tests/test_wl109_mcp_lsp_tools.py` for:
  - concrete default Python diagnostics path
  - concrete symbol+hover path
  - guarded non-Python fallback failure.

### WL-110: Top-level human-facing `resume` passthrough

- Added top-level `thegent resume` command in `src/thegent/cli/apps/main.py` as passthrough to `resume_cmd` (stable contract path).
- Added focused passthrough test in `tests/test_wl110_resume_contract.py`.

### WL-114: Vision capability validation for `--image` across fg/bg flows

- Added strict model capability checks in `src/thegent/cli/commands/impl.py`:
  - `_model_supports_vision(model)` loads catalog metadata from `src/thegent/agents/cliproxy_data/model_indices.json`
  - `_validate_image_capability(agent, model)` enforces:
    - agent image support (`CODEX_AGENTS`)
    - model-level vision capability when model is specified
- Wired this validation into both foreground (`run_impl`) and background (`bg_impl`) `--image` paths.
- Added focused capability rejection test in `tests/test_wl108_wl114_slices.py`.

## Files Touched

- `src/thegent/cli/apps/main.py`
- `src/thegent/cli/commands/cli.py`
- `src/thegent/cli/commands/impl.py`
- `src/thegent/mcp/lsp_tools.py`
- `tests/test_wl107_review_output.py`
- `tests/test_wl108_wl114_slices.py`
- `tests/test_wl109_mcp_lsp_tools.py`
- `tests/test_wl110_resume_contract.py`
- `.thegent/agent-batch/wave3-agent-b.md`

## Validation

### 1) Syntax / compile checks

- Command:
  - `python -m py_compile src/thegent/cli/apps/main.py src/thegent/cli/commands/cli.py src/thegent/cli/commands/impl.py src/thegent/mcp/lsp_tools.py tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py`
- Result: pass

### 2) Focused pytest (targeted WL tests)

- Command:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py`
- Result: blocked by environment plugin import error (`pytest_asyncio` missing from repo-level plugin loading).

### 3) Focused runtime smoke checks

- Command:
  - `python - <<'PY' ... targeted WL-107/108/109/114 checks ... PY`
- Result: pass (`wave3-smoke-ok`)

## Notes

- No changes were made to `docs/reference/WORK_STREAM.md`.
- Worktree is heavily dirty from concurrent edits; this slice only changed the files listed above.
