# Wave 5 Agent C Report (WL-115, WL-116, WL-118, WL-119, WL-120)

Date: 2026-02-21

## Scope Completed

### WL-115: bench compare output-format json + one table renderer test

- Code changes:
  - Added explicit `--output-format` option (with `--format` alias retained) for bench CLI commands.
  - `bench compare` rich output now renders a `rich.Table` with baseline/candidate latency and run IDs.
- Files changed:
  - `src/thegent/cli/apps/bench.py`
  - `tests/test_wl115_bench_cli.py`
- Test coverage added:
  - `test_bench_compare_renders_table_in_rich_mode`
  - Existing JSON compare test updated to exercise `--output-format json`.

### WL-116: include transcript length/metadata in run summary output

- Code changes:
  - Added `_build_audio_summary_metadata()` helper to build transcript metadata.
  - Run payload now includes `audio_metadata` when transcript input exists:
    - `transcript_length_chars`
    - `source_count`
    - `sources`
  - Human-facing run output now shows transcript summary line via CLI formatter.
- Files changed:
  - `src/thegent/cli/commands/impl.py`
  - `src/thegent/cli/commands/cli.py`
  - `tests/test_wl116_audio_inputs.py`
- Test coverage added:
  - `test_build_audio_summary_metadata_includes_length_and_sources`

### WL-118: add ollama doctor actionable remediation docs in guide

- Docs changes:
  - Added `WL-118: thegent doctor Ollama remediation playbook` section with signal->meaning->action table and a short remediation command loop.
- File changed:
  - `docs/guides/PROVIDER_SETUP_GUIDE.md`

### WL-119: include grounding sources in one human-facing CLI output option

- Code changes:
  - Added CLI formatter for grounding-source display in `run` output.
  - Human-facing output now includes a dimmed source summary block with URL count and truncation.
- Files changed:
  - `src/thegent/cli/commands/cli.py`
  - `tests/test_wl119_run_cli_output.py`
- Test coverage added:
  - `test_format_grounding_sources_lines_includes_count_and_truncation`

### WL-120: add current checkpoint table in modernization master plan

- Docs changes:
  - Added `Current Checkpoint Table (as of 2026-02-21)` to the modernization master plan with WL-115/116/118/119/120 status + evidence rows.
- File changed:
  - `docs/plans/2026-02-21-MODERNIZATION-MASTER-PLAN.md`

## Focused Validation

1. Initial run (system pytest, failed due env plugin mismatch):

- `pytest -q tests/test_wl115_bench_cli.py tests/test_wl116_audio_inputs.py tests/test_wl119_grounding_sources.py tests/test_wl119_run_cli_output.py tests/test_wl118_ollama_doctor_slice.py`
- Result: failed before test collection (`ImportError: No module named 'pytest_asyncio'`).

2. Project-venv run (authoritative):

- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/.venv/bin/pytest -q tests/test_wl115_bench_cli.py tests/test_wl116_audio_inputs.py tests/test_wl119_grounding_sources.py tests/test_wl119_run_cli_output.py tests/test_wl118_ollama_doctor_slice.py`
- Result: `22 passed in 31.29s`.

## Constraints Check

- `docs/reference/WORK_STREAM.md` not modified.
- Changes were scoped to owned WL surfaces; unrelated worktree edits left untouched.
