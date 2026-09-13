---
title: "B90-W3-B2: Parity Gap Report — Rust/Python Parser Migration"
date: "2026-02-21"
status: "in_progress"
owner: "Runtime Core"
tags: ["WL-131", "B90-W3", "parity", "rust", "pyo3", "maturin"]
---

# B90-W3-B2: Parity Gap Report — Rust/Python Parser Migration

## Summary

This report documents the current state of parity testing between the Python
parser implementations in `thegent.routing` and the Rust implementations in
`crates/thegent-parser/src/lib.rs` as of B90 Wave-3.

---

## Parity Test Files (Wave-2 Artifacts)

| File                                             | Purpose                                                                                                          | Status                                       |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `tests/routing/test_wl131_parser_parity.py`      | Python-vs-expected parity for `parse_model_suffixes` (11 cases + property tests)                                 | **PASSING** (Python only)                    |
| `tests/routing/test_wl131_rust_python_parity.py` | Cross-language parity for `extract_xml_tags`, `parse_model_suffixes`, `parse_checkpoint_by_id`, `parse_dlq_item` | **PASSING** (Python path; Rust path skipped) |

---

## Gap Analysis

### Functions with Rust Implementations (crates/thegent-parser/src/lib.rs)

All of the following have complete Rust implementations behind the PyO3 boundary
and are exported via the `thegent_parser` module:

| Function                   | Rust Status       | Python Baseline                       | Parity Tests                                  | Rust Parity Active?                       |
| -------------------------- | ----------------- | ------------------------------------- | --------------------------------------------- | ----------------------------------------- |
| `parse_model_suffixes`     | PyO3 wrapper done | `thegent.routing.model_suffix_parser` | 11 cases in `test_wl131_parser_parity.py`     | No — skipped (maturin build not verified) |
| `extract_xml_tags`         | PyO3 wrapper done | Reference regex in test helper        | 7 cases in `test_wl131_rust_python_parity.py` | No — skipped                              |
| `strip_think_blocks`       | PyO3 wrapper done | Not yet mapped to a Python module     | —                                             | No — skipped                              |
| `strip_noise`              | PyO3 wrapper done | Not yet mapped to a Python module     | —                                             | No — skipped                              |
| `parse_checkpoint_by_id`   | PyO3 wrapper done | Reference impl in test helper         | 5 cases in `test_wl131_rust_python_parity.py` | No — skipped                              |
| `parse_dlq_item`           | PyO3 wrapper done | Reference impl in test helper         | 5 cases in `test_wl131_rust_python_parity.py` | No — skipped                              |
| `parse_override_unexpired` | PyO3 wrapper done | Not mapped                            | —                                             | No — skipped                              |
| `parse_fatigue_line`       | PyO3 wrapper done | Not mapped                            | —                                             | No — skipped                              |
| `parse_circuit_failure`    | PyO3 wrapper done | Not mapped                            | —                                             | No — skipped                              |
| `parse_jsonl_file`         | PyO3 wrapper done | Not mapped                            | —                                             | No — skipped                              |

### Current Behavior of Cross-Language Parity Tests

The `test_rust_*_parity_if_available` tests in both parity files use a guard:

```python
try:
    import thegent_parser
except ImportError:
    pytest.skip("thegent_parser Rust extension not built; skipping cross-language parity")
```

Since `maturin develop` has not been run for `crates/thegent-parser`, the
`thegent_parser` Python extension module is not importable. All cross-language
parity assertions are currently **skipped**, not failed.

### What Is Actually Tested (Python vs Python baseline)

`test_wl131_parser_parity.py` — 11 parametrized `parse_model_suffixes` cases
exercising the Python implementation directly. These all pass.

`test_wl131_rust_python_parity.py` — Python-side helper tests for
`extract_xml_tags`, extended `parse_model_suffixes`, `parse_checkpoint_by_id`,
and `parse_dlq_item`. These pass because they use reference Python implementations
or imports with fallback reference implementations.

---

## Current Status

### What Is Done

- PyO3 wrapper in `crates/thegent-parser/src/lib.rs`: complete, covers 11 functions
- Python parity test cases written: 11 cases for `parse_model_suffixes`, 7 for `extract_xml_tags`, 5 for `parse_checkpoint_by_id`, 5 for `parse_dlq_item`
- Python-side parity tests: all passing

### Remaining Gaps

| Gap                                                                                                                                | Description                                           | Blocking?                          |
| ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------- |
| `parse_model_suffixes` (Rust)                                                                                                      | Rust PyO3 ready, `maturin develop --release` not run  | Yes for cross-language parity      |
| `extract_xml_tags`                                                                                                                 | Python only; Rust wrapper ready but maturin not run   | Yes for cross-language parity      |
| `parse_checkpoint_by_id`                                                                                                           | Python only in tests                                  | Yes for cross-language parity      |
| `parse_dlq_item`                                                                                                                   | Python only in tests                                  | Yes for cross-language parity      |
| `strip_think_blocks`, `strip_noise`, `parse_override_unexpired`, `parse_fatigue_line`, `parse_circuit_failure`, `parse_jsonl_file` | Python reference not yet written; Rust wrapper exists | Low priority — no parity tests yet |

---

## maturin Build Status

The Rust PyO3 extension `thegent_parser` is defined in
`crates/thegent-parser/Cargo.toml` with a `[lib] crate-type = ["cdylib"]` section.

To build the extension and activate full cross-language parity:

```bash
cd crates/thegent-parser && maturin develop --release
```

This has **not been run** as of Wave-3. The CI job for maturin builds is not
yet triggered. The cross-language parity tests are designed to skip gracefully
when the extension is absent, so there are no CI failures from this gap.

---

## Recommendation for Wave-4

1. Run `cd crates/thegent-parser && maturin develop --release` in the CI
   zig-readiness job (or a dedicated rust-pyo3 job).
2. Re-run `tests/routing/test_wl131_parser_parity.py` and
   `tests/routing/test_wl131_rust_python_parity.py` with the extension installed.
3. All currently-skipped `test_rust_*_parity_if_available` tests should then
   execute and validate full cross-language parity.
4. If parity failures arise, fix them in the Rust implementation before promoting
   the extension as the default path.

---

## Decision Delta

- **Wave-3 decision**: Accept Python-only parity testing as sufficient for Wave-3.
  Cross-language parity gates are deferred to Wave-4 maturin build step.
- **Wave-4 trigger**: Any merge touching `crates/thegent-parser/src/lib.rs`
  must trigger the maturin build + parity test job.

---

## Residual Risks

- If the Rust implementation diverges from the Python baseline between now and
  the maturin build, the divergence will only surface at that time.
- Risk is mitigated by the Rust unit tests in `crates/thegent-parser/src/lib.rs`
  (12 cases in `model_suffix_tests`) which cover the same input space as the
  Python parity tests.

---

_Generated by B90-W3-B2 agent. Follow-up review date: 2026-03-07._
