<DONE>
# Agent Hierarchy and Team Structure

> **Date**: 2026-02-18
> **Status**: Research-Validated Design
> **Purpose**: Define agent role hierarchy, parent-child relationships, and team mappings

---

## Executive Summary

This document defines a comprehensive agent hierarchy system for `thegent` that enables:
- **Hierarchical delegation**: Manager → Subagent relationships with clear ownership
- **Team-based organization**: Agents grouped into teams with tighter coordination
- **Cross-team interaction**: Agents can interact across teams while maintaining team boundaries
- **Role-based capabilities**: Specialized roles with defined responsibilities and permissions

**Research Validation**: This design has been validated through extensive research:
- ✅ **Local Codebase**: 3 coordination strategies, multiple framework implementations, production patterns
- ✅ **Web Frameworks**: CrewAI hierarchical process, MetaGPT role-based teams, LangGraph stateful workflows, AutoGen multi-agent orchestration
- ✅ **Academic Research**: Cursor Planner-Worker-Judge hierarchy, MetaGPT global message pool
- ✅ **Production Systems**: Claude Code Teams, heliosShield coordination, SmolGents execution modes

**See**: [RESEARCH_SYNTHESIS.md](./RESEARCH_SYNTHESIS.md) for complete research validation.

---

## 1. Agent Role Hierarchy

### 1.1 Role Levels

```
┌─────────────────────────────────────────────────────────┐
│ Level 0: User (Human)                                   │
│   - Ultimate authority and decision maker                │
│   - Can override any agent decision                      │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ Level 1: Executive / Orchestrator                       │
│   - Primary interface with user                          │
│   - Strategic planning and coordination                  │
│   - Examples: "sitback", "manager", "orchestrator"      │
└─────────────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Level 2:      │ │ Level 2:      │ │ Level 2:      │
│ Team Lead     │ │ Team Lead     │ │ Team Lead     │
│ (Frontend)    │ │ (Backend)     │ │ (DevOps)      │
└───────────────┘ └───────────────┘ └───────────────┘
        │               │               │
        ▼               ▼               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Level 3:      │ │ Level 3:      │ │ Level 3:      │
│ Specialist    │ │ Specialist    │ │ Specialist    │
│ Agents        │ │ Agents        │ │ Agents        │
└───────────────┘ └───────────────┘ └───────────────┘
```

### 1.2 Role Definitions

#### Level 1: Executive / Orchestrator
- **Purpose**: Primary agent that interfaces with the user
- **Responsibilities**:
  - Understand user intent and requirements
  - Break down complex tasks into sub-tasks
  - Coordinate multiple teams
  - Make strategic decisions
  - Monitor overall progress
- **Capabilities**:
  - Can delegate to any team lead or specialist
  - Can create new teams dynamically
  - Can escalate to user
  - Full visibility into all teams
- **Examples**: `sitback`, `manager`, `orchestrator`

#### Level 2: Team Lead
- **Purpose**: Manages a specialized team of agents
- **Responsibilities**:
  - Coordinate team members
  - Assign tasks within team
  - Ensure team quality standards
  - Report progress to orchestrator
- **Capabilities**:
  - Can delegate to team specialists
  - Can request resources from orchestrator
  - Can coordinate with other team leads
  - Limited visibility (own team + cross-team requests)
- **Examples**: `frontend-lead`, `backend-lead`, `devops-lead`, `qa-lead`

#### Level 3: Specialist
- **Purpose**: Execute specific tasks within domain expertise
- **Responsibilities**:
  - Complete assigned tasks
  - Report to team lead
  - Collaborate with other specialists
- **Capabilities**:
  - Execute tasks within expertise
  - Request help from team lead
  - Limited delegation (to peers or lower-level specialists)
  - Visibility limited to own work + team context
- **Examples**: `coder`, `researcher`, `reviewer`, `tester`, `designer`

---

## 2. Parent-Child Relationships

### 2.1 Relationship Model

Each agent maintains explicit parent-child relationships:

```python
@dataclass
class AgentRelationship:
    """Parent-child relationship between agents."""

    parent_id: str  # Parent agent run ID
    child_id: str  # Child agent run ID
    relationship_type: str  # "direct", "team", "cross-team"
    created_at: datetime
    status: str  # "active", "completed", "failed"

    # Delegation context
    task_id: Optional[str] = None
    delegation_prompt: Optional[str] = None
    handoff_context: Optional[dict] = None
```

### 2.2 Relationship Types

#### Direct Parent-Child
- **Definition**: Explicit delegation from parent to child
- **Characteristics**:
  - Parent directly spawns child
  - Child reports directly to parent
  - Strong ownership and accountability
- **Example**: Orchestrator → Team Lead → Specialist

#### Team Membership
- **Definition**: Agents working within same team
- **Characteristics**:
  - Shared team context
  - Team lead coordinates
  - Peer-to-peer collaboration
- **Example**: Frontend team (lead + 3 specialists)

#### Cross-Team Collaboration
- **Definition**: Agents from different teams working together
- **Characteristics**:
  - Requires explicit coordination
  - Team leads mediate
  - Temporary relationships
- **Example**: Frontend specialist + Backend specialist on API contract

### 2.3 Relationship Graph

```
Orchestrator (sitback)
├── Direct Child: Frontend Team Lead
│   ├── Direct Child: React Specialist
│   ├── Direct Child: CSS Specialist
│   └── Team Member: TypeScript Specialist
│
├── Direct Child: Backend Team Lead
│   ├── Direct Child: API Specialist
│   ├── Direct Child: Database Specialist
│   └── Team Member: Auth Specialist
│
└── Direct Child: DevOps Team Lead
    ├── Direct Child: CI/CD Specialist
    └── Team Member: Infrastructure Specialist

Cross-Team Relationships:
- React Specialist ↔ API Specialist (collaboration)
- Frontend Lead ↔ Backend Lead (coordination)
```

---

## 3. Team Structure and Mappings

### 3.1 Team Definition

```python
@dataclass
class AgentTeam:
    """A team of agents working together."""

    team_id: str
    name: str
    description: str

    # Team composition
    lead_id: str  # Team lead agent ID
    members: list[str]  # Specialist agent IDs

    # Team boundaries
    team_type: str  # "functional", "project", "ad-hoc"
    boundaries: dict[str, Any]  # Access control, resource limits

    # Team coordination
    coordination_mode: str  # "hierarchical", "collaborative", "swarm"
    communication_channels: list[str]  # How team communicates

    # Metadata
    created_at: datetime
    status: str  # "active", "paused", "completed"
```

### 3.2 Team Types

#### Functional Teams
- **Purpose**: Long-lived teams organized by domain expertise
- **Examples**:
  - Frontend Team (React, CSS, TypeScript specialists)
  - Backend Team (API, Database, Auth specialists)
  - DevOps Team (CI/CD, Infrastructure specialists)
- **Characteristics**:
  - Stable membership
  - Deep domain expertise
  - Reusable across projects

#### Project Teams
- **Purpose**: Temporary teams for specific projects
- **Examples**:
  - "E-commerce MVP Team" (Frontend + Backend + DevOps)
  - "Mobile App Team" (Mobile + Backend + Design)
- **Characteristics**:
  - Project-scoped
  - Cross-functional
  - Disband after project completion

#### Ad-Hoc Teams
- **Purpose**: Temporary teams for specific tasks
- **Examples**:
  - "Security Audit Team" (Security specialists from multiple teams)
  - "Performance Optimization Team" (Performance specialists)
- **Characteristics**:
  - Task-scoped
  - Dynamic membership
  - Short-lived

### 3.3 Team Coordination Modes

#### Hierarchical
- **Structure**: Team Lead → Specialists
- **Use Case**: Clear task breakdown, sequential dependencies
- **Communication**: Top-down delegation, bottom-up reporting

#### Collaborative
- **Structure**: Peer-to-peer collaboration
- **Use Case**: Complex problems requiring multiple perspectives
- **Communication**: Shared context, consensus building

#### Swarm
- **Structure**: Many agents working in parallel
- **Use Case**: Independent tasks, exploration, testing
- **Communication**: Minimal coordination, result aggregation

---

## 4. Cross-Team Interaction

### 4.1 Interaction Patterns

#### Direct Collaboration
- **Pattern**: Specialist ↔ Specialist (cross-team)
- **Mechanism**: Explicit handoff with context
- **Example**: Frontend specialist needs API contract from Backend specialist
- **Protocol**: XML-based handoff with structured context

#### Mediated Collaboration
- **Pattern**: Team Lead ↔ Team Lead
- **Mechanism**: Coordination through team leads
- **Example**: Frontend Lead coordinates with Backend Lead on API design
- **Protocol**: Structured coordination messages

#### Orchestrated Collaboration
- **Pattern**: Orchestrator coordinates multiple teams
- **Mechanism**: Top-down coordination
- **Example**: Orchestrator coordinates Frontend + Backend + DevOps for deployment
- **Protocol**: Task decomposition and assignment

### 4.2 Team Boundaries

While agents can interact across teams, team boundaries provide:

#### Access Control
- **Team Context**: Agents have full access to team context
- **Cross-Team Context**: Requires explicit sharing
- **External Context**: Orchestrator approval required

#### Resource Limits
- **Team Budget**: Each team has resource budget
- **Cross-Team Requests**: Require approval
- **Resource Sharing**: Orchestrator manages allocation

#### Quality Gates
- **Team Standards**: Each team enforces own quality standards
- **Cross-Team Integration**: Requires integration tests
- **Escalation**: Team leads can escalate to orchestrator

---

## 5. Implementation Architecture

### 5.1 Data Models

```python
# src/thegent/governance/agent_hierarchy.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum


class AgentRole(Enum):
    """Agent role levels."""

    EXECUTIVE = "executive"  # Level 1
    TEAM_LEAD = "team_lead"  # Level 2
    SPECIALIST = "specialist"  # Level 3


class RelationshipType(Enum):
    """Types of agent relationships."""

    DIRECT_PARENT_CHILD = "direct_parent_child"
    TEAM_MEMBERSHIP = "team_membership"
    CROSS_TEAM_COLLABORATION = "cross_team_collaboration"


class TeamType(Enum):
    """Types of teams."""

    FUNCTIONAL = "functional"
    PROJECT = "project"
    AD_HOC = "ad_hoc"


class CoordinationMode(Enum):
    """Team coordination modes."""

    HIERARCHICAL = "hierarchical"
    COLLABORATIVE = "collaborative"
    SWARM = "swarm"


@dataclass
class AgentNode:
    """Represents an agent in the hierarchy."""

    agent_id: str
    run_id: str
    role: AgentRole
    team_id: Optional[str] = None

    # Relationships
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    team_member_ids: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "active"


@dataclass
class AgentRelationship:
    """Parent-child relationship between agents."""

    relationship_id: str
    parent_id: str
    child_id: str
    relationship_type: RelationshipType
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "active"

    # Delegation context
    task_id: Optional[str] = None
    delegation_prompt: Optional[str] = None
    handoff_context: Optional[Dict[str, Any]] = None


@dataclass
class AgentTeam:
    """A team of agents working together."""

    team_id: str
    name: str
    description: str

    # Team composition
    lead_id: str
    members: List[str] = field(default_factory=list)

    # Team configuration
    team_type: TeamType
    coordination_mode: CoordinationMode
    boundaries: Dict[str, Any] = field(default_factory=dict)
    communication_channels: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "active"
```

### 5.2 Hierarchy Manager

```python
class AgentHierarchyManager:
    """Manages agent hierarchy, relationships, and teams."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self._agents: Dict[str, AgentNode] = {}
        self._relationships: Dict[str, AgentRelationship] = {}
        self._teams: Dict[str, AgentTeam] = {}
        self._load()

    def register_agent(
        self,
        agent_id: str,
        run_id: str,
        role: AgentRole,
        parent_id: Optional[str] = None,
        team_id: Optional[str] = None,
    ) -> AgentNode:
        """Register a new agent in the hierarchy."""
        node = AgentNode(agent_id=agent_id, run_id=run_id, role=role, parent_id=parent_id, team_id=team_id)
        self._agents[run_id] = node

        # Update parent's children list
        if parent_id:
            parent = self._agents.get(parent_id)
            if parent:
                parent.children_ids.append(run_id)

        # Update team membership
        if team_id:
            team = self._teams.get(team_id)
            if team:
                if role == AgentRole.TEAM_LEAD:
                    team.lead_id = run_id
                else:
                    team.members.append(run_id)

        self._save()
        return node

    def create_relationship(
        self,
        parent_id: str,
        child_id: str,
        relationship_type: RelationshipType,
        task_id: Optional[str] = None,
        delegation_prompt: Optional[str] = None,
    ) -> AgentRelationship:
        """Create a relationship between agents."""
        rel_id = f"REL-{uuid.uuid4().hex[:8]}"
        relationship = AgentRelationship(
            relationship_id=rel_id,
            parent_id=parent_id,
            child_id=child_id,
            relationship_type=relationship_type,
            task_id=task_id,
            delegation_prompt=delegation_prompt,
        )
        self._relationships[rel_id] = relationship
        self._save()
        return relationship

    def create_team(
        self,
        team_id: str,
        name: str,
        description: str,
        team_type: TeamType,
        coordination_mode: CoordinationMode,
        lead_id: str,
    ) -> AgentTeam:
        """Create a new team."""
        team = AgentTeam(
            team_id=team_id,
            name=name,
            description=description,
            team_type=team_type,
            coordination_mode=coordination_mode,
            lead_id=lead_id,
        )
        self._teams[team_id] = team
        self._save()
        return team

    def get_team_members(self, team_id: str) -> List[AgentNode]:
        """Get all members of a team."""
        team = self._teams.get(team_id)
        if not team:
            return []

        members = []
        if team.lead_id:
            lead = self._agents.get(team.lead_id)
            if lead:
                members.append(lead)

        for member_id in team.members:
            member = self._agents.get(member_id)
            if member:
                members.append(member)

        return members

    def get_children(self, parent_id: str) -> List[AgentNode]:
        """Get all direct children of an agent."""
        parent = self._agents.get(parent_id)
        if not parent:
            return []

        children = []
        for child_id in parent.children_ids:
            child = self._agents.get(child_id)
            if child:
                children.append(child)

        return children

    def get_ancestors(self, agent_id: str) -> List[AgentNode]:
        """Get all ancestors of an agent (parent chain)."""
        ancestors = []
        current = self._agents.get(agent_id)

        while current and current.parent_id:
            parent = self._agents.get(current.parent_id)
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break

        return ancestors

    def can_delegate(self, from_agent_id: str, to_agent_id: str, task_context: Dict[str, Any]) -> bool:
        """Check if agent can delegate to another agent."""
        from_agent = self._agents.get(from_agent_id)
        to_agent = self._agents.get(from_agent_id)

        if not from_agent or not to_agent:
            return False

        # Executive can delegate to anyone
        if from_agent.role == AgentRole.EXECUTIVE:
            return True

        # Team leads can delegate to team members
        if from_agent.role == AgentRole.TEAM_LEAD:
            if to_agent.team_id == from_agent.team_id:
                return True

        # Cross-team delegation requires approval
        if from_agent.team_id != to_agent.team_id:
            # Check if cross-team collaboration is allowed
            return task_context.get("allow_cross_team", False)

        # Specialists can delegate to peers or lower-level agents
        if from_agent.role == AgentRole.SPECIALIST:
            if to_agent.role == AgentRole.SPECIALIST:
                return True

        return False
```

### 5.3 Team Coordination Protocol

```python
class TeamCoordinator:
    """Coordinates team activities and cross-team collaboration."""

    def __init__(self, hierarchy_manager: AgentHierarchyManager):
        self.hierarchy = hierarchy_manager

    def delegate_within_team(
        self, from_agent_id: str, to_agent_id: str, task: str, context: Dict[str, Any]
    ) -> DelegationRequest:
        """Delegate task within same team."""
        from_agent = self.hierarchy._agents.get(from_agent_id)
        to_agent = self.hierarchy._agents.get(to_agent_id)

        if not from_agent or not to_agent:
            raise ValueError("Agent not found")

        if from_agent.team_id != to_agent.team_id:
            raise ValueError("Agents not in same team")

        # Create delegation
        relationship = self.hierarchy.create_relationship(
            parent_id=from_agent_id,
            child_id=to_agent_id,
            relationship_type=RelationshipType.TEAM_MEMBERSHIP,
            delegation_prompt=task,
        )

        return relationship

    def delegate_cross_team(
        self,
        from_agent_id: str,
        to_agent_id: str,
        task: str,
        context: Dict[str, Any],
        mediator_id: Optional[str] = None,
    ) -> DelegationRequest:
        """Delegate task across teams (requires coordination)."""
        from_agent = self.hierarchy._agents.get(from_agent_id)
        to_agent = self.hierarchy._agents.get(to_agent_id)

        if not from_agent or not to_agent:
            raise ValueError("Agent not found")

        if from_agent.team_id == to_agent.team_id:
            raise ValueError("Agents in same team, use delegate_within_team")

        # Cross-team delegation requires team lead or orchestrator approval
        if not mediator_id:
            # Use orchestrator as default mediator
            mediator_id = self._find_orchestrator()

        # Create cross-team relationship
        relationship = self.hierarchy.create_relationship(
            parent_id=from_agent_id,
            child_id=to_agent_id,
            relationship_type=RelationshipType.CROSS_TEAM_COLLABORATION,
            delegation_prompt=task,
            handoff_context={"mediator_id": mediator_id, "cross_team": True, **context},
        )

        return relationship
```

---

## 6. Integration with Existing Teammate System

### 6.1 Extending TeammateManager

The existing `TeammateManager` will be extended to support hierarchy:

```python
# src/thegent/governance/teammates.py (extended)


class TeammateManager:
    """Manages discovery and delegation for the teammate swarm."""

    def __init__(self, storage_path: Path, hierarchy_manager: Optional[AgentHierarchyManager] = None):
        self.storage_path = storage_path
        self.hierarchy = hierarchy_manager or AgentHierarchyManager(storage_path / "hierarchy.json")
        self._delegations: dict[str, DelegationRequest] = {}
        self._load()

    def delegate(
        self,
        teammate_id: str,
        parent_run_id: str,
        prompt: str,
        team_id: Optional[str] = None,
        relationship_type: RelationshipType = RelationshipType.DIRECT_PARENT_CHILD,
    ) -> DelegationRequest:
        """WP-16002: Delegate a task to a teammate with hierarchy support."""
        req_id = f"DEL-{uuid.uuid4().hex[:8]}"

        # Register child agent in hierarchy
        child_node = self.hierarchy.register_agent(
            agent_id=teammate_id,
            run_id=req_id,
            role=self._infer_role(teammate_id),
            parent_id=parent_run_id,
            team_id=team_id,
        )

        # Create relationship
        relationship = self.hierarchy.create_relationship(
            parent_id=parent_run_id, child_id=req_id, relationship_type=relationship_type, delegation_prompt=prompt
        )

        # Create delegation request
        request = DelegationRequest(
            id=req_id, teammate_id=teammate_id, parent_run_id=parent_run_id, prompt=prompt, status="pending"
        )
        self._delegations[req_id] = request
        self._save()

        return request

    def create_team(
        self,
        team_id: str,
        name: str,
        description: str,
        team_type: TeamType,
        coordination_mode: CoordinationMode,
        lead_id: str,
    ) -> AgentTeam:
        """Create a new team."""
        return self.hierarchy.create_team(
            team_id=team_id,
            name=name,
            description=description,
            team_type=team_type,
            coordination_mode=coordination_mode,
            lead_id=lead_id,
        )
```

---

## 7. CLI Extensions

### 7.1 New Commands

```bash
# Team management
thegent teams create --name "Frontend Team" --type functional --lead frontend-lead
thegent teams list
thegent teams show <team-id>
thegent teams add-member <team-id> <agent-id>
thegent teams remove-member <team-id> <agent-id>

# Hierarchy visualization
thegent hierarchy show [--agent-id <id>] [--team-id <id>]
thegent hierarchy tree [--root <agent-id>]
thegent hierarchy relationships [--agent-id <id>]

# Delegation with team awareness
thegent teammates delegate <teammate-id> <prompt> [--team <team-id>] [--cross-team]
thegent teammates delegate --to-team <team-id> <prompt>
```

---

## 8. Use Cases

### 8.1 Scenario: Multi-Team Feature Development

**Setup**:
- Orchestrator: `sitback`
- Frontend Team: Lead + 3 specialists
- Backend Team: Lead + 2 specialists
- DevOps Team: Lead + 1 specialist

**Task**: "Build user authentication feature"

**Flow**:
1. Orchestrator breaks down task:
   - Frontend: Login UI
   - Backend: Auth API
   - DevOps: Deployment config

2. Orchestrator delegates to team leads:
   - `sitback` → `frontend-lead` (Login UI)
   - `sitback` → `backend-lead` (Auth API)
   - `sitback` → `devops-lead` (Deployment)

3. Team leads delegate to specialists:
   - `frontend-lead` → `react-specialist` (Login component)
   - `frontend-lead` → `css-specialist` (Styling)
   - `backend-lead` → `api-specialist` (Auth endpoints)
   - `backend-lead` → `db-specialist` (User schema)

4. Cross-team collaboration:
   - `react-specialist` ↔ `api-specialist` (API contract)
   - Mediated by team leads

5. Integration:
   - Team leads report to orchestrator
   - Orchestrator coordinates integration
   - DevOps deploys

### 8.2 Scenario: Ad-Hoc Security Audit

**Setup**:
- Orchestrator creates ad-hoc team
- Security specialists from multiple teams

**Task**: "Audit authentication security"

**Flow**:
1. Orchestrator creates ad-hoc team:
   - `thegent teams create --name "Security Audit" --type ad-hoc --lead security-lead`

2. Orchestrator invites specialists:
   - `thegent teams add-member security-audit frontend-security-specialist`
   - `thegent teams add-member security-audit backend-security-specialist`

3. Team lead coordinates:
   - `security-lead` assigns tasks to specialists
   - Specialists collaborate (swarm mode)

4. Results aggregated:
   - Team lead consolidates findings
   - Reports to orchestrator

---

## 9. Benefits

### 9.1 Clear Accountability
- Explicit parent-child relationships
- Clear ownership chains
- Traceable delegation paths

### 9.2 Efficient Coordination
- Team-based organization reduces coordination overhead
- Cross-team collaboration when needed
- Hierarchical escalation for conflicts

### 9.3 Scalability
- Teams can scale independently
- New teams can be created dynamically
- Specialists can join multiple teams

### 9.4 Observability
- Full hierarchy visualization
- Team activity tracking
- Relationship graph analysis

---

## 10. Next Steps

### Phase 1: Core Hierarchy (Week 1-2)
- [ ] Implement `AgentHierarchyManager`
- [ ] Extend `TeammateManager` with hierarchy support
- [ ] Add hierarchy visualization commands
- [ ] Unit tests for hierarchy operations

### Phase 2: Team Management (Week 3-4)
- [ ] Implement team creation and management
- [ ] Add team coordination protocols
- [ ] Cross-team collaboration support
- [ ] Integration tests

### Phase 3: UI/UX (Week 5-6)
- [ ] Hierarchy visualization in dashboard
- [ ] Team activity monitoring
- [ ] Relationship graph visualization
- [ ] CLI improvements

### Phase 4: Advanced Features (Week 7-8)
- [ ] Dynamic team creation
- [ ] Team templates
- [ ] Advanced coordination modes
- [ ] Performance optimization

---

## 11. Research Validation

This design has been validated through comprehensive research:

### 11.1 Local Research
- **CRUN Deep Dive**: Hierarchical, P2P, and hybrid coordination strategies
- **SmolGents**: Hierarchical execution modes, manager-first assignment
- **Multi-Swarm Hierarchy**: Hierarchical blackboard, stigmergic handoff
- **heliosShield Agent Mesh**: File-based IPC, Maildir pattern, atomic operations
- **Teammates System**: Delegation patterns, handoff protocols

### 11.2 Web Framework Research
- **CrewAI**: Hierarchical process with manager agent, role-based teams
- **MetaGPT**: Software company simulation, SOP-driven teams, role-based hierarchy
- **LangGraph**: Stateful workflows, durable execution, graph-based orchestration
- **AutoGen**: Multi-agent orchestration, AgentTool pattern, group chat

### 11.3 Academic & Production Research
- **Cursor Research**: Planner-Worker-Judge hierarchy, partitioned work
- **MetaGPT Patterns**: Global message pool, artifact-based coordination
- **Claude Code Teams**: Team lead coordination, peer-to-peer messaging
- **Google A2A Protocol**: Agent Cards, task lifecycle, JSON-RPC

**See**:
- [LOCAL_RESEARCH_AUDIT.md](./LOCAL_RESEARCH_AUDIT.md) - Complete local codebase audit
- [WEB_RESEARCH_AUDIT.md](./WEB_RESEARCH_AUDIT.md) - Framework and production system analysis
- [RESEARCH_SYNTHESIS.md](./RESEARCH_SYNTHESIS.md) - Comprehensive synthesis and validation

---

## 12. References

- [TEAMMATES_RESEARCH_AND_PLAN.md](./TEAMMATES_RESEARCH_AND_PLAN.md) - Original teammate research
- [CLAUDE.md](../CLAUDE.md) - Agent governance and delegation patterns
- heliosShield Phase 6-18 - Coordination and conflict resolution
- MetaGPT - Multi-agent collaboration patterns
- CrewAI - Role-based agent teams
- [AGENT_HIERARCHY_RESEARCH_PLAN.md](./AGENT_HIERARCHY_RESEARCH_PLAN.md) - Research methodology

---

## Appendix: Role Definitions

### Executive Roles
- `sitback`: Primary orchestrator, strategic planning
- `manager`: Project management, coordination
- `orchestrator`: Multi-team coordination

### Team Lead Roles
- `frontend-lead`: Frontend team coordination
- `backend-lead`: Backend team coordination
- `devops-lead`: DevOps team coordination
- `qa-lead`: Quality assurance coordination
- `security-lead`: Security team coordination

### Specialist Roles
- `coder`: Code implementation
- `researcher`: Research and investigation
- `reviewer`: Code review
- `tester`: Testing and QA
- `designer`: UI/UX design
- `api-specialist`: API development
- `db-specialist`: Database design
- `infrastructure-specialist`: Infrastructure management
