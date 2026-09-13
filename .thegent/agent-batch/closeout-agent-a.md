# Track A Closeout Report (Agent A)

Date: 2026-02-21
Scope: Closeout remaining executable Track A slices for WL-120 and WL-136.

## Summary

Track A closeout was completed for the remaining executable slices tied to:

- WL-120 (`B90-W3-A1` intent): harden extraction interfaces and remove deprecated import routing where extracted modules exist.
- WL-136 (`B90-W3-A2` intent): finalize two-surface architecture decision record.

## Implemented Slices

### WL-120: extraction interface hardening

Changes:

- Updated command routing imports to use extracted modules instead of `impl.py` where extraction already exists:
  - `src/thegent/cli/commands/plan_cmds.py`
    - `dag_status_impl` now imported from `dag_impl`
    - `incorporate_impl`, `work_stream_claim_impl`, `work_stream_complete_impl`, `wait_next_impl`, `do_next_impl` now imported from `work_stream_impl`
  - `src/thegent/cli/commands/cli_dag.py`
    - `dag_status_impl` now imported from `dag_impl`
- Fixed extraction API parity bug discovered by focused tests:
  - Added missing `dag_remove_cmd` to `cli_dag.__all__` in `src/thegent/cli/commands/cli_dag.py`.
- Added focused contract test:
  - `tests/commands/test_wl120_extraction_import_routing.py`

Result:

- Plan/DAG command surfaces now route through extracted modules for those handlers, reducing direct dependency on monolithic `impl.py` in these paths.

### WL-136: two-surface architecture decision finalization

Changes:

- Added accepted ADR:
  - `docs/reference/ADR-016-two-python-surfaces.md`
- Updated ADR index:
  - `ADR.md` now includes ADR-016 entry.
- Linked plan to finalized decision record:
  - `docs/plans/WL-136-TWO-PYTHON-SURFACES.md`

Result:

- The two-surface architecture is now explicitly ratified as an ADR, with concrete routing implications and implementation notes.

## Workstream Status/Notes Updates

Updated `docs/reference/WORK_STREAM.md` notes for closeout evidence:

- WL-120 section: added Track A closeout slice notes and evidence pointer.
- WL-136 section: added Track A closeout slice notes and ADR finalization pointer.
- CLAIMED table notes for WL-120/WL-136 rows updated to reflect closeout slice progress.

Status decision:

- WL-120 and WL-136 remain `in_progress` at epic level (multi-week blocker epics), but Track A executable closeout slices are complete and validated.

## Focused Validation

Commands run:

1. Syntax/compile check

```bash
python3 -m py_compile src/thegent/cli/commands/plan_cmds.py src/thegent/cli/commands/cli_dag.py tests/commands/test_wl120_extraction_import_routing.py
```

Result: success.

2. Core boundary strict check

```bash
python3 scripts/check_thegent_core_boundary.py --strict --format summary-json
```

Result:

```json
{
  "blocked_count": 0,
  "clean_file_count": 4,
  "disallowed_count": 0,
  "file_count": 4,
  "import_count": 2,
  "mode": "strict",
  "ok": true,
  "violation_count": 0,
  "violation_file_count": 0
}
```

3. Focused extraction tests

```bash
python3 -m pytest -q tests/cli/test_cli_dag_extraction.py tests/commands/test_wl120_extraction_import_routing.py
```

Result: `9 passed in 25.80s`.

## Files Changed (Track A closeout scope)

- `src/thegent/cli/commands/plan_cmds.py`
- `src/thegent/cli/commands/cli_dag.py`
- `tests/commands/test_wl120_extraction_import_routing.py`
- `docs/reference/ADR-016-two-python-surfaces.md`
- `ADR.md`
- `docs/plans/WL-136-TWO-PYTHON-SURFACES.md`
- `docs/reference/WORK_STREAM.md`
- `.thegent/agent-batch/closeout-agent-a.md`
