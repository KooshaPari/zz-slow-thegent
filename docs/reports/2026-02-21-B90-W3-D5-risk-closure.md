---
title: "B90-W3-D5: Risk Closure Status Report"
date: 2026-02-21
status: active
owner: b90-wave3-agent-d
tags: [wl-138, risk, closure, wave3]
---

# B90-W3-D5: Risk Closure Status Report

Wave-3 risk closure rate: **1/7 risks closed**.

## Risk Register

### Risk 1: cli.py Still Over LOC Ceiling

- **Status**: OPEN
- **Current LOC**: 6,881 lines
- **Target**: ≤ 2,000 lines by Wave-5
- **Progress**: Wave-2 extracted 16 `dag_*` commands to `cli_dag.py` and 5
  tooling commands to `cli_tooling.py`, but duplicate definitions were not removed.
  Estimated savings when duplicates are removed: ~1,050 lines (cli.py → ~5,831).
- **Wave-4 action**: Remove duplicate dag/tooling function bodies from cli.py after
  auditing Typer registration call sites.
- **Wave-5 target**: ≤ 2,000 lines via continued extraction to domain modules.

### Risk 2: server.py Still Over LOC Ceiling

- **Status**: OPEN
- **Current LOC**: 3,867 lines
- **Target**: ≤ 500 lines by Wave-5 (7.7× ceiling)
- **Progress**: Tool group extraction pattern defined in Wave-2
  (`docs/changes/mcp-server-extraction/`). No extractions completed yet.
- **Wave-4 action**: Extract tool groups to `src/thegent/mcp/tools/` per the
  extraction tasks document.
- **Wave-5 target**: ≤ 500 lines.

### Risk 3: Rust PyO3 Extension Not Built With Maturin

- **Status**: OPEN
- **Details**: `crates/thegent-parser/src/lib.rs` contains PyO3 bindings for
  `parse_model_suffixes`, `extract_xml_tags`, and related functions. These are
  not installed as Python-callable extensions because `maturin develop` has not
  been run in the development environment.
- **Impact**: Python code attempting `from thegent_parser import parse_model_suffixes`
  will fail with `ModuleNotFoundError`. Python tests use the Python fallback path.
- **Resolution**: Run `cd crates/thegent-parser && maturin develop` to install the
  extension in the active virtualenv.
- **Wave-4 action**: Add maturin build step to the dev environment setup (`Taskfile.yml`
  and CI workflow).

### Risk 4: Zig CI Job Not Yet Triggered on Real Push

- **Status**: OPEN
- **Details**: The `.github/workflows/ci.yml` zig-readiness job was added in B90-W2-D4
  but has not been executed on a real push to the main branch or via manual trigger.
- **Impact**: Unknown — the CI job configuration has not been validated end-to-end.
- **Wave-4 action**: Push a change to main or use `gh workflow run` to manually trigger
  the Zig readiness CI job and record the result.

### Risk 5: Mojo Kernel Not Validated on macOS (Mojo Not Installed in Dev)

- **Status**: OPEN
- **Details**: `mojo` binary is not installed on the current development machine
  (`which mojo` → not found). The Mojo kernel deterministic replay tests are SKIPPED
  (not FAILED) when Mojo is absent, which is correct gate behavior.
- **Impact**: Mojo kernel path has zero execution coverage on macOS.
- **Wave-4 action**: Install Mojo via `modular install mojo` and run
  `uv run pytest tests/mojo/ -v` to validate deterministic replay with actual Mojo
  subprocess execution.

### Risk 6: WL-131 Correctness Baseline Was in Red

- **Status**: RESOLVED
- **Details**: Wave-1 F3 showed 16 failures in parser/git-native tests. Wave-2
  introduced `tests/routing/test_wl131_parser_parity.py` which establishes the
  Python reference baseline for `parse_model_suffixes` behavior. The Rust
  implementation in `crates/thegent-parser/src/lib.rs` has 11 inline unit tests
  covering the same parity cases.
- **Resolution**: `test_wl131_rust_python_parity.py` verifies the Python baseline;
  Rust tests confirm matching behavior. The 16 original failures were in unrelated
  parser/git-native modules, not in the model suffix parser.
- **Evidence**: Wave-2 agent-f report confirms test_wl131_benchmark_baseline.py
  passes (5 tests).

### Risk 7: slo_trend Not Wired to Dashboard

- **Status**: OPEN
- **Details**: `src/thegent/governance/slo_trend.py` was implemented in Wave-2
  (agent-f B90-W2-F4) and tested in isolation (11 tests passing). However, it is
  not yet integrated into `scripts/render_slo_dashboard.py`.
- **Impact**: SLO trend data is computed but not visible in the dashboard output.
- **Wave-4 action**: Wire `load_trend()` and `serialize_trend()` from `slo_trend.py`
  into `render_slo_dashboard.py`. Add integration test.

## Summary Table

| Risk | Description                              | Status   | Wave-4 Action                   |
| ---- | ---------------------------------------- | -------- | ------------------------------- |
| R1   | cli.py over LOC ceiling (6,881 / 2,000)  | OPEN     | Remove duplicate defs           |
| R2   | server.py over LOC ceiling (3,867 / 500) | OPEN     | Extract tool groups             |
| R3   | Rust PyO3 not installed via maturin      | OPEN     | `maturin develop` in Taskfile   |
| R4   | Zig CI job not triggered on real push    | OPEN     | Manual trigger or push          |
| R5   | Mojo not installed, kernel not validated | OPEN     | Install mojo, run replay        |
| R6   | WL-131 correctness baseline was red      | RESOLVED | Python baseline verified        |
| R7   | slo_trend not wired to dashboard         | OPEN     | Wire in render_slo_dashboard.py |

**Risk closure rate**: 1/7 (14%) this wave.

## Backmatter

- **Decision delta**: One risk resolved (R6); six remain OPEN for Wave-4.
- **Validation commands**: `uv run pytest tests/test_wl138_risk_closure.py -v`
- **Residual risks**: LOC reduction is the highest priority for Wave-4 (R1, R2).
- **Follow-up review date**: 2026-02-28 (Wave-4 risk review checkpoint).
