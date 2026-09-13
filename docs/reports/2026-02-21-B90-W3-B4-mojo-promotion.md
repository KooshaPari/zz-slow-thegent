---
title: "B90-W3-B4: Mojo Kernel Promotion and Deterministic Replay Validation Report"
date: "2026-02-21"
status: "in_progress"
owner: "ML Runtime"
tags: ["WL-133", "B90-W3", "mojo", "kernel", "deterministic", "promotion"]
---

# B90-W3-B4: Mojo Kernel Promotion and Deterministic Replay Validation Report

## Test Results: tests/mojo/test_wl133_mojo_kernel_smoke.py

All 21 smoke tests passed on 2026-02-21:

```
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_kernel_contract_file_exists               PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_kernel_contract_has_version               PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_kernel_contract_has_kernel_catalog        PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_kernel_catalog_entry_has_required_fields  PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_kernel_catalog_deterministic_flag_is_true PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_kernel_contract_has_schemas               PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_kernel_contract_score_rank_input_schema   PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_kernel_contract_score_rank_output_schema  PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_mojo_bridge_module_importable             PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_mojo_bridge_has_validate_kernel_contract  PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_mojo_bridge_has_build_provider_score_kernel_script PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_mojo_bridge_has_mojo_kernel_contracts     PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_mojo_bridge_contract_references_calculate_provider_score PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_validate_kernel_contract_is_deterministic PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_validate_kernel_contract_fails_fast_on_missing_arg PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_build_kernel_script_is_deterministic      PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_build_kernel_script_non_empty             PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_deterministic_fixture_file_exists         PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_deterministic_fixture_has_three_cases     PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_deterministic_fixture_cases_have_required_fields PASSED
tests/mojo/test_wl133_mojo_kernel_smoke.py::test_deterministic_fixture_inputs_match_contract_schema PASSED

21 passed in 0.21s
```

---

## Mojo Binary Availability

Mojo is **not installed** on this machine:

- **`mojo` binary**: Not found in PATH
- **Impact**: Tests that require Mojo subprocess execution skip gracefully
  (not fail hard); the smoke test suite does not use subprocess Mojo execution
  and passes entirely on Python bridge layer assertions

---

## Fixture Validation

### deterministic_score_v1.json

| Property                 | Value                                                                           | Status               |
| ------------------------ | ------------------------------------------------------------------------------- | -------------------- |
| Path                     | `tests/mojo/fixtures/deterministic_score_v1.json`                               | Present              |
| `fixture_id`             | `deterministic_score_v1`                                                        | Present              |
| `kernel_id`              | `score.rank.v1`                                                                 | Matches contract     |
| Case count               | 3 cases                                                                         | Meets minimum (>= 3) |
| Case IDs                 | `basic-two-candidates`, `single-candidate`, `three-candidates-quality-weighted` | All valid            |
| Required fields per case | `case_id`, `input`, `expected_output`                                           | All present          |
| Input schema conformance | `request_id`, `candidates`, `weights` (cost/latency/quality)                    | All present          |

Note: The spec mentions `score_deterministic_v1.json` with 7 cases — this file
was not found in Wave-2 artifacts. The Wave-2 fixture is `deterministic_score_v1.json`
with 3 cases. The 7-case fixture is planned for Wave-4 full deterministic replay.

---

## Kernel Contract Status

### contracts/runtime/mojo_kernel_contract_v1.json

| Field                         | Value                                                 | Status             |
| ----------------------------- | ----------------------------------------------------- | ------------------ |
| `contract_id`                 | `runtime.mojo_kernel.v1`                              | Present            |
| `version`                     | `1.0.0`                                               | Present            |
| `status`                      | `draft`                                               | Active draft       |
| `kernel_catalog` count        | 1 kernel                                              | Non-empty          |
| Kernel `kernel_id`            | `score.rank.v1`                                       | Present            |
| Kernel `deterministic` flag   | `true`                                                | Required — present |
| Input schema required fields  | `request_id`, `candidates`, `weights`                 | All defined        |
| Output schema required fields | `request_id`, `ranked`                                | All defined        |
| Promotion gate                | p95 speedup >= 1.5x vs Python; 0 correctness failures | Defined            |

---

## Fallback Behavior

The test suite is designed to skip — not fail — when Mojo is unavailable:

- No tests use `subprocess.run(["mojo", ...])` without a `which mojo` guard.
- The Python bridge layer (`thegent.infra.mojo_bridge`) handles the case where
  the Mojo binary is absent by raising `RuntimeError` only when execution is
  actually attempted (not at import time).
- All 21 smoke tests exercise the Python bridge layer only (contract schema
  validation, determinism of the bridge function itself, fixture schema checks).

---

## Promotion Gate Decision

| Gate                                     | Status  | Notes                                                 |
| ---------------------------------------- | ------- | ----------------------------------------------------- |
| Kernel contract JSON valid               | PASS    | 8 structural tests pass                               |
| `deterministic` flag = `true` in catalog | PASS    | Verified                                              |
| Python bridge importable                 | PASS    | `thegent.infra.mojo_bridge` imports clean             |
| Bridge determinism (Python layer)        | PASS    | `build_provider_score_kernel_script` is deterministic |
| Fixture schema conformance               | PASS    | 3/3 cases pass schema checks                          |
| Mojo binary available                    | SKIP    | `mojo` not installed; tests skip gracefully           |
| Full deterministic replay (N >= 10 runs) | PENDING | Requires Mojo binary                                  |
| Python baseline parity                   | PENDING | Requires Mojo binary for full comparison              |
| p95 speedup >= 1.5x vs Python            | PENDING | Requires Mojo binary + benchmark harness              |

**Overall Promotion Gate: SKIP** — deterministic replay cannot be validated
without the Mojo binary. Python bridge smoke tests all pass.

**Decision**: PASS if deterministic replay validates (Mojo installed + replay harness
run); SKIP if Mojo not installed (current state).

---

## Wave-4 Recommendations

1. **Install Mojo in CI**: Add the Magic CLI / Mojo SDK installation step to the
   CI pipeline for the `mojo-kernel` job lane.
2. **Expand fixture to 7 cases**: Create `tests/mojo/fixtures/score_deterministic_v1.json`
   with 7 cases as specified in `benchmarks/mojo_score_rank_v1_fixture_spec.json`.
3. **Run full deterministic replay**: Run the kernel with each fixture case
   N >= 10 times and assert identical output.
4. **Benchmark against Python baseline**: Run `benchmarks/mojo_score_rank_v1_harness.json`
   and verify p95 speedup >= 1.5x and rank order exact.
5. **Promote contract from `draft` to `stable`**: Only after all gates pass.

---

_Generated by B90-W3-B4 agent. Follow-up review date: 2026-03-07._
