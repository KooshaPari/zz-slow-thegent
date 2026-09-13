# Governance Rollout Roadmap (DAG)

## Scope

Implement policy-driven multi-agent governance that avoids rigid `1 agent = 1 worktree`.

## Phased WBS

### Phase A0: Delegation Architecture

1. A0.1 Publish classifier schema.
2. A0.2 Publish Ln delegation contract template.
3. A0.3 Publish domain playbooks.

### Phase A: Worktree and Commit Policy

1. A1.1 Publish scale-to-worktree matrix.
2. A1.2 Publish commit/micro-commit/pkg policy.
3. A1.3 Publish PR branch topology and merge rules.

### Phase B: Scheduler and Placement

1. B1.1 Build placement engine for `shared_lane`, `burst_isolated`, `integration`.
2. B1.2 Add overlap-risk scoring and escalation.
3. B1.3 Add lease/TTL for active assignments.

### Phase C: Concurrency and Conflict Handling

1. C1.1 Add file-claim registry.
2. C1.2 Add conflict fork retention policy.
3. C1.3 Add pkg-aware lock semantics.

### Phase D: Protocol Layering

1. D1.1 Define MCP tool/data boundaries.
2. D1.2 Define A2A task handoff boundaries.
3. D1.3 Define internal scheduler control API.

### Phase E: Observability and SLOs

1. E1.1 Add trace propagation policy.
2. E1.2 Instrument delegation and conflict metrics.
3. E1.3 Add SLO dashboards and alerts.

### Phase F: Enforcement

1. F1.1 Add policy checks in pre-commit/pre-push.
2. F1.2 Add CI policy checks for branch/worktree metadata.
3. F1.3 Add policy exception workflow and audit trail.

### Phase G: Rollout

1. G1.1 Pilot on 10 percent of lanes.
2. G1.2 Expand to 50 percent with measured tuning.
3. G1.3 Enforce 100 percent policy coverage.

## Dependency DAG

1. A0.1 -> A0.2 -> A0.3
2. A0.1 -> A1.1
3. A1.1 -> A1.2 -> A1.3
4. A1.1 -> B1.1
5. B1.1 -> B1.2 -> B1.3
6. B1.2 -> C1.1 -> C1.2 -> C1.3
7. A0.1 -> D1.1 -> D1.2 -> D1.3
8. C1.1 + D1.3 -> E1.1 -> E1.2 -> E1.3
9. A1.3 + C1.3 + E1.2 -> F1.1 -> F1.2 -> F1.3
10. F1.2 + E1.3 -> G1.1 -> G1.2 -> G1.3

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->

## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.
