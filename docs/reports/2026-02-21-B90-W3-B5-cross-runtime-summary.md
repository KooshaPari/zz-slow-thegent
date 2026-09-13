---
title: "B90-W3-B5: Cross-Runtime Promotion Summary — Wave-3"
date: "2026-02-21"
status: "in_progress"
owner: "Runtime Core"
tags:
  [
    "WL-138",
    "B90-W3",
    "python",
    "rust",
    "zig",
    "mojo",
    "promotion",
    "cross-runtime",
  ]
---

# B90-W3-B5: Cross-Runtime Promotion Summary — Wave-3

## Summary Table

| Runtime    | Function / Workload                 | Wave-2 Status                                              | Wave-3 Status                                        | Gap                                                                     | Next Action                                                                  |
| ---------- | ----------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **Python** | `parse_model_suffix` (baseline)     | Baseline recorded; 11 parity cases passing                 | DONE — Python parity green                           | None                                                                    | Maintain as authoritative baseline                                           |
| **Rust**   | `parse_model_suffixes` PyO3 wrapper | PyO3 wrapper written in `crates/thegent-parser/src/lib.rs` | IN PROGRESS — parity gap report produced (B90-W3-B2) | `maturin develop --release` not run; cross-language parity tests skip   | Run `maturin develop --release` in Wave-4 CI job                             |
| **Zig**    | ABI contract v1                     | Contract JSON + 9 contract tests                           | IN PROGRESS — promotion report produced (B90-W3-B3)  | CI zig-readiness job not triggered; FFI roundtrip + wasm target pending | Wire `tests/test_wl132_zig_abi_contract.py` into CI zig job                  |
| **Mojo**   | Kernel smoke (`score.rank.v1`)      | Fixture JSON (3 cases) + smoke test (21 passing)           | IN PROGRESS — promotion report produced (B90-W3-B4)  | Mojo binary not installed; full deterministic replay (N >= 10) pending  | Install Mojo in CI; expand fixture to 7 cases; run full deterministic replay |

---

## Per-Runtime Detail

### Python — parse_model_suffix (Baseline)

**Status**: DONE

- Python implementation: `thegent.routing.model_suffix_parser.parse_model_suffixes`
- Parity test coverage: 11 cases in `tests/routing/test_wl131_parser_parity.py`
- All Python-side parity tests pass
- Serves as the authoritative baseline for Rust parity comparison

### Rust — parse_model_suffixes (PyO3)

**Status**: IN PROGRESS

- Rust implementation: `crates/thegent-parser/src/lib.rs` — `parse_model_suffixes_rust` + `parse_model_suffixes` (PyO3)
- Rust unit tests: 12 cases in `model_suffix_tests` module (all pass via `cargo test`)
- PyO3 module: `thegent_parser` — exports `parse_model_suffixes` returning `{"base_model": str, "suffixes": list[str], "raw": str}`
- Cross-language parity tests: written in `tests/routing/test_wl131_parser_parity.py` and `tests/routing/test_wl131_rust_python_parity.py`
- Current gap: `maturin develop --release` has not been run; `thegent_parser` is not importable; all Rust parity tests skip

**Wave-4 action**: Run `cd crates/thegent-parser && maturin develop --release`. Re-run parity tests. If all pass, promote Rust as co-default path.

### Zig — ABI Contract v1

**Status**: IN PROGRESS

- Contract: `contracts/runtime/zig_abi_contract_v1.json` — version `1.0.0`, 4 ABI symbols
- Rust interop crate: `crates/thegent-zmx-interop` — `ZMX_ABI_CONTRACT_VERSION = "1.0.0"` — builds clean
- Contract tests: 9/9 pass in `tests/test_wl132_zig_abi_contract.py`
- Zig binary available: `zig 0.15.2` at `/opt/homebrew/bin/zig`
- Current gap: CI zig-readiness job not defined; FFI roundtrip smoke test not wired; wasm32-wasi build not attempted

**Wave-4 action**: Add `.github/workflows/ci.yml` stage for zig-readiness. Trigger `zig build` on the interop lib. Run FFI roundtrip + wasm target build checks. If all pass, promote contract from `"draft"` to `"stable"`.

### Mojo — Kernel Smoke (score.rank.v1)

**Status**: IN PROGRESS

- Contract: `contracts/runtime/mojo_kernel_contract_v1.json` — version `1.0.0`, kernel `score.rank.v1`
- Fixture: `tests/mojo/fixtures/deterministic_score_v1.json` — 3 cases
- Smoke tests: 21/21 pass in `tests/mojo/test_wl133_mojo_kernel_smoke.py`
- Mojo binary: **not installed** — tests skip gracefully where Mojo subprocess would be needed
- Python bridge: `thegent.infra.mojo_bridge` — importable, deterministic, validates contracts

**Wave-4 action**: Install Magic CLI / Mojo SDK in CI. Expand fixture to 7 cases (`score_deterministic_v1.json`). Run full deterministic replay N >= 10. Run benchmark harness. Verify p95 speedup >= 1.5x and zero correctness failures.

---

## Overall Wave-3 Promotion Gate Assessment

**Gate**: Rust/Zig/Mojo promotion to production co-default paths.

**Decision**: **BLOCKED on multiple prerequisites**

| Blocker                             | Runtime | Resolution                         |
| ----------------------------------- | ------- | ---------------------------------- |
| `maturin develop --release` not run | Rust    | Wave-4: Add to CI rust-pyo3 job    |
| CI zig-readiness job not triggered  | Zig     | Wave-4: Add CI stage + `zig build` |
| FFI roundtrip not wired             | Zig     | Wave-4: After CI job is live       |
| Mojo binary not available in CI     | Mojo    | Wave-4: Install Magic CLI          |
| Full deterministic replay pending   | Mojo    | Wave-4: After Mojo installed       |

---

## Wave-4 Recommended Action Plan

### Priority 1 (Unblock Rust Parity)

1. Add `maturin` to the CI environment and run `cd crates/thegent-parser && maturin develop --release`
2. Re-run `tests/routing/test_wl131_parser_parity.py` with `THEGENT_USE_RUST_PARSER=1`
3. Verify all 11 parity cases pass cross-language

### Priority 2 (Trigger CI Zig Readiness)

4. Add `.github/workflows/ci.yml` job `zig-readiness` that runs `tests/test_wl132_zig_abi_contract.py`
5. Add `zig build` step to compile the interop shared library
6. Run FFI roundtrip smoke in CI

### Priority 3 (Mojo Full Replay)

7. Install Mojo SDK in CI (`magic run mojo`)
8. Create `tests/mojo/fixtures/score_deterministic_v1.json` with 7 cases
9. Run `test_wl133_mojo_kernel_smoke.py` with Mojo installed; confirm no skips
10. Run benchmark harness from `benchmarks/mojo_score_rank_v1_harness.json`

### Priority 4 (Promote to Stable)

11. Promote Rust PyO3 extension as co-default for model suffix parsing
12. Promote Zig ABI contract from `draft` to `stable`
13. Promote Mojo kernel contract from `draft` to `stable`
14. Update `runtime-modularization-matrix-v2.json` entries to `migration_status: "done"`

---

_Generated by B90-W3-B5 agent. Follow-up review date: 2026-03-07._
