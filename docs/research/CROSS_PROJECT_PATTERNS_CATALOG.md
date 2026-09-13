<DONE>
# Cross-Project Patterns Catalog

> **Status**: 📚 **CATALOG COMPLETE** | **Date**: 2026-02-18
> **Purpose**: Comprehensive catalog of reusable patterns, strategies, and implementations across the kush ecosystem

---

## Executive Summary

This catalog organizes **all borrowable patterns** from the kush ecosystem into a searchable, categorized reference. It serves as a **quick lookup** for developers and architects seeking proven patterns.

**Total Patterns Cataloged**: 100+ patterns across 10 categories

---

## Part 1: Work Stream & Planning Patterns

### 1.1 Priority Systems

| Pattern                    | Source       | Description                                                                                  | Borrowable To                 |
| -------------------------- | ------------ | -------------------------------------------------------------------------------------------- | ----------------------------- |
| **P0-P4 Priority System**  | heliosShield | P0 Blocker, P1 Feature (1 sprint), P2 Polish (2 sprints), P3 Research (3 sprints), P4 Icebox | All projects                  |
| **Story Point Estimation** | smolgents    | Detailed point estimates with velocity tracking                                              | Complex projects              |
| **Phase-Based Planning**   | trace, dphi  | Clear phase boundaries with completion tracking                                              | MCP servers, planning systems |

---

### 1.2 Work Stream Structures

| Pattern                      | Source                | Description                                         | Borrowable To        |
| ---------------------------- | --------------------- | --------------------------------------------------- | -------------------- |
| **Agent Claiming System**    | thegent               | Agent-based work claiming with timestamps           | Multi-agent projects |
| **Research Doc Integration** | thegent               | Link research docs to work items, track extensions  | All projects         |
| **Dependency Tracking**      | thegent, heliosShield | Explicit dependency columns, blocking relationships | All projects         |
| **Status Badges**            | kimaki                | Visual status indicators (✅, 🚧, 📋)               | All projects         |
| **Recently Completed**       | heliosShield          | Track completed items in last 30 days               | All projects         |

---

### 1.3 Planning Patterns

| Pattern                    | Source | Description                                     | Borrowable To    |
| -------------------------- | ------ | ----------------------------------------------- | ---------------- |
| **WBS Decomposition**      | morph  | Feature development, refactoring, migration WBS | All projects     |
| **PERT Network**           | morph  | Sequential, parallel, phased rollout patterns   | All projects     |
| **Adaptive Decomposition** | crun   | AI-driven task decomposition                    | Planning systems |
| **Tree of Thoughts**       | crun   | Multi-step reasoning for planning               | Planning systems |
| **Risk Assessment Matrix** | morph  | Probability × Impact severity calculation       | All projects     |

---

## Part 2: Testing Patterns

### 2.1 Test Pyramid Strategies

| Pattern               | Source       | Distribution                               | Coverage Target | Borrowable To      |
| --------------------- | ------------ | ------------------------------------------ | --------------- | ------------------ |
| **Standard Pyramid**  | heliosShield | 70% unit, 20% integration, 10% E2E         | 80%+            | All projects       |
| **Agent Pyramid**     | smolgents    | 60-70% unit, 20-30% integration, 5-10% E2E | 80%+ core       | Agent systems      |
| **Hexagonal Pyramid** | morph        | 80% unit, 15% integration, 5% E2E          | 90%+ domain     | Hexagonal projects |

---

### 2.2 Testing Strategies

| Pattern                    | Source       | Description                                             | Borrowable To       |
| -------------------------- | ------------ | ------------------------------------------------------- | ------------------- |
| **Hexagonal Testing**      | morph        | Layer-based testing (domain 90%+, app 80%+, infra 70%+) | Hexagonal projects  |
| **Test Data Management**   | morph        | Fixtures, factories, mocks hierarchy                    | All Python projects |
| **Characterization Tests** | heliosShield | Gate for brownfield refactoring                         | Legacy projects     |
| **Mutation Testing**       | heliosShield | PIT/Stryker/Infection for critical systems              | Critical systems    |
| **Property Testing**       | heliosShield | Echidna for smart contracts                             | Smart contracts     |

---

### 2.3 Test Organization

| Pattern                    | Source       | Structure                           | Borrowable To |
| -------------------------- | ------------ | ----------------------------------- | ------------- |
| **Test Pyramid Rebalance** | heliosShield | 63% → 70% unit tests                | All projects  |
| **Coverage Targets**       | smolgents    | Component-specific coverage targets | All projects  |
| **Test Categorization**    | plangent     | Unit, integration, E2E, regression  | All projects  |

---

## Part 3: Deployment Patterns

### 3.1 Rollout Strategies

| Pattern               | Source | Phases                                                   | Risk Level | Borrowable To             |
| --------------------- | ------ | -------------------------------------------------------- | ---------- | ------------------------- |
| **Phased Rollout**    | morph  | Pilot (10%) → Canary (25%) → Gradual (50%) → Full (100%) | Low        | Production deployments    |
| **Canary Deployment** | morph  | Gradual traffic increase with validation                 | Low        | Production services       |
| **Feature Flags**     | morph  | Controlled rollout with toggle capability                | Medium     | Feature rollouts          |
| **Big Bang**          | morph  | Complete migration at once                               | High       | When gradual not feasible |

---

### 3.2 Migration Patterns

| Pattern              | Source | Timeline                                      | Risk   | Borrowable To         |
| -------------------- | ------ | --------------------------------------------- | ------ | --------------------- |
| **Strangler Fig**    | morph  | Weeks to months                               | Low    | Legacy migrations     |
| **Dual-Run Phase**   | morph  | Run both systems, compare outputs             | Low    | System migrations     |
| **Cutover Strategy** | morph  | Traffic migration, data migration, monitoring | Medium | Production migrations |

---

## Part 4: Monitoring & Observability Patterns

### 4.1 Monitoring Stacks

| Pattern                       | Source         | Components                              | Features                                         | Borrowable To       |
| ----------------------------- | -------------- | --------------------------------------- | ------------------------------------------------ | ------------------- |
| **Prometheus + Grafana**      | claude-squad   | Prometheus, Grafana, Alertmanager, Loki | 7 dashboards, multi-channel alerts, SLO tracking | Production services |
| **Performance Monitoring**    | atoms-mcp-prod | Query performance, slow query detection | Real-time metrics                                | Database services   |
| **Voice Pipeline Monitoring** | kimaki         | STT/TTS latency, quality metrics        | Real-time tracking                               | Voice AI systems    |

---

### 4.2 Metrics Patterns

| Pattern                    | Source       | Metrics                                                | Borrowable To       |
| -------------------------- | ------------ | ------------------------------------------------------ | ------------------- |
| **Application Metrics**    | smolgents    | Execution time, token usage, cost tracking, error rate | Agent systems       |
| **Infrastructure Metrics** | smolgents    | CPU, memory, disk, network, DB connections             | All services        |
| **Business Metrics**       | smolgents    | Cost per execution, task completion rate               | Business systems    |
| **SLO/SLA Tracking**       | claude-squad | Error budgets, SLA monitoring                          | Production services |

---

### 4.3 Logging Patterns

| Pattern                 | Source                | Levels                             | Features             | Borrowable To     |
| ----------------------- | --------------------- | ---------------------------------- | -------------------- | ----------------- |
| **Structured Logging**  | smolgents             | ERROR, WARNING, INFO, DEBUG, TRACE | Structured format    | All projects      |
| **Audit Logging**       | trace, atoms-mcp-prod | Security events, access logs       | Immutable logs       | All systems       |
| **Performance Logging** | atoms-mcp-prod        | Query performance, slow queries    | Performance tracking | Database services |

---

## Part 5: Security Patterns

### 5.1 Authentication Patterns

| Pattern                        | Source         | Flow                                    | Features                               | Borrowable To     |
| ------------------------------ | -------------- | --------------------------------------- | -------------------------------------- | ----------------- |
| **OAuth PKCE + Bearer Hybrid** | atoms-mcp-prod | OAuth for external, Bearer for internal | Composite provider, session management | MCP servers, APIs |
| **OAuth 2.0 (GitHub)**         | claude-squad   | Standard OAuth flow                     | CSRF protection, PKCE, revocable       | Web applications  |
| **JWT Tokens**                 | trace          | Token-based auth                        | Token expiry, refresh                  | API services      |

---

### 5.2 Authorization Patterns

| Pattern                      | Source              | Mechanism                      | Features                                  | Borrowable To        |
| ---------------------------- | ------------------- | ------------------------------ | ----------------------------------------- | -------------------- |
| **Row-Level Security (RLS)** | atoms-mcp-prod      | Database-level security        | Automatic query scoping, org-based access | PostgreSQL projects  |
| **RBAC**                     | trace, claude-squad | Role-based access control      | Role definitions, permission mapping      | Multi-user systems   |
| **Policy Federation**        | heliosShield        | Multi-tenant policy federation | Cross-tenant policies                     | Multi-tenant systems |

---

### 5.3 Encryption Patterns

| Pattern                 | Source              | Encryption                          | Features                              | Borrowable To |
| ----------------------- | ------------------- | ----------------------------------- | ------------------------------------- | ------------- |
| **Data Encryption**     | trace, claude-squad | AES-256 at rest, TLS 1.3 in transit | Encrypted backups, secrets management | All projects  |
| **Certificate Pinning** | claude-squad        | Certificate validation              | MITM protection                       | Mobile apps   |

---

### 5.4 Security Features

| Pattern                    | Source                | Features                                    | Borrowable To       |
| -------------------------- | --------------------- | ------------------------------------------- | ------------------- |
| **Threat Modeling**        | claude-squad          | Threat matrix, attack scenarios, mitigation | Production services |
| **Security Monitoring**    | claude-squad          | Intrusion detection, anomaly detection      | Production services |
| **Vulnerability Scanning** | heliosShield          | Dependency scanning, DAST                   | All projects        |
| **Audit Trail**            | trace, atoms-mcp-prod | Immutable logs, change tracking             | All systems         |

---

## Part 6: Architecture Patterns

### 6.1 Architectural Styles

| Pattern                    | Source                   | Description                                      | Borrowable To              |
| -------------------------- | ------------------------ | ------------------------------------------------ | -------------------------- |
| **Hexagonal Architecture** | morph, atoms-mcp-prod    | Domain → Application → Infrastructure layers     | New projects, refactoring  |
| **Adapter Pattern**        | plangent, atoms-mcp-prod | Generic interfaces, multiple implementations     | Agent systems, MCP servers |
| **Event-Driven**           | plangent                 | Message queues, pub/sub, decoupled communication | Multi-agent systems        |
| **Hierarchical Agents**    | plangent, kimaki         | Root agent + sub-agents                          | Multi-agent systems        |

---

### 6.2 Design Patterns

| Pattern                     | Source         | Description                   | Borrowable To      |
| --------------------------- | -------------- | ----------------------------- | ------------------ |
| **Port/Adapter Separation** | morph          | Clear boundaries, testability | Hexagonal projects |
| **Service Layer**           | atoms-mcp-prod | Business logic separation     | All projects       |
| **Repository Pattern**      | atoms-mcp-prod | Data access abstraction       | Database projects  |
| **Factory Pattern**         | morph          | Test data generation          | All projects       |

---

## Part 7: Performance Optimization Patterns

### 7.1 Caching Strategies

| Pattern                    | Source       | Strategy                    | Features            | Borrowable To         |
| -------------------------- | ------------ | --------------------------- | ------------------- | --------------------- |
| **Hierarchical Cache**     | heliosShield | L1/L2/L3 cache layers       | Multi-level caching | High-traffic services |
| **Stale-While-Revalidate** | heliosShield | Serve stale, update async   | Fast responses      | Cache systems         |
| **LLM Response Caching**   | smolgents    | Semantic similarity caching | Cost reduction      | Agent systems         |
| **Tool Result Caching**    | smolgents    | Time-based TTL              | Performance         | Tool systems          |

---

### 7.2 Parallelization Patterns

| Pattern                | Source         | Strategy                       | Features            | Borrowable To     |
| ---------------------- | -------------- | ------------------------------ | ------------------- | ----------------- |
| **Parallel Execution** | smolgents      | Concurrent independent tasks   | Speed improvement   | Agent systems     |
| **Batch Operations**   | atoms-mcp-prod | Bulk operations                | Efficiency          | Database services |
| **Resource Pooling**   | smolgents      | Connection pooling, HTTP reuse | Resource efficiency | All services      |

---

### 7.3 Optimization Features

| Pattern                | Source       | Feature                     | Borrowable To       |
| ---------------------- | ------------ | --------------------------- | ------------------- |
| **Lazy Loading**       | smolgents    | Load on demand              | All projects        |
| **Code Splitting**     | heliosShield | Manual chunks, optimization | Frontend projects   |
| **Image Optimization** | heliosShield | WebP/AVIF, lazy loading     | Documentation sites |
| **Font Optimization**  | heliosShield | Subset fonts, preload       | Web projects        |

---

## Part 8: Cost Optimization Patterns

### 8.1 Model Routing

| Pattern                      | Source    | Strategy                    | Savings         | Borrowable To |
| ---------------------------- | --------- | --------------------------- | --------------- | ------------- |
| **Intelligent Routing**      | smolgents | Route to cost-optimal model | 40-80%          | Agent systems |
| **Model Tier Strategy**      | smolgents | 4 tiers (Haiku → GPT-4)     | Cost reduction  | Agent systems |
| **Task Complexity Analysis** | smolgents | Route based on complexity   | Optimal routing | Agent systems |

---

### 8.2 Cost Tracking

| Pattern           | Source       | Metrics                        | Features          | Borrowable To |
| ----------------- | ------------ | ------------------------------ | ----------------- | ------------- |
| **Cost Tracking** | smolgents    | Per task, per agent, per model | Detailed tracking | Agent systems |
| **Budget Alerts** | heliosShield | Cost-overage gates             | Budget management | All projects  |
| **Cost Metrics**  | smolgents    | Cost per execution, savings    | Business metrics  | Agent systems |

---

## Part 9: Multi-Agent Patterns

### 9.1 Agent Orchestration

| Pattern                | Source           | Architecture                     | Features           | Borrowable To         |
| ---------------------- | ---------------- | -------------------------------- | ------------------ | --------------------- |
| **Root + Sub-Agents**  | plangent         | Hierarchical coordination        | Parallel execution | Multi-agent systems   |
| **Agent Pause/Resume** | plangent, kimaki | Checkpoint-based resumption      | Fault tolerance    | Agent systems         |
| **Conversation Rules** | kimaki           | Collaboration modes, moderation  | Agent-to-agent     | Multi-agent systems   |
| **Project Context**    | kimaki           | Multi-project context management | Context switching  | Multi-project systems |

---

### 9.2 Agent Communication

| Pattern                 | Source   | Mechanism                  | Features          | Borrowable To       |
| ----------------------- | -------- | -------------------------- | ----------------- | ------------------- |
| **Event-Driven**        | plangent | Message queues             | Decoupled         | Multi-agent systems |
| **Verification Agents** | plangent | Separate validation agents | Quality assurance | Agent systems       |
| **State Persistence**   | plangent | Checkpoint-based           | Resumption        | Agent systems       |

---

## Part 10: Research & Innovation Patterns

### 10.1 LLM Quality

| Pattern                   | Source       | Approach              | Tools                      | Borrowable To    |
| ------------------------- | ------------ | --------------------- | -------------------------- | ---------------- |
| **LLM-as-Judge**          | heliosShield | Binary classification | Gemini Flash, Claude Haiku | Code quality     |
| **Local ML Models**       | heliosShield | On-device inference   | Qwen-Coder, MLX            | Pre-commit hooks |
| **Semantic Verification** | heliosShield | Intent verification   | LLM APIs                   | Code review      |

---

### 10.2 Chaos Engineering

| Pattern                | Source       | Tool                    | Level       | Borrowable To |
| ---------------------- | ------------ | ----------------------- | ----------- | ------------- |
| **Fault Injection**    | heliosShield | Toxiproxy, WireMock     | Integration | All projects  |
| **Resilience Testing** | heliosShield | Resilience libraries    | Unit        | All projects  |
| **Platform Chaos**     | heliosShield | Chaos Mesh, LitmusChaos | Platform    | Kubernetes    |

---

### 10.3 Research Areas

| Area                       | Source       | Status   | Borrowable To          |
| -------------------------- | ------------ | -------- | ---------------------- |
| **MLX Optimization**       | heliosShield | Research | Apple Silicon projects |
| **Monte Carlo Simulation** | heliosShield | Research | Planning systems       |
| **ZK-Proofs**              | heliosShield | Research | Security systems       |

---

## Part 11: Documentation Patterns

### 11.1 Documentation Systems

| Pattern                 | Source         | System             | Features                       | Borrowable To   |
| ----------------------- | -------------- | ------------------ | ------------------------------ | --------------- |
| **VitePress Rich Docs** | thegent        | VitePress          | Mermaid, CodePlayground, demos | All projects    |
| **MkDocs Material**     | atoms-mcp-prod | MkDocs             | Advanced navigation, search    | Python projects |
| **Auto-Generated API**  | thegent        | Python AST parsing | From docstrings                | Python projects |

---

### 11.2 Documentation Features

| Feature                   | Source  | Description        | Borrowable To    |
| ------------------------- | ------- | ------------------ | ---------------- |
| **Math Support**          | thegent | KaTeX rendering    | Technical docs   |
| **Emoji Support**         | thegent | markdown-it-emoji  | All docs         |
| **Tooltips**              | thegent | Vue component      | Interactive docs |
| **Architecture Diagrams** | thegent | Mermaid generation | All projects     |

---

## Part 12: Quick Reference Matrix

### By Project Need

| Need                  | Recommended Pattern       | Source         | Priority |
| --------------------- | ------------------------- | -------------- | -------- |
| **Work Stream**       | P0-P4 Priority System     | heliosShield   | P1       |
| **Testing**           | Test Pyramid (60-70-5-10) | smolgents      | P1       |
| **Deployment**        | Phased Rollout            | morph          | P1       |
| **Monitoring**        | Prometheus + Grafana      | claude-squad   | P1       |
| **Security**          | OAuth PKCE + Bearer       | atoms-mcp-prod | P1       |
| **Architecture**      | Hexagonal Architecture    | morph          | P1       |
| **Cost Optimization** | Intelligent Routing       | smolgents      | P1       |
| **Multi-Agent**       | Root + Sub-Agents         | plangent       | P1       |

---

### By Project Type

| Project Type      | Key Patterns                                        | Sources                     |
| ----------------- | --------------------------------------------------- | --------------------------- |
| **Agent Systems** | Cost optimization, multi-agent patterns, monitoring | smolgents, plangent, kimaki |
| **MCP Servers**   | Tool categorization, composition, OAuth             | trace, dphi, atoms-mcp-prod |
| **CLI Tools**     | Rich output, async-first, type safety               | heliosShield, bloc, trace   |
| **Web Services**  | OAuth, RBAC, monitoring, security                   | claude-squad, trace         |
| **Documentation** | VitePress, auto-generation, rich elements           | thegent                     |

---

## See Also

- [CROSS_PROJECT_DEEP_EXPANDED_ANALYSIS.md](./CROSS_PROJECT_DEEP_EXPANDED_ANALYSIS.md) - Deep analysis
- [CROSS_PROJECT_WORK_STREAM_ANALYSIS.md](./CROSS_PROJECT_WORK_STREAM_ANALYSIS.md) - Work stream analysis
- [CROSS_PROJECT_FEATURE_BORROWING_PLAN.md](./CROSS_PROJECT_FEATURE_BORROWING_PLAN.md) - Implementation plan

---

**Status**: 📚 **CATALOG COMPLETE** - 100+ patterns cataloged and organized
