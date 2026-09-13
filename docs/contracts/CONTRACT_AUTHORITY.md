# Contract Authority

**Status:** Authoritative
**Date:** 2026-02-14
**Scope:** Structured output contracts for thegent orchestration

---

## 1. Purpose

This document is the **single source of truth** for structured output contracts used by thegent. All agent outputs, XML protocols, and provider-specific formats normalize to the canonical schema defined here.

---

## 2. Contract Registry

| Contract ID | Version      | Description                                          | Compatibility             |
| ----------- | ------------ | ---------------------------------------------------- | ------------------------- |
| csm         | csm-v1       | Canonical Structured Message: unified schema         | task-tool-18, zen-rich-v1 |
| task-tool   | task-tool-18 | Task-tool 18-tag XML (snake_case)                    | csm-v1                    |
| zen         | zen-rich-v1  | Zen rich protocol (status, progress, actions, files) | csm-v1                    |

---

## 3. Canonical Schema (CSM v1)

All agent outputs normalize to `CanonicalStructuredMessage`:

| Field                | Type      | Required | Description                                                 |
| -------------------- | --------- | -------- | ----------------------------------------------------------- |
| task_id              | str       | No       | Task identifier                                             |
| run_id               | str       | No       | Run correlation ID                                          |
| chunk_id             | str       | No       | Chunk identifier                                            |
| status               | enum      | Yes      | pending, in_progress, completed, failed, blocked, cancelled |
| phase                | enum      | No       | planner, operator, reviewer, unknown                        |
| progress             | float     | No       | 0.0–1.0                                                     |
| objective            | str       | No       | Task objective                                              |
| summary              | str       | No       | Condensed summary                                           |
| actions_completed    | list[str] | No       | Completed action list                                       |
| issues               | list[str] | No       | Issues encountered                                          |
| next_steps           | list[str] | No       | Recommended next steps                                      |
| evidence_set_hash    | str       | No       | Governance evidence hash                                    |
| policy_gate_id       | str       | No       | Policy gate identifier                                      |
| decision_reason_code | str       | No       | Decision rationale code                                     |
| schema_version       | str       | Yes      | Always "csm-v1"                                             |
| source_contract      | str       | No       | Original contract (task-tool-18, zen-rich-v1, etc.)         |

---

## 4. Versioning Policy

- **contract_id**: Logical contract (csm, task-tool, zen).
- **version**: Semantic version string (e.g. csm-v1, task-tool-18).
- **compatible_with**: Versions that can be normalized to this contract.
- **deprecated**: If true, do not use for new integrations.

Migration: Use dual-read/dual-write windows when upgrading. Never remove a version without a deprecation period. See `docs/contracts/UPGRADE_PLAYBOOK.md` for upgrade, canary, and rollback procedures.

---

## 5. Adapter Contract

Provider adapters implement `OutputAdapter`:

- `provider`: Provider identifier (copilot, gemini, codex, claude, etc.)
- `normalize(raw, context) -> AdapterResult`: Convert raw output to CSM

Adapters must:

- Return `AdapterResult` with `csm` and `confidence` (0.0–1.0).
- Populate `parse_errors` on partial failure.
- Set `source_contract` when known.

---

## 6. Implementation Location

- **Registry**: `src/thegent/contracts/registry.py`
- **CSM schema**: `src/thegent/contracts/csm.py`
- **Adapters**: `src/thegent/contracts/adapters.py`
- **Provider contracts**: `docs/contracts/PROVIDER_ADAPTER_CONTRACTS.md`
- **Usage**: `from thegent.contracts import get_registry, CanonicalStructuredMessage, normalize_output`

---

## 7. Legacy Adapter (G-KD-01)

Legacy or non-XML outputs are handled via:

- **GenericOutputAdapter**: Uses `extract_condensed` for plain text; sets `source_contract=plain`, confidence 0.7.
- **Fallback path**: When XML adapter fails or no tags, `normalize_output` returns CSM with `source_contract=fallback-plain`, confidence 0.3–0.5.
- **Contract negotiation**: `source_contract` in CSM identifies origin (xml-tags, plain, fallback-plain). Policy gates may reject fallback-plain for critical lanes.

All adapters produce CSM with `schema_version="csm-v1"`. Legacy outputs are never rejected at parse time; they are normalized and tagged for policy decisions.

---

## 8. Fallback Control Plane

See **FALLBACK_POLICY.md** for normalization fallback policy, observability, and guardrails.

---

## 9. References

- Research validation: `docs/docset/thegent-research-validation-2026-02-14.md`
- Cross-analysis: `docs/docset/thegent-cross-analysis-matrix-2026-02-14.md`
- Kush docs: `docs/docset/thegent-kush-docs-deep-dive-2026-02-14.md`
- Gap analysis: `docs/docset/thegent-gaps-and-discovery-2026-02-14.md`
- **Task-tool XML contract (authoritative):** `../task-tool/docs/xml_contract.md` — aligned with implementation (task_graph root, snake_case tags)
