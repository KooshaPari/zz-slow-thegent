<DONE>
# Agent Hierarchy Quick Reference

> **Quick reference guide for agent hierarchy, roles, and team structure**

---

## Role Levels

| Level | Role       | Examples                                       | Can Delegate To                                |
| ----- | ---------- | ---------------------------------------------- | ---------------------------------------------- |
| **0** | User       | Human                                          | All agents                                     |
| **1** | Executive  | `sitback`, `manager`, `orchestrator`           | All agents                                     |
| **2** | Team Lead  | `frontend-lead`, `backend-lead`, `devops-lead` | Team members, other team leads (with approval) |
| **3** | Specialist | `coder`, `researcher`, `reviewer`, `tester`    | Peers, lower-level specialists                 |

---

## Relationship Types

### Direct Parent-Child

- **Definition**: Explicit delegation from parent to child
- **Example**: `sitback` → `frontend-lead` → `react-specialist`
- **Characteristics**: Strong ownership, direct reporting

### Team Membership

- **Definition**: Agents working within same team
- **Example**: Frontend team (lead + 3 specialists)
- **Characteristics**: Shared context, peer collaboration

### Cross-Team Collaboration

- **Definition**: Agents from different teams working together
- **Example**: `react-specialist` ↔ `api-specialist` (API contract)
- **Characteristics**: Requires mediation, temporary relationships

---

## Team Types

### Functional Teams

- **Purpose**: Long-lived, domain expertise
- **Examples**: Frontend, Backend, DevOps
- **Lifespan**: Permanent

### Project Teams

- **Purpose**: Temporary, project-scoped
- **Examples**: "E-commerce MVP Team"
- **Lifespan**: Project duration

### Ad-Hoc Teams

- **Purpose**: Temporary, task-scoped
- **Examples**: "Security Audit Team"
- **Lifespan**: Task completion

---

## Coordination Modes

### Hierarchical

- **Structure**: Team Lead → Specialists
- **Use Case**: Clear task breakdown, sequential dependencies
- **Communication**: Top-down delegation

### Collaborative

- **Structure**: Peer-to-peer
- **Use Case**: Complex problems, multiple perspectives
- **Communication**: Shared context, consensus

### Swarm

- **Structure**: Many agents in parallel
- **Use Case**: Independent tasks, exploration
- **Communication**: Minimal coordination

---

## Common Patterns

### Pattern 1: Simple Delegation

```
Orchestrator → Team Lead → Specialist
```

### Pattern 2: Team Coordination

```
Orchestrator
├── Frontend Lead → React Specialist
├── Backend Lead → API Specialist
└── DevOps Lead → CI/CD Specialist
```

### Pattern 3: Cross-Team Collaboration

```
Frontend Specialist ↔ Backend Specialist
     (mediated by team leads)
```

### Pattern 4: Ad-Hoc Team

```
Orchestrator → Security Lead → [Specialists from multiple teams]
```

---

## CLI Commands

### Team Management

```bash
# Create team
thegent teams create --name "Frontend Team" --type functional --lead frontend-lead

# List teams
thegent teams list

# Add member
thegent teams add-member frontend-team react-specialist
```

### Hierarchy Visualization

```bash
# Show hierarchy
thegent hierarchy show --agent-id <id>

# Show tree
thegent hierarchy tree --root sitback

# Show relationships
thegent hierarchy relationships --agent-id <id>
```

### Delegation

```bash
# Delegate to teammate
thegent teammates delegate coder "Implement login component"

# Delegate to team
thegent teammates delegate --to-team frontend-team "Build UI"

# Cross-team delegation
thegent teammates delegate api-specialist "Design API" --cross-team
```

---

## Decision Tree: When to Delegate?

```
Is task >3 files or complex?
├─ YES → Delegate
│   ├─ Is it domain-specific?
│   │   ├─ YES → Delegate to team lead
│   │   └─ NO → Delegate to orchestrator
│   └─ Is it cross-domain?
│       ├─ YES → Create project team
│       └─ NO → Delegate to functional team
└─ NO → Handle directly
```

---

## Team Boundaries

### Within Team

- ✅ Full access to team context
- ✅ Direct peer collaboration
- ✅ Team lead coordination

### Cross-Team

- ⚠️ Requires explicit sharing
- ⚠️ Mediated by team leads
- ⚠️ Resource approval needed

### External

- 🔒 Orchestrator approval required
- 🔒 Limited context access
- 🔒 Quality gates enforced

---

## See Also

- [AGENT_HIERARCHY_AND_TEAM_STRUCTURE.md](./AGENT_HIERARCHY_AND_TEAM_STRUCTURE.md) - Complete documentation
- [TEAMMATES_RESEARCH_AND_PLAN.md](./TEAMMATES_RESEARCH_AND_PLAN.md) - Teammate system research
