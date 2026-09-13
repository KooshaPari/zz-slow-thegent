# WL-341 to WL-344 Evidence Report (2026-02-23)

## Scope Delivered

- WL-341: Governance baseline persisted for policy contracts.
- WL-342: Governance validation compares current contracts against stored baseline.
- WL-343: Governance watchdog behavior fails loudly on invalid baseline format.
- WL-344: Governance diff output added for changed policy contracts.

## Commands Run

```bash
python -m pytest tests/test_unit_drift.py -q
python -m ruff check src/thegent/governance/drift.py tests/test_unit_drift.py
```

## Outcome

- `python -m pytest tests/test_unit_drift.py -q` passed.
- `python -m ruff check src/thegent/governance/drift.py tests/test_unit_drift.py` passed.

## Files

- `src/thegent/governance/drift.py`
- `tests/test_unit_drift.py`
- `docs/reference/WORK_STREAM.md`
- `docs/reference/WBS_AGENT_PROGRESS.md`
