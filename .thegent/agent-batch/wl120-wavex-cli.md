# WL-120 Wave X — `cli.py` Extraction Report

## Scope

Focused file: `src/thegent/cli/commands/cli.py`

Extracted one cohesive cluster from `cli.py`:

- Private helper compatibility re-exports for `_cli_shared` symbols.

## What Changed

1. Shifted private compatibility export ownership into existing extracted module `src/thegent/cli/commands/_cli_shared.py`.

- Added explicit `_CLI_PRIVATE_COMPAT_EXPORTS` list.
- Added explicit `__all__` contract that exports:
  - Existing non-private shared names.
  - Required private compatibility names previously re-imported explicitly from `cli.py`.

2. Simplified `src/thegent/cli/commands/cli.py`.

- Removed the large explicit private import block:
  `from thegent.cli.commands._cli_shared import (...)`
- Kept wildcard export wiring:
  `from thegent.cli.commands._cli_shared import *`
- Backward compatibility preserved because `_cli_shared.__all__` now carries the private surface.

3. Added focused extraction routing tests in `tests/commands/test_wl120_extraction_import_routing.py`:

- Verifies `cli.py` no longer uses explicit private `_cli_shared` import block.
- Verifies `_cli_shared.__all__` includes private compatibility exports.
- Verifies `cli.py` still exposes private helper names for legacy imports.

## LOC Delta

- `src/thegent/cli/commands/cli.py`: **109 -> 49** (**-60 LOC**).
- Wave-X patch (this slice) net estimate: **+44 LOC** across touched files.
  - Rationale: removed explicit import block in `cli.py`, added explicit export contract + tests.

## Validation

Executed:

1. `uv run pytest -q tests/commands/test_wl120_extraction_import_routing.py tests/cli/test_wl136_tooling_routing.py tests/test_wl124_cli_split.py`

- Result: **405 passed, 1 skipped**.

2. `python -m py_compile src/thegent/cli/commands/cli.py src/thegent/cli/commands/_cli_shared.py tests/commands/test_wl120_extraction_import_routing.py`

- Result: **pass**.

## Compatibility/Wiring Outcome

- `thegent.cli.commands.cli` remains a backward-compatible re-export shim.
- Private helper names remain importable from `thegent.cli.commands.cli` via `_cli_shared.__all__` wildcard export.
- No command-surface behavior changes introduced in this slice.
