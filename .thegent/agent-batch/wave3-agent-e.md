# Wave 3 - Agent E Report

## Scope

Implemented follow-up slices:

- WL-121: boundary checker enforcement in a default quality lane (non-breaking)
- WL-123: strict-mode deprecated alias checker wiring + migration note
- WL-124: first domain module extraction wiring with compatibility shim
- WL-125: first service/helper extraction parity hardening + tests
- WL-126: first bounded `mcp/server` extraction with stable import surface

## Changes

### WL-121

- Added advisory boundary checker into default `quality_project` lane (invoked by `task quality`).
- File:
  - `Taskfile.yml`
- Details:
  - `quality_project` now runs `scripts/check_thegent_core_boundary.py` as non-blocking advisory.

### WL-123

- Added task wiring for deprecated alias checker:
  - `quality:deprecated-aliases` (non-strict audit)
  - `quality:deprecated-aliases:strict` (non-zero when deprecated aliases/canonical gaps remain)
- Added migration note in quality docs with canonical command guidance.
- Files:
  - `Taskfile.yml`
  - `docs/guides/QUALITY_ASSURANCE.md`
  - `tests/test_wl123_deprecated_quality_aliases.py` (strict-mode test)

### WL-124

- Wired extracted domain module into top-level CLI app:
  - Registered `domain` app in `thegent` command tree.
- Added parity-safe legacy shim:
  - Hidden `thegent domain-map` command delegates to extracted domain module.
- Files:
  - `src/thegent/cli/apps/main.py`
  - `tests/commands/test_domain_map.py` (includes shim coverage)

### WL-125

- Hardened extracted observability service module to avoid import-cycle regressions by lazy-loading heavy symbols inside helper function.
- File:
  - `src/thegent/cli/services/observability.py`

### WL-126

- Added stable import surface module for catalog MCP tool handlers:
  - `src/thegent/mcp/server_catalog_tools.py`
- Switched `mcp/server.py` to import stable module directly instead of dynamic file loading for that bounded extraction.
- Fixed two incorrect dynamic-loader paths (`server/server/...`) discovered during focused validation.
- Added stable-surface assertion test.
- Files:
  - `src/thegent/mcp/server.py`
  - `src/thegent/mcp/server_catalog_tools.py`
  - `tests/test_wl124_125_126_monolith_baselines.py`

## Focused Validation

### Tests

- `uv run pytest -q tests/test_wl121_core_boundary_checker.py tests/test_wl123_deprecated_quality_aliases.py tests/test_wl124_125_126_monolith_baselines.py tests/commands/test_domain_map.py tests/test_unit_cli_services_observability.py`
  - Result: `18 passed`
- `uv run pytest -q tests/test_unit_mcp_server_deep.py::TestThegentListOperationsTool::test_list_all_operations tests/test_unit_mcp_server_deep.py::TestThegentListModesTool::test_list_all_modes`
  - Result: `2 passed`

### Commands

- `uv run python scripts/check_thegent_core_boundary.py`
  - Result: pass (`thegent-core boundary check passed.`)
- `uv run python scripts/check_deprecated_quality_aliases.py`
  - Result: audit output produced (non-strict, exit 0)
- `uv run python scripts/check_deprecated_quality_aliases.py --strict`
  - Result: expected non-zero exit with current deprecated alias inventory
- `uv run python scripts/collect_wl_monolith_baselines.py --format text`
  - Result: baseline metrics emitted for WL-124/WL-125/WL-126 targets

## Notes

- Existing repo contains broad unrelated edits; this slice only touched targeted WL files above.
- `docs/reference/WORK_STREAM.md` was not modified.
