<DONE>
# Social Signal Forensic Audit

Date: February 23, 2026

## Scope

Public-post/link surfaces previously cited (LinkedIn, Reddit, marketplace listings, profile pages).

## Method

- Treat social/public posts as hypothesis generators, not technical truth.
- Require independent technical evidence before promotion decisions.

## Findings

1. Social amplification was high for ruvnet ecosystem claims; engineering evidence confidence remained mixed.
2. bar181 public signals were concept-heavy relative to code-level reproducibility evidence.
3. Marketplace/listing surfaces provided adoption signal but not production-readiness proof.

## Forensic Rule Applied

- `claim_without_reproducible_benchmark` => `unverified_claim`
- `repo_activity+tests+release+governance` => `engineering_evidence`

## Decision

- Keep social-derived claims in `signal_only` column in audits.
- Never promote to `adopt` based on social signal alone.
