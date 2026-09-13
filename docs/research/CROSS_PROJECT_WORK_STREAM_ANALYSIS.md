<DONE>
# Cross-Project Work Stream Analysis

> **Status**: 🔍 **ANALYSIS COMPLETE** | **Date**: 2026-02-18
> **Purpose**: Cross-analyze unified work streams, features, and research plans across kush ecosystem projects to identify borrowing opportunities

---

## Executive Summary

This document analyzes work streams, features, and research plans across **8 active projects** in the kush ecosystem:

1. **thegent** - Unified agent orchestration (most active)
2. **heliosShield** - Agent harness with governance (very structured)
3. **plangent** - Multi-agent orchestration (TypeScript)
4. **kimaki** - Voice AI multi-agent system (complete)
5. **smolgents** - Microagent delegation (production-ready)
6. **trace** - Traceability MCP server (planning complete)
7. **dphi** - Package discovery + code research (active planning)
8. **usage** - AI usage tracking (migration in progress)

**Key Finding**: Projects demonstrate **mature patterns** that can be borrowed:

- **heliosShield's P0-P4 priority system** → Adopt across all projects
- **thegent's unified work stream** → Template for others
- **smolgents' cost optimization patterns** → Apply to other agent systems
- **trace's comprehensive planning** → Model for MCP servers

---

## Part 1: Work Stream Structures

### 1.1 thegent (Most Active)

**File**: `docs/reference/WORK_STREAM.md`

**Structure**:

- **BACKLOG** - Not started items with priority (P1-P2)
- **CLAIMED** - Active work with agent ID and timestamp
- **COMPLETED** - Finished items with completion date
- **Research Docs Extended** - Batch tracking

**Key Features**:

- ✅ Agent-based claiming system
- ✅ Dependency tracking (`Depends` column)
- ✅ Source file references
- ✅ Research doc integration
- ✅ Auto-incorporation workflow

**Strengths**:

- Most comprehensive tracking
- Clear agent accountability
- Research integration
- Dependency management

**Borrowable**:

- Agent claiming pattern
- Research doc integration
- Dependency tracking format

---

### 1.2 heliosShield (Most Structured)

**File**: `docs/unified/BACKLOG.md`

**Structure**:

- **P0: Blockers** - Critical path items
- **P1: Features** - High-value features (1 sprint SLA)
- **P2: Polish** - Quality improvements (2 sprint SLA)
- **P3: Research** - Investigation (3 sprint SLA)
- **P4: Icebox** - Long-term ideas (no SLA)
- **Recently Completed** - Last 30 days

**Key Features**:

- ✅ SLA-based priority system
- ✅ Module categorization
- ✅ Dependency tracking
- ✅ Feature Request (FR) linking
- ✅ Status tracking (Planned, Blocked, etc.)
- ✅ Metrics summary

**Strengths**:

- Clear priority definitions
- SLA enforcement
- Module organization
- Feature request traceability

**Borrowable**:

- **P0-P4 priority system** → Adopt everywhere
- SLA definitions
- Module categorization
- Feature request linking
- Metrics tracking

---

### 1.3 plangent (TypeScript Project)

**File**: `docs/reference/PROJECT_SUMMARY.md`, `docs/planning/`

**Structure**:

- Phase-based planning (6 phases)
- User stories (US-1 to US-5)
- Adapter pattern focus
- AgilePlus governance

**Key Features**:

- ✅ Phase-based roadmap
- ✅ User story tracking
- ✅ Adapter pattern documentation
- ✅ Testing matrix

**Strengths**:

- Clear phase boundaries
- User story focus
- Architecture-first approach

**Borrowable**:

- Phase-based planning structure
- User story format
- Adapter pattern documentation

---

### 1.4 kimaki (Complete Implementation)

**File**: `IMPLEMENTATION-SUMMARY.md`, `COMPREHENSIVE-MULTI-AGENT-PLAN.md`

**Structure**:

- Multi-phase implementation
- User stories (1-4)
- Component tracking
- Status badges

**Key Features**:

- ✅ Multi-phase tracking
- ✅ Component-level status
- ✅ Implementation files tracking
- ✅ Quick reference

**Strengths**:

- Clear completion tracking
- Component organization
- Implementation focus

**Borrowable**:

- Status badge system
- Component tracking
- Quick reference format

---

### 1.5 smolgents (Production-Ready)

**File**: `STAGE3_IMPLEMENTATION_ROADMAP.md`, `agileplus/project.md`

**Structure**:

- Stage-based roadmap (Stage 1-3)
- User stories with point estimates
- Sprint planning
- Critical path analysis

**Key Features**:

- ✅ Story point estimation
- ✅ Sprint-based planning
- ✅ Critical path identification
- ✅ Resource allocation
- ✅ Go/No-Go criteria

**Strengths**:

- Detailed estimation
- Sprint planning
- Risk management
- Resource planning

**Borrowable**:

- Story point system
- Sprint planning format
- Critical path analysis
- Go/No-Go criteria

---

### 1.6 trace (MCP Server)

**File**: `scripts/mcp/COMPLETE_TRACERTM_ROADMAP_UPDATED.md`

**Structure**:

- Phase-based (Phase 1-4)
- Tool/Resource/Prompt categorization
- Feature count tracking
- Effort estimation (days)

**Key Features**:

- ✅ Phase completion tracking
- ✅ Feature categorization
- ✅ Effort estimation
- ✅ Integration planning

**Strengths**:

- Clear phase boundaries
- Feature organization
- Effort tracking

**Borrowable**:

- Phase completion format
- Feature categorization
- Effort estimation approach

---

### 1.7 dphi (Active Planning)

**File**: `agileplus/changes/add-unified-mcp-composition-server/tasks.md`

**Structure**:

- Task-based (10 sections)
- Numbered subtasks (1.1, 1.2, etc.)
- Workflow-focused
- Integration planning

**Key Features**:

- ✅ Task breakdown
- ✅ Workflow design
- ✅ Integration focus
- ✅ Testing planning

**Strengths**:

- Detailed task breakdown
- Workflow orientation
- Integration planning

**Borrowable**:

- Task numbering system
- Workflow documentation
- Integration planning format

---

### 1.8 usage (Migration Project)

**File**: `todo.md`

**Structure**:

- Simple numbered list
- Migration-focused
- Provider logic extraction

**Key Features**:

- ✅ Simple tracking
- ✅ Migration focus
- ✅ Provider extraction plan

**Strengths**:

- Simple format
- Clear migration path

**Borrowable**:

- Simple list format (for small projects)

---

## Part 2: Feature Cross-Analysis

### 2.1 Priority Systems

| Project          | Priority System  | Strengths                          | Borrowable                   |
| ---------------- | ---------------- | ---------------------------------- | ---------------------------- |
| **heliosShield** | P0-P4 with SLAs  | Clear definitions, SLA enforcement | ✅ **Adopt everywhere**      |
| **thegent**      | P1-P2 (implicit) | Simple, flexible                   | Use for lightweight projects |
| **smolgents**    | Story points     | Detailed estimation                | Use for complex projects     |
| **trace**        | Phase-based      | Clear boundaries                   | Use for MCP servers          |

**Recommendation**: **Adopt heliosShield's P0-P4 system** across all projects.

---

### 2.2 Dependency Tracking

| Project          | Dependency Format      | Strengths            |
| ---------------- | ---------------------- | -------------------- |
| **thegent**      | `Depends` column       | Clear, explicit      |
| **heliosShield** | `Depends On` column    | Links to other items |
| **smolgents**    | Critical path analysis | Visual dependencies  |

**Recommendation**: **Use thegent's `Depends` column format** with heliosShield's linking.

---

### 2.3 Status Tracking

| Project          | Status System                 | Strengths       |
| ---------------- | ----------------------------- | --------------- |
| **heliosShield** | Planned, Blocked, In Progress | Clear states    |
| **thegent**      | BACKLOG, CLAIMED, COMPLETED   | Simple workflow |
| **kimaki**       | Status badges (✅, 🚧, 📋)    | Visual          |

**Recommendation**: **Combine heliosShield's states with kimaki's badges**.

---

### 2.4 Research Integration

| Project          | Research Tracking        | Strengths     |
| ---------------- | ------------------------ | ------------- |
| **thegent**      | Research doc integration | Comprehensive |
| **heliosShield** | Research doc references  | Linked        |
| **smolgents**    | Stage-based research     | Phased        |

**Recommendation**: **Adopt thegent's research doc integration**.

---

## Part 3: Borrowable Features by Category

### 3.1 Governance & Quality (from heliosShield)

**Features**:

- ✅ Methodology enforcer (TDD/BDD/Contract/Property)
- ✅ Reliability gate (flaky quarantine, SLO)
- ✅ Supply chain gate (SBOM, attestations)
- ✅ Typed agent claim runtime enforcement
- ✅ SARIF ingestion adapter

**Borrowable To**:

- **thegent** - Agent governance
- **plangent** - Task validation
- **smolgents** - Quality gates
- **trace** - Completion validation

---

### 3.2 Cost Optimization (from smolgents)

**Features**:

- ✅ Intelligent model routing
- ✅ Cost-aware task delegation
- ✅ Performance metrics
- ✅ Cost tracking

**Borrowable To**:

- **thegent** - Agent cost tracking
- **plangent** - Sub-agent routing
- **kimaki** - Voice cost optimization
- **usage** - Usage tracking integration

---

### 3.3 Multi-Agent Patterns (from plangent, kimaki)

**Features**:

- ✅ Root agent + sub-agents pattern
- ✅ Agent pause/resume mechanisms
- ✅ Agent-to-agent collaboration
- ✅ Conversation rules engine
- ✅ Project context management

**Borrowable To**:

- **thegent** - Multi-agent orchestration
- **smolgents** - Delegation patterns
- **trace** - Agent integration

---

### 3.4 MCP Server Patterns (from trace, dphi)

**Features**:

- ✅ Tool/Resource/Prompt categorization
- ✅ Unified MCP composition
- ✅ Cross-service orchestration
- ✅ Health monitoring

**Borrowable To**:

- **thegent** - MCP server management
- **atoms-mcp-prod** - Composition patterns
- **zen-mcp-server** - Tool organization

---

### 3.5 Documentation Patterns (from thegent)

**Features**:

- ✅ VitePress rich documentation
- ✅ Auto-generated API docs
- ✅ Architecture diagrams
- ✅ LLM-friendly docs

**Borrowable To**:

- **heliosShield** - Documentation system
- **plangent** - API documentation
- **smolgents** - Usage guides
- **trace** - MCP documentation

---

## Part 4: Research Plan Cross-Analysis

### 4.1 Active Research Areas

| Project          | Research Focus                        | Status   | Borrowable |
| ---------------- | ------------------------------------- | -------- | ---------- |
| **thegent**      | Cross-platform, governance, FastMCP   | Active   | ✅         |
| **heliosShield** | LLM gates, chaos engineering          | Active   | ✅         |
| **smolgents**    | Cost optimization, routing            | Complete | ✅         |
| **trace**        | MCP integration, BMM/AgilePlus        | Planning | ✅         |
| **dphi**         | MCP composition, workflow integration | Active   | ✅         |

---

### 4.2 Research Patterns to Borrow

**From heliosShield**:

- LLM-as-judge gate feasibility
- Small local model gate (Ollama)
- Chaos Toolkit experiment format
- MLX-optimized inference

**From smolgents**:

- Cost routing research
- Model tier strategy
- Delegation patterns

**From thegent**:

- Cross-platform research
- Governance evolution
- FastMCP patterns

**From trace**:

- AgilePlus integration
- Completion validation research
- Progress tracking patterns

---

## Part 5: Implementation Recommendations

### 5.1 Immediate Actions

1. **Adopt heliosShield's P0-P4 priority system** across all projects
   - Standardize priority definitions
   - Add SLA tracking
   - Implement module categorization

2. **Borrow thegent's research integration** pattern
   - Link research docs to work items
   - Track research doc extensions
   - Auto-incorporation workflow

3. **Adopt smolgents' cost optimization** patterns
   - Model routing strategies
   - Cost tracking
   - Performance metrics

---

### 5.2 Short-Term Actions

1. **Create unified work stream template**
   - Based on thegent's structure
   - Incorporate heliosShield's priority system
   - Add kimaki's status badges

2. **Cross-project feature borrowing**
   - Governance gates → thegent, plangent
   - Cost optimization → all agent projects
   - MCP patterns → all MCP servers

3. **Research plan consolidation**
   - Identify overlapping research
   - Share findings across projects
   - Avoid duplicate work

---

### 5.3 Long-Term Actions

1. **Unified work stream API**
   - Cross-project visibility
   - Dependency tracking
   - Status aggregation

2. **Feature registry**
   - Catalog borrowable features
   - Track adoption
   - Share patterns

3. **Research collaboration**
   - Shared research repository
   - Cross-project findings
   - Consolidated knowledge base

---

## Part 6: Priority Matrix

### High Priority Borrows

| Feature               | Source       | Target Projects                | Impact |
| --------------------- | ------------ | ------------------------------ | ------ |
| P0-P4 Priority System | heliosShield | All projects                   | High   |
| Research Integration  | thegent      | All projects                   | High   |
| Cost Optimization     | smolgents    | thegent, plangent, kimaki      | High   |
| Governance Gates      | heliosShield | thegent, plangent              | High   |
| MCP Composition       | trace, dphi  | atoms-mcp-prod, zen-mcp-server | Medium |

---

## Part 7: Work Stream Template

### Recommended Unified Structure

```markdown
# [Project] Unified Work Stream

## Priority Definitions

- P0: Blocker (Immediate)
- P1: Feature (1 sprint)
- P2: Polish (2 sprints)
- P3: Research (3 sprints)
- P4: Icebox (No SLA)

## BACKLOG

| ID  | Title | Source | Priority | Depends | Module |
| --- | ----- | ------ | -------- | ------- | ------ |
| ... | ...   | ...    | ...      | ...     | ...    |

## CLAIMED

| ID  | Agent | Started |
| --- | ----- | ------- |
| ... | ...   | ...     |

## COMPLETED

| ID  | Completed | Notes |
| --- | --------- | ----- |
| ... | ...       | ...   |

## Research Integration

| Doc | Extensions | Status |
| --- | ---------- | ------ |
| ... | ...        | ...    |
```

---

## See Also

- [KUSH_ECOSYSTEM_DEEP_DIVE.md](./KUSH_ECOSYSTEM_DEEP_DIVE.md) - Ecosystem overview
- [CROSS_PROJECT_DEEP_EXPANDED_ANALYSIS.md](./CROSS_PROJECT_DEEP_EXPANDED_ANALYSIS.md) - **EXPANDED** Deep analysis with testing, deployment, monitoring, security patterns
- [CROSS_PROJECT_INTEGRATION_GUIDE.md](./CROSS_PROJECT_INTEGRATION_GUIDE.md) - Integration guide
- [UNIFIED_AGENT_REGISTRY_API.md](./UNIFIED_AGENT_REGISTRY_API.md) - Agent registry design

---

**Status**: 🔍 **ANALYSIS COMPLETE** - Expanded analysis available in CROSS_PROJECT_DEEP_EXPANDED_ANALYSIS.md
