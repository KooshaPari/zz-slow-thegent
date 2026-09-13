<DONE>
# Kush Ecosystem — Architecture Diagram

> **Status**: 🏗️ **ARCHITECTURE DIAGRAM** | **Date**: 2026-02-18
> **Purpose**: Visual representation of the kush ecosystem architecture, relationships, and data flows

---

## Executive Summary

This document provides comprehensive architecture diagrams for the kush ecosystem, showing:

- **System Architecture**: High-level view of all projects
- **Layer Architecture**: Layered view by responsibility
- **Integration Architecture**: How projects integrate
- **Data Flow Architecture**: How data flows through the system
- **Agent Architecture**: Agent orchestration patterns

---

## Part 1: System Architecture Overview

```mermaid
graph TB
    subgraph "User Interfaces"
        CLI[CLI Tools]
        WEB[Web Interfaces]
        VOICE[Voice Interface]
        GUI[GUI/TUI]
    end

    subgraph "Agent Orchestration Layer"
        THEGENT[thegent<br/>Unified Orchestration]
        PLANGENT[plangent<br/>Multi-Agent]
        KIMAKI[kimaki<br/>Voice AI]
        SMOLGENTS[smolgents<br/>Delegation]
        CRUN[crun<br/>DSL Planning]
    end

    subgraph "MCP Server Layer"
        ATOMS_MCP[atoms-mcp-prod<br/>Knowledge & Entities]
        ZEN_MCP[zen-mcp-server]
        SG4M[4sgm<br/>LangGraph + MCP]
        MORPH[morph<br/>Workspace & Research]
        TASK_TOOL[task-tool<br/>Task Management]
        TASK2[task2<br/>Advanced Tasks]
    end

    subgraph "CLI & Utility Layer"
        heliosShield[heliosShield<br/>Agent Harness]
        BLOC[bloc<br/>Code Analysis]
        TRACE[trace<br/>RTM]
        USAGE[usage<br/>AI Tracking]
        DPHI[dphi<br/>Package Discovery]
    end

    subgraph "Infrastructure Layer"
        PHENO_SDK[pheno-sdk<br/>Infrastructure SDK]
        SMARTCP[smartcp<br/>MCP Router]
        JOBHUNTER[jobhunter<br/>Job Platform]
        KNOWLEDGEBASE[knowledgebase<br/>KB System]
        AGENTAPI[agentapi<br/>Agent API]
    end

    subgraph "External Systems"
        LLM_PROVIDERS[LLM Providers<br/>OpenAI, Anthropic, etc.]
        DATABASES[Databases<br/>PostgreSQL, Redis, etc.]
        STORAGE[Storage<br/>File System, S3, etc.]
        APIS[External APIs<br/>GitHub, Slack, etc.]
    end

    CLI --> THEGENT
    CLI --> heliosShield
    CLI --> BLOC
    CLI --> TRACE
    CLI --> USAGE
    CLI --> DPHI

    WEB --> JOBHUNTER
    WEB --> KNOWLEDGEBASE
    WEB --> AGENTAPI
    WEB --> DPHI

    VOICE --> KIMAKI

    GUI --> heliosShield
    GUI --> USAGE

    THEGENT --> ATOMS_MCP
    THEGENT --> ZEN_MCP
    THEGENT --> MORPH
    THEGENT --> TASK_TOOL

    PLANGENT --> ATOMS_MCP
    PLANGENT --> TASK_TOOL

    KIMAKI --> ATOMS_MCP
    KIMAKI --> TASK_TOOL

    SMOLGENTS --> ATOMS_MCP
    CRUN --> ATOMS_MCP

    heliosShield --> PHENO_SDK
    BLOC --> PHENO_SDK
    CRUN --> PHENO_SDK
    USAGE --> PHENO_SDK

    SMARTCP --> ATOMS_MCP
    SMARTCP --> ZEN_MCP
    SMARTCP --> MORPH
    SMARTCP --> TASK_TOOL

    ATOMS_MCP --> DATABASES
    ATOMS_MCP --> STORAGE
    ATOMS_MCP --> APIS

    TASK_TOOL --> LLM_PROVIDERS
    TASK2 --> LLM_PROVIDERS

    TRACE --> DATABASES
    JOBHUNTER --> DATABASES
    KNOWLEDGEBASE --> STORAGE

    style THEGENT fill:#42b883
    style PLANGENT fill:#42b883
    style KIMAKI fill:#42b883
    style SMOLGENTS fill:#42b883
    style CRUN fill:#42b883
    style ATOMS_MCP fill:#646cff
    style PHENO_SDK fill:#f59e0b
```

---

## Part 2: Layer Architecture

```mermaid
graph TB
    subgraph "Presentation Layer"
        CLI_APPS[CLI Applications]
        WEB_APPS[Web Applications]
        VOICE_APPS[Voice Applications]
        GUI_APPS[GUI/TUI Applications]
    end

    subgraph "Orchestration Layer"
        AGENT_ORCH[Agent Orchestrators<br/>thegent, plangent, kimaki, smolgents, crun]
    end

    subgraph "Service Layer"
        MCP_SERVERS[MCP Servers<br/>atoms-mcp-prod, zen-mcp-server, 4sgm, morph, task-tool, task2]
        CLI_SERVICES[CLI Services<br/>heliosShield, bloc, trace, usage, dphi]
    end

    subgraph "Infrastructure Layer"
        SDK[SDKs<br/>pheno-sdk]
        ROUTERS[Routers<br/>smartcp]
        PLATFORMS[Platforms<br/>jobhunter, knowledgebase, agentapi]
    end

    subgraph "Data Layer"
        DATABASES[(Databases)]
        CACHE[(Cache)]
        STORAGE[(Storage)]
    end

    subgraph "External Layer"
        LLMS[LLM Providers]
        APIS[External APIs]
        SERVICES[External Services]
    end

    CLI_APPS --> AGENT_ORCH
    WEB_APPS --> AGENT_ORCH
    VOICE_APPS --> AGENT_ORCH
    GUI_APPS --> AGENT_ORCH

    AGENT_ORCH --> MCP_SERVERS
    AGENT_ORCH --> CLI_SERVICES

    MCP_SERVERS --> SDK
    CLI_SERVICES --> SDK

    SDK --> ROUTERS
    SDK --> PLATFORMS

    ROUTERS --> DATABASES
    PLATFORMS --> DATABASES
    PLATFORMS --> CACHE
    PLATFORMS --> STORAGE

    MCP_SERVERS --> LLMS
    AGENT_ORCH --> LLMS
    PLATFORMS --> APIS
    PLATFORMS --> SERVICES

    style AGENT_ORCH fill:#42b883
    style MCP_SERVERS fill:#646cff
    style SDK fill:#f59e0b
```

---

## Part 3: Agent Orchestration Architecture

```mermaid
graph TB
    subgraph "User"
        USER[User/Developer]
    end

    subgraph "Entry Points"
        CLI_ENTRY[CLI Entry<br/>thegent, heliosShield]
        VOICE_ENTRY[Voice Entry<br/>kimaki]
        WEB_ENTRY[Web Entry<br/>jobhunter, knowledgebase]
    end

    subgraph "Orchestration Layer"
        ROOT_ORCH[Root Orchestrator<br/>thegent, plangent]

        subgraph "Specialized Orchestrators"
            VOICE_ORCH[Voice Orchestrator<br/>kimaki]
            DELEG_ORCH[Delegation Orchestrator<br/>smolgents]
            DSL_ORCH[DSL Orchestrator<br/>crun]
        end
    end

    subgraph "Agent Pool"
        AGENT1[Agent 1<br/>Specialized]
        AGENT2[Agent 2<br/>Specialized]
        AGENT3[Agent 3<br/>Specialized]
        AGENTN[Agent N<br/>Specialized]
    end

    subgraph "Tool Layer"
        MCP_TOOLS[MCP Tools<br/>atoms-mcp-prod, morph, task-tool]
        CLI_TOOLS[CLI Tools<br/>bloc, trace, usage, dphi]
        CUSTOM_TOOLS[Custom Tools]
    end

    subgraph "Infrastructure"
        REGISTRY[Agent Registry<br/>Unified]
        CONTEXT[Context Manager<br/>Project Context]
        MEMORY[Memory System<br/>Persistent Context]
    end

    USER --> CLI_ENTRY
    USER --> VOICE_ENTRY
    USER --> WEB_ENTRY

    CLI_ENTRY --> ROOT_ORCH
    VOICE_ENTRY --> VOICE_ORCH
    WEB_ENTRY --> ROOT_ORCH

    ROOT_ORCH --> DELEG_ORCH
    ROOT_ORCH --> DSL_ORCH
    VOICE_ORCH --> ROOT_ORCH

    ROOT_ORCH --> REGISTRY
    REGISTRY --> AGENT1
    REGISTRY --> AGENT2
    REGISTRY --> AGENT3
    REGISTRY --> AGENTN

    AGENT1 --> MCP_TOOLS
    AGENT2 --> CLI_TOOLS
    AGENT3 --> CUSTOM_TOOLS
    AGENTN --> MCP_TOOLS

    ROOT_ORCH --> CONTEXT
    CONTEXT --> MEMORY

    style ROOT_ORCH fill:#42b883
    style REGISTRY fill:#646cff
    style CONTEXT fill:#f59e0b
```

---

## Part 4: MCP Integration Architecture

```mermaid
graph LR
    subgraph "MCP Clients"
        THEGENT_CLIENT[thegent]
        PLANGENT_CLIENT[plangent]
        KIMAKI_CLIENT[kimaki]
        OTHER_CLIENTS[Other Clients]
    end

    subgraph "MCP Router Layer"
        SMARTCP_ROUTER[smartcp<br/>Discovery & Routing]
    end

    subgraph "MCP Servers"
        ATOMS_SERVER[atoms-mcp-prod<br/>Knowledge & Entities]
        ZEN_SERVER[zen-mcp-server]
        SG4M_SERVER[4sgm<br/>LangGraph + MCP]
        MORPH_SERVER[morph<br/>Workspace & Research]
        TASK_SERVER[task-tool<br/>Task Management]
        TASK2_SERVER[task2<br/>Advanced Tasks]
    end

    subgraph "Shared Tool Library"
        TOOL_LIB[Shared MCP Tools<br/>Common Tools]
    end

    subgraph "Backend Services"
        DB[(Databases)]
        STORAGE[(Storage)]
        APIS[External APIs]
    end

    THEGENT_CLIENT --> SMARTCP_ROUTER
    PLANGENT_CLIENT --> SMARTCP_ROUTER
    KIMAKI_CLIENT --> SMARTCP_ROUTER
    OTHER_CLIENTS --> SMARTCP_ROUTER

    SMARTCP_ROUTER --> ATOMS_SERVER
    SMARTCP_ROUTER --> ZEN_SERVER
    SMARTCP_ROUTER --> SG4M_SERVER
    SMARTCP_ROUTER --> MORPH_SERVER
    SMARTCP_ROUTER --> TASK_SERVER
    SMARTCP_ROUTER --> TASK2_SERVER

    ATOMS_SERVER --> TOOL_LIB
    MORPH_SERVER --> TOOL_LIB
    TASK_SERVER --> TOOL_LIB

    ATOMS_SERVER --> DB
    ATOMS_SERVER --> STORAGE
    ATOMS_SERVER --> APIS

    MORPH_SERVER --> STORAGE
    TASK_SERVER --> APIS

    style SMARTCP_ROUTER fill:#646cff
    style TOOL_LIB fill:#f59e0b
```

---

## Part 5: Data Flow Architecture

```mermaid
sequenceDiagram
    participant User
    participant CLI as CLI Entry
    participant Orch as Orchestrator
    participant Registry as Agent Registry
    participant Agent as Agent
    participant MCP as MCP Server
    participant Tools as Tools
    participant DB as Database
    participant LLM as LLM Provider

    User->>CLI: Execute Command
    CLI->>Orch: Route Request
    Orch->>Registry: Get Agent
    Registry-->>Orch: Agent Instance
    Orch->>Agent: Assign Task
    Agent->>MCP: Request Tool
    MCP->>Tools: Execute Tool
    Tools->>DB: Query Data
    DB-->>Tools: Return Data
    Tools-->>MCP: Tool Result
    MCP-->>Agent: Tool Response
    Agent->>LLM: Process with LLM
    LLM-->>Agent: LLM Response
    Agent->>MCP: Update State
    MCP->>DB: Persist State
    Agent-->>Orch: Task Complete
    Orch-->>CLI: Result
    CLI-->>User: Display Result
```

---

## Part 6: Project Dependency Graph

```mermaid
graph TD
    subgraph "Foundation Layer"
        PHENO[pheno-sdk<br/>Infrastructure SDK]
    end

    subgraph "Core Layer"
        THEGENT[thegent<br/>Orchestration]
        heliosShield[heliosShield<br/>Harness]
    end

    subgraph "MCP Layer"
        ATOMS[atoms-mcp-prod]
        SMARTCP[smartcp]
        MORPH[morph]
        TASK_TOOL[task-tool]
    end

    subgraph "Orchestration Layer"
        PLANGENT[plangent]
        KIMAKI[kimaki]
        SMOLGENTS[smolgents]
        CRUN[crun]
    end

    subgraph "Tool Layer"
        BLOC[bloc]
        TRACE[trace]
        USAGE[usage]
        DPHI[dphi]
    end

    PHENO --> BLOC
    PHENO --> CRUN
    PHENO --> USAGE

    THEGENT --> ATOMS
    THEGENT --> MORPH
    THEGENT --> TASK_TOOL

    heliosShield --> PHENO

    SMARTCP --> ATOMS
    SMARTCP --> MORPH
    SMARTCP --> TASK_TOOL

    PLANGENT --> ATOMS
    PLANGENT --> TASK_TOOL

    KIMAKI --> ATOMS
    KIMAKI --> TASK_TOOL

    SMOLGENTS --> ATOMS
    CRUN --> ATOMS

    style PHENO fill:#f59e0b
    style THEGENT fill:#42b883
    style ATOMS fill:#646cff
```

---

## Part 7: Integration Points

```mermaid
graph TB
    subgraph "Integration Hub"
        HUB[Unified Integration Hub]
    end

    subgraph "Agent Registry Integration"
        REG1[thegent Registry]
        REG2[kimaki Registry]
        REG3[plangent Registry]
        UNIFIED_REG[Unified Registry]
    end

    subgraph "MCP Tool Integration"
        TOOLS1[atoms-mcp-prod Tools]
        TOOLS2[morph Tools]
        TOOLS3[task-tool Tools]
        SHARED_TOOLS[Shared Tool Library]
    end

    subgraph "Context Integration"
        CTX1[kimaki Context]
        CTX2[trace Context]
        CTX3[atoms-mcp-prod Context]
        UNIFIED_CTX[Unified Context]
    end

    subgraph "Configuration Integration"
        CONFIG1[Project Configs]
        CONFIG2[Environment Configs]
        UNIFIED_CONFIG[Unified Config]
    end

    HUB --> UNIFIED_REG
    HUB --> SHARED_TOOLS
    HUB --> UNIFIED_CTX
    HUB --> UNIFIED_CONFIG

    REG1 --> UNIFIED_REG
    REG2 --> UNIFIED_REG
    REG3 --> UNIFIED_REG

    TOOLS1 --> SHARED_TOOLS
    TOOLS2 --> SHARED_TOOLS
    TOOLS3 --> SHARED_TOOLS

    CTX1 --> UNIFIED_CTX
    CTX2 --> UNIFIED_CTX
    CTX3 --> UNIFIED_CTX

    CONFIG1 --> UNIFIED_CONFIG
    CONFIG2 --> UNIFIED_CONFIG

    style HUB fill:#42b883
    style UNIFIED_REG fill:#646cff
    style SHARED_TOOLS fill:#f59e0b
```

---

## Part 8: Technology Stack Distribution

```mermaid
pie title Technology Stack Distribution
    "Python" : 70
    "TypeScript" : 20
    "Rust" : 7
    "Go" : 3
```

---

## Part 9: Component Interaction Flow

```mermaid
graph LR
    A[User Request] --> B{Request Type}
    B -->|CLI| C[CLI Handler]
    B -->|Voice| D[Voice Handler]
    B -->|Web| E[Web Handler]

    C --> F[Orchestrator]
    D --> F
    E --> F

    F --> G{Agent Selection}
    G -->|Specialized| H[Specialized Agent]
    G -->|General| I[General Agent]

    H --> J[Tool Selection]
    I --> J

    J -->|MCP| K[MCP Server]
    J -->|CLI| L[CLI Tool]
    J -->|Custom| M[Custom Tool]

    K --> N[Execute Tool]
    L --> N
    M --> N

    N --> O[Process Result]
    O --> P[Update State]
    P --> Q[Return Response]
    Q --> A
```

---

## Part 10: Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        DEV_ENV[Development Environment]
        DEV_TOOLS[Development Tools]
    end

    subgraph "CI/CD"
        GITHUB[GitHub Actions]
        TESTS[Test Suite]
        BUILD[Build System]
    end

    subgraph "Staging"
        STAGING[Staging Environment]
        STAGING_DB[(Staging DB)]
    end

    subgraph "Production"
        PROD[Production Environment]
        PROD_DB[(Production DB)]
        MONITORING[Monitoring]
        LOGGING[Logging]
    end

    DEV_ENV --> GITHUB
    DEV_TOOLS --> GITHUB

    GITHUB --> TESTS
    TESTS --> BUILD

    BUILD --> STAGING
    STAGING --> STAGING_DB

    STAGING --> PROD
    PROD --> PROD_DB
    PROD --> MONITORING
    PROD --> LOGGING

    style PROD fill:#42b883
    style MONITORING fill:#f59e0b
```

---

## Part 11: Key Architectural Patterns

### Pattern 1: Hub-and-Spoke (Current)

```
        Orchestrator (Hub)
              |
    +---------+---------+
    |         |         |
  Agent1   Agent2   Agent3
    |         |         |
  Tools    Tools    Tools
```

### Pattern 2: Mesh (Proposed)

```
  Agent1 <--> Agent2
    |           |
    v           v
  Agent3 <--> Agent4
    |           |
    v           v
  Tools      Tools
```

### Pattern 3: Hybrid (Recommended)

```
        Root Orchestrator
              |
    +---------+---------+
    |         |         |
  Group1   Group2   Group3
    |         |         |
  Mesh      Mesh      Mesh
```

---

## Part 12: Scalability Architecture

```mermaid
graph TB
    subgraph "Horizontal Scaling"
        LB[Load Balancer]
        INST1[Instance 1]
        INST2[Instance 2]
        INST3[Instance N]
    end

    subgraph "Vertical Scaling"
        CACHE[(Distributed Cache)]
        QUEUE[Message Queue]
    end

    subgraph "Data Scaling"
        SHARD1[(Shard 1)]
        SHARD2[(Shard 2)]
        SHARD3[(Shard N)]
    end

    LB --> INST1
    LB --> INST2
    LB --> INST3

    INST1 --> CACHE
    INST2 --> CACHE
    INST3 --> CACHE

    INST1 --> QUEUE
    INST2 --> QUEUE
    INST3 --> QUEUE

    QUEUE --> SHARD1
    QUEUE --> SHARD2
    QUEUE --> SHARD3

    style LB fill:#42b883
    style CACHE fill:#646cff
```

---

## See Also

- [KUSH_ECOSYSTEM_DEEP_DIVE.md](./KUSH_ECOSYSTEM_DEEP_DIVE.md) - Detailed ecosystem analysis
- [KUSH_ECOSYSTEM_UNIFIED_DOCS_INDEX.md](./KUSH_ECOSYSTEM_UNIFIED_DOCS_INDEX.md) - Documentation index
- [UNIFIED_AGENT_REGISTRY_API.md](./UNIFIED_AGENT_REGISTRY_API.md) - Agent registry API design
- [SHARED_MCP_TOOL_LIBRARY.md](./SHARED_MCP_TOOL_LIBRARY.md) - Shared MCP tools design
- [CROSS_PROJECT_INTEGRATION_GUIDE.md](./CROSS_PROJECT_INTEGRATION_GUIDE.md) - Integration guide

---

**Status**: 🏗️ **ARCHITECTURE DIAGRAM COMPLETE** - Comprehensive visual architecture documentation
