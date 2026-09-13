# Architecture Refactor Requirements Quality Checklist

Purpose: Validate the quality of requirements for cross-repo architecture audit, refactor planning, and shared-module decomposition.
Created: 2026-02-28
Depth: Standard
Audience: Reviewer (PR/architecture planning)

## Requirement Completeness

- [ ] CHK001 Are the target repositories explicitly enumerated (cliproxyapi++, thegent, agentapi++, helios app/cli/others, tokenledger, and named "other" repos) with inclusion/exclusion boundaries? [Completeness, Gap]
- [ ] CHK002 Does the requirements set define a per-repo current-state inventory format (architecture style, language stack, service boundaries, coupling hotspots)? [Completeness, Gap]
- [ ] CHK003 Are required outputs defined for both audit and plan artifacts (findings, recommended moves, phased DAG, and owner-ready action list)? [Completeness, Gap]
- [ ] CHK004 Are shared-code extraction requirements defined separately for "within one repo" vs "across multiple repos" reuse cases? [Completeness, Gap]
- [ ] CHK005 Are requirements defined for evaluating hexagonal, clean architecture, SOLID, microservice boundaries, and polyglot constraints as independent dimensions? [Completeness, Gap]

## Requirement Clarity

- [ ] CHK006 Are terms such as "dedmodularization", "shared code projects", and "individual refactors" explicitly defined with unambiguous meaning? [Clarity, Ambiguity]
- [ ] CHK007 Are decision thresholds for when to split into subprojects vs keep in-place modules quantified (e.g., ownership, change frequency, dependency churn)? [Clarity, Gap]
- [ ] CHK008 Is "best practices research" scoped to authoritative sources and dated evidence windows rather than broad unspecific guidance? [Clarity, Gap]
- [ ] CHK009 Are required architecture quality attributes (maintainability, deployability, observability, performance, security) explicitly ranked by priority? [Clarity, Gap]

## Requirement Consistency

- [ ] CHK010 Are monorepo/shared-library requirements consistent with microservice autonomy requirements, with conflict-resolution rules defined? [Consistency, Conflict]
- [ ] CHK011 Are polyglot standardization requirements consistent with language-specific optimization requirements (no contradictory mandates)? [Consistency, Conflict]
- [ ] CHK012 Do decomposition requirements align with existing governance constraints (worktree policy, quality gates, no-fallback policy)? [Consistency, Assumption]

## Acceptance Criteria Quality

- [ ] CHK013 Are acceptance criteria measurable for each repo audit (e.g., mandatory architecture map, dependency graph, risk matrix, and scored recommendations)? [Acceptance Criteria, Gap]
- [ ] CHK014 Are acceptance criteria measurable for each proposed refactor plan phase (entry/exit criteria, deliverables, rollback requirements)? [Acceptance Criteria, Gap]
- [ ] CHK015 Is there an explicit requirement for traceability between findings and proposed actions (Finding ID -> Plan Task ID -> Validation Gate)? [Traceability, Gap]

## Scenario Coverage

- [ ] CHK016 Are primary scenarios specified for each repo: keep as-is, internal modular split, external shared module extraction, or service boundary extraction? [Coverage, Gap]
- [ ] CHK017 Are alternate scenarios specified where one repo is blocked (permissions/conflicts) but cross-repo planning must still continue? [Coverage, Gap]
- [ ] CHK018 Are exception scenarios specified for contradictory repo constraints (e.g., different release cadences or incompatible runtime assumptions)? [Coverage, Gap]
- [ ] CHK019 Are recovery scenarios specified when a proposed decomposition increases coupling or breaks ownership boundaries after trial adoption? [Coverage, Gap]

## Edge Case Coverage

- [ ] CHK020 Are edge-case requirements defined for tiny repos where extraction overhead may exceed benefit? [Edge Case, Gap]
- [ ] CHK021 Are requirements defined for legacy or generated code areas where hexagonal boundaries cannot be cleanly introduced? [Edge Case, Gap]
- [ ] CHK022 Are requirements defined for cross-language shared contract drift (schema/protocol mismatch across TS/Python/Go/Rust consumers)? [Edge Case, Gap]

## Non-Functional Requirements

- [ ] CHK023 Are performance and latency impact requirements defined for any proposed service split or shared library abstraction layer? [Non-Functional, Gap]
- [ ] CHK024 Are security requirements defined for extracted shared modules (auth boundary, secret handling, dependency supply-chain checks)? [Non-Functional, Gap]
- [ ] CHK025 Are operability requirements specified (monitoring, alerting, failure isolation, and incident ownership after decomposition)? [Non-Functional, Gap]
- [ ] CHK026 Are developer-experience requirements defined (build/test speed, local setup complexity, cognitive load) for each refactor pattern? [Non-Functional, Gap]

## Dependencies and Assumptions

- [ ] CHK027 Are external dependencies and assumptions explicitly documented (repo accessibility, branch policy, CI capacity, release windows)? [Dependencies, Assumption]
- [ ] CHK028 Is the assumption about cross-repo shared package versioning strategy documented (single version stream vs per-repo pinned versions)? [Dependencies, Assumption]
- [ ] CHK029 Are assumptions about ownership model for shared modules (central platform team vs federated ownership) explicitly stated? [Dependencies, Assumption]

## Ambiguities and Conflicts

- [ ] CHK030 Does the requirements set resolve ambiguity on audit depth (lightweight inventory vs formal architecture decision package per repo)? [Ambiguity, Gap]
- [ ] CHK031 Does the requirements set resolve ambiguity on intended consumers (author-only planning artifact vs org-level review gate)? [Ambiguity, Gap]
- [ ] CHK032 Are conflicting goals (rapid decomposition vs stability risk minimization) explicitly prioritized with tie-break rules? [Conflict, Gap]
