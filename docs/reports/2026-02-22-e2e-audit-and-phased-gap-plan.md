# End-to-End Audit and Phased Gap Plan (2026-02-22)

## Scope

- Repos: `thegent`, `cliproxyapi-plusplus`
- Surfaces: CLI harness parity (`dex`/`clode`/`roid`/`fanta`), provider cheapest-model matrix, CLIProxy websocket/HTTP compatibility, CI gate wiring, and holistic quality lanes (coverage, security, perf, chaos, a11y, integration).
- Method: child-agent parallel audits + live command verification.

## Live Baseline (2026-02-22)

### Commands executed

1. `python -m pytest --collect-only -q`
2. `python -m pytest -q tests/e2e/test_coverage_contract.py`
3. `python scripts/cliproxy_provider_smoke.py --strict-required-providers --required-provider openai --required-provider anthropic`

### Results

- Collection: `13544 tests collected in 80.38s` (green).
- Coverage contract tests: `4 passed`.
- Provider required gate: strict required providers pass (`openai`, `anthropic`).

## Evidence Index

### thegent evidence

- CI jobs and required gates: `.github/workflows/ci.yml:10` (preflight), `.github/workflows/ci.yml:66` (test), `.github/workflows/ci.yml:120` (quality), `.github/workflows/ci.yml:183` (coverage gate), `.github/workflows/ci.yml:237` (integration)
- Coverage threshold policy (`fail_under = 100`): `pyproject.toml:159`
- Marker taxonomy includes `chaos` and `a11y`: `pyproject.toml:129`
- Coverage lifecycle contract tests: `tests/e2e/test_coverage_contract.py:1`
- E2E CLI gap register (297 total commands, 63 covered, 234 missing): `docs/governance/TEST_COVERAGE_CRITICAL_GAP.md:13`
- Coverage analyzer script now executes but still undercounts command surface (reports only 3 commands): `scripts/analyze_test_coverage.py:25`
- Collection blocker in IPC watcher loop fixed during this pass: `src/thegent/infra/ipc.py:221`
- Provider smoke task wiring: `Taskfile.yml:516`

### cliproxyapi-plusplus evidence

- Websocket executor fallback only on `426 Upgrade Required`: `pkg/llmproxy/executor/codex_websockets_executor.go:243`
- Websocket incremental mode gated by `websockets` attribute/metadata: `sdk/api/handlers/openai/openai_responses_websocket.go:314`
- `websockets` attribute only set when `ck.Websockets` true: `pkg/llmproxy/watcher/synthesizer/config.go:237`
- Existing websocket tests are normalization-focused, not full stack: `sdk/api/handlers/openai/openai_responses_websocket_test.go:14`
- Keep-alive server surface has unit tests but no builder+daemon readiness integration path coverage: `pkg/llmproxy/api/server_test.go:80`

## Current State Verdict

- Harness translation logic has strong unit coverage in shim normalization and alias governance.
- End-to-end reliability is not yet release-safe due to:
  - stale coverage-analysis semantics (script runs, output is not yet authoritative),
  - missing end-to-end coverage for most CLI command surface,
  - cliproxy websocket/HTTP fallback and lifecycle gaps at integration level.

## Gap Register

| Gap ID | Area                                    | Gap                                                                                                                                      | Evidence                                                                                                      | Severity              | Exit Criteria                                                                                                           |
| ------ | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| G-001  | Test baseline                           | Collection was red at audit start due to IPC indentation; fixed in this pass and now green.                                              | `src/thegent/infra/ipc.py:221`; live rerun `13544 collected`                                                  | Closed (was Critical) | Keep preflight gate to prevent regressions.                                                                             |
| G-002  | Coverage posture                        | Policy requires 100%, and CI now runs `coverage:ci` through a required coverage gate job, but analyzer semantics are stale.              | `pyproject.toml:159`, `scripts/analyze_test_coverage.py:25`, `.github/workflows/ci.yml:183`                   | High                  | Keep gap doc + `coverage:ci` gate; analyzer needs topology refresh.                                                     |
| G-003  | CLI E2E completeness                    | Agent-only requirement unmet: 234/297 CLI commands lack E2E tests.                                                                       | `docs/governance/TEST_COVERAGE_CRITICAL_GAP.md:13`                                                            | Critical              | Command-level E2E matrix reaches 100% or approved staged target with enforced roadmap gates.                            |
| G-004  | Provider strict gate                    | Required-provider strict gate now passes in this environment, but needs deterministic CI lifecycle preflight to stay stable.             | Live strict smoke pass; `Taskfile.yml:516`                                                                    | Medium                | Required providers pass in CI with explicit proxy lifecycle setup.                                                      |
| G-005  | Harness E2E parity                      | `clode` has stronger E2E than `dex`/`roid`/`fanta`; resume/continue/headless matrix mostly unit-level.                                   | Child-agent audit; `tests/test_e2e_cli_core_a.py` coverage asymmetry                                          | High                  | Equal E2E parity suite across harnesses where native capability exists; explicit expected-fail tests where it does not. |
| G-006  | CLIProxy websocket fallback             | Codex websocket executor retries HTTP only for 426; other handshake failures do not auto-fallback.                                       | `pkg/llmproxy/executor/codex_websockets_executor.go:243`                                                      | High                  | Integration test-proven fallback policy for non-success websocket handshakes.                                           |
| G-007  | CLIProxy incremental websocket contract | Incremental mode depends on `websockets` attr/meta; default config may silently disable expected behavior.                               | `sdk/api/handlers/openai/openai_responses_websocket.go:314`, `pkg/llmproxy/watcher/synthesizer/config.go:237` | Medium                | Explicit config contract + integration tests for both incremental enabled/disabled paths.                               |
| G-008  | Daemon lifecycle preflight              | No full-stack readiness test proving service is truly ready before client traffic and keep-alive shutdown semantics across builder path. | Child-agent audit; `pkg/llmproxy/api/server_test.go:80`                                                       | Medium                | E2E lifecycle tests cover start hooks, readiness, keep-alive timeout shutdown.                                          |
| G-009  | Holistic gates reliability              | Security/chaos/a11y/perf lanes are configured, but reliability depends on baseline green and deterministic fixtures.                     | `.github/workflows/ci.yml:108`                                                                                | Medium                | All domain lanes deterministic; no flaky/non-blocking loopholes for required gates.                                     |

## End-to-End Phased Plan (DAG)

### Phase P0: Baseline Stabilization (Blockers)

- P0-T1: Fix collection blockers (completed in this pass: `src/thegent/infra/ipc.py` indentation).
- P0-T2: Add/verify local preflight command (`collect-only + coverage-contract + provider required gate`) and run in CI bootstrap lane.
- P0-T3: Repair stale coverage analyzer semantics (`scripts/analyze_test_coverage.py`) to current CLI topology and command discovery.
- P0-T4: Add required CI `coverage:ci` lane (fail-closed).

Dependencies:

- P0-T2 depends on P0-T1.
- P0-T4 depends on P0-T2 and P0-T3.

### Phase P1: Harness + Provider Contract Hardening

- P1-T1: Lock Anthropic provider smoke contract with regression tests so strict gate remains stable across runs.
- P1-T2: Expand harness parity E2E tests for `dex`, `roid`, `fanta` to match `clode` depth for supported capabilities.
- P1-T3: Add explicit expected unsupported-capability E2E assertions (e.g., fanta resume/continue).
- P1-T4: Promote provider strict required gate as merge-blocking invariant (already present; enforce as red/green SLO).

Dependencies:

- P1-T4 depends on P1-T1.
- P1-T3 depends on P1-T2.

### Phase P2: CLIProxy Native Compatibility Lifecycle

- P2-T1: Implement/test broader websocket->HTTP fallback policy for non-success websocket handshakes.
- P2-T2: Add integration tests for incremental websocket mode toggled by `websockets` capability metadata.
- P2-T3: Add service-builder readiness + keep-alive timeout E2E tests.
- P2-T4: Add provider/model endpoint capability integration test to prevent unknown-provider/model translation regressions.

Dependencies:

- P2-T2 depends on P2-T1.
- P2-T3 independent.
- P2-T4 depends on P2-T1.

### Phase P3: Holistic 100% Governance Closure

- P3-T1: Execute command-by-command E2E backfill plan from 63/297 to full target.
- P3-T2: Strengthen chaos/perf/security/a11y suites with deterministic fixtures and artifact contracts.
- P3-T3: Add mutation and resilience score tracking in CI report artifacts.
- P3-T4: Add weekly drift job producing automated gap delta report (commands covered, failing providers, flaky domains).

Dependencies:

- P3-T1 depends on P0 complete.
- P3-T2 depends on P0 complete.
- P3-T3 depends on P3-T2.
- P3-T4 depends on P3-T1 and P3-T2.

## Execution Batches (Child-Agent Ready)

- Batch A (Fast unblock, ~5-10 min): P0-T1, P0-T2.
- Batch B (Coverage governance, ~10-15 min): P0-T3, P0-T4.
- Batch C (Provider/harness parity, ~10-20 min): P1-T1, P1-T2, P1-T3, P1-T4.
- Batch D (Proxy lifecycle, ~15-25 min): P2-T1, P2-T2, P2-T3, P2-T4.
- Batch E (Holistics/closure, rolling): P3-T1..P3-T4.

## Immediate Next Actions

1. Land P0-T2 as a CI preflight job running the exact three baseline commands.
2. Land P0-T4 so coverage becomes a required CI status, not a policy-only statement.
3. Land P2 websocket/lifecycle integration tests in `cliproxyapi-plusplus` to close native Codex compatibility gaps.
