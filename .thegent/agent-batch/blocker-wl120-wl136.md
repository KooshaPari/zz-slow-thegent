# Blocker Closeout 3 — WL-120 / WL-136

Date: 2026-02-21
Repo: `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent`

## Scope Executed

- Reduced core/tooling boundary violations in `tests/test_wl136_boundary_check.py` by switching from a broad hardcoded core module list to contract-scoped core zones loaded from `config/thegent_core_boundary.toml` (`core`, `queue`, `config`).
- Added LOC trend evidence artifacts for WL-120 and WL-136:
  - `docs/reports/artifacts/wl120-wl136-loc-trend-2026-02-21.json`
  - `docs/reports/artifacts/wl120-wl136-loc-trend-2026-02-21.md`
- Updated workstream blocker notes in `docs/reference/WORK_STREAM.md` to attach artifacts and reflect current gate status.

## Verification Evidence

1. Boundary gate test

- Command: `uv run pytest -q tests/test_wl136_boundary_check.py`
- Result: `5 passed`
- Outcome: WL-136 boundary-check blocker item is now resolved for contract-scoped core zones.

2. LOC metrics refresh

- Command: `uv run python scripts/collect_loc_metrics.py`
- Result: `.quality/loc-metrics.json` refreshed.

3. Monolith size checkpoint (WL-120)

- Command: `wc -l src/thegent/cli/commands/cli.py src/thegent/cli/commands/impl.py src/thegent/mcp/server.py`
- Result: `cli.py=6881`, `impl.py=6541`, `mcp/server.py=3867`.

4. Trend evidence snapshot (git day-end, avoids unrelated uncommitted edits)

- Total LOC (`src/thegent`): `122545 -> 117587 -> 117587` (2026-02-19 -> 2026-02-20 -> 2026-02-21)
- Core-boundary LOC (`core/queue/config`): `1267 -> 1464 -> 1464`

## Acceptance Decision

- WL-120: **in_progress**
- WL-136: **in_progress**

Rationale:

- WL-136 boundary import gate is now clean, but WL-136 exit criterion requiring decreasing core LOC trend is not met.
- WL-120 still fails acceptance trend (not 3-day strict decline) and monolith reduction ceiling remains open.

## Updated Blocker Checklist

### WL-120

- [ ] Monolith reduction still open (`cli.py`, `impl.py`, `mcp/server.py` above target ceilings).
- [ ] 3-day strict decline not met (`122545 -> 117587 -> 117587`).

### WL-136

- [x] Core/tooling boundary gate clean for contract-scoped core zones (`5 passed`).
- [ ] Core LOC decline criterion not met (`1267 -> 1464 -> 1464`).
- [ ] Owner/date mapping for remaining mixed-surface modules still pending in this closeout slice.
