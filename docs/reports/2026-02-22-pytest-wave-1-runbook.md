# 2026-02-22 Pytest Optimization Wave-1 Runbook

## Objective

Execute the first enforceable tranche using the 100-item plan and close hard blockers for reliable fast-lane execution.

## Wave 1 Scope

- 7 owners: 6 agents + owner (Codex)
- Priority: P0 + FR traceability minimum viable loop
- Exit criteria: clean collection, deterministic lanes, traceability artifacts generated

## Task Mapping

- Wave-1 mandatory baseline: `16-30` (agent-2), `31-44` (agent-3), `73-76` (agent-6), `87` and `88` (Codex), `91` and `92` (Codex)
- Hard-stop checks: collection errors remain at 0 and marker semantics are strict.

## Codex-owned immediate commands

1. Create execution tracker for task progress

- File: `thegent/docs/reports/2026-02-22-pytest-wave-1-progress.md`
- Include per-task: status, owner, output artifact, blocking reason.

2. Add lane-aware PR guidance section

- Update `thegent/docs/reports/2026-02-22-pytest-optimization-and-atoms-research.md` with a short “Do this before pushing” block.
- Include exact lane commands and required artifacts.

3. Add PR local helper command notes

- Provide standard invocation for PR verification in docs.
- Example commands to document (not execute):
  - `python -m pytest --collect-only -q`
  - `python -m pytest --collect-only -q --maxfail=1 -m "not slow and not integration and not e2e and not load"`
  - `python -m pytest --collect-only -q -m fast`

4. Draft placeholder template for traceability gap file

- `FR_TEST_GAP_TEMPLATE.json`
- Fields: `fr_id`, `suite`, `tests`, `first_seen`, `owner`, `risk`, `target_date`.

5. Draft baseline artifact naming and retention policy

- JSON artifact: `artifacts/pytest/baseline/collect-{utc_date}.json`
- Markdown summary: `artifacts/pytest/baseline/collect-{utc_date}.md`
- Retain last 30 days.

## Acceptance Checklist

- [ ] New Wave-1 tracker exists.
- [ ] Baseline collection command and thresholds documented.
- [ ] PR lane and nightly lane commands are defined and deterministic.
- [ ] FR coverage artifact format and path are defined.
- [ ] Traceability gap file template exists and includes owner + owner action.
- [ ] No step requires immediate execution from agent instructions.

## Coordination Notes

- Agent-2 and Agent-3 are responsible for collection stability and traceability extraction contracts first.
- Agent-6 handles collection scope + lane split hardening.
- Codex handles command runbook, templates, and tracker wiring.
- No code changes are required to start this wave; this is orchestration-first.
