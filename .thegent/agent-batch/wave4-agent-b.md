# Wave-4 Agent-B Execution Report (WL-107, WL-108, WL-109, WL-110, WL-114)

Date: 2026-02-21
Owner: agent-b

## Scope Completed

### WL-107: JSON output mode for `review` command + contract test

- Hardened `thegent review` output mode handling in `src/thegent/cli/apps/main.py`:
  - validates `--format` (`rich|json`) with explicit error exit for invalid values.
  - `--format json` now emits a stable contract payload including parsed review fields and `context_usage` when available.
  - rich mode keeps existing readable rendering.
- Added contract-focused CLI test in `tests/test_wl107_review_output.py`:
  - validates JSON payload shape/keys for `review --format json`.

### WL-108: Context budget in JSON output + status bar parity

- Extended context payload in `src/thegent/cli/commands/impl.py`:
  - `_append_context_usage(...)` now includes `display` + `level` using `compute_context_usage_display(...)` (same source as status bar).
- Updated CLI context line renderer in `src/thegent/cli/commands/cli.py`:
  - `_format_context_usage_line(...)` now prefers precomputed `display` (status bar parity) and falls back to recompute if missing.
- Wired review JSON mode to pass context usage through (`src/thegent/cli/apps/main.py`).
- Updated focused WL-108 tests in `tests/test_wl108_wl114_slices.py` to assert new parity fields.

### WL-109: Tightened LSP error mapping + unavailable backend integration test

- Improved backend error mapping in `src/thegent/mcp/lsp_tools.py`:
  - normalizes unavailable backend and unsupported adapter failures to deterministic `LSP_BACKEND_UNAVAILABLE`-prefixed errors.
- Improved MCP remediation mapping in `src/thegent/mcp/server/tools_workstream_lsp.py`:
  - unavailable-backend errors now return explicit backend-setup remediation text.
- Added/updated focused tests in `tests/test_wl109_mcp_lsp_tools.py`:
  - asserts unavailable backend maps to `LSP_BACKEND_UNAVAILABLE`.
  - adds integration-style tool handler test for remediation copy when backend is unavailable.

### WL-110: `thegent resume` no-arg most-recent behavior + tests

- Refined latest-session resolution in `src/thegent/cli/commands/impl.py`:
  - `_resolve_latest_session_id(...)` now prioritizes newest `state.json` (`updated_at_utc`) to choose most-recent resumable session.
  - retains metadata fallback when state contracts are absent.
- Added focused no-arg resume test in `tests/test_wl110_resume_contract.py`:
  - verifies `resume_impl()` picks most recent session by state timestamp.

### WL-114: URL image constraint validation + clearer error copy

- Tightened URL/path constraints in `src/thegent/cli/commands/impl.py`:
  - URL must be HTTPS.
  - URL must include hostname.
  - URL path must end with supported image extension (`.png/.jpg/.jpeg/.webp/.gif`).
  - clearer local file extension/missing-file error messages.
- Updated focused tests in `tests/test_wl108_wl114_slices.py` to cover new URL extension constraint and updated copy.

## Files Changed

- `src/thegent/cli/apps/main.py`
- `src/thegent/cli/commands/cli.py`
- `src/thegent/cli/commands/impl.py`
- `src/thegent/mcp/lsp_tools.py`
- `src/thegent/mcp/server/tools_workstream_lsp.py`
- `tests/test_wl107_review_output.py`
- `tests/test_wl108_wl114_slices.py`
- `tests/test_wl109_mcp_lsp_tools.py`
- `tests/test_wl110_resume_contract.py`
- `.thegent/agent-batch/wave4-agent-b.md`

## Focused Validation

### 1) Syntax / compile checks

- Command:
  - `python -m py_compile src/thegent/cli/apps/main.py src/thegent/cli/commands/cli.py src/thegent/cli/commands/impl.py src/thegent/mcp/lsp_tools.py src/thegent/mcp/server/tools_workstream_lsp.py tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py`
- Result: pass

### 2) Focused pytest (targeted WL suites)

- Command:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py`
- Result: blocked by environment plugin import error (`pytest_asyncio` missing).

### 3) Focused smoke checks for new behavior

- Command:
  - `python - <<'PY' ... targeted checks for WL-108 parity fields, WL-114 URL constraints, WL-110 no-arg latest-state resolution, WL-109 unavailable-backend mapping/remediation ... PY`
- Result: pass (`wave4-smoke-ok`)

## Notes

- Did not edit `docs/reference/WORK_STREAM.md`.
- Worktree is heavily dirty from concurrent edits; this wave touched only the files listed above.
