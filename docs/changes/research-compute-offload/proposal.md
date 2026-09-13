# Proposal: Mac ↔ PC Compute Offload Research

**Document Version:** 1.0
**Change ID:** research-compute-offload
**Date:** 2026-02-18
**Status:** Proposal
**Priority:** P2

---

## Executive Summary

This research initiative investigates intelligent compute offloading between macOS (Mac) and Windows/Linux (PC) environments within the thegent orchestration framework. The goal is to enable agents to transparently route workloads to the most suitable execution environment based on platform-specific capabilities, cost, and resource availability.

**Key Outcomes:**

- Feasibility analysis of cross-platform execution bridging
- Design patterns for environment-aware task routing
- Prototype implementation of Mac ↔ PC offload mechanism
- Integration architecture with thegent's existing multi-agent framework

---

## Problem Statement

### Current State

- thegent executes agents on a single machine (the host running the CLI)
- No mechanism exists to leverage compute resources across heterogeneous environments
- Mac-specific workloads (e.g., Xcode builds, iOS development) cannot run on Windows/Linux hosts
- Windows-specific workloads (e.g., .NET builds, DirectX development) cannot run on macOS
- Each environment pays for compute independently; no cost optimization across platforms

### Gaps

1. **Workload Awareness**: thegent has no notion of platform-specific tool requirements
2. **Environment Bridging**: No standardized protocol for remote execution between platforms
3. **Resource Orchestration**: Can't leverage idle or cost-effective compute in peer environments
4. **Cost Optimization**: No ability to route to cheapest/fastest platform per task
5. **Dependency Resolution**: No mechanism to detect or validate platform compatibility

---

## Proposed Solution

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│             Unified thegent Control Plane                │
│  (agent dispatch, policy eval, cost aggregation)         │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ Host A  │  │ Host B  │  │ Host C  │
   │ (Mac)   │  │ (PC)    │  │ (Linux) │
   │         │  │         │  │         │
   │ Local   │  │ Local   │  │ Local   │
   │ Executor│  │ Executor│  │ Executor│
   └────┬────┘  └────┬────┘  └────┬────┘
        │            │            │
        └────────────┼────────────┘
             ▲       │       ▲
             │ Offload Bridge │
             └────────────────┘
```

### Key Components

1. **Compute Catalog** (`src/thegent/offload/compute_catalog.py`)
   - Registry of available compute environments (Mac, Windows, Linux)
   - Capabilities per environment (installed tools, SDKs, runtimes)
   - Resource profiles (CPU, memory, storage, network)
   - Cost profiles ($/minute per environment)

2. **Workload Classifier** (`src/thegent/offload/workload_classifier.py`)
   - Analyzes prompt and task to infer platform requirements
   - Detects language/framework/tool requirements from code snippets
   - Assigns compatibility matrix per target platform
   - Computes suitability scores (0.0-1.0) per environment

3. **Offload Router** (`src/thegent/offload/offload_router.py`)
   - Receives workload classification and available environments
   - Applies routing policies (cost-optimal, fastest, most capable)
   - Selects target environment and agent
   - Encodes execution context for remote agent

4. **Bridge Protocol** (`src/thegent/offload/bridge_protocol.py`)
   - Standardized message format for cross-platform execution
   - Encapsulates prompt, working directory, environment variables
   - Marshals/unmarshals execution context
   - Supports both synchronous (HTTP) and asynchronous (AMQP/gRPC) transport

5. **Remote Executor** (`src/thegent/offload/remote_executor.py`)
   - Listens on host for offload requests
   - Validates incoming requests against local policy
   - Prepares sandbox/container for execution
   - Executes task and returns normalized output

6. **Capability Resolver** (`src/thegent/offload/capability_resolver.py`)
   - Probes local environment for installed tools/SDKs
   - Generates capability fingerprint (git, docker, python, node, ruby, go, rust, etc.)
   - Caches fingerprint with TTL
   - Publishes to shared registry

---

## Research Questions

### Feasibility

1. **Network Reliability**: Can we maintain stable connections for long-running tasks (>10min)?
2. **Latency Impact**: What overhead does network roundtrip add vs. local execution? Acceptable threshold?
3. **Authentication & Trust**: How do we securely authenticate Mac ↔ PC without SSH keys per pair?
4. **Isolation**: Can we safely sandbox offloaded workloads without full VM/container overhead?

### Architecture

5. **Protocol Choice**: HTTP (simple, ubiquitous), gRPC (typed, streaming), AMQP (async), WebSocket (bidirectional)?
6. **Registry Model**: Centralized (shared server), Decentralized (gossip), Hybrid (local cache + sync)?
7. **Routing Algorithm**: Cost-based greedy, ML-based predictor, game-theoretic equilibrium?
8. **Failure Modes**: How do we handle network partition, task timeout, agent crash mid-execution?

### Economics

9. **Cost Benefit**: At what workload volume does offload cost < local cost?
10. **SLA Guarantees**: Can we maintain latency SLAs across heterogeneous networks?

---

## Scope & Constraints

### In Scope

- ✅ Feasibility analysis (theory + prototype)
- ✅ Workload classification heuristics
- ✅ Capability probing and registry
- ✅ Router logic and policy integration
- ✅ Synchronous HTTP bridge protocol
- ✅ Reference implementation for 2 platforms (Mac, Linux)

### Out of Scope

- ❌ Asynchronous protocols (AMQP, gRPC) — prototype only with HTTP
- ❌ Full multi-cloud federation (AWS, GCP, Azure) — research only
- ❌ ML-based routing optimization — heuristic-based only
- ❌ Automatic infrastructure provisioning — manual setup
- ❌ Container/VM orchestration — sandboxing via lightweight isolation (OS-level)

### Constraints

- **Timeline**: Fit within Phase 10-12 research window (2-3 weeks)
- **Code Debt**: Prototype code must be marked `@experimental`; no production guarantees
- **Network**: Assume LAN-only or VPN (no internet-scale)
- **Auth**: Use temporary tokens or pre-shared secrets; no PKI infrastructure
- **Latency**: Target <1s overhead for offload decision + handoff

---

## Success Criteria

### Research Validation

- [ ] **Complete Feasibility Matrix**: Document yes/no answers for all 10 research questions
- [ ] **Prototype Execution**: Offload a real agent task (e.g., git repo analysis) from Mac to Linux
- [ ] **Capability Detection**: Fingerprint ≥5 environments; match 90%+ accuracy against manual audit
- [ ] **Routing Logic**: Correctly select environment for ≥3 workload types (Python, Node, Rust)
- [ ] **Performance Baseline**: Measure latency overhead; document per task type

### Prototype Artifacts

- [ ] **Compute Catalog** populated with ≥3 environments and ≥10 capabilities per env
- [ ] **Workload Classifier** with ≥5 heuristics (language detection, tool inference, dependency scanning)
- [ ] **Offload Router** integrates with thegent policy engine; respects cost/trust gates
- [ ] **Bridge Protocol** message schema defined in Pydantic; examples for ≥3 workflows
- [ ] **Remote Executor** runs on 2+ platforms; passes smoke tests
- [ ] **Test Coverage**: ≥70% unit test coverage for core modules

### Documentation

- [ ] **Design Document**: Detailed architecture, protocol, integration points
- [ ] **Runbook**: Step-by-step setup for Mac + Linux + Windows environments
- [ ] **Decision Log**: Rationale for protocol, registry, routing choices
- [ ] **Next Phase Roadmap**: Clear path from prototype → production

---

## Proposed Phases

### Phase 1: Research & Design (Week 1)

- Stakeholder interviews (thegent team, users with multi-platform setups)
- Competitive analysis (Kubernetes federation, Terraform, Nomad, Temporal)
- Network architecture design
- Protocol spec in YAML/Pydantic
- **Deliverable**: design.md

### Phase 2: Prototype Implementation (Week 2-3)

- Implement compute catalog, workload classifier, router
- Implement HTTP bridge protocol + reference server
- Integrate with thegent policy engine
- Write unit tests for core modules
- **Deliverable**: src/thegent/offload/ + tests

### Phase 3: Validation & Runbook (Week 3)

- Deploy prototype to 2+ environments (Mac + Linux VM)
- Validate end-to-end offload workflow
- Write setup + operations runbook
- Document findings in design.md + decision log
- **Deliverable**: docs/changes/research-compute-offload/design.md, runbook.md

### Phase 4: Decision & Handoff (End of Week 3)

- Present findings to team
- Decide: Refine prototype, archive for future work, or pursue production path
- Handoff artifacts (code, docs, lessons learned)
- **Deliverable**: tasks.md (updated with outcomes)

---

## Dependencies & Integrations

### Internal

- thegent policy engine (for gate evaluation)
- thegent settings & configuration
- thegent run registry (for cost tracking)
- thegent contract telemetry (for audit trail)

### External

- No mandatory external dependencies beyond stdlib + existing thegent deps
- Optional: `docker` CLI for sandbox creation (if exploring container-based isolation)

---

## Risks & Mitigations

| Risk                                      | Probability | Impact                   | Mitigation                                                                        |
| ----------------------------------------- | ----------- | ------------------------ | --------------------------------------------------------------------------------- |
| Network unreliability in production       | High        | Task hangs / timeouts    | Prototype assumes LAN; add timeout + retry logic; doc as future work              |
| Authentication/trust complexity           | Medium      | Security vulnerabilities | Use pre-shared tokens for prototype; recommend mTLS for production                |
| Workload classification mismatches        | Medium      | Wrong platform selected  | Start with simple heuristics; add manual override; collect misclassification logs |
| Integration complexity with policy engine | Medium      | Schedule slip            | Start with simplified policy; iterate based on feedback                           |
| Prototype code becomes "legacy"           | Low         | Maintenance burden       | Mark all code `@experimental`; clear upgrade path in handoff                      |

---

## Success Stories & Related Work

### Kubernetes Federation

Inspired by Kubernetes multi-cluster support: declarative resource affinity, cluster-aware routing, federated control plane.

### Terraform

Uses provider-specific execution backends; each platform (AWS, GCP, local) has a provider. Our compute catalog is analogous.

### Temporal

Workflow engine with worker pools across regions/datacenters; workers register capabilities. Our capability resolver + registry is inspired by this.

---

## Open Questions for Stakeholders

1. **Priority**: Is Mac ↔ PC offload critical for Phase 10-12, or can it wait for Phase 13+?
2. **Network Assumption**: Do we assume LAN-only (VPN) or internet-scale?
3. **Auth Model**: Pre-shared secrets (simple), mTLS (secure), OAuth (enterprise)?
4. **Sandbox Strategy**: OS-level isolation (fast, less secure) or containers (slower, more secure)?
5. **Routing Policy**: Cost-optimal (cheapest) or quality-optimal (fastest + most capable)?

---

## Resources & References

### Existing Documentation

- `docs/reference/ARCHITECTURE_LAYERS.md` — thegent architecture
- `docs/plans/02-UNIFIED-WBS.md` — Phase 10-12 work breakdown
- `FUNCTIONAL_REQUIREMENTS.md` — FR-EXE-_, FR-MOD-_, FR-AGT-\* (agent execution, models, routing)

### External References

- [Kubernetes Federation](https://kubernetes.io/docs/concepts/cluster-administration/federation/)
- [Terraform Providers](https://www.terraform.io/language/providers)
- [Temporal Worker Pools](https://docs.temporal.io/workers)
- [gRPC Load Balancing](https://grpc.io/docs/guides/performance-best-practices/)

---

## Timeline & Effort Estimate

| Phase             | Duration     | Effort             | Owner |
| ----------------- | ------------ | ------------------ | ----- |
| Research & Design | 3 days       | 3 agent-days       | TBD   |
| Implementation    | 5 days       | 8 agent-days       | TBD   |
| Validation & Docs | 2 days       | 4 agent-days       | TBD   |
| **Total**         | **~2 weeks** | **~15 agent-days** | TBD   |

---

## Approval & Sign-Off

| Role                | Name             | Date       | Comments         |
| ------------------- | ---------------- | ---------- | ---------------- |
| Proposer            | (auto-generated) | 2026-02-18 | Initial proposal |
| Architecture Review | (pending)        | (pending)  | –                |
| Product Manager     | (pending)        | (pending)  | –                |
| Security Review     | (pending)        | (pending)  | –                |

---

## Next Steps

1. **Stakeholder Review**: Share this proposal with thegent team (sync or async)
2. **Go/No-Go Decision**: Decide if research should proceed in this or next phase window
3. **Design Phase Start**: If approved, begin design.md immediately
4. **Resource Allocation**: Assign agent(s) to research + prototype tracks

---

## Appendix A: Workload Classification Examples

### Example 1: Python Project

```
Prompt: "Analyze this Python monorepo for dependency cycles"
Detected: python, pip, git
Suitable: [Mac (score 0.95), Linux (score 0.95), Windows (score 0.80)]
Reason: Python is cross-platform; Windows lacks git-bash by default
Recommended: Linux (lowest cost)
```

### Example 2: iOS Development

```
Prompt: "Build and test this iOS app with Xcode"
Detected: swift, xcodebuild, ios-simulator
Suitable: [Mac (score 1.0), Linux (score 0.0), Windows (score 0.0)]
Reason: Xcode only on Mac; iOS simulator requires Mac hardware
Recommended: Mac (only viable)
```

### Example 3: Node.js Service

```
Prompt: "Profile CPU usage of this Node.js service"
Detected: node, npm, perf-tools
Suitable: [Mac (score 0.90), Linux (score 0.95), Windows (score 0.80)]
Reason: All support Node; Linux perf tools more sophisticated
Recommended: Linux (fastest + most capable)
```

---

**End of Proposal Document**
