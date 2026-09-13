# 2026-02-21 Polyglot Runtime Matrix and CLAUDE Normalization

## Request scope

1. Establish full polyglot runtime/test coverage governance.
2. Add frontmatter/backmatter defaults and conversion/refactor decision matrix.
3. Apply policy to governance docs, templates, and `CLAUDE.md`.
4. Scan and normalize typo files (`calude.md`) and enforce split policy when `CLAUDE.md` exceeds ~20k tokens.

## Changes completed

1. Added canonical governance matrix:

- `docs/governance/POLYGLOT_RUNTIME_COVERAGE_AND_CONVERSION_MATRIX_2026-02-21.md`

2. Updated governance summary linkage:

- `docs/governance/GOVERNANCE_SUMMARY.md`

3. Updated root `CLAUDE.md` with:

- runtime/test baseline,
- conversion/refactor rules,
- frontmatter/backmatter defaults,
- `calude.md` normalization policy,
- `CLAUDE.md` >20k token split policy to `docs/docsets/claude/`.

4. Updated project template `CLAUDE.md` with same policy baseline:

- `templates/initialize-project/'{{cookiecutter.project_name}}'/CLAUDE.md`

5. Added template governance doc:

- `templates/initialize-project/docs/governance/POLYGLOT_RUNTIME_DECISION_MATRIX.md`

6. Updated template docs/readme links:

- `templates/initialize-project/docs/index.md`
- `templates/initialize-project/README.md`

## Scan results: CLAUDE typo normalization

Repository-wide within `thegent`:

1. Canonical files found:

- `CLAUDE.md`
- `templates/initialize-project/'{{cookiecutter.project_name}}'/CLAUDE.md`

2. `calude.md` typo files found:

- none

3. Lowercase `claude.md` files found:

- none inside `thegent` root scope (outside this repo there are lowercase files in other projects).

## Size/split policy check

1. `thegent/CLAUDE.md` current size is below split threshold (~20k tokens).
2. Split policy is now explicitly documented and enforced by governance guidance.

## Operational decision

Adopt strict matrix baseline:

1. Python via `uv`: CPython 3.14 primary, PyPy 3.11 secondary, CPython 3.13 fallback lane.
2. Rust/Go/Zig/Mojo baseline lanes and conversion triggers documented centrally.

## Follow-up recommendations

1. Add CI jobs for matrix lanes and runtime badges.
2. Add automated `calude.md` typo detector pre-commit check.
3. Add CLAUDE size check script that prompts docset split at threshold.
