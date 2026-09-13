# Wave 4 - Agent E Report

## Scope

Implemented the assigned Wave-4 slices:

- WL-121: boundary checker strict switch for CI with non-breaking default behavior
- WL-123: alias migration utility + replacement suggestion docs/wiring
- WL-124: one additional CLI command group extraction with backward-compatible wrappers
- WL-125: one additional impl helper/service extraction with parity tests
- WL-126: one additional MCP helper split into dedicated module with safe re-export

## Changes

### WL-121

- Added strict/advisory mode switch to the boundary checker:
  - default mode remains advisory (prints violations, exits 0)
  - `--strict` enables CI-failing mode (exits non-zero on violations)
- Added task wiring:
  - `quality:core-boundary` (advisory)
  - `quality:core-boundary:strict` (strict)
- Files:
  - `scripts/check_thegent_core_boundary.py`
  - `Taskfile.yml`
  - `tests/test_wl121_core_boundary_checker.py`

### WL-123

- Added concrete deprecated-alias replacement map and migration output mode:
  - `--format migration` prints `legacy -> canonical` suggestions
- Added task wiring:
  - `quality:deprecated-aliases`
  - `quality:deprecated-aliases:strict`
- Documented migration + strict usage in QA guide.
- Files:
  - `scripts/check_deprecated_quality_aliases.py`
  - `Taskfile.yml`
  - `docs/guides/QUALITY_ASSURANCE.md`
  - `tests/test_wl123_deprecated_quality_aliases.py`

### WL-124

- Extracted a small CLI command group from monolith `cli.py`:
  - new module: `src/thegent/cli/commands/team_commands.py`
  - moved handlers: `team_create_cmd`, `team_task_add_cmd`, `team_task_list_cmd`
- Preserved backward compatibility:
  - same function names remain in `cli.py` as wrappers delegating to extracted module.
- Files:
  - `src/thegent/cli/commands/team_commands.py`
  - `src/thegent/cli/commands/cli.py`
  - `tests/commands/test_team_commands_compat.py`
  - `tests/test_wl124_125_126_monolith_baselines.py`

### WL-125

- Extracted additional impl helper/service:
  - new module: `src/thegent/cli/services/run_input_helpers.py`
  - moved logic for image input normalization/capability checks, context usage payload shaping, and grounding-source resolution
- Preserved backward compatibility:
  - private helper names in `impl.py` remain and delegate to service module.
- Files:
  - `src/thegent/cli/services/run_input_helpers.py`
  - `src/thegent/cli/commands/impl.py`
  - `tests/test_wl125_run_input_helpers_parity.py`
  - `tests/test_wl124_125_126_monolith_baselines.py`

### WL-126

- Split one additional MCP server helper into dedicated module:
  - new: `src/thegent/mcp/server_result_helpers.py` (`stable_json`, `error_result`)
- Safe re-export:
  - `src/thegent/mcp/__init__.py` now re-exports as `server_stable_json` / `server_error_result`
- `server.py` now aliases these shared helpers via extracted module surface.
- Files:
  - `src/thegent/mcp/server_result_helpers.py`
  - `src/thegent/mcp/__init__.py`
  - `src/thegent/mcp/server.py`
  - `tests/test_wl124_125_126_monolith_baselines.py`

## Focused Validation

### Syntax/Compile

- `python -m py_compile scripts/check_thegent_core_boundary.py scripts/check_deprecated_quality_aliases.py src/thegent/cli/commands/team_commands.py src/thegent/cli/services/run_input_helpers.py src/thegent/mcp/server_result_helpers.py`
  - result: pass

### Targeted test suites

- `uv run pytest -q tests/test_wl121_core_boundary_checker.py tests/test_wl123_deprecated_quality_aliases.py tests/test_wl124_125_126_monolith_baselines.py tests/commands/test_team_commands_compat.py tests/test_wl125_run_input_helpers_parity.py`
  - result: `21 passed`

### Script/task checks

- `uv run python scripts/check_thegent_core_boundary.py`
  - result: pass (advisory default)
- `uv run python scripts/check_thegent_core_boundary.py --strict`
  - result: pass in current tree (no current boundary violations)
- `uv run python scripts/check_deprecated_quality_aliases.py --format migration`
  - result: emitted replacement suggestions + missing canonical commands
- `uv run python scripts/check_deprecated_quality_aliases.py --strict`
  - result: non-zero (expected with currently-present deprecated aliases)
- `task quality:core-boundary`
  - result: pass
- `task quality:deprecated-aliases`
  - result: pass (advisory output)
- `task quality:deprecated-aliases:strict`
  - result: non-zero (expected strict behavior)

### Noted unrelated failure during broader focused run

- Command:
  - `uv run pytest -q tests/test_wl121_core_boundary_checker.py tests/test_wl123_deprecated_quality_aliases.py tests/test_wl124_125_126_monolith_baselines.py tests/commands/test_team_commands_compat.py tests/test_wl125_run_input_helpers_parity.py tests/test_wl108_wl114_slices.py tests/test_wl119_grounding_sources.py`
- Result:
  - 1 failing test: `tests/test_wl108_wl114_slices.py::test_wl114_run_agent_bg_forwards_image_to_bg_cmd`
  - failure surface: remote execution path uses `OptionInfo` in subprocess args (`TypeError`), unrelated to wave-4 WL edits above.

## Notes

- `docs/reference/WORK_STREAM.md` was not modified.
- Unrelated working tree changes were left untouched.
