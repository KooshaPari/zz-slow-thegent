# Documentation Navigation Map

This guide helps you find documentation based on what you're trying to do, rather than where it is in the hierarchy.

---

## Quick Navigation by Task

### "I want to..."

#### ...get started with the system

1. **First**: [CRUN Setup & Installation Guide](./guides/setup-guide.md)
2. **Then**: [Developer Quickstart](./guides/DEVELOPER_QUICKSTART.md)
3. **Reference**: [Getting Started with Ante](./context/wiki/getting-started.md)

#### ...understand the architecture

1. **Start**: [Multi-Tenant Agent Civilization Framework - Architecture Summary](./architecture/civilization-architecture.md)
2. **Dive deeper**: [Multi-Tenant Agent Civilization Framework - Complete Architecture](./architecture/civilization.md)
3. **Specific topics**:
   - [Agent Identity System](./architecture/agent-identity.md)
   - [Multi-Tenant Design](./architecture/multi-tenant.md)
   - [Swarm Architecture](./concepts/swarm-architecture.md)

#### ...deploy to production

1. **Overview**: [CRUN Deployment Guide](./deployment/deployment-overview.md)
2. **Configuration**: [MCP Configuration](./deployment/mcp-configuration.md)
3. **Scaling**: [Civilization-Scale Performance & Resource Orchestration](./deployment/scaling-guide.md)
4. **Startup**: [CRUN Startup Runbook](./deployment/runbooks/startup.md)

#### ...integrate with the API

- **REST API**: [REST API Reference](./api/rest-api.md)
- **MCP Protocol**: [MCP Protocol Guide](./api/mcp-protocol.md)
- **CLI**: [CRUN CLI Command Reference](./api/cli-reference.md)
- **Comparison**: [MCP Implementation Comparison](./api/mcp-comparison.md)

#### ...use the Swarm Controller

1. **Start**: [Self-Healing Swarm Controller - START HERE](./guides/swarm-controller.md)
2. **Usage**: [Self-Healing Swarm Controller Usage Guide](./guides/SWARM_CONTROLLER_USAGE.md)
3. **Integration**: [Swarm Controller Integration Guide](./guides/SWARM_INTEGRATION_GUIDE.md)

#### ...migrate data

- [Data Migration Guide](./guides/data-migration.md)
- [Phase 6: JSONL to SQLite Memory Migration Guide](./guides/PHASE_6_MEMORY_MIGRATION_GUIDE.md)
- [Legacy Dependency Migration Guide](./guides/legacy-migration.md)

#### ...set up governance & standards

1. **Overview**: [Ante LLM Context Documentation Governance Framework](./context/governance/GOVERNANCE.md)
2. **Standards**: [Ante LLM Context Documentation Standards](./context/governance/STANDARDS.md)
3. **Processes**: [Ante LLM Context Documentation Operational Processes](./context/governance/PROCESSES.md)
4. **Templates**: [Documentation Governance Implementation Templates](./context/governance/templates/README.md)

#### ...troubleshoot issues

- [CRUN Frequently Asked Questions (FAQ)](./troubleshooting/faq.md)
- [Maintenance Runbook](./MAINTENANCE_RUNBOOK.md)
- [Failure Recovery Playbook](./reference/FAILURE_RECOVERY_PLAYBOOK.md)

#### ...understand multi-tenant setup

1. [Multi-Tenant Cross-Project Agent Civilization Architecture](./architecture/multi-tenant.md)
2. [Multi-Tenant Agent Civilization Controller - Implementation Plan](./deployment/multi-tenant-config.md)

#### ...learn about agent identity

1. [Agent Identity and Discovery System](./architecture/agent-identity.md)
2. [Phase 1: Agent Identity System & Global Registry](./reference/PHASE_1_AGENT_IDENTITY_IMPLEMENTATION.md)
3. [Integrating Agent Identity System with Swarm Controller](./guides/INTEGRATING_AGENT_IDENTITY_WITH_SWARM_CONTROLLER.md)

#### ...explore resilience patterns

1. [Resilience Pattern Comparison & Decision Trees](./reference/RESILIENCE_PATTERN_COMPARISON.md)
2. [Resilience Patterns: Quick-Start Implementation Guide](./guides/RESILIENCE_IMPLEMENTATION_QUICKSTART.md)
3. [Failure Recovery Playbook](./reference/FAILURE_RECOVERY_PLAYBOOK.md)

#### ...understand security

- [CRUN Security Model](./concepts/security-model.md)
- [Ante LLM Context Documentation Governance Framework](./context/governance/GOVERNANCE.md)

---

## Navigation Flowchart

```
START HERE
    ↓
    └─→ Are you NEW to the system?
        ├─ YES → Setup & Installation Guide → Developer Quickstart
        └─ NO  → What do you need?
            ├─→ Understand the system
            │   ├─ Architecture → Civilization Framework (Summary or Complete)
            │   ├─ Agent Identity → Agent ID System docs
            │   ├─ Security → Security Model
            │   └─ Coordination → Coordination Patterns
            │
            ├─→ Deploy/Operate
            │   ├─ Deploy → Deployment Guide
            │   ├─ Configure → MCP Configuration
            │   ├─ Scale → Scaling Guide
            │   ├─ Run → Startup Runbook
            │   └─ Troubleshoot → FAQ or Maintenance Runbook
            │
            ├─→ Integrate/Develop
            │   ├─ REST API → REST API Reference
            │   ├─ MCP → MCP Protocol Guide
            │   ├─ CLI → CLI Reference
            │   ├─ Swarm → Swarm Controller docs
            │   └─ Memory → Phase 6 Memory Migration Guide
            │
            ├─→ Migrate/Modernize
            │   ├─ Data → Data Migration Guide
            │   ├─ Legacy → Legacy Migration Guide
            │   ├─ Memory → JSONL to SQLite Migration
            │   └─ Dependencies → Dependency Upgrade Guide
            │
            └─→ Governance/Standards
                ├─ Policies → Governance Framework
                ├─ Writing → Standards Guide
                ├─ Process → Operational Processes
                └─ Templates → Template Library
```

---

## Common Workflows & Document Paths

### Workflow 1: Initial Setup & Local Development

**Goal**: Get the system running locally

**Document path**:

1. [CRUN Setup & Installation Guide](./guides/setup-guide.md) - Initial setup
2. [Developer Quickstart](./guides/DEVELOPER_QUICKSTART.md) - Quickstart workflow
3. [Frontend Development Guide](./guides/frontend-development.md) - If building UI
4. [CRUN Frequently Asked Questions](./troubleshooting/faq.md) - When stuck

### Workflow 2: Production Deployment

**Goal**: Deploy to production with proper configuration

**Document path**:

1. [CRUN Deployment Guide](./deployment/deployment-overview.md) - Overview
2. [System-Scoped MCP Setup](./deployment/mcp-configuration.md) - Configure MCP
3. [Civilization-Scale Performance & Resource Orchestration](./deployment/scaling-guide.md) - Scaling considerations
4. [CRUN Startup Runbook](./deployment/runbooks/startup.md) - Startup procedure
5. [CRUN Security Model](./concepts/security-model.md) - Security considerations

### Workflow 3: Understanding the Multi-Agent System

**Goal**: Learn how agents coordinate and communicate

**Document path**:

1. [Multi-Tenant Agent Civilization Framework - Architecture Summary](./architecture/civilization-architecture.md) - Overview
2. [Agent Identity and Discovery System](./architecture/agent-identity.md) - Agent registration
3. [Cross-Project Coordination Patterns](./concepts/coordination.md) - Coordination
4. [Self-Healing Swarm Controller](./guides/swarm-controller.md) - Swarm management
5. [Multi-Level Coordination (L1/L2/L3)](./reference/COORDINATION.md) - Detailed coordination

### Workflow 4: Integrating with APIs

**Goal**: Build clients or integrate with external systems

**Document path**:

1. [REST API Reference](./api/rest-api.md) - HTTP endpoints
2. [MCP Protocol Guide](./api/mcp-protocol.md) - MCP protocol
3. [MCP Merge Summary](./api/mcp-integration.md) - Integration details
4. [CRUN CLI Command Reference](./api/cli-reference.md) - CLI usage

### Workflow 5: Memory & Persistence

**Goal**: Set up and manage agent memory

**Document path**:

1. [Memory feature guide](./context/wiki/features/memory.md) - Memory basics
2. [Phase 6: JSONL to SQLite Memory Migration Guide](./guides/PHASE_6_MEMORY_MIGRATION_GUIDE.md) - Migration
3. [Memory - Ante Wiki](./context/wiki/09-memory.md) - Detailed reference

### Workflow 6: Multi-Tenant Setup

**Goal**: Configure for multi-tenant deployment

**Document path**:

1. [Multi-Tenant Cross-Project Agent Civilization Architecture](./architecture/multi-tenant.md) - Design
2. [Multi-Tenant Agent Civilization Controller - Implementation Plan](./deployment/multi-tenant-config.md) - Implementation

### Workflow 7: Modernization & Migration

**Goal**: Migrate from legacy systems

**Document path**:

1. [Migration Overview & Strategy Guide](./guides/migration-overview.md) - Strategy
2. [Legacy Dependency Migration Guide](./guides/legacy-migration.md) - Migration guide
3. [Deep Legacy Dependency Audit & Modern Alternatives](./guides/legacy-alternatives.md) - Alternatives
4. [Dependency Upgrade Guide](./guides/dependency-updates.md) - Upgrading dependencies

### Workflow 8: Resilience & Recovery

**Goal**: Implement resilient systems and recovery procedures

**Document path**:

1. [Resilience Pattern Comparison & Decision Trees](./reference/RESILIENCE_PATTERN_COMPARISON.md) - Patterns
2. [Resilience Patterns: Quick-Start Implementation Guide](./guides/RESILIENCE_IMPLEMENTATION_QUICKSTART.md) - Quick start
3. [Failure Recovery Playbook](./reference/FAILURE_RECOVERY_PLAYBOOK.md) - Recovery

---

## Document Organization by Purpose

### Learning Resources

- **Beginner**: Setup Guide, Developer Quickstart, Getting Started guides
- **Intermediate**: Architecture docs, Concepts, API Reference
- **Advanced**: Implementation guides, Resilience patterns, Research docs

### Reference Materials

- [Complete Document Index](./INDEX.md) - Alphabetical with descriptions
- [CRUN Glossary & Terminology](./references/glossary.md) - Definitions
- [Dependency Audit Report](./references/dependencies.md) - Dependencies

### How-To Guides

- All files in `guides/` directory
- Workflow-specific runbooks in `deployment/runbooks/`
- Integration guides and implementation guides

### Standards & Governance

- `context/governance/` directory
- Templates: `context/governance/templates/`

### Technical Specifications

- `specs/prds/` - Product requirements documents
- `plans/` - Phase-based implementation plans
- Architecture documents in `architecture/`

### Research & Planning

- `research/` directory for deep dives
- `reference/` directory for decision logs
- `reports/` directory for completion summaries

---

## Finding Specific Topics

### By Technology/Component

- **Agent Identity**: [Architecture docs](./architecture/agent-identity.md), [Phase 1 docs](./reference/PHASE_1_AGENT_IDENTITY_IMPLEMENTATION.md)
- **MCP (Model Context Protocol)**: [API reference](./api/), [Integration guide](./guides/SWARM_INTEGRATION_GUIDE.md)
- **Swarm Controller**: [Guides directory](./guides/swarm-controller.md)
- **Memory/Persistence**: [Memory features](./context/wiki/features/memory.md), [Migration guides](./guides/PHASE_6_MEMORY_MIGRATION_GUIDE.md)
- **Multi-Tenant**: [Architecture](./architecture/multi-tenant.md), [Deployment](./deployment/multi-tenant-config.md)
- **Security**: [Security model](./concepts/security-model.md), [Governance](./context/governance/GOVERNANCE.md)

### By Role

- **Developers**: Start with [Developer Quickstart](./guides/DEVELOPER_QUICKSTART.md) and [Architecture](./architecture/)
- **DevOps/Operations**: Start with [Deployment Guide](./deployment/deployment-overview.md)
- **Architects**: Start with [Architecture Overview](./architecture/civilization-architecture.md)
- **API Users**: Start with [API Reference](./api/rest-api.md)
- **Contributors**: Start with [Standards](./context/governance/STANDARDS.md)

---

## Breadcrumb Navigation

Use these breadcrumbs to navigate between related docs:

**Core System Understanding**:
[Architecture Overview](./architecture/civilization-architecture.md)
→ [Complete Architecture](./architecture/civilization.md)
→ [Agent Identity](./architecture/agent-identity.md)
→ [Multi-Tenant Design](./architecture/multi-tenant.md)

**Getting Productive**:
[Setup Guide](./guides/setup-guide.md)
→ [Developer Quickstart](./guides/DEVELOPER_QUICKSTART.md)
→ [Frontend Development](./guides/frontend-development.md)

**Production Operations**:
[Deployment Overview](./deployment/deployment-overview.md)
→ [Startup Runbook](./deployment/runbooks/startup.md)
→ [Scaling Guide](./deployment/scaling-guide.md)

---

## Quick Reference Matrix

| If you need...       | Go to...                                                            |
| -------------------- | ------------------------------------------------------------------- |
| To get started       | [Setup Guide](./guides/setup-guide.md)                              |
| API documentation    | [API Reference](./api/rest-api.md)                                  |
| Architecture details | [Architecture Summary](./architecture/civilization-architecture.md) |
| Deployment info      | [Deployment Guide](./deployment/deployment-overview.md)             |
| How to troubleshoot  | [FAQ](./troubleshooting/faq.md)                                     |
| Swarm Controller     | [Swarm Controller Docs](./guides/swarm-controller.md)               |
| MCP Protocol         | [MCP Protocol](./api/mcp-protocol.md)                               |
| Memory/Migration     | [Memory Migration](./guides/PHASE_6_MEMORY_MIGRATION_GUIDE.md)      |
| Security info        | [Security Model](./concepts/security-model.md)                      |
| Governance/Standards | [Governance](./context/governance/GOVERNANCE.md)                    |
| Complete index       | [INDEX.md](./INDEX.md)                                              |

---

**Last updated**: 2026-02-20  
**For questions**: See [FAQ](./troubleshooting/faq.md) or [Documentation Hub](./README.md)
