### [WL-6500] Harden execution registry schema-marker initialization

**Title:** Ensure registry bootstrap writes a single schema marker with a valid hash chain seed.
**Source:** [thegent/src/thegent/execution.py:1438]
**Acceptance Checklist:**

- [ ] Add a focused unit test for first-run registry creation.
- [ ] Verify only one schema marker is written when registry is absent.
- [ ] Confirm marker hash is reproducible for deterministic payloads.
      **Notes:** Targets startup integrity for append-only run registry creation.

### [WL-6501] Validate execution schema marker payload construction

**Title:** Refactor marker event assembly to enforce required fields before persistence.
**Source:** [thegent/src/thegent/execution.py:1442]
**Acceptance Checklist:**

- [ ] Assert marker includes schema version and hash before file append.
- [ ] Add a negative test for malformed marker payload shape.
- [ ] Keep backward behavior for existing valid registries unchanged.
      **Notes:** Keeps registry write path explicit and testable at payload-construction time.

### [WL-6502] Strengthen AGENTS.md template auto-detection signal

**Title:** Improve thematic AGENTS marker detection to reduce false template selection.
**Source:** [thegent/src/thegent/cli/apps/project.py:670]
**Acceptance Checklist:**

- [ ] Add tests covering thematic and non-thematic AGENTS.md examples.
- [ ] Document the decision signal used for template auto-selection.
- [ ] Preserve current fallback behavior when markers are inconclusive.
      **Notes:** Focuses on deterministic project template inference.

### [WL-6503] Add marker-presence diagnostics for template inference

**Title:** Emit structured debug context for marker checks during template resolution.
**Source:** [thegent/src/thegent/cli/apps/project.py:672]
**Acceptance Checklist:**

- [ ] Capture which marker path triggered selection in debug output.
- [ ] Add regression coverage for mixed marker-state repositories.
- [ ] Confirm no user-visible verbosity increase in default mode.
      **Notes:** Aims to speed root-cause analysis for auto-template mismatches.

### [WL-6504] Cache discovery settings in parent-agent checks

**Title:** Eliminate repeated settings initialization inside parent process scanning loops.
**Source:** [thegent/src/thegent/discovery/__init__.py:252]
**Acceptance Checklist:**

- [ ] Move settings resolution out of per-parent iteration path.
- [ ] Add benchmark-style test or timing assertion for loop efficiency.
- [ ] Verify discovery behavior parity on successful and failing scans.
      **Notes:** Reduces overhead in frequent process ancestry checks.

### [WL-6505] Harden discovered-parent marker lookup behavior

**Title:** Tighten ppid marker file checks to handle invalid or stale discovery artifacts.
**Source:** [thegent/src/thegent/discovery/__init__.py:257]
**Acceptance Checklist:**

- [ ] Add validation for malformed `ppid_*.json` discovery entries.
- [ ] Ensure stale marker files do not produce false agent attribution.
- [ ] Add a test fixture for stale and missing marker combinations.
      **Notes:** Prevents incorrect process classification from artifact drift.

### [WL-6506] Align evidence ledger marker semantics with execution registry

**Title:** Standardize schema marker write contract across ledger and execution stores.
**Source:** [thegent/src/thegent/governance/evidence_ledger.py:63]
**Acceptance Checklist:**

- [ ] Compare marker field set with execution registry implementation.
- [ ] Add cross-module test asserting consistent schema marker keys.
- [ ] Verify ledger bootstrap remains append-only and idempotent.
      **Notes:** Improves consistency across hash-chained JSONL ledgers.

### [WL-6507] Expand governance suppression rule coverage

**Title:** Broaden justified-noqa parsing to support explicit code lists with reason clauses.
**Source:** [thegent/src/thegent/governance/native_governance_scan.py:81]
**Acceptance Checklist:**

- [ ] Add rule tests for multi-code `noqa` suppressions with `-- reason`.
- [ ] Confirm bare suppressions remain violations.
- [ ] Update rule documentation with accepted suppression syntax examples.
      **Notes:** Tightens governance scanner correctness for practical suppression patterns.

### [WL-6508] Unify marker defaults across perf lane subcommands

**Title:** Centralize default marker expression for `xdist` and sibling parser commands.
**Source:** [thegent/scripts/pytest_wave_perf_orchestrator.py:938]
**Acceptance Checklist:**

- [ ] Replace duplicated literal marker strings with one shared constant.
- [ ] Add parser tests asserting default equality across relevant subcommands.
- [ ] Ensure CLI help output remains clear and unchanged in intent.
      **Notes:** Reduces drift risk between perf-lane entrypoints.

### [WL-6509] Elevate requirements marker alert remediation guidance

**Title:** Improve missing-requirement alert action text with concrete fix workflow.
**Source:** [thegent/scripts/test_pytest_wave_artifacts.py:1746]
**Acceptance Checklist:**

- [ ] Update remediation copy to include command and expected artifact path.
- [ ] Add snapshot/assertion test for alert payload content.
- [ ] Verify alert code and severity remain stable for downstream consumers.
      **Notes:** Makes quality-gate alerts directly actionable during CI triage.
