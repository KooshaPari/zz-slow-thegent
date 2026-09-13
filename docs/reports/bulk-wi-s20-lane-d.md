### [WL-6550] Harden execution schema marker bootstrap on first-write

**Title:** Ensure registry initialization emits a single schema marker before run events are appended.
**Source:** [thegent/src/thegent/execution.py:1442]
**Acceptance Checklist:**

- [ ] Add a targeted unit test for new-registry creation with empty session state.
- [ ] Assert bootstrap writes exactly one schema marker record on first open.
- [ ] Verify subsequent `register_start` calls do not duplicate schema markers.
      **Notes:** Focuses on deterministic append-only startup behavior for run registry creation.

### [WL-6551] Make registry tail-hash reads failure-transparent

**Title:** Replace silent hash-read exception handling with structured diagnostics and safe fallback.
**Source:** [thegent/src/thegent/execution.py:1452]
**Acceptance Checklist:**

- [ ] Catch JSON decode and IO errors explicitly when reading the last record hash.
- [ ] Emit debug-level context for corrupted or partial trailing lines.
- [ ] Preserve `None` fallback behavior to avoid breaking existing call sites.
      **Notes:** Improves operability when registry files are truncated or malformed.

### [WL-6552] Tighten thematic AGENTS marker signal for auto template resolution

**Title:** Improve AGENTS thematic detection criteria used by migration template inference.
**Source:** [thegent/src/thegent/cli/apps/project.py:670]
**Acceptance Checklist:**

- [ ] Add tests for thematic and non-thematic `AGENTS.md` fixtures.
- [ ] Reduce false positives where a generic AGENTS file should not force `ag-dd`.
- [ ] Keep fallback template behavior unchanged when no markers are present.
      **Notes:** Reduces accidental template selection drift during `project migrate --template auto`.

### [WL-6553] Surface marker-hit diagnostics in project template auto mode

**Title:** Expose which existing marker path triggered `ag-dd` selection during auto resolution.
**Source:** [thegent/src/thegent/cli/apps/project.py:672]
**Acceptance Checklist:**

- [ ] Add optional debug metadata for marker match outcomes.
- [ ] Verify default CLI output remains unchanged without debug flags.
- [ ] Add regression tests for mixed marker states in the same repository.
      **Notes:** Speeds triage when inferred template differs from operator expectation.

### [WL-6554] Cache ThegentSettings lookup in parent process ancestry scans

**Title:** Remove per-parent settings instantiation from parent-agent detection loops.
**Source:** [thegent/src/thegent/discovery/__init__.py:252]
**Acceptance Checklist:**

- [ ] Resolve settings once per scan invocation and pass discovery directory into checks.
- [ ] Confirm behavior parity for successful and failed parent traversal.
- [ ] Add a focused test or benchmark assertion for reduced repeated initialization.
      **Notes:** Targets avoidable overhead in hot process ancestry checks.

### [WL-6555] Validate discovered-parent marker file shape before trust

**Title:** Require minimal JSON structure checks for `ppid_<pid>.json` before attributing parent agent status.
**Source:** [thegent/src/thegent/discovery/__init__.py:257]
**Acceptance Checklist:**

- [ ] Parse marker content instead of treating file existence as sufficient.
- [ ] Ignore stale or malformed marker payloads without raising.
- [ ] Add fixture-based tests for valid, stale, and corrupt marker files.
      **Notes:** Prevents false-positive parent attribution from orphaned discovery artifacts.

### [WL-6556] Align evidence-ledger schema marker contract with run registry

**Title:** Normalize ledger schema marker fields to match execution registry marker semantics.
**Source:** [thegent/src/thegent/governance/evidence_ledger.py:66]
**Acceptance Checklist:**

- [ ] Compare ledger marker key set against `build_schema_marker_event` output.
- [ ] Add cross-module test coverage for shared marker invariants.
- [ ] Preserve hash-chain integrity and append-only behavior after alignment.
      **Notes:** Improves consistency across JSONL ledgers used by governance and execution paths.

### [WL-6557] Expand justified-noqa matcher to handle multi-code suppressions

**Title:** Support comma-delimited `noqa` code lists when accompanied by inline `-- reason` text.
**Source:** [thegent/src/thegent/governance/native_governance_scan.py:81]
**Acceptance Checklist:**

- [ ] Update justification regex to accept multi-code suppressions.
- [ ] Add rule tests covering valid/invalid suppression comment variants.
- [ ] Keep bare `noqa` annotations as violations.
      **Notes:** Closes practical parsing gaps in governance suppression validation.

### [WL-6558] Deduplicate default marker expression across perf subcommands

**Title:** Centralize shared marker default string used by `collect-tests`, `xdist`, and `testmon-pilot`.
**Source:** [thegent/scripts/pytest_wave_perf_orchestrator.py:932]
**Acceptance Checklist:**

- [ ] Introduce a single constant for the default marker expression.
- [ ] Wire all relevant parser options to the shared constant.
- [ ] Add parser-level test assertions to prevent future literal drift.
      **Notes:** Prevents inconsistent lane selection defaults across perf workflows.

### [WL-6559] Improve unmapped-requirement alert remediation guidance

**Title:** Make `requirements.missing_marker` action text explicitly reference the preferred marker fix flow.
**Source:** [thegent/scripts/test_pytest_wave_artifacts.py:1750]
**Acceptance Checklist:**

- [ ] Update warning action copy with concrete remediation steps and command hints.
- [ ] Add assertion coverage for alert payload wording.
- [ ] Keep alert code/severity stable for downstream consumers.
      **Notes:** Makes artifact health warnings immediately actionable during PR triage.
