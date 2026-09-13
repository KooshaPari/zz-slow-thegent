<DONE>
# Cross-Project Feature Borrowing Plan

> **Status**: 📋 **IMPLEMENTATION PLAN** | **Date**: 2026-02-18
> **Purpose**: Detailed plan for borrowing and adapting features across kush ecosystem projects

---

## Executive Summary

This plan details **specific features** that can be borrowed from more active/recent projects and adapted to other projects in the ecosystem. Based on cross-project analysis, we've identified **25+ borrowable features** across **5 categories**.

---

## Part 1: Priority System Adoption

### 1.1 Borrow: heliosShield's P0-P4 System

**Source**: `heliosShield/docs/unified/BACKLOG.md`

**Target Projects**: All projects

**Implementation**:

1. **Add Priority Definitions** to each project's work stream:

   ```markdown
   ## Priority Definitions

   | Priority | Name     | SLA       | Description           |
   | -------- | -------- | --------- | --------------------- |
   | P0       | Blocker  | Immediate | Blocks all other work |
   | P1       | Feature  | 1 sprint  | High-value features   |
   | P2       | Polish   | 2 sprints | Quality improvements  |
   | P3       | Research | 3 sprints | Investigation needed  |
   | P4       | Icebox   | No SLA    | Long-term ideas       |
   ```

2. **Categorize Existing Items**:
   - Review current backlog
   - Assign priorities
   - Add SLA tracking

3. **Update Work Stream Format**:
   - Add Priority column
   - Add Module column
   - Add Status column

**Effort**: 2-4 hours per project

**Priority**: P1

### 1.2 Backlog Schema Borrowing (heliosguard backlog/priority closure)

To close `borrow-heliosguard-priority` and `borrow-heliosguard-backlog`, this plan standardizes the minimum backlog schema borrowed from heliosShield-style governance:

| Column       | Required    | Purpose                                             |
| ------------ | ----------- | --------------------------------------------------- |
| `ID`         | Yes         | Stable work item identifier                         |
| `Priority`   | Yes         | P0-P4 operational urgency                           |
| `Module`     | Yes         | Owning subsystem/domain                             |
| `SLA`        | Yes         | Expected response/completion window                 |
| `Status`     | Yes         | `todo`, `claimed`, `in_progress`, `blocked`, `done` |
| `Depends On` | Recommended | DAG predecessor IDs                                 |
| `Evidence`   | Recommended | Validation command, artifact path, or report link   |

Recommended row format:

```markdown
| ID     | Priority | Module     | SLA      | Status      | Depends On | Evidence                 |
| ------ | -------- | ---------- | -------- | ----------- | ---------- | ------------------------ |
| WG-001 | P1       | delegation | 1 sprint | in_progress | WG-000     | docs/reports/<report>.md |
```

---

## Part 2: Governance Features

### 2.1 Borrow: Methodology Enforcer (heliosShield FT-001)

**Source**: `heliosShield/docs/unified/BACKLOG.md` (FT-001)

**Target Projects**: thegent, plangent, smolgents

**Feature**: Enforce TDD/BDD/Contract/Property testing methodologies

**Implementation**:

- Add methodology gates
- Integrate with agent workflows
- Add validation rules

**Effort**: 1-2 weeks

**Priority**: P1

---

### 2.2 Borrow: Reliability Gate (heliosShield FT-002)

**Source**: `heliosShield/docs/unified/BACKLOG.md` (FT-002)

**Target Projects**: thegent, plangent, smolgents, trace

**Feature**: Flaky test quarantine, SLO tracking

**Implementation**:

- Add flaky test detection
- Implement quarantine system
- Add SLO tracking

**Effort**: 1-2 weeks

**Priority**: P1

---

### 2.3 Borrow: Typed Agent Claim Enforcement (heliosShield FT-004)

**Source**: `heliosShield/docs/unified/BACKLOG.md` (FT-004)

**Target Projects**: thegent, plangent, kimaki

**Feature**: Runtime enforcement of typed agent claims

**Implementation**:

- Add type checking for agent claims
- Runtime validation
- Error handling

**Effort**: 1 week

**Priority**: P1

---

## Part 3: Cost Optimization

### 3.1 Borrow: Intelligent Model Routing (smolgents)

**Source**: `smolgents/STAGE3_IMPLEMENTATION_ROADMAP.md`

**Target Projects**: thegent, plangent, kimaki

**Feature**: Route tasks to cost-optimal models

**Implementation**:

- Add model tier classification
- Implement routing logic
- Add cost tracking

**Effort**: 2-3 weeks

**Priority**: P1

---

### 3.2 Borrow: Cost Tracking & Metrics (smolgents)

**Source**: `smolgents/agileplus/project.md`

**Target Projects**: thegent, plangent, kimaki, usage

**Feature**: Track and report cost metrics

**Implementation**:

- Integrate with usage tracking
- Add cost dashboards
- Implement alerts

**Effort**: 1-2 weeks

**Priority**: P1

---

## Part 4: Multi-Agent Patterns

### 4.1 Borrow: Root Agent + Sub-Agents Pattern (plangent)

**Source**: `plangent/docs/reference/PROJECT_SUMMARY.md`

**Target Projects**: thegent, smolgents

**Feature**: Hierarchical agent architecture

**Implementation**:

- Add root agent coordinator
- Implement sub-agent spawning
- Add coordination logic

**Effort**: 2-3 weeks

**Priority**: P2

---

### 4.2 Borrow: Agent Pause/Resume (plangent, kimaki)

**Source**: `plangent/docs/reference/PROJECT_SUMMARY.md`, `kimaki/IMPLEMENTATION-SUMMARY.md`

**Target Projects**: thegent, smolgents

**Feature**: Checkpoint-based agent resumption

**Implementation**:

- Add checkpoint system
- Implement pause/resume
- Add state persistence

**Effort**: 2-3 weeks

**Priority**: P2

---

### 4.3 Borrow: Conversation Rules Engine (kimaki)

**Source**: `kimaki/COMPREHENSIVE-MULTI-AGENT-PLAN.md`

**Target Projects**: thegent, plangent

**Feature**: Rules for agent-to-agent collaboration

**Implementation**:

- Add rules engine
- Implement collaboration modes
- Add moderation

**Effort**: 2-3 weeks

**Priority**: P2

---

## Part 5: MCP Server Patterns

### 5.1 Borrow: Tool/Resource/Prompt Categorization (trace)

**Source**: `trace/scripts/mcp/COMPLETE_TRACERTM_ROADMAP_UPDATED.md`

**Target Projects**: atoms-mcp-prod, zen-mcp-server, dphi

**Feature**: Organize MCP capabilities by type

**Implementation**:

- Categorize existing tools
- Add resource support
- Add prompt templates

**Effort**: 1-2 weeks

**Priority**: P1

---

### 5.2 Borrow: Unified MCP Composition (dphi)

**Source**: `dphi/agileplus/changes/add-unified-mcp-composition-server/tasks.md`

**Target Projects**: thegent, atoms-mcp-prod, zen-mcp-server

**Feature**: Compose multiple MCP servers

**Implementation**:

- Add composition layer
- Implement routing
- Add health monitoring

**Effort**: 2-3 weeks

**Priority**: P1

---

### 5.3 Borrow: Cross-Service Orchestration (dphi)

**Source**: `dphi/agileplus/changes/add-unified-mcp-composition-server/tasks.md`

**Target Projects**: thegent, plangent

**Feature**: Orchestrate across multiple services

**Implementation**:

- Add orchestration layer
- Implement query optimization
- Add result synthesis

**Effort**: 2-3 weeks

**Priority**: P2

---

## Part 6: Documentation Patterns

### 6.1 Borrow: VitePress Rich Documentation (thegent)

**Source**: `thegent/docs/guides/VITEPRESS_USAGE_GUIDE.md`

**Target Projects**: heliosShield, plangent, smolgents, trace

**Feature**: Rich documentation with diagrams, code playgrounds, demos

**Implementation**:

- Set up VitePress
- Add Mermaid support
- Add CodePlayground component
- Add demo GIFs

**Effort**: 1-2 weeks per project

**Priority**: P2

---

### 6.2 Borrow: Auto-Generated API Docs (thegent)

**Source**: `thegent/scripts/generate-api-docs.py`

**Target Projects**: heliosShield, plangent, smolgents

**Feature**: Auto-generate API docs from docstrings

**Implementation**:

- Add docstring parser
- Generate markdown
- Integrate with docs

**Effort**: 1 week per project

**Priority**: P2

---

## Part 7: Research Integration

### 7.1 Borrow: Research Doc Integration (thegent)

**Source**: `thegent/docs/reference/WORK_STREAM.md`

**Target Projects**: All projects

**Feature**: Link research docs to work items

**Implementation**:

- Add research doc references
- Track extensions
- Add auto-incorporation

**Effort**: 1 week per project

**Priority**: P1

---

## Part 8: Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

1. **Adopt Priority System** (all projects)
   - Add P0-P4 definitions
   - Categorize existing items
   - Update work streams

2. **Research Integration** (all projects)
   - Link research docs
   - Track extensions
   - Add references

**Deliverables**:

- Updated work streams
- Research doc links
- Priority categorization

---

### Phase 2: High-Value Features (Weeks 3-6)

1. **Governance Features** (thegent, plangent)
   - Methodology enforcer
   - Reliability gate
   - Typed agent claims

2. **Cost Optimization** (thegent, plangent, kimaki)
   - Model routing
   - Cost tracking
   - Metrics

**Deliverables**:

- Governance gates implemented
- Cost tracking integrated
- Metrics dashboards

---

### Phase 3: Patterns & Integration (Weeks 7-10)

1. **Multi-Agent Patterns** (thegent, smolgents)
   - Root agent pattern
   - Pause/resume
   - Conversation rules

2. **MCP Patterns** (atoms-mcp-prod, zen-mcp-server)
   - Tool categorization
   - Composition
   - Orchestration

**Deliverables**:

- Multi-agent patterns implemented
- MCP composition working
- Cross-service orchestration

---

### Phase 4: Documentation (Weeks 11-12)

1. **Rich Documentation** (heliosShield, plangent, smolgents)
   - VitePress setup
   - Auto-generated docs
   - Examples

**Deliverables**:

- Documentation sites
- API docs generated
- Usage guides

---

## Part 9: Success Metrics

### Adoption Metrics

- **Priority System**: 100% of projects using P0-P4
- **Research Integration**: 100% of projects linking research docs
- **Governance Features**: 3+ projects with gates
- **Cost Optimization**: 3+ projects tracking costs
- **Documentation**: 4+ projects with rich docs

### Quality Metrics

- **Work Stream Clarity**: Improved organization
- **Feature Reuse**: Reduced duplicate work
- **Knowledge Sharing**: Increased cross-project learning

---

## See Also

- [CROSS_PROJECT_WORK_STREAM_ANALYSIS.md](./CROSS_PROJECT_WORK_STREAM_ANALYSIS.md) - Analysis
- [CROSS_PROJECT_DEEP_EXPANDED_ANALYSIS.md](./CROSS_PROJECT_DEEP_EXPANDED_ANALYSIS.md) - **EXPANDED** Deep analysis with 50+ features, testing/deployment/monitoring/security patterns
- [KUSH_ECOSYSTEM_DEEP_DIVE.md](./KUSH_ECOSYSTEM_DEEP_DIVE.md) - Ecosystem overview
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream

---

**Status**: 📋 **IMPLEMENTATION PLAN READY** - Expanded analysis available with 50+ features identified
