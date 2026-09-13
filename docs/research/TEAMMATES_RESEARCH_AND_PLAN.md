<DONE>
# Thegent Teammates: Research and Implementation Plan (2026-02-15)

## 1. Research: Claude Code Teammates
Claude Code's "teammates" feature represents a shift from a single monolithic agent to a collaborative team of specialized agents. Key characteristics identified:
- **Delegation**: A primary orchestrator (the "Manager") breaks down complex tasks into sub-tasks.
- **Specialization**: Teammates have specific roles (e.g., researcher, coder, reviewer, tester).
- **Collaboration**: Multiple agents work on the same codebase, often asynchronously.
- **Context Handoff**: Structured data (like XML tags) is used to pass instructions and results between agents.

## 2. Competitive Analysis: Thegent vs. Teammates

| Capability | Claude Code Teammates | Thegent + heliosShield |
|------------|-----------------------|--------------------|
| **Orchestration** | Centralized | `thegent sitback` (Manager) |
| **Isolation** | Workspace-based (likely) | Git Parallelism (Private Index) |
| **Coordination** | Internal protocol | heliosShield Phase 6-18 (OCC + Locks) |
| **Handoff** | Structured prompts | XML Tags (Task Tool Contract) |
| **Observability** | CLI Dashboard | Sitback Dashboard v2 |

## 3. Implementation Strategy: The "Teammate Swarm"

### 3.1 Orchestration (Thegent Layer)
We will leverage `thegent sitback` as the primary entry point. The sitback agent will be enhanced with "Teammate Awareness":
- **`thegent teammates list`**: Discover specialized personas in `agents/*.md`.
- **`thegent teammates delegate <persona> <prompt>`**: Spawn an asynchronous sub-agent to handle a specific task.
- **Status Tracking**: Use the `EvidenceGraph` to link teammate actions back to the primary run.

### 3.2 Coordination (heliosShield Layer)
To allow teammates to work safely in the same directory, we must implement the **Shared-Directory Architecture** from heliosShield Phase 6+:
- **Git Parallelism (Phase 6)**: Enable multiple agents to commit concurrently using private `GIT_INDEX_FILE` and CAS ref updates.
- **Smart Merge (Phase 7)**: Use `Mergiraf` for AST-aware conflict resolution when teammates edit the same files.
- **Task Coordination (Phase 11)**: A filesystem-native task queue (Maildir style) for teammates to claim work.

### 3.3 Handoff Protocol (Task Tool Layer)
We will adopt and extend the XML contract from `task-tool`:
- `<Thought>`: Internal reasoning.
- `<Action>`: The delegated task.
- `<Result>`: The teammate's output.
- `<Handoff>`: Explicit transfer of ownership with confidence scores.

## 4. Work Packages (WPs)

### WP-16001: Teammate Persona Registry
- Expand `PersonaManager` to support "Teammate" metadata (role, priority, ODD).
- Auto-discovery of teammates from the `agents/` directory.

### WP-16002: Async Delegation CLI
- Implement `thegent teammates delegate` command.
- Implement `thegent teammates status` to monitor the swarm.

### WP-16003: heliosShield Integration Bridge
- Wire `thegent` into heliosShield's Phase 11 task queue.
- Ensure `thegent_run` automatically respects heliosShield locks and intents.

### WP-16004: Intelligent Conflict Resolution Bridge
- Implement a `thegent merge` helper that wraps heliosShield's Phase 7 AST merge.

## 5. Success Criteria
- [ ] A single `thegent sitback` session can delegate a sub-task to a "coder" teammate.
- [ ] The teammate completes the task in the background and reports back via XML.
- [ ] Multiple teammates can work on different files simultaneously without git lock contention.
- [ ] The `sitback` dashboard shows a live view of the "Teammate Swarm".

## 6. Reference Implementation: OpenCode
The `opencode-openai-codex-auth` plugin and `task-tool` provide the baseline for XML-based tool remapping and Planner→Operator→Reviewer sequencing. We will refine these patterns into a more generic "Teammate" interface.

---

## 5. IMPLEMENTATION: Teammates CLI

### 5.1 Teammates Command Implementation

```python
#!/usr/bin/env python3
# src/thegent/commands/teammates.py

import typer
from pathlib import Path
from typing import Optional

app = typer.Typer()


@app.command()
def list():
    """List all available teammates."""
    from thegent.agents.registry import AGENT_REGISTRY

    print("\n📋 Available Teammates:\n")
    for agent_id, agent_def in AGENT_REGISTRY.items():
        if agent_def.get("type") == "teammate":
            desc = agent_def.get("description", "")[:60]
            print(f"  • {agent_id}: {desc}...")


@app.command()
def delegate(
    teammate: str = typer.Argument(..., help="Teammate agent ID"),
    task: str = typer.Argument(..., help="Task description"),
    context: Optional[Path] = typer.Option(None, "-c", "--context", help="Context directory"),
):
    """Delegate task to a teammate."""
    from thegent.agents.runner import AgentRunner
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        if context:
            ctx_file = Path(tmpdir) / "context.md"
            ctx_file.write_text(f"# Context from {context}\n\n{context.read_text()}")

        runner = AgentRunner(agent_id=teammate, task_prompt=task, work_dir=Path(tmpdir))

        result = runner.run()

        if result.success:
            print(f"\n✅ Teammate {teammate} completed: {result.summary}")
        else:
            print(f"\n❌ Teammate {teammate} failed: {result.error}")
            raise SystemExit(1)


@app.command()
def status():
    """Show status of all teammate runs."""
    from thegent.orchestration.state import get_active_runs

    runs = get_active_runs()
    print("\n📊 Active Teammate Runs:\n")
    if not runs:
        print("  No active runs")
        return

    for run in runs:
        print(f"  • {run.id}: {run.status} ({run.teammate})")
```

### 5.2 Handoff Protocol Implementation

```python
#!/usr/bin/env python3
# src/thegent/agents/handoff.py

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class HandoffState(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Handoff:
    """Handoff between teammates."""

    from_agent: str
    to_agent: str
    task: str
    context: str
    state: HandoffState = HandoffState.PENDING
    confidence: float = 1.0
    result: Optional[str] = None

    def to_xml(self) -> str:
        return f"""<Handoff>
    <From>{self.from_agent}</From>
    <To>{self.to_agent}</To>
    <Task>{self.task}</Task>
    <Context>{self.context}</Context>
    <Confidence>{self.confidence}</Confidence>
</Handoff>"""


class HandoffProtocol:
    """Manage handoffs between teammates."""

    def __init__(self):
        self.pending_handoffs: list[Handoff] = []

    def create_handoff(self, from_agent: str, to_agent: str, task: str, context: str) -> Handoff:
        """Create a new handoff."""
        handoff = Handoff(from_agent=from_agent, to_agent=to_agent, task=task, context=context)
        self.pending_handoffs.append(handoff)
        return handoff

    def complete_handoff(self, handoff_id: int, result: str):
        """Mark handoff as completed."""
        if 0 <= handoff_id < len(self.pending_handoffs):
            h = self.pending_handoffs[handoff_id]
            h.state = HandoffState.COMPLETED
            h.result = result
```

---

## 6. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added Section 5:** Teammates CLI Implementation
   - Typer commands for list/delegate/status
   - AgentRunner integration
   - Active run tracking

2. **Added Section 6:** Handoff Protocol Implementation
   - Handoff dataclass with XML serialization
   - HandoffProtocol class for management
   - State machine (pending → in_progress → completed/failed)

### Cross-References Added

- heliosShield Phase 6-18 Integration
- Task Tool Contract documentation

### Practical Additions

- Python teammates CLI with typer
- XML-based handoff protocol
- Status tracking for active runs

---

## 7. Agent Hierarchy Integration

**Extended on:** 2026-02-18
**Extended by:** Agent Hierarchy System

### Integration with Hierarchy System

The teammate system now integrates with a comprehensive agent hierarchy:

- **Role Levels**: Executive → Team Lead → Specialist
- **Parent-Child Relationships**: Explicit delegation chains
- **Team Organization**: Functional, Project, and Ad-Hoc teams
- **Cross-Team Collaboration**: Mediated collaboration across team boundaries

See [AGENT_HIERARCHY_AND_TEAM_STRUCTURE.md](./AGENT_HIERARCHY_AND_TEAM_STRUCTURE.md) for complete details.

### Enhanced Delegation

Delegation now supports:
- **Team-aware delegation**: Delegate to team members or cross-team
- **Hierarchy-aware delegation**: Respect role levels and permissions
- **Relationship tracking**: Full parent-child relationship graph
- **Team coordination**: Team leads coordinate team activities

### New Capabilities

1. **Team Management**:
   - Create functional, project, or ad-hoc teams
   - Assign team leads and members
   - Configure team coordination modes

2. **Hierarchy Visualization**:
   - View agent hierarchy tree
   - Track parent-child relationships
   - Monitor team composition

3. **Cross-Team Collaboration**:
   - Explicit cross-team delegation
   - Mediated collaboration through team leads
   - Resource and access control

---

## See Also

- [AGENT_HIERARCHY_AND_TEAM_STRUCTURE.md](./AGENT_HIERARCHY_AND_TEAM_STRUCTURE.md) - Complete hierarchy system
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [IN_DEPTH_TOOLING_AUDIT_2026.md](./IN_DEPTH_TOOLING_AUDIT_2026.md) - Tooling audit
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
