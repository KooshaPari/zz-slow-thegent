<DONE>
# Conversation Dump 2026-02-21 — Pyright Zero-Error Sweep

## Session Goal

Eliminate ALL Pyright type errors from the thegent codebase. Started session at 1218+ errors, previous session had brought it to 276, this session completes the sweep.

## Final Result

**0 errors, 0 warnings** (down from 1218+ at start of multi-session effort)

## Fixes Applied This Session

### infra/fast\_\*.py — Forbidden import fallbacks removed

- `fast_file_watcher.py`: Replaced `try/except ImportError` blocks with mandatory direct imports from `watchfiles` and `watchdog`. Set `WATCHFILES_AVAILABLE = True` and `WATCHDOG_AVAILABLE = True` unconditionally. Fixed `_observer` type to `Any` (watchdog Observer not statically typed). Fixed `__exit__` and `on_any_event` param naming.
- `fast_compression.py`: Same pattern — direct imports of `brotli` and `zstandard as zstd`.
- `fast_http_client.py`: Same pattern — direct imports of `curl_cffi` and `httpx`.

### prompts.py

- Removed `Optional` unused import
- Removed unused `_resolve_project_root` function (never called anywhere)
- Fixed `CURSOR_PROJECTS / folder` — added `if CURSOR_PROJECTS is None: return None` guard
- Fixed `return None, []` → `return None` (return type is `tuple[...] | None`, not `tuple[None, ...]`)

### tui/session_state.py

- Removed `except OSError as e: pass` silent error handlers (FORBIDDEN). Both `save_session` and `save_layout` now let OSError propagate (fail loud).

### tui/widgets/dialog.py

- Renamed `toast = Toast(...)` → `_toast = Toast(...)` (unused variable)

### task/types.py

- Changed `default_factory=TaskMetadata` → `default_factory=lambda: TaskMetadata()` (Pydantic requires callable, not class directly)

### team/coordination.py

- Changed `return None` on timeout → `raise TimeoutError(...)` (fail loud; return type was `dict[str, Any | None]`)

### terminal_cli.py

- Added `assert pane_id is not None` before subprocess.run to narrow the type

### utils/ fixes

- `agslag.py`: Fixed `from .deep_research import` → `from thegent.skills.deep_research import` (correct module path)
- `batch_operations.py`: Changed `next(..., None)` → `next(...)` (removes the Optional from the type, StopIteration on miss is correct behavior)
- `terminal_capture.py`: Added `# type: ignore[reportMissingImports]` on `from termitty import VirtualTerminal` (optional native dep, used inside try/except)
- `batch_file_ops.py`: Added `# type: ignore[reportMissingImports]` on `import thegent_fs` (native C extension)

### resources/

- `__init__.py`: Removed `try: import importlib.resources; except ImportError: import importlib_resources` fallback. Python 3.14 target; `importlib.resources` is always available. Direct import only.
- `distributed.py`: Fixed `import importlib` → `import importlib.util` (needed for `importlib.util.find_spec`)

### skills/deep_research.py

- Fixed mangled sed output: `from bs4 import BeautifulSoup  # type: ignore[reportMissingImports]`

### trace/integration.py

- Fixed `RecorderConfig(trace_dir=trace_dir)` → `RecorderConfig(trace_dir=str(trace_dir))` (param expects `str`, not `Path`)

### contracts/**init**.py

- Removed `ADAPTER_REGISTRY`, `AdapterResult`, `OutputAdapter`, `normalize_output` from `__all__` (provided via `__getattr__` lazy-loading, Pyright can't verify them)

### research/**init**.py

- Removed `AutonomousLearningSurface` from `__all__` (module/class doesn't exist)

### trace/**init**.py

- Removed `"replay"` from `__all__` (no `replay` module exists in `trace/`)

### tools/terminal_capture.py

- Removed the never-called `_is_tmux_available` function

### Parallel agent sweeps (multi-session)

- ~50 agents dispatched in waves covering every file with errors
- Wave 1-2: high-error files (impl.py 153 errors, \_cli_shared.py, **init**.py, etc.)
- Wave 3-6: 4-error, 3-error, 2-error, 1-error file batches
- All agents applied: remove unused imports, rename unused vars to `_var`, fix type mismatches, add correct static imports

## Key Patterns Fixed Globally

1. **Unused imports**: `from typing import Any, Optional` → keep only what's used
2. **Unused variables**: `e = ...` → `_e = ...` in except clauses
3. **Forbidden fallbacks**: `try: import X; except ImportError: X_AVAILABLE = False` → mandatory direct imports
4. **Silent errors**: `except E: pass` → let exceptions propagate (fail loud)
5. **Dynamic `__all__`**: `sorted({*globals(),...})` → static literal lists
6. **Wrong module paths**: relative imports pointing to non-existent modules → absolute paths to correct modules

## Open Questions / Residual

- None. Zero errors achieved.

## Next Steps

- Run `task quality` for full quality gate
- Run test suite for 100% coverage check
- FR traceability audit (≥85% target)
