# Hook Spiral Guard

## Purpose

The regression spiral guard prevents agent sessions from accumulating hidden failures until quality collapses.

It enforces:

- continuous regression detection,
- interrupt-style escalation for critical growth,
- test/build/environment-first workflow,
- e2e-first evidence requirements for no-human-feedback development loops,
- freshness thresholds on test/build/e2e evidence artifacts,
- deterministic per-band retry budgets and cooldown windows with explicit remediation directives.

## Components

- `hooks/governance-gates.sh`
  - Gate: `regression-spiral-guard`
  - Selector mode:
    - `QA_GATES_ONLY` / `THEGENT_GATES_ONLY` enable selected-gate execution
    - selectors are canonicalized (trim, drop empty, dedupe, sort) before execution/cache scope
  - Writes:
    - `.claude/verification/regression-spiral-guard.json`
    - `.claude/verification/regression-spiral-state.json`
    - `.claude/verification/regression-spiral-alert.json`
    - `.claude/verification/regression-spiral-metrics.jsonl`
- `hooks/continuous-work-guard.sh`
  - Reads `regression-spiral-alert.json`
  - Emits interrupt instructions and exits `2` only for `severity=critical`
- `hooks/lib/spiral-config.sh`
  - Shared loader that consumes Rust `hook-dispatcher governance spiral-config`
- `hooks/hook-dispatcher/src/main.rs`
  - Subcommand: `governance spiral-config [path] [--format env|json]`
  - Subcommand: `governance spiral-trend [path] [--window N]`
  - Central parser authority for spiral policy defaults + YAML overrides
  - Trend aggregation over metrics stream (breach rate, interrupt count, max streak, MTTR proxy, stale evidence event counts)

## Config Resolution Order

1. Environment variables (`QA_SPIRAL_*`, `QA_REQUIRE_*`)
2. `hooks/hook-config.yaml` at `settings.regression_spiral_guard`
3. Built-in defaults in `hooks/lib/spiral-config.sh`

## Selector Canonicalization Contract

- Input sources: `QA_GATES_ONLY` (preferred), fallback `THEGENT_GATES_ONLY`
- Canonicalization pipeline in `hooks/governance-gates.sh`:
  - remove whitespace
  - split CSV
  - drop empty entries
  - dedupe entries
  - stable sort (`LC_ALL=C sort -u`)
  - rejoin CSV
- Canonical selector value is used for:
  - selected-mode execution list
  - cache key scope (`GOVERNANCE-GATES:<canonical-selector>`)
- Empty selector behavior:
  - If selector env is explicitly provided but canonical list is empty, selector mode still activates and fails closed with explicit reason (`no valid gate labels ...`).

### Selector Examples

- Single gate:
  - `QA_GATES_ONLY=regression_spiral_guard hooks/governance-gates.sh`
- Multi gate (canonicalized for execution + cache scope):
  - input: `QA_GATES_ONLY="reliability, regression_spiral_guard, reliability"`
  - canonical selector: `regression_spiral_guard,reliability`
- Empty entries fail closed:
  - `QA_GATES_ONLY=" , , " hooks/governance-gates.sh`
  - expected: fail-closed with `no valid gate labels in QA_GATES_ONLY=,,`
- Malformed/unknown token fail closed:
  - `QA_GATES_ONLY="regression_spiral_guard;rm-rf/" hooks/governance-gates.sh`
  - expected: fail-closed with `unknown gate label: ...`

## Supported Environment Overrides

- `QA_SPIRAL_MAX_FAILED_TESTS`
- `QA_SPIRAL_MAX_FLAKY_TESTS`
- `QA_SPIRAL_MAX_MISSING_TEST_PAIRS`
- `QA_SPIRAL_MAX_MISSING_TEST_TYPES`
- `QA_SPIRAL_MAX_TEST_EVIDENCE_AGE_MINUTES`
- `QA_SPIRAL_MAX_BUILD_EVIDENCE_AGE_MINUTES`
- `QA_SPIRAL_MAX_E2E_EVIDENCE_AGE_MINUTES`
- `QA_SPIRAL_STREAK_TRIGGER`
- `QA_REQUIRE_E2E_FIRST`
- `QA_REQUIRE_ENV_READY_FIRST`
- `QA_SPIRAL_MAX_YELLOW_RETRIES`
- `QA_SPIRAL_MAX_RED_RETRIES`
- `QA_SPIRAL_YELLOW_COOLDOWN_MINUTES`
- `QA_SPIRAL_RED_COOLDOWN_MINUTES`
- `QA_SPIRAL_DIRECTIVE_GREEN`
- `QA_SPIRAL_DIRECTIVE_YELLOW`
- `QA_SPIRAL_DIRECTIVE_RED`
- `QA_REGRESSION_SPIRAL_FAIL_CLOSED`

## Freshness Threshold Defaults

From `hooks/hook-config.yaml` (`settings.regression_spiral_guard`):

- `max_test_evidence_age_minutes: 90` for async test evidence (`RESULTS_FILE`)
- `max_build_evidence_age_minutes: 90` for build/env evidence (`.claude/verification/qa-state.json`)
- `max_e2e_evidence_age_minutes: 180` for e2e evidence (`.claude/verification/qa-attestation.json`, when `require_e2e_first=true`)

Missing files count as stale evidence violations.

## Trend Output Fields

`hook-dispatcher governance spiral-trend` now includes:

- `stale_test_evidence_events`
- `stale_build_evidence_events`
- `stale_e2e_evidence_events`
- `pressure_score`
- `policy_band` (`green`, `yellow`, `red`)

Pressure score is deterministic and normalized to `[0,1]`:

- `0.40 * breach_rate`
- `0.20 * interrupt_rate`
- `0.20 * stale_evidence_rate`
- `0.15 * streak_pressure` (`max_streak/3`, capped at `1`)
- `0.05 * positive_violations_delta_pressure` (`max(violations_delta,0)/3`, capped at `1`)

Policy bands:

- `red` when `pressure_score >= 0.75`
- `yellow` when `pressure_score >= 0.45` and `< 0.75`
- `green` otherwise

Shell gate parity:

- `hooks/governance-gates.sh` writes `pressure_score` and `policy_band` to both:
  - `.claude/verification/regression-spiral-guard.json`
  - `.claude/verification/regression-spiral-metrics.jsonl`
- `policy_band=red` is a strict hard-interrupt contract in shell gate logic:
  - `interrupt=true`
  - `enforcement_path=fail_closed`

## Spiral Band Ops Fields

The spiral state/report/alert/metrics now share deterministic operational fields:

- State (`.claude/verification/regression-spiral-state.json`)
  - `band_retry_counts.green`
  - `band_retry_counts.yellow`
  - `band_retry_counts.red`
  - `cooldown_until` (epoch seconds, nullable)
  - `escalation_stage`
  - `last_policy_band`
  - `last_directive`
- Report (`.claude/verification/regression-spiral-guard.json`)
  - `remediation_directive`
  - `band_retry_count`
  - `cooldown_until`
  - `escalation_stage`
- Alert (`.claude/verification/regression-spiral-alert.json`)
  - `policy_band`
  - `band_retry_count`
  - `cooldown_until`
  - `escalation_stage`
  - `remediation_directive`
- Metrics JSONL (`.claude/verification/regression-spiral-metrics.jsonl`)
  - `remediation_directive`
  - `band_retry_count`
  - `cooldown_until`
  - `escalation_stage`

## Operational Lifecycle

1. Spiral policy computes `pressure_score` and assigns a policy band (`green|yellow|red`).
2. Per-band retry counters are incremented deterministically and constrained by:
   - `max_yellow_retries`
   - `max_red_retries`
3. Cooldown windows are applied with:
   - `yellow_cooldown_minutes`
   - `red_cooldown_minutes`
4. If cooldown has elapsed, retry counters reset before evaluating the next event.
5. Repeated yellow events past threshold escalate deterministically into the red interrupt path.
6. Red remains a hard interrupt contract (`fail_closed`) and carries red remediation directive.
7. `continuous-work-guard.sh` consumes alert fields and prints deterministic directive/cooldown context; it exits `2` only for `severity=critical`.

## Operational Notes

- Warning alerts do not hard-stop work.
- Critical alerts trigger interruption behavior.
- Alerts are cleared automatically when spiral conditions recover.
- Attempt counters are session-scoped to reduce cross-session false lockouts.

## Pre-Work Hard Gate

- Task start surfaces enforce a pre-work hard gate before starting new work.
- The gate blocks when required freshness evidence is missing or stale:
  - test evidence: `~/.claude/.async-test-results.json`
  - build/env evidence: `<project>/.claude/verification/qa-state.json`
  - e2e evidence (when `require_e2e_first=true`): `<project>/.claude/verification/qa-attestation.json`
- Thresholds are loaded from `hooks/hook-config.yaml` at `settings.regression_spiral_guard`, with defaults:
  - `require_e2e_first=true`
  - `max_test_evidence_age_minutes=90`
  - `max_build_evidence_age_minutes=90`
  - `max_e2e_evidence_age_minutes=180`

### Start-Surface Parity Matrix

| Surface     | Entry Point                                                     | Gate Behavior on Failure                                                                               |
| ----------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| CLI         | `thegent plan next` (`do_next_impl`)                            | Returns `governance_blocked=true` payload, includes `governance_block.remediation_steps`, blocks start |
| CLI         | `thegent plan get-next` (`do_next_impl` wrapper)                | Propagates `governance_blocked=true` with remediation and exits non-zero                               |
| CLI         | `thegent plan spawn-next` (`spawn_next_impl`)                   | Propagates `governance_blocked=true`; does not spawn or claim                                          |
| CLI         | `thegent plan claim` (`work_stream_claim_impl`)                 | Returns `success=false` + `governance_blocked=true` with remediation                                   |
| MCP         | `thegent_do_next`                                               | Returns blocked payload unchanged from `do_next_impl`                                                  |
| MCP         | `thegent_plan_get_next`                                         | Returns error payload that preserves `governance_blocked` + remediation                                |
| Auto-launch | `AutoLaunchSystem._try_launch_next` fallback via `do_next_impl` | Records `governance_blocked` event and skips launch batch                                              |
| Auto-launch | `AutoLaunchSystem._launch_item` claim/start path                | Uses `work_stream_claim_impl`; on block records `claim_failed` and skips `bg_impl` start               |

## Validation

Run:

```bash
task test:hooks:governance
```

This runs:

- shell syntax checks for relevant hooks,
- unit tests for YAML config loading and defaults,
- trend command tests over spiral metrics stream,
- selector-mode fast + strict lanes,
- selector artifact schema checks and schema-drift sentinel checks.

## CI Lane Mapping

- PR / manual:
  - GitHub Actions job: `governance-selector-fast`
  - Task target: `task test:hooks:selector-fast`
- Push / nightly / manual:
  - GitHub Actions job: `governance-selector-strict`
  - Task target: `task test:hooks:selector-strict`
- Both lanes emit fail-closed evidence snippets (`fail-closed`, `policy_band=red`, `critical_interrupt`) on failure and upload logs as artifacts.

## Artifact Schema Contract

- Selector-mode contracts are enforced by tests in `tests/test_hook_governance_gate_selector.py`:
  - Required key/type assertions:
    - report (`regression-spiral-guard.json`)
    - metrics line (`regression-spiral-metrics.jsonl`)
    - state (`regression-spiral-state.json`)
    - alert (`regression-spiral-alert.json`, when expected)
  - Schema-drift sentinel:
    - exact key-set assertions for report/metric/state/alert payloads to catch accidental contract drift.
  - Contract version:
    - all spiral artifacts emit `contract_version: "v1"` and tests enforce it.
