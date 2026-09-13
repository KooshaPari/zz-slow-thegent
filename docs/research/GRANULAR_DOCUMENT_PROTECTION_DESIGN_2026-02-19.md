<DONE>
# Granular Document R/W Protection — Design

> **Target**: Strict R/W protection for BACKLOG and all markdown; thegent MCP–based; 200 types; 200 params/attributes per type; 100 polishes/QOL/optimizations.
> **Status**: Design / Research
> **Date**: 2026-02-19

---

## 1. Vision

- **Strict R/W protection** for BACKLOG and all `.md` in projects going forward.
- **thegent MCP–based**: all document access and mutations go through MCP tools/servers.
- **Highly granular**: not only plans/research/other, but per–chat-turn write-ups, session management, and many more dimensions.
- **Scale targets**:
  - **200 types**: document types, writedowns, and/or features.
  - **200 params/attributes per type**: fine-grained metadata and controls.
  - **100 polishes**: QOL, optimizations, and refinements layered on top.

---

## 2. Problem

| Current                                   | Target                                                |
| ----------------------------------------- | ----------------------------------------------------- |
| Flat categories (plans, research, other)  | 200+ document/feature types                           |
| Broad R/W (file-level or directory-level) | Per-type, per-attribute R/W                           |
| Ad-hoc session write-ups                  | Every chat turn ends with a write-up for session mgmt |
| Scattered access control                  | Single MCP-based protection layer                     |
| Few metadata dimensions                   | 200 params/attributes per type                        |

---

## 3. Architecture: MCP-Based Protection

### 3.1 Core Principle

**All markdown R/W flows through thegent MCP.** No direct file I/O for `.md` by agents; all access is via MCP tools that enforce:

- Type-aware permissions
- Attribute-level visibility
- Audit trail for every read/write

### 3.2 MCP Server Roles

| Server                    | Responsibility                                        |
| ------------------------- | ----------------------------------------------------- |
| `thegent-docs-rw`         | Document read/write with type + attribute checks      |
| `thegent-backlog-guard`   | BACKLOG-specific R/W; strict claim/complete semantics |
| `thegent-session-writeup` | Per-turn write-ups for session management             |
| `thegent-audit-docs`      | Audit log for all doc access                          |

### 3.3 Protection Layers

1. **Type layer**: Each document has a `doc_type` from the 200-type taxonomy.
2. **Attribute layer**: Each type has up to 200 params/attributes; R/W can be scoped per attribute.
3. **Session layer**: Every chat turn produces a write-up; session mgmt consumes these.
4. **Feature layer**: Types can represent features; feature flags gate R/W.

---

## 4. Type Taxonomy (200 Types — Framework)

A **type** = document type / writedown **and/or** feature. Target: 200 types.

### 4.1 Document / Writedown Types (Sample — expand to 200)

| Category        | Types (examples)                                                                                                                                                                                                                                                                                                                                                                               |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Plans**       | plan-phase, plan-wbs, plan-roadmap, plan-sprint, plan-milestone, plan-dependency, plan-risk, plan-assumption, plan-constraint, plan-budget, plan-timeline, plan-resource, plan-stakeholder, plan-rollout, plan-fallback, plan-contingency, plan-baseline, plan-variant, plan-approval, plan-signoff                                                                                            |
| **Research**    | research-seed, research-audit, research-gap, research-consolidated, research-deep-dive, research-comparison, research-benchmark, research-interview, research-survey, research-literature, research-prototype, research-poc, research-spike, research-exploration, research-validation, research-synthesis, research-recommendation, research-open-question, research-follow-up, research-meta |
| **Session**     | session-turn-writeup, session-handoff, session-escalation, session-checkpoint, session-summary, session-context, session-decision, session-action, session-outcome, session-feedback, session-correction, session-clarification, session-deferral, session-resumption, session-close, session-archive, session-replay, session-audit, session-metadata, session-link                           |
| **Backlog**     | backlog-item, backlog-epic, backlog-story, backlog-task, backlog-bug, backlog-spike, backlog-tech-debt, backlog-refactor, backlog-migration, backlog-deprecation, backlog-enhancement, backlog-fix, backlog-doc, backlog-test, backlog-review, backlog-claim, backlog-complete, backlog-block, backlog-priority, backlog-depends                                                               |
| **Specs**       | spec-prd, spec-fr, spec-api, spec-schema, spec-contract, spec-adr, spec-rfc, spec-design, spec-architecture, spec-interface, spec-data-model, spec-workflow, spec-state-machine, spec-error-handling, spec-security, spec-compliance, spec-test-plan, spec-release, spec-version, spec-changelog                                                                                               |
| **Governance**  | gov-policy, gov-override, gov-escalation, gov-audit, gov-compliance, gov-sla, gov-slo, gov-budget, gov-cost, gov-approval, gov-signoff, gov-delegation, gov-ownership, gov-tenant, gov-boundary, gov-trust, gov-risk, gov-incident, gov-remediation, gov-report                                                                                                                                |
| **Execution**   | exec-run-meta, exec-artifact, exec-log, exec-trace, exec-metrics, exec-telemetry, exec-cost, exec-duration, exec-result, exec-error, exec-retry, exec-fallback, exec-checkpoint, exec-resume, exec-cancel, exec-timeout, exec-deadline, exec-priority, exec-lane, exec-owner                                                                                                                   |
| **Integration** | int-mcp-tool, int-mcp-server, int-adapter, int-bridge, int-webhook, int-api, int-schema, int-mapping, int-transform, int-sync, int-queue, int-event, int-callback, int-config, int-secret, int-credential, int-token, int-session, int-handshake, int-health                                                                                                                                   |
| **UX / DX**     | ux-flow, ux-error, ux-feedback, ux-progress, ux-prompt, ux-confirm, ux-choice, ux-retry, ux-fallback, dx-cli, dx-env, dx-config, dx-script, dx-template, dx-snippet, dx-example, dx-guide, dx-tutorial, dx-reference, dx-migration                                                                                                                                                             |
| **Quality**     | qual-test-plan, qual-test-case, qual-test-result, qual-coverage, qual-lint, qual-security-scan, qual-perf, qual-benchmark, qual-regression, qual-smoke, qual-e2e, qual-integration, qual-unit, qual-mock, qual-fixture, qual-assertion, qual-expectation, qual-baseline, qual-threshold, qual-report                                                                                           |
| **…**           | _Expand to 200 types across all domains_                                                                                                                                                                                                                                                                                                                                                       |

### 4.2 Feature Types (Overlap with Document Types)

Types can also represent **features** (e.g. `feature-backlog-guard`, `feature-session-writeup`). Feature flags gate R/W for documents of that type.

---

## 5. Attribute Taxonomy (200 per Type — Framework)

For each type, up to **200 params/attributes**. Examples:

| Attribute Category | Attributes (examples)                                                                                         |
| ------------------ | ------------------------------------------------------------------------------------------------------------- |
| **Identity**       | id, slug, title, version, created_at, updated_at, author, owner, tenant, project, repo, path, hash, signature |
| **State**          | status, phase, stage, progress, blocked, claimed, completed, archived, deprecated, draft, published, locked   |
| **Access**         | read_policy, write_policy, visibility, scope, allowed_agents, denied_agents, ttl, expiry                      |
| **Relations**      | parent_id, child_ids, depends_on, blocks, relates_to, supersedes, replaces, merges_into                       |
| **Content**        | body, summary, tags, labels, priority, effort, risk, impact, confidence                                       |
| **Audit**          | last_read_at, last_write_at, read_count, write_count, audit_trail, checksum                                   |
| **Session**        | turn_id, session_id, correlation_id, agent_id, model_id, prompt_hash, output_hash                             |
| **…**              | _Expand to 200 per type_                                                                                      |

---

## 6. Session Write-Up (Per Turn)

**Every chat turn ends with a write-up** for session management:

- Type: `session-turn-writeup`
- Attributes: turn_id, session_id, agent, model, prompt_preview, output_preview, decision, action, outcome, next_step, handoff, escalation, checkpoint, timestamp
- R/W: Write at turn end; read for session resume, handoff, audit

---

## 7. BACKLOG Strict Protection

| Rule     | Enforcement                                                                     |
| -------- | ------------------------------------------------------------------------------- |
| Read     | MCP tool `thegent_backlog_read`; type `backlog-*`; attribute-level visibility   |
| Write    | MCP tool `thegent_backlog_write`; claim/complete semantics only; no direct edit |
| Claim    | `thegent_backlog_claim`; appends to CLAIMED; validates Depends                  |
| Complete | `thegent_backlog_complete`; moves to COMPLETED; requires run_id, artifact_ref   |
| Audit    | Every R/W logged to `thegent-audit-docs`                                        |

---

## 8. 100 Polishes / QOL / Optimizations

Target: 100 refinements. Sample categories:

| #      | Category          | Examples                                                                                                                   |
| ------ | ----------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 1–10   | **Read UX**       | Pagination, search, filter by type/attr, sort, export, preview, diff, version compare, full-text index, fuzzy match        |
| 11–20  | **Write UX**      | Templates, validation, auto-complete, schema hints, conflict detection, merge preview, undo, draft save, auto-save, backup |
| 21–30  | **Performance**   | Caching, lazy load, incremental sync, batch R/W, compression, dedup, indexing, prefetch, streaming, parallel               |
| 31–40  | **Security**      | Rate limit, quota, token scope, expiry, revocation, audit retention, redaction, PII mask, encryption at rest               |
| 41–50  | **Session**       | Turn coalescing, summary generation, handoff templates, escalation routing, checkpoint compression, replay, diff           |
| 51–60  | **Integration**   | Webhook on write, event bus, MCP broadcast, CLI sync, git hook, CI trigger, notification                                   |
| 61–70  | **Governance**    | Policy engine, override flow, approval chain, delegation, tenant isolation, cost tracking                                  |
| 71–80  | **DX**            | CLI shortcuts, aliases, bulk ops, scripts, templates, snippets, snippets library                                           |
| 81–90  | **Observability** | Metrics, traces, dashboards, alerts, health checks, SLO                                                                    |
| 91–100 | **Resilience**    | Retry, backoff, fallback, circuit breaker, graceful degradation, offline mode                                              |

---

## 9. Implementation Phases

| Phase  | Scope                                                         |
| ------ | ------------------------------------------------------------- |
| **P1** | MCP tools for BACKLOG read/write/claim/complete; strict guard |
| **P2** | 20 core document types; 20 attributes per type                |
| **P3** | Session turn write-up; per-turn write-up flow                 |
| **P4** | Expand to 200 types; 200 attributes per type                  |
| **P5** | 100 polishes; QOL and optimizations                           |

---

## 10. Related

- [UNIFIED_WORK_STREAM_DESIGN.md](../reference/UNIFIED_WORK_STREAM_DESIGN.md)
- [MCP_SLO_DOCUMENTATION.md](../reference/MCP_SLO_DOCUMENTATION.md)
- [WORK_STREAM.md](../reference/WORK_STREAM.md)
