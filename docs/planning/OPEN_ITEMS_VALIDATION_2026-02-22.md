# OPEN ITEMS Validation (2026-02-22)

Date validated: 2026-02-23
Lane: THEGENT lane B

## Baseline artifact status

- `docs/planning/OPEN_ITEMS_VALIDATION_2026-02-22.md` was missing before this run; restored in this change.
- `next_10_work_items.txt` and `next_20_work_items.txt` contained stale/unrelated backlog entries only; lane-B completion entries were appended with factual status.

## Harness parity validation summary

1. Fail-first evidence captured for Rust shim parity:

- `cargo test -p thegent-shims normalize_harness_labels_for_antigma_exec_without_prompt_uses_prompt_flag` failed before fix (`left: ["exec", "hi there"]`, `right: ["-p", "hi there"]`).
- `cargo test -p thegent-shims should_inject_proxy_env_defaults_for_supported_harnesses` failed before fix (`should_inject_proxy_env_defaults("antigma")`).

2. Fix implemented in `crates/thegent-shims/src/main.rs`:

- Canonicalized `anen`/`antigma` to `fanta` for shim routing and command normalization.
- Added `anen`/`antigma` support to symlink/program-name dispatch and `thegent-*` alias whitelist.
- Added proxy-default coverage for `anen`/`antigma`.

3. Post-fix verification:

- `cargo test -p thegent-shims normalize_harness_labels_for_antigma_exec_without_prompt_uses_prompt_flag` passed.
- `cargo test -p thegent-shims should_inject_proxy_env_defaults_for_supported_harnesses` passed.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -m pytest -q tests/test_unit_rust_wrappers.py tests/test_unit_cli_impl_pre_work_gate.py` passed (`12 passed`).
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 task quality:sitback-contracts` passed (`44 passed`).

## Test additions included in this run

- `tests/test_unit_rust_wrappers.py`
  - Added `anen` and `antigma` wrapper shim passthrough tests.
- `tests/test_unit_cli_impl_pre_work_gate.py`
  - Added config-driven regression proving `hooks/hook-config.yaml` `require_e2e_first: false` is honored via temp project fixture.
- `crates/thegent-shims/src/main.rs`
  - Added regression tests for antigma label normalization and proxy-default support expectations.
