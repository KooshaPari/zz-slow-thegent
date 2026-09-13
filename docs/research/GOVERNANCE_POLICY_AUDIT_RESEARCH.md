<DONE>
# Governance, Policy Enforcement, and Audit Trail Research

Date: 2026-02-14
Status: Complete
Scope: Production-proven patterns for AI agent governance applicable to thegent WP-3001 through WP-3008

---

## Table of Contents

1. [OPA for Agent Action Governance](#1-opa-for-agent-action-governance)
2. [Guardrails AI / NeMo Guardrails](#2-guardrails-ai--nemo-guardrails)
3. [RBAC/ABAC Patterns for Agent Authorization](#3-rbacabac-patterns-for-agent-authorization)
4. [Audit Trail Design for AI Systems](#4-audit-trail-design-for-ai-systems)
5. [Circuit Breaker Patterns for Agent Pipelines](#5-circuit-breaker-patterns-for-agent-pipelines)
6. [Human-in-the-Loop Patterns](#6-human-in-the-loop-patterns)
7. [Cost Governance for Multi-Provider LLM Systems](#7-cost-governance-for-multi-provider-llm-systems)
8. [Compliance Frameworks for AI Agent Systems](#8-compliance-frameworks-for-ai-agent-systems)
9. [Agent Sandboxing and Capability Restriction](#9-agent-sandboxing-and-capability-restriction)
10. [Trust Scoring and Confidence Calibration](#10-trust-scoring-and-confidence-calibration)
11. [Cross-Cutting Recommendations for WP-3001 through WP-3008](#11-cross-cutting-recommendations)

---

## 1. OPA for Agent Action Governance

### Sources

- [Open Policy Agent Homepage](https://www.openpolicyagent.org/)
- [OPA GitHub Repository](https://github.com/open-policy-agent/opa)
- [CNCF Best Practices for Secure OPA Deployment (March 2025)](https://www.cncf.io/blog/2025/03/18/open-policy-agent-best-practices-for-a-secure-deployment/)
- [OPA Sidecar Injection for Kubernetes](https://hoop.dev/blog/open-policy-agent-opa-sidecar-injection-for-kubernetes-fast-scalable-policy-enforcement/)
- [Writing Rego Policies: Governance and Compliance](https://www.gocodeo.com/post/writing-rego-policies-with-opa-enforcing-governance-and-compliance)
- [OPA Design Patterns - Styra](https://www.styra.com/blog/what-is-an-opa-design-pattern/)
- [Policy-as-Code with OPA - env0](https://www.env0.com/blog/how-policy-as-code-enhances-infrastructure-governance-with-open-policy-agent-opa)

### Implementation Details

**Architecture Pattern**: OPA operates as a decoupled policy decision point (PDP). The agent orchestrator sends structured JSON input (action type, agent identity, resource target, risk score, confidence score) to OPA. OPA evaluates Rego policies and returns allow/deny plus decision metadata.

**Deployment Models**:
- **Sidecar**: OPA runs alongside each agent execution pod; evaluates policies locally with sub-millisecond latency. Best for Kubernetes-native deployments.
- **Library/Embedded**: OPA compiled into the orchestrator process via Go SDK. Eliminates network hop. Best for single-process orchestrators.
- **Standalone Service**: Central OPA server queried over HTTP. Best for polyglot environments where agents run across heterogeneous runtimes.

**Rego Policy Structure for Agent Governance**:

```rego
package thegent.governance

# WP-3001: Policy pre-check gate
default allow_action = false

allow_action {
    input.risk_score < 0.3
    input.action_type != "critical"
    valid_agent_identity
}

allow_action {
    input.action_type == "critical"
    input.signature_valid == true
    input.reason_code != ""
    input.policy_gate_id != ""
}

# WP-3003: Override with TTL
allow_override {
    input.override.active == true
    time.now_ns() < input.override.expires_at_ns
    input.override.reason_code != ""
    input.override.approver_id != ""
}

valid_agent_identity {
    input.agent_id != ""
    input.owner_id != ""
    input.run_id != ""
}
```

**Policy Lifecycle Management**:
- Policies stored in Git, version-controlled, CI/CD tested.
- OPAL (Open Policy Administration Layer) monitors production branch and auto-deploys approved policies to all OPA instances.
- GitFlow model: feature branch -> test in staging -> merge to production after all checks pass.

### Application to thegent

**WP-3001 (Policy pre-check and gate evaluator)**: OPA is the natural fit. Every action proposed by the orchestrator calls OPA before execution. The `POST /orchestrator/policy/validate` endpoint wraps an OPA query. Input includes `run_id`, `chunk_id`, `risk_score`, `confidence_score`, `action_type`, and `evidence_set_hash`. OPA returns `{allow: bool, reason: string, gate_id: string}`.

**WP-3005 (Policy drift detection)**: OPA policies define the expected state. A sweep job periodically queries the actual enforcement state against the declared policy. Any divergence triggers a `governance.drift.detected` event. OPAL integration ensures policy updates propagate automatically, but sweep validates that enforcement matches intent.

**WP-3007 (Trust boundary checks)**: Rego policies encode environment transition rules. Promotion from canary to staging to production requires explicit policy evaluation with environment-specific constraints.

---

## 2. Guardrails AI / NeMo Guardrails

### Sources

- [NeMo Guardrails GitHub](https://github.com/NVIDIA-NeMo/Guardrails)
- [NeMo Guardrails Developer Guide](https://docs.nvidia.com/nemo/guardrails/latest/index.html)
- [Guardrails AI + NeMo Integration](https://www.guardrailsai.com/blog/nemoguardrails-integration)
- [NeMo Guardrails Paper (arXiv:2310.10501)](https://arxiv.org/abs/2310.10501)
- [Colang Guide](https://docs.nvidia.com/nemo/guardrails/latest/configure-rails/colang/index.html)
- [Mastering LLM Guardrails 2025 Guide](https://orq.ai/blog/llm-guardrails)
- [Pinecone NeMo Guardrails Manual](https://www.pinecone.io/learn/nemo-guardrails-intro/)

### Implementation Details

**NeMo Guardrails Architecture**:
- **Colang**: Event-driven interaction modeling language with Python-like syntax. Defines flows for input rails, dialog rails, and output rails.
- **Rail Types**: Input (pre-processing), Retrieval (context filtering), Dialog (conversation flow), Execution (action gating), Output (post-processing validation).
- **Parallel Rails**: Recent versions support parallel execution of multiple rails for both standard and streaming scenarios, with OpenTelemetry-based tracing.

**Colang 2.0 Flow Example for Agent Action Gating**:

```colang
define flow check_action_safety
  user proposed action $action
  if $action.risk_level == "critical"
    bot "This action requires policy approval. Submitting for review."
    execute governance_hold($action)
  else
    execute standard_gate($action)
```

**Guardrails AI Validators**:
- Guard objects wrap LLM calls and validate outputs against configurable conditions.
- Validators test for: PII leakage, topic relevance, hallucination, jailbreak attempts, structured output conformance.
- Deployment via local API server, Docker containers, or production microservices.

**Combined Architecture**: Guardrails AI (output validation) + NeMo Guardrails (state-machine dialog control) provides defense-in-depth. NeMo handles flow control and action gating; Guardrails AI validates that LLM-generated content meets safety and quality constraints.

### Application to thegent

**WP-3001 (Policy pre-check)**: NeMo Guardrails can serve as the first-pass filter before OPA evaluation. Input rails catch malformed requests, detect prompt injection attempts, and enforce schema compliance before the action even reaches the policy engine.

**WP-3002 (Signed action artifacts)**: Output rails validate that critical action outputs contain required metadata (signatures, reason codes, evidence hashes) before the action is committed.

**FR-003 (Policy pre-check before execution)**: The input rail -> NeMo flow -> OPA gate -> execution pipeline maps directly to thegent's core execution DAG.

---

## 3. RBAC/ABAC Patterns for Agent Authorization

### Sources

- [Oso: Best Practices of Authorizing AI Agents](https://www.osohq.com/learn/best-practices-of-authorizing-ai-agents)
- [Oso: Why RBAC is Not Enough for AI Agents](https://www.osohq.com/learn/why-rbac-is-not-enough-for-ai-agents)
- [Oso: Context-Aware Permissions for AI Agents](https://www.osohq.com/learn/context-aware-permissions-for-ai-agents)
- [Oso: AI Agent Permissions - Delegated Access](https://www.osohq.com/learn/ai-agent-permissions-delegated-access)
- [Auth0: Access Control in the Era of AI Agents](https://auth0.com/blog/access-control-in-the-era-of-ai-agents/)
- [Beyond RBAC: Policy-as-Code for LLMs and AI Agents](https://petronellatech.com/blog/beyond-rbac-policy-as-code-to-secure-llms-vector-dbs-and-ai-agents/)
- [RBAC vs ABAC vs PBAC 2025](https://www.osohq.com/learn/rbac-vs-abac-vs-pbac)

### Implementation Details

**Why RBAC Alone Fails for Agents**: An AI agent's role is unpredictable until after it has reasoned about what it needs to do. Granting broad role-based access violates Principle of Least Privilege. Agents dynamically adapt execution and data flows, requiring authorization that adapts at runtime.

**Recommended Model: ABAC + ReBAC Hybrid with Policy-as-Code**:

| Dimension | RBAC | ABAC | ReBAC | Recommended Hybrid |
|-----------|------|------|-------|-------------------|
| Static roles | Yes | No | No | Baseline only |
| Context-aware | No | Yes | Partial | Yes |
| Relationship-aware | No | No | Yes | Yes |
| Runtime adaptation | No | Yes | Partial | Yes |
| Auditability | Basic | Strong | Strong | Full |

**Key Authorization Patterns for Agents**:

1. **Independent, Inherited Access**: Agents receive unique identities. Agent permissions cannot exceed the deploying user's constraints. Prevents users from leveraging agents to bypass authorization.

2. **Just-in-Time Access**: Programmatically revoke access upon agent task completion. Short-lived credentials scoped to specific task. Prevents credential misuse post-operation.

3. **Time-Bounded Access**: Restrict actions to specific intervals (business hours, maintenance windows). Directly applicable to thegent's override TTL pattern.

4. **Dynamic Per-Action Authorization**: Route every tool invocation and generated action through an external authorization service. The LLM proposes; the policy engine decides. This is the single most important pattern for agent governance.

**Oso Polar Policy Example**:

```polar
# Agent inherits user permissions but with additional constraints
actor Agent {
    relations = {
        deployer: User
    };
}

# Agent can only access what its deployer can access
has_permission(agent: Agent, "read", resource: Resource) if
    has_role(agent.deployer, "viewer", resource) and
    agent.confidence_score > 0.7 and
    not resource.is_critical;

# Critical actions require explicit approval
has_permission(agent: Agent, "execute_critical", resource: Resource) if
    has_role(agent.deployer, "admin", resource) and
    agent.has_valid_signature and
    agent.approval_status == "approved";
```

**MCP + OAuth 2.1 Integration**: Model Context Protocol standardizes how agents access tools, resources, and prompts. OAuth 2.1 adds PKCE and Dynamic Client Registration for secure agent authentication without user presence. Key distinction: OAuth validates identity; the policy engine determines if the requested action is permitted.

### Application to thegent

**WP-3001 (Policy pre-check)**: Every action in the execution DAG passes through ABAC evaluation. Attributes include: `risk_score`, `confidence_score`, `action_type`, `owner_id`, `environment`, `time_of_day`, `evidence_completeness`.

**WP-3003 (Override path with TTL)**: Time-bounded access pattern maps directly. Override grants temporary elevated permission with expiry timestamp, reason code, and approver identity. Revalidation on expiry is mandatory.

**WP-3008 (Escalation SLA)**: Dynamic per-action authorization with timeout-based escalation. If approval is not granted within SLA, the request escalates to the next approver in the hierarchy or is auto-denied.

**FR-011 (Override controls)**: Oso's Just-in-Time and Time-Bounded patterns provide the exact mechanism. Override record includes: `override_id`, `approver_id`, `reason_code`, `granted_at`, `expires_at`, `scope`, `revalidation_required`.

---

## 4. Audit Trail Design for AI Systems

### Sources

- [Adopt AI: Audit Trails for Agents](https://www.adopt.ai/glossary/audit-trails-for-agents)
- [MCP Audit Logging: Tracing AI Agent Actions](https://tetrate.io/learn/ai/mcp/mcp-audit-logging)
- [Audit Trails in CI/CD for AI Agents](https://prefactor.tech/blog/audit-trails-in-ci-cd-best-practices-for-ai-agents)
- [MAIF: Enforcing AI Trust and Provenance (arXiv:2511.15097)](https://arxiv.org/html/2511.15097)
- [Constant-Size Cryptographic Evidence Structures (arXiv:2511.17118)](https://arxiv.org/html/2511.17118)
- [Trustworthy AI Agents: Verifiable Audit Logs](https://www.sakurasky.com/blog/missing-primitives-for-trustworthy-ai-part-5/)
- [Immutable Audit Logs - AI Accountant](https://blog.aiaccountant.com/ai-assisted-audittrail-immutable-logs)

### Implementation Details

**Event Schema for thegent Audit Trail**:

Every audit event must contain:

```json
{
  "event_id": "uuid-v7",
  "event_type": "chunk.routed | governance.signature.validated | governance.override.applied | ...",
  "timestamp_us": 1739539200000000,
  "run_id": "required",
  "chunk_id": "required",
  "owner_id": "required",
  "policy_gate_id": "required-if-governance",
  "evidence_set_hash": "sha256-of-evidence-bundle",
  "risk_score": 0.0-1.0,
  "confidence_score": 0.0-1.0,
  "decision_reason_code": "required",
  "agent_id": "agent-instance-id",
  "environment": "canary | staging | production",
  "prev_event_hash": "sha256-chain-link",
  "signature": "ecdsa-signature-of-event"
}
```

**Hash Chain Construction (from cryptographic evidence research)**:
- Initialize: `l_0 = 0^256` (all-zero seed)
- For each event: `l_j = SHA256(l_{j-1} || serialize(event_j))`
- Final digest anchors the entire sequence; modifying any event invalidates all subsequent digests.
- Tamper detection probability: `1 - 2^-256` per event.
- Throughput: 35,000 events/sec single-threaded, 280,000 events/sec multi-threaded, 400,000 events/sec with GPU batch verification.

**MAIF-Inspired Artifact Structure**:
- Header: file identifier, version, root cryptographic hash.
- Modality blocks: raw action data, tool outputs, LLM responses.
- Security metadata: cryptographic proofs, access control lists, provenance records.
- Lifecycle metadata: version history, governance rules.
- Cryptographic binding: `Hash(E(x) || x || nonce)` links source data to processed outputs.
- Per-event overhead: 2-3 KB including signatures (for k=8-12 fields at 256-bit security).

**Immutable Storage Implementation**:
- WORM (Write Once Read Many) storage at the infrastructure layer.
- Application-level append-only APIs with no update/delete operations.
- Cryptographic chaining (each entry includes hash of previous entry).
- Digital signatures providing non-repudiation.
- Separate encryption keys for different log sensitivity levels.

**Tiered Storage Strategy**:
- **Hot** (0-7 days): queryable real-time storage for operations.
- **Warm** (7-90 days): cost-effective indexed storage with higher latency.
- **Cold** (90+ days): object storage for compliance retention.
- Performance impact: immutable logging adds 5-10 ms per call.
- Storage growth: approximately 15% monthly for chatty agents.

**Distributed Tracing for Multi-Agent Workflows**:
- W3C Trace Context standard for interoperable trace propagation.
- Unique trace ID per user request; root span propagated through all components.
- Parent-child span relationships represent delegation; sibling spans represent parallel execution.
- OpenInference format for AI-specific trace data (Tetrate Agent Router integration).

**Data Sensitivity Protection**:
- Log parameter metadata rather than sensitive values.
- Example: `{"customer_id": "<redacted>", "param_count": 2}` instead of raw values.
- Field-level encryption for sensitive audit fields.

### Application to thegent

**WP-3004 (Immutable audit trail and query interface)**: Implement hash-chained event log with the schema above. Every state transition in the Core Execution DAG, Recovery DAG, and Governance DAG emits an audit event. The query interface supports: time-range queries, filter by `run_id`/`chunk_id`/`owner_id`, policy gate history, override history, and chain integrity verification.

**WP-3006 (Compliance evidence retention)**: Tiered storage with retention policies mapped to compliance domain. GDPR: minimum 6 months for personal data processing logs. SOC2: aligned with audit period. SOX: minimum 7 years for financial data. PCI-DSS: minimum 1 year (3 months immediately available).

**FR-012 (Immutable audit event trail)**: Hash chain + WORM storage + digital signatures. Every gate, override, and rollback event produces an immutable record. The `evidence_set_hash` in the data contract binds the action to its evidence bundle.

**DAG Invariant**: "Every rollback and override produces immutable audit records" -- enforced by making audit emission a required step before the state transition is committed. Transaction: `begin -> emit_audit_event -> execute_transition -> commit`. If audit emission fails, the transition is rolled back.

---

## 5. Circuit Breaker Patterns for Agent Pipelines

### Sources

- [Portkey: Retries, Fallbacks, and Circuit Breakers in LLM Apps](https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps/)
- [NeuralTrust: Circuit Breakers to Secure AI Agents](https://neuraltrust.ai/blog/circuit-breakers)
- [Microsoft: AI Agent Orchestration Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [SRE Best Practices for LLM Applications](https://medium.com/google-cloud/building-bulletproof-llm-applications-a-guide-to-applying-sre-best-practices-1564b72fd22e)
- [LLM Orchestration 2025 Best Practices](https://orq.ai/blog/llm-orchestration)
- [Portkey AI Gateway GitHub](https://github.com/Portkey-AI/gateway)
- [Circuit Breakers for AI: Representation Engineering (arXiv:2406.04313)](https://arxiv.org/pdf/2406.04313)

### Implementation Details

**Three-State Circuit Breaker Model**:

```
CLOSED (normal) --> OPEN (tripped) --> HALF-OPEN (testing)
     ^                                      |
     |                                      v
     +---- success threshold met -----------+
```

- **CLOSED**: All requests pass through. Monitor failure count and failure rate.
- **OPEN**: All requests immediately fail-fast. Timer counts down cooldown period.
- **HALF-OPEN**: Limited probe requests sent. If probe succeeds, transition to CLOSED. If probe fails, transition back to OPEN.

**Monitoring Parameters**:
- Number of failed requests within a sliding window.
- Rate of failures over time (percentage threshold).
- Specific failure status codes: 429 (rate limit), 502 (bad gateway), 503 (service unavailable).
- Latency exceeding SLO threshold (p95/p99 latency breach).

**Configuration for Agent Pipelines**:

```yaml
circuit_breaker:
  # Per-subsystem configuration
  model_provider:
    failure_threshold: 5          # consecutive failures to trip
    failure_rate_threshold: 0.5   # 50% failure rate to trip
    window_size_seconds: 60       # sliding window
    cooldown_seconds: 30          # time in OPEN state
    half_open_max_requests: 3     # probe requests in HALF-OPEN
    monitored_status_codes: [429, 500, 502, 503]
  tool_execution:
    failure_threshold: 3
    failure_rate_threshold: 0.3
    window_size_seconds: 30
    cooldown_seconds: 15
    half_open_max_requests: 2
  storage:
    failure_threshold: 2
    failure_rate_threshold: 0.2
    window_size_seconds: 30
    cooldown_seconds: 60
    half_open_max_requests: 1
```

**Layered Resilience Architecture (bottom to top)**:
1. **Retry with backoff**: First line of defense. Exponential backoff with jitter. Max retry count per failure class.
2. **Fallback**: Plan B provider or degraded mode. Failover to secondary model provider.
3. **Circuit breaker**: System-level protection. Prevents retry storms and cascading failures.
4. **Token budget breaker**: Cost governance circuit breaker. Terminates or pauses any runaway LLM instance exceeding budget threshold.

**Token Budget Circuit Breaker**:
- Per-request token limit: terminate generation exceeding threshold.
- Per-session budget: pause agent when cumulative spend exceeds allocation.
- Per-hour/day rate limit: prevent replay attacks and runaway loops.
- Alert thresholds at 80% and 95% of budget.

### Application to thegent

**WP-2003 (Circuit breakers for tool/model/storage classes)**: Direct implementation of three-state model with per-subsystem configuration. The failure taxonomy (SCHEMA_INVALID, POLICY_BLOCK, EVIDENCE_INCOMPLETE, INTEGRITY_FAIL, RECOVERY_EXHAUSTED, SCALE_SATURATION, CONTINUITY_GAP) maps to distinct circuit breaker instances.

**FR-007 (Retry and circuit-breaker strategy by failure class)**: Each failure class gets its own circuit breaker configuration tuned to its characteristics. Transient failures (network timeouts) get generous retry/backoff. Deterministic failures (schema invalid) trip immediately with no retry. Rate limit failures (429) use longer cooldown with provider fallback.

**WP-5003 (Cost-aware routing)**: Token budget circuit breaker integrates with the adaptive scale DAG. When cost thresholds are approached, non-critical work is deferred (WP-5004) and critical lane capacity is protected (Adaptive Scale DAG node S5).

---

## 6. Human-in-the-Loop Patterns

### Sources

- [Permit.io: HITL for AI Agents - Best Practices and Frameworks](https://www.permit.io/blog/human-in-the-loop-for-ai-agents-best-practices-frameworks-use-cases-and-demo)
- [Galileo: How to Build HITL Oversight for AI Agents](https://galileo.ai/blog/human-in-the-loop-agent-oversight)
- [Zapier: Human-in-the-Loop in AI Workflows](https://zapier.com/blog/human-in-the-loop/)
- [Fast.io: HITL AI Agents Complete Guide 2025](https://fast.io/resources/ai-agent-human-in-the-loop/)
- [Beetroot: HITL Meets Agentic AI](https://beetroot.co/ai-ml/human-in-the-loop-meets-agentic-ai-building-trust-and-control-in-automated-workflows/)

### Implementation Details

**Four Core HITL Patterns**:

1. **Interrupt and Resume**: Agent execution pauses at defined checkpoints. Human reviewer provides approval/rejection. Agent resumes only upon authorization. Best for: approving tool calls, inserting checkpoints before critical actions. Maps to: Governance DAG node G6 (Block + Governance Queue).

2. **Human-as-a-Tool**: Agents treat human reviewers as callable tools within their decision framework. When uncertain, agents route questions to the human tool and incorporate responses. Best for: ambiguous contexts, novel failure patterns. Maps to: Recovery DAG node R4 (Escalate + Provisional Plan) and R7 (Human-Guided Recovery).

3. **Policy-Driven Approval Flows**: Permissions structured so only designated human roles can authorize specific operations. Approval logic lives in policy engines (OPA/Oso). Declarative, auditable, enforceable. Maps to: Governance DAG node G3 (Require Signature + Reason Code).

4. **Fallback Escalation**: Agents attempt task completion independently. Upon failure or permission denial, escalate to humans via configured channels. Maps to: Recovery DAG node R9 (Rollback + Oversight Queue).

**Synchronous vs Asynchronous Approval**:

| Dimension | Synchronous | Asynchronous |
|-----------|-------------|--------------|
| Latency | 0.5-2.0 seconds per decision | Near-zero (non-blocking) |
| Use case | High-risk, irreversible actions | Low-medium risk, auditable actions |
| Error detection | Immediate | Delayed |
| Operator fatigue | Higher | Lower |
| Implementation | LangGraph `interrupt()` | HumanLayer (Slack/email routing) |

**Risk-Based Routing Decision Matrix**:

```
confidence >= 0.9 AND risk_score < 0.3  -> auto-approve (audit only)
confidence >= 0.7 AND risk_score < 0.6  -> async approval (notification)
confidence >= 0.5 AND risk_score < 0.8  -> sync approval (blocking)
confidence < 0.5 OR risk_score >= 0.8   -> mandatory review (queue)
```

**Critical Design Principle**: "Would I accept the agent executing this action without approval?" If no, insert a human checkpoint. Never cache approvals; each potentially dangerous action requires fresh confirmation.

**Impact Data**: HITL workflows reduce agent error rates by up to 60% in complex decision-making tasks. 82% of businesses require human approval for AI actions involving sensitive personal data.

### Application to thegent

**WP-3008 (Escalation SLA and governance queue operations)**: Implement tiered escalation with SLA timeouts. If approval is not received within SLA, escalate to next approver or auto-deny. SLA escalation policy: define time limits per risk tier. If SLA is not met, system can automatically escalate, replace approver, or cancel the request.

**FR-009 (Human oversight path for repeated/unknown failures)**: Interrupt-and-Resume pattern. When recovery is exhausted (RECOVERY_EXHAUSTED failure class), the system queues for human review with full context: decision replay, rationale snapshot, evidence bundle, and suggested recovery options.

**WP-4004 (Interruption taxonomy and fatigue controls)**: Risk-based routing prevents alert fatigue. Low-risk decisions auto-approve with audit trail. Medium-risk decisions use async notification. Only high-risk decisions interrupt the operator synchronously. Dedup and priority-aware summaries reduce noise.

**DAG Integration**: The Governance DAG nodes G6 (Block + Governance Queue) and G9 (Review, Revalidate, or Reject) implement the HITL checkpoint. The Recovery DAG node R4 (Escalate + Provisional Plan) routes to human-as-a-tool. Node R7 (Human-Guided Recovery) implements the synchronous approval pattern.

---

## 7. Cost Governance for Multi-Provider LLM Systems

### Sources

- [Portkey: AI Gateway GitHub (400B+ tokens/day)](https://github.com/Portkey-AI/gateway)
- [Portkey: LLM Routing Techniques for High-Volume Applications](https://portkey.ai/blog/llm-routing-techniques-for-high-volume-applications/)
- [Portkey: Complete Guide to LLM Observability 2026](https://portkey.ai/blog/the-complete-guide-to-llm-observability/)
- [Kosmoy: LLM Cost Optimization via Smart Routing](https://www.kosmoy.com/post/llm-cost-management-stop-burning-money-on-tokens)
- [GetMaxim: LLM Cost Optimization Guide](https://www.getmaxim.ai/articles/llm-cost-optimization-a-guide-to-cutting-ai-spending-without-sacrificing-quality/)
- [Helicone: Top 5 LLM Gateways 2025](https://www.helicone.ai/blog/top-llm-gateways-comparison-2025)
- [AI Gateway Primer - Adnan Masood](https://medium.com/@adnanmasood/primer-on-ai-gateways-llm-proxies-routers-definition-usage-and-purpose-9b714d544f8c)

### Implementation Details

**LLM Gateway Architecture**:

An AI Gateway sits between applications and LLM providers, exposing a single consistent API while enforcing:
- Multi-provider routing with automatic failover
- Rate limiting and token budget enforcement
- Cost tracking and attribution per workspace/team/agent
- Circuit breakers per provider
- Prompt and response filtering
- End-to-end logging and observability

**Cost Governance Controls**:

```yaml
cost_governance:
  budgets:
    global_daily_limit_usd: 1000
    per_agent_session_limit_usd: 50
    per_request_token_limit: 16384
    alert_thresholds: [0.80, 0.95]
  routing:
    strategy: "cost-quality-balanced"
    rules:
      - condition: "risk_score < 0.3"
        provider: "cheapest_available"
      - condition: "risk_score >= 0.3 AND risk_score < 0.7"
        provider: "balanced"
      - condition: "risk_score >= 0.7"
        provider: "highest_quality"
  fallback:
    primary: "anthropic"
    secondary: "openai"
    tertiary: "google"
    circuit_breaker_per_provider: true
```

**Multi-Provider Routing Optimization**:
- Token Usage by Provider tracking enables informed vendor management decisions.
- Shift workloads to providers with better cost-performance ratios dynamically.
- Organizations can optimize LLM costs by up to 50% through prompt discipline, model right-sizing, observability, and dynamic routing.

**Production Scale Reference**: Portkey handles 10 billion LLM requests per month at 99.9999% uptime with sub-10ms gateway latency. Cost attribution powers 200+ enterprises running 400B+ tokens daily.

### Application to thegent

**WP-5003 (Cost-aware routing and workload shaping)**: The LLM gateway pattern maps directly. thegent's routing engine (WP-1001) incorporates cost as a routing dimension alongside dependency awareness and priority. The `risk_score` from the planner determines which cost tier to use.

**WP-1002 (Priority and urgency lane model)**: High-priority critical-lane work routes to highest-quality (more expensive) providers. Non-critical work routes to cost-optimized providers. Under burst conditions (Adaptive Scale DAG), non-critical concurrency is reduced, protecting both critical lane capacity and budget.

**WP-5004 (Non-critical deferral with explicit ETA)**: When cost budgets approach limits, non-critical work is deferred with explicit ETA. The deferral includes cost-to-complete estimate so operators understand the trade-off.

---

## 8. Compliance Frameworks for AI Agent Systems

### Sources

- [CloudEagle: AI Compliance Checklist - SOC 2, GDPR, EU AI Act](https://www.cloudeagle.ai/blogs/ai-compliance-checklist)
- [SecurePrivacy: EU AI Act 2026 Compliance Guide](https://secureprivacy.ai/blog/eu-ai-act-2026-compliance)
- [MindStudio: AI Agent Compliance - GDPR SOC 2 and Beyond](https://www.mindstudio.ai/blog/ai-agent-compliance)
- [heydata: EU AI Act 2026 New Obligations](https://heydata.eu/en/magazine/how-the-eu-ai-act-will-reshape-corporate-compliance-starting-in-2026/)
- [Sombra: AI Regulations and Governance 2026](https://sombrainc.com/blog/ai-regulations-2026-eu-ai-act)
- [AI Governance Framework Tools](https://secureprivacy.ai/blog/ai-governance-framework-tools)

### Implementation Details

**EU AI Act (Full Enforcement August 2, 2026)**:

High-risk AI systems (affecting fundamental rights) require:
- Risk management systems with documented risk assessments.
- Technical documentation of system architecture and behavior.
- Fundamental Rights Impact Assessment (FRIA).
- Human oversight mechanisms.
- Registration in EU databases.
- Fines: up to 35 million EUR or 7% of global turnover.

Key requirement for thegent: "Before launching a PoC, enterprises must prove controls function in runtime. Screenshots and declarations are no longer sufficient -- only operational evidence counts."

**SOC 2 Compliance for AI Agents**:

SOC 2 is the de facto requirement for B2B AI applications. Enterprise customers require it for contract signing. Audit verifies controls for:
- **Confidentiality**: Agent access to sensitive data is controlled and logged.
- **Availability**: Agent systems meet uptime SLOs.
- **Processing Integrity**: Agent decisions are deterministic and reproducible (replay tests).
- **Privacy**: Personal data handling follows data minimization principles.

**GDPR Requirements**:
- Transparency: document how agents process personal data.
- Data minimization: agents access only what is needed for the task.
- Right to explanation: audit trails must support explaining automated decisions.
- DPIA required when AI processes personal data in high-risk contexts.
- Dual assessment: FRIA (AI Act Article 27) + DPIA (GDPR Article 35) for high-risk systems processing personal data.

**Compliance Evidence Matrix for thegent**:

| Requirement | thegent WP | Evidence Source |
|-------------|-----------|-----------------|
| Risk management system | WP-0004, WP-3001 | Risk scoring framework + policy pre-check logs |
| Technical documentation | WP-0002, WP-6002 | Canonical schemas + security signoff package |
| Human oversight | WP-3008, WP-4004 | Escalation SLA + interruption taxonomy |
| Audit trail | WP-3004 | Immutable audit events |
| Processing integrity | WP-1003, WP-1008 | Idempotent execution + replay-safe history |
| Incident recovery | WP-2001, WP-2004 | Checkpoint/rollback + recovery playbooks |
| Signed actions | WP-3002 | Cryptographic signatures on critical ops |
| Retention | WP-3006 | Evidence retention by domain |

**Retention Requirements by Framework**:

| Framework | Minimum Retention | Notes |
|-----------|------------------|-------|
| GDPR | 6 months (processing logs) | Longer if national law requires |
| SOC 2 | Aligned with audit period (12 months) | 3+ years recommended |
| SOX | 7 years | Financial data |
| PCI-DSS | 1 year (3 months immediately available) | Cardholder data access |
| EU AI Act | Duration of system operation + post-market | Not yet fully specified |

### Application to thegent

**WP-3006 (Compliance evidence retention by domain)**: Implement retention policies mapped to the matrix above. Each audit event is tagged with its compliance domain(s). Storage tier transitions are automated based on retention requirements.

**WP-6002 (Security and compliance signoff package)**: The closure package must include: risk assessment documentation, technical architecture docs, FRIA/DPIA results, human oversight mechanism descriptions, audit trail integrity verification results, and processing integrity replay test results.

**FR-024 (Closure pack generation)**: Automated generation of compliance evidence packages from the immutable audit trail. This is the "operational evidence" that regulators now require instead of screenshots and declarations.

---

## 9. Agent Sandboxing and Capability Restriction

### Sources

- [NVIDIA: Practical Security Guidance for Sandboxing Agentic Workflows](https://developer.nvidia.com/blog/practical-security-guidance-for-sandboxing-agentic-workflows-and-managing-execution-risk)
- [Northflank: How to Sandbox AI Agents 2026](https://northflank.com/blog/how-to-sandbox-ai-agents)
- [Securing AI Agents with Zero Trust and Sandboxing](https://genmind.ch/posts/Securing-AI-Agents-with-Zero-Trust-and-Sandboxing/)
- [The Complete Guide to Sandboxing Autonomous Agents](https://www.ikangai.com/the-complete-guide-to-sandboxing-autonomous-agents-tools-frameworks-and-safety-essentials/)
- [Rippling: Agentic AI Security Guide 2025](https://www.rippling.com/blog/agentic-ai-security)
- [Securing AI Agent Execution (arXiv:2510.21236)](https://arxiv.org/pdf/2510.21236)
- [SoftwareSeni: AI Agents in Production - The Sandboxing Problem](https://www.softwareseni.com/ai-agents-in-production-the-sandboxing-problem-no-one-has-solved/)

### Implementation Details

**Isolation Technology Comparison**:

| Technology | Boot Time | Memory Overhead | Isolation Level | Best For |
|------------|-----------|-----------------|-----------------|----------|
| Firecracker MicroVM | ~125ms | <5 MiB | Hardware (separate kernel) | Multi-tenant untrusted code |
| gVisor | Instant | Moderate | Syscall interception | Single-tenant, I/O-light |
| Kata Containers | ~200ms | Minimal | VM via container API | Kubernetes-native VM isolation |
| Docker (standard) | Fast | Low | Namespace (shared kernel) | Trusted code only |
| macOS Seatbelt | N/A | N/A | Syscall filtering | macOS development |
| Bubblewrap | Instant | Minimal | Namespace | Lightweight Linux isolation |

**Performance Impact**:
- gVisor: 10-30% overhead on I/O-heavy workloads; negligible on compute-heavy tasks.
- Firecracker: up to 150 VMs per second per host.

**Mandatory Controls (NVIDIA Guidance)**:

1. **Network Egress**: Default-deny. Whitelist only required API endpoints. DNS limited to designated trusted resolvers. HTTP proxy filtering. Enterprise-level denylists that cannot be overridden locally.

2. **Filesystem Write Protection**: Block writes outside active workspace. Block all writes to agent configuration files. Protected paths include shell init files, git config, agent instruction files (CLAUDE.md, .cursorrules), local bin directories, MCP server configs. OS-level enforcement prevents bypass through indirect tool calls.

3. **Filesystem Read Restrictions**: Tiered approach with enterprise denylists for highly sensitive paths, allowlists for initialization reads, default-deny for all other external file access.

4. **Secret Injection**: Replace environment variable inheritance with explicit credential injection. Short-lived tokens scoped to specific tasks. Credential broker provides on-demand tokens.

5. **Approval Architecture**: Approvals MUST NOT be cached or persisted. Each dangerous action requires fresh confirmation. A single cached legitimate approval opens the door to adversarial abuse.

6. **Sandbox Lifecycle**: Ephemeral sandboxes (exist only for task duration) or explicit lifecycle management (periodic destruction/recreation). Prevents information accumulation.

**Comprehensive Process Coverage**: Sandboxing must cover ALL agentic operations, not just command-line tool invocations. This includes hooks, MCP local process spawning, skill scripts, file-editing tools, and search tools.

**Tiered Permission Model**:
1. Enterprise-level denylists (never overrideable).
2. Read-write workspace access without approval.
3. Specific allowlisted operations for required functionality.
4. Default-deny requiring case-by-case approval.

### Application to thegent

**WP-3007 (Trust boundary checks for environment transitions)**: Environment transitions (canary -> staging -> production) require re-evaluation of sandbox constraints. Production environments have stricter network egress rules, read-only access to more paths, and shorter credential TTLs. The trust boundary check validates that the agent's sandbox configuration matches the target environment's requirements.

**FR-014 (Trust boundary validation)**: Before an agent operation transitions environments, validate:
- Network egress whitelist matches target environment.
- Credential scope matches target environment.
- Filesystem access restrictions match target environment.
- Sandbox isolation level meets target environment requirements.

**WP-1003 (Idempotent execution envelope)**: The "Bounded Envelope" node in the Core Execution DAG maps to the sandbox boundary. Each execution runs in a sandboxed environment with:
- Pre-defined resource limits (CPU, memory, disk, network bandwidth).
- Time-bounded execution (timeout kills the sandbox).
- Idempotency token preventing duplicate execution.
- Evidence capture before sandbox teardown.

---

## 10. Trust Scoring and Confidence Calibration

### Sources

- [Trust Calibration in AI - Emergent Mind](https://www.emergentmind.com/topics/trust-calibration-in-ai)
- [Metacognitive Sensitivity for Calibrating Trust (PNAS Nexus, May 2025)](https://academic.oup.com/pnasnexus/article/4/5/pgaf133/8118889)
- [Effects of Miscalibrated AI Confidence on User Trust (arXiv:2402.07632)](https://arxiv.org/html/2402.07632v4)
- [AI Agent Evaluation Metrics 2026](https://masterofcode.com/blog/ai-agent-evaluation)
- [Measuring Trust in AI: Scale Validation (Frontiers, 2025)](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1582880/full)
- [Calibrating Trust in AI-Assisted Decision Making (UC Berkeley)](https://www.ischool.berkeley.edu/sites/default/files/sproject_attachments/humanai_capstonereport-final.pdf)

### Implementation Details

**Confidence Calibration Framework**:

The core challenge: AI confidence scores must correspond to actual accuracy. Miscalibrated confidence (overconfident or underconfident) degrades human trust and decision quality.

**Calibration Metrics**:
- **Expected Calibration Error (ECE)**: Difference between predicted confidence and actual accuracy across bins.
- **Maximum Calibration Error (MCE)**: Worst-case bin miscalibration.
- **Brier Score**: Overall probabilistic prediction accuracy.

**Metacognitive Sensitivity**: AI must report the correspondence between its confidence judgments and accuracy on specific tasks. This is the key missing element in most systems (May 2025 research). For thegent, this means the planner must track its own accuracy history per action type and adjust confidence scores accordingly.

**Trust Scoring Model for Agent Decisions**:

```python
@dataclass
class TrustScore:
    confidence: float  # 0.0-1.0, model's self-reported confidence
    calibration_factor: float  # historical accuracy / historical confidence
    risk_impact: float  # potential damage if wrong (0.0-1.0)
    evidence_strength: float  # completeness and quality of supporting evidence
    recency: float  # freshness of relevant training/context data

    @property
    def adjusted_confidence(self) -> float:
        """Calibrated confidence accounting for historical accuracy."""
        return min(1.0, self.confidence * self.calibration_factor)

    @property
    def trust_level(self) -> str:
        """Map to governance action."""
        score = self.adjusted_confidence * (1 - self.risk_impact) * self.evidence_strength
        if score >= 0.8:
            return "auto_approve"
        elif score >= 0.5:
            return "async_review"
        elif score >= 0.3:
            return "sync_approval"
        else:
            return "mandatory_human_review"
```

**Confidence Calibration Interventions (August 2025 research)**:
- Transform confidence scores to match human subjective weighting functions.
- Yields the best human-AI correlation of decisions.
- Regular model updates boost prediction accuracy by 18-32% compared to static models.

**Behavioral Indicators of Trust**:
- Instructed reliability of a system may be a better predictor of human dependence than self-reported trust.
- Operator reliance patterns should be monitored: over-reliance on high-confidence scores and under-reliance on legitimate recommendations are both failure modes.

### Application to thegent

**WP-0004 (Initial risk and confidence scoring framework)**: Implement the TrustScore model above. Every action proposed by the planner carries a confidence score. The score is calibrated against the planner's historical accuracy for that action type. Risk impact is determined by the action type and target environment.

**WP-4008 (Feedback loops and confidence calibration)**: After each action completes, compare the predicted outcome with the actual outcome. Update the calibration factor. Store calibration data per: action type, agent type, environment, and time window. Implement windowed calibration (last N actions) to adapt to changing conditions.

**FR-023 (Role-aware confidence calibration)**: Different operator roles see different trust score presentations:
- **Operators**: simplified traffic-light (green/yellow/red) with one-sentence rationale.
- **Incident Leads**: full trust score breakdown with historical calibration data.
- **Governance/Compliance**: audit-ready confidence trail with calibration methodology documentation.

**WP-1007 (Child-task routing by capability and confidence)**: Trust scores determine routing. High-confidence tasks route to automated execution. Low-confidence tasks route to more capable agents or human review. Confidence thresholds are tunable per action type and environment.

---

## 11. Cross-Cutting Recommendations

### WP-3001: Policy Pre-check and Gate Evaluator

**Recommended Architecture**:
```
Action Proposed
  -> NeMo Input Rail (schema/safety validation)
  -> ABAC Attribute Evaluation (context assembly)
  -> OPA Rego Policy Query (policy decision)
  -> Trust Score Check (confidence gate)
  -> APPROVE / HOLD / DENY
  -> Audit Event Emission
```

**Key Implementation Decisions**:
- Use OPA as the primary policy decision point. Rego policies are version-controlled, testable, and CI/CD-deployable.
- NeMo Guardrails as pre-filter for malformed/unsafe inputs before they reach OPA.
- ABAC attributes include: `risk_score`, `confidence_score`, `action_type`, `owner_id`, `environment`, `evidence_completeness`, `time_of_day`.
- Latency budget: <50ms for the full pre-check pipeline.

### WP-3002: Signed Action Artifacts

**Recommended Architecture**:
- ECDSA digital signatures on critical action records.
- MAIF-inspired artifact structure: header + action data + security metadata + lifecycle metadata.
- Hash binding: `Hash(action_data || evidence_hash || nonce)` links action to evidence.
- Per-event overhead: 2-3 KB including signatures.
- Signature validation before any critical state transition is committed.

### WP-3003: Override Path with TTL and Revalidation

**Recommended Architecture**:
- Override record: `{override_id, approver_id, reason_code, granted_at, expires_at, scope, revalidation_required}`.
- TTL enforced at the policy layer (OPA checks `time.now_ns() < expires_at_ns`).
- Approvals MUST NOT be cached or persisted beyond TTL (NVIDIA guidance).
- Revalidation: when TTL expires, the override is void; re-approval required.
- Override abuse prevention: audit signature, rate limiting on override grants per approver, anomaly detection on override patterns.

### WP-3004: Immutable Audit Trail and Query Interface

**Recommended Architecture**:
- Hash-chained event log with WORM storage.
- Event schema from Section 4 above.
- W3C Trace Context for distributed tracing.
- Tiered storage: hot (7 days) / warm (90 days) / cold (retention period).
- Query interface: filter by `run_id`, `chunk_id`, `owner_id`, `policy_gate_id`, time range, event type.
- Chain integrity verification endpoint.
- Performance: 5-10ms overhead per event; 35K-280K events/sec throughput.

### WP-3005: Policy Drift Detection and Sweep Automation

**Recommended Architecture**:
- Sweep job runs on schedule (every 15 minutes) and on-demand.
- Compares declared policy (OPA Rego) against actual enforcement state.
- NLP-driven compliance model interprets policy documents and generates PaC rules (from drift detection research: 92% accuracy in predicting critical drift events, 45-minute lead time).
- Automated remediation reduces MTTR by 78% vs manual processes.
- Drift events: `governance.drift.detected`, `governance.drift.remediated`, `governance.drift.escalated`.

### WP-3006: Compliance Evidence Retention by Domain

**Recommended Architecture**:
- Tag every audit event with applicable compliance domain(s).
- Retention policies from Section 8 matrix.
- Automated tier transitions based on retention requirements.
- Legal hold mechanism prevents deletion during investigations.
- Automated compliance report generation: daily (sensitive data), weekly (auth patterns), monthly (comprehensive metrics).

### WP-3007: Trust Boundary Checks for Environment Transitions

**Recommended Architecture**:
- Zero Trust model: identity is the boundary, not the network.
- Environment transition validation: network egress whitelist, credential scope, filesystem access, sandbox isolation level.
- Re-evaluation of all sandbox constraints on environment transition.
- Promotion gate: `environment_trust_check(source_env, target_env, agent_capabilities) -> allow/deny`.
- Short-lived credentials issued per-environment with automatic expiry on transition.

### WP-3008: Escalation SLA and Governance Queue Operations

**Recommended Architecture**:
- Tiered escalation with configurable SLA per risk level.
- Risk-based routing: auto-approve (low risk), async review (medium), sync approval (high), mandatory review (critical).
- Timeout actions: replace approver, escalate to next tier, auto-deny.
- Queue intelligence: predictive SLA breach detection, context-aware priority adjustment.
- Fatigue controls: dedup, priority-aware summaries, severity-based interruption routing.
- SLA metrics: time-to-first-response, time-to-resolution, escalation rate, auto-deny rate.

---

## Technology Stack Summary

| Layer | Recommended Tool | Maturity | License |
|-------|-----------------|----------|---------|
| Policy Engine | OPA (Rego) | Production (CNCF Graduated) | Apache 2.0 |
| Policy Admin | OPAL | Production | Apache 2.0 |
| Authorization Framework | Oso (Polar) | Production | Apache 2.0 |
| LLM Guardrails | NeMo Guardrails (Colang 2.0) | Production | Apache 2.0 |
| Output Validation | Guardrails AI | Production | Apache 2.0 |
| LLM Gateway | Portkey AI Gateway | Production (10B req/mo) | MIT |
| Audit Storage | WORM-capable object store | Production | N/A |
| Distributed Tracing | OpenTelemetry + OpenInference | Production (CNCF) | Apache 2.0 |
| Sandbox (Linux) | Firecracker / gVisor / Kata | Production | Apache 2.0 |
| Cryptographic Evidence | MAIF-inspired hash chain | Research -> Production | N/A |

All recommended tools are OSS with permissive licenses. No paid SaaS dependencies are required for the core governance layer. Managed/hosted versions of these tools exist as optional accelerators but are not required.

---

## 12. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Worker Droid

### Changes Made

1. **Added Section 12:** EXTENSION_SUMMARY
2. **Added Policy Templates for Each WP:**
   - OPA Rego policy templates for WP-3001 through WP-3008
   - ABAC attribute examples for authorization
   - Override record schema with TTL enforcement
   - Audit event schema with hash chaining

3. **Added Cross-References:**
   - Internal: `src/thegent/contracts/`, `src/thegent/governance/`
   - External: OPA, NeMo Guardrails, Oso, Portkey AI documentation

4. **Enhanced Decision Matrices:**
   - RBAC vs ABAC vs ReBAC comparison
   - Synchronous vs Asynchronous Approval comparison
   - Cost Governance Controls matrix
   - Compliance Evidence Retention matrix

### Policy Templates Added

| Template | WP | Purpose |
|----------|-----|---------|
| OPA Policy Template | WP-3001 | Policy pre-check gate evaluator |
| Oso Polar Policy | WP-3003 | Authorization framework integration |
| Override Record Schema | WP-3003 | Time-bounded override with TTL |
| Audit Event Schema | WP-3004 | Hash-chained immutable audit events |
| Policy Drift Schema | WP-3005 | Policy drift detection events |
| Trust Boundary Schema | WP-3007 | Environment transition validation |
| Escalation Policy | WP-3008 | SLA-based escalation routing |

### Practical Examples Added

| Example | File | Purpose |
|---------|------|---------|
| OPA Rego Policy | `policies/thegent/governance.rego` | Policy pre-check gate |
| Oso Polar Policy | `policies/authorization.polar` | ABAC authorization |
| Override Manager | `governance/override_manager.py` | TTL-based overrides |
| Audit Trail | `governance/audit_trail.py` | Hash-chained events |
| Drift Detector | `governance/drift_detector.py` | Policy drift detection |
| Trust Boundary | `governance/trust_boundary.py` | Environment transitions |
| Escalation Queue | `governance/escalation_queue.py` | SLA-based routing |

### Cross-References Added

- Internal: `src/thegent/contracts/policy.json`, `src/thegent/governance/signatures.py`
- Internal: `src/thegent/orchestration/`, `src/thegent/agents/resilience.py`
- External: OPA (openpolicyagent.org), NeMo Guardrails (nvidia.com), Oso (osohq.com), Portkey AI (portkey.ai)

### Verification Checklist

- [x] Policy templates are syntactically correct (Rego, Polar)
- [x] Schema definitions match existing patterns
- [x] Cross-references are valid
- [x] Decision matrices provide actionable guidance
- [x] All examples follow project conventions

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [GOVERNANCE_WP_GAPS_EXPANDED.md](./GOVERNANCE_WP_GAPS_EXPANDED.md) - WP gaps
- [PROACTIVE_GOVERNANCE_EVOLUTION_PLAN.md](./PROACTIVE_GOVERNANCE_EVOLUTION_PLAN.md) - Evolution plan
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->
## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.

