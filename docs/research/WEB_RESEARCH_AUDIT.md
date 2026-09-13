<DONE>
# Web Research Audit: Agent Hierarchy & Multi-Agent Frameworks

> **Date**: 2026-02-18
> **Status**: In Progress
> **Scope**: Industry frameworks, academic research, production systems

---

## Executive Summary

This audit covers web research on:
- **Industry Frameworks**: CrewAI, MetaGPT, AutoGen, LangGraph
- **Academic Research**: Multi-agent hierarchies, coordination protocols
- **Production Systems**: Claude Code Teams, GitHub Copilot, Cursor

**Key Findings:**
- CrewAI: Role-based agents, hierarchical process, manager coordination
- MetaGPT: Software company simulation, SOP-based teams
- LangGraph: Low-level orchestration, stateful workflows, durable execution
- AutoGen: Group chat patterns, multi-agent collaboration

---

## 1. Industry Frameworks

### 1.1 CrewAI

**Source**: https://docs.crewai.com/

#### Core Concepts

**Agents:**
- Role-based specialization
- Goal-oriented behavior
- Backstory for personality
- Tool capabilities
- Memory support
- Delegation support (`allow_delegation`)

**Key Agent Attributes:**
- `role`: Agent's function and expertise
- `goal`: Individual objective
- `backstory`: Context and personality
- `allow_delegation`: Can delegate to other agents
- `max_iter`: Maximum iterations (default: 20)
- `max_rpm`: Rate limiting
- `memory`: Conversation memory
- `tools`: Capabilities/functions

**Crews:**
- Collaborative group of agents
- Task execution strategies
- Process flows (sequential, hierarchical)
- Manager coordination

**Crew Process Types:**
- **Sequential**: Tasks executed one after another
- **Hierarchical**: Manager agent coordinates and delegates
- **Custom**: User-defined execution logic

**Hierarchical Process:**
- Manager agent coordinates crew
- Delegates tasks to agents
- Validates outcomes before proceeding
- Requires `manager_llm` or `manager_agent`

**Key Features:**
- YAML configuration (recommended)
- Direct code definition (alternative)
- Memory utilization (short-term, long-term, entity)
- Cache utilization for tool results
- Streaming execution
- Task replay capability
- Usage metrics tracking

**Delegation Pattern:**
```python
agent = Agent(
    role="Manager",
    goal="Coordinate team",
    allow_delegation=True,  # Can delegate to other agents
    verbose=True,
)
```

**Manager Coordination:**
```python
crew = Crew(
    agents=[manager, worker1, worker2],
    tasks=[task1, task2, task3],
    process=Process.hierarchical,
    manager_llm="gpt-4",  # Required for hierarchical
)
```

---

### 1.2 MetaGPT

**Source**: https://github.com/geekan/MetaGPT

#### Core Philosophy

**"Code = SOP(Team)"**
- Materialize SOP (Standard Operating Procedures)
- Apply to teams composed of LLMs
- Software company as multi-agent system

**Architecture:**
- Product managers
- Architects
- Project managers
- Engineers
- Complete software company process

**Key Features:**
- One-line requirement → Full software output
- User stories generation
- Competitive analysis
- Requirements documentation
- Data structures
- APIs
- Documents

**Agent Roles:**
- Product Manager: Requirements, user stories
- Architect: System design
- Project Manager: Task coordination
- Engineer: Code implementation

**Team Structure:**
- Hierarchical organization
- Role-based specialization
- SOP-driven workflows
- Collaborative problem-solving

**Usage:**
```python
from metagpt.software_company import generate_repo

repo = generate_repo("Create a 2048 game")
```

**Data Interpreter:**
```python
from metagpt.roles.di.data_interpreter import DataInterpreter

di = DataInterpreter()
await di.run("Run data analysis on sklearn Iris dataset")
```

---

### 1.3 LangGraph

**Source**: https://langchain-ai.github.io/langgraph/

#### Core Philosophy

**Low-level orchestration framework**
- Focused entirely on agent orchestration
- Production-ready deployment
- Stateful, long-running agents
- Durable execution

**Key Features:**

**1. Production-Ready Deployment**
- Scalable infrastructure
- Handles stateful, long-running workflows
- Unique challenges of agent systems

**2. Debugging with LangSmith**
- Deep visibility into agent behavior
- Visualization tools
- Execution path tracing
- State transition capture
- Runtime metrics

**3. Comprehensive Memory**
- Short-term working memory
- Long-term memory across sessions
- Stateful agent creation

**4. Human-in-the-Loop**
- Inspect agent state at any point
- Modify agent state
- Human oversight

**5. Durable Execution**
- Persist through failures
- Resume from where left off
- Extended period execution

**Core Benefits:**
- Stateful workflows
- Streaming support
- Human-in-the-loop
- Durable execution
- Production deployment

**Architecture:**
- Inspired by Pregel (Google)
- Inspired by Apache Beam
- Interface inspired by NetworkX
- Built by LangChain Inc

**Basic Example:**
```python
from langgraph.graph import StateGraph, MessagesState, START, END


def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}


graph = StateGraph(MessagesState)
graph.add_node(mock_llm)
graph.add_edge(START, "mock_llm")
graph.add_edge("mock_llm", END)
graph = graph.compile()

graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
```

---

### 1.4 AutoGen (Microsoft)

**Source**: https://github.com/microsoft/autogen

#### Core Concepts

**Multi-Agent AI Application Framework**
- Create multi-agent applications
- Act autonomously or work alongside humans
- Layered and extensible design
- Cross-language support (.NET and Python)

**Architecture Layers:**

**1. Core API** (`autogen-core`)
- Message passing
- Event-driven agents
- Local and distributed runtime
- Cross-language support

**2. AgentChat API** (`autogen-agentchat`)
- Simpler, opinionated API
- Rapid prototyping
- Built on Core API
- Common multi-agent patterns:
  - Two-agent chat
  - Group chats
  - Multi-agent orchestration

**3. Extensions API** (`autogen-ext`)
- First- and third-party extensions
- LLM clients (OpenAI, AzureOpenAI)
- Code execution capabilities
- Tool integrations

**Key Features:**

**Multi-Agent Orchestration:**
```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.tools import AgentTool

# Create specialized agents
math_agent = AssistantAgent("math_expert", ...)
chemistry_agent = AssistantAgent("chemistry_expert", ...)

# Create agent tools
math_agent_tool = AgentTool(math_agent, return_value_as_last_message=True)
chemistry_agent_tool = AgentTool(chemistry_agent, ...)

# Main agent uses expert tools
agent = AssistantAgent("assistant", tools=[math_agent_tool, chemistry_agent_tool], max_tool_iterations=10)
```

**Patterns:**
- **AgentTool**: Basic multi-agent orchestration
- **Group Chat**: Multiple agents in conversation
- **Two-Agent Chat**: Direct agent-to-agent
- **Tool-Based Delegation**: Agents as tools

**Developer Tools:**
- **AutoGen Studio**: No-code GUI for multi-agent workflows
- **AutoGen Bench**: Benchmarking suite for agent performance

**Key Insights:**
- Layered design enables different abstraction levels
- AgentTool pattern for delegation
- Group chat for collaborative problem-solving
- Extensible via extensions API

---

## 2. Framework Comparison

### 2.1 Architecture Patterns

| Framework | Pattern | Key Feature | Best For |
|-----------|---------|-------------|----------|
| **CrewAI** | Role-based teams | Manager coordination | Collaborative workflows |
| **MetaGPT** | Software company | SOP-driven teams | Software development |
| **LangGraph** | Graph-based | Stateful workflows | Complex orchestration |
| **AutoGen** | Group chat | Multi-agent conversation | Collaborative problem-solving |

### 2.2 Hierarchy Support

| Framework | Hierarchy Support | Manager Pattern | Delegation |
|-----------|------------------|-----------------|------------|
| **CrewAI** | ✅ Hierarchical process | ✅ Manager agent | ✅ Built-in |
| **MetaGPT** | ✅ Role-based hierarchy | ✅ Product Manager | ✅ SOP-driven |
| **LangGraph** | ⚠️ Custom (graph-based) | ⚠️ User-defined | ⚠️ Custom |
| **AutoGen** | ⚠️ Group chat | ❌ No explicit manager | ✅ Agent-to-agent |

### 2.3 Team Organization

| Framework | Team Concept | Coordination | Communication |
|-----------|--------------|--------------|---------------|
| **CrewAI** | Crews | Manager-based | Task-based |
| **MetaGPT** | Software company | SOP-driven | Role-based |
| **LangGraph** | Graph nodes | State-based | Message-based |
| **AutoGen** | Group chat | Conversation-based | Chat-based |

---

## 3. Academic Research Patterns

### 3.1 Cursor Multi-Agent Research (January 2026)

**Key Finding:**
- Hundreds of concurrent agents
- Building web browser with 1M+ lines of code
- **Planner-Worker-Judge hierarchy**
- Workers never coordinate directly with each other

**Architecture:**
```
Planner
  ├─→ Worker 1
  ├─→ Worker 2
  ├─→ Worker 3
  └─→ Judge
```

**Key Insight:**
- Hierarchical structure prevents conflicts
- Clear ownership prevents coordination overhead
- Workers operate on partitioned areas

---

### 3.2 MetaGPT Global Message Pool

**Pattern:**
- Agents publish structured artifacts
- Subscribe by role (not direct dialogue)
- Most transferable architecture for file-based coordination

**Key Insight:**
- Indirect coordination via artifacts
- Role-based subscription
- Reduces direct communication overhead

---

## 4. Production Systems

### 4.1 Claude Code Agent Teams

**Status**: Experimental (CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1)

**Features:**
- Team lead coordinates
- Spawns teammates
- Synthesizes results
- Teammates work independently
- Own context windows
- Shared task list
- Dependency tracking
- Peer-to-peer messaging
- JSON inboxes
- Split pane mode (tmux/iTerm2)

**Limitations:**
- No session resumption
- No nested teams
- High token overhead
- Claude-to-Claude only

**TeammateTool Operations (13 total):**
- spawnTeam, spawn, write, broadcast, read, list, shutdown
- Directory: `~/.claude/teams/{name}/inboxes/{agent}.json`
- Task files: `~/.claude/tasks/{team-name}/{n}.json`
- `blockedBy` dependency tracking

---

### 4.2 Google A2A Protocol (April 2025)

**Purpose**: Agent-to-Agent communication

**Components:**
- Agent Cards: JSON capability manifests (`.well-known/agent.json`)
- Tasks: Core work abstraction with lifecycle states
- JSON-RPC over HTTP for transport

**Key Insight:**
- "MCP equips individual agents with capabilities, while A2A helps them coordinate as a team"
- Complements MCP (Model Context Protocol)
- Assumes HTTP endpoints (limitation for local agents)

---

## 5. Best Practices Identified

### 5.1 Hierarchy Design

1. **Clear Role Levels**
   - Executive/Orchestrator
   - Team Lead
   - Specialist

2. **Manager Coordination**
   - Manager delegates tasks
   - Validates outcomes
   - Coordinates team

3. **Partitioned Work**
   - Workers operate on partitioned areas
   - No direct worker coordination
   - Clear ownership

### 5.2 Team Organization

1. **Role-Based Teams**
   - Specialized roles
   - Clear responsibilities
   - SOP-driven workflows

2. **Functional Teams**
   - Domain expertise
   - Long-lived teams
   - Reusable across projects

3. **Project Teams**
   - Temporary teams
   - Project-scoped
   - Cross-functional

### 5.3 Communication Patterns

1. **Indirect Coordination**
   - Artifact-based (MetaGPT)
   - Message pool (MetaGPT)
   - Stigmergic handoff

2. **Direct Coordination**
   - Manager-based (CrewAI)
   - Task-based (CrewAI)
   - Conversation-based (AutoGen)

3. **File-Based IPC**
   - Maildir pattern
   - Atomic operations
   - Heartbeat-based failure detection

---

## 6. Gaps & Opportunities

### 6.1 What Frameworks Provide

**CrewAI:**
- ✅ Role-based agents
- ✅ Hierarchical process
- ✅ Manager coordination
- ✅ Delegation support
- ❌ Explicit parent-child relationships
- ❌ Cross-team collaboration
- ❌ Team management API

**MetaGPT:**
- ✅ Software company simulation
- ✅ SOP-driven teams
- ✅ Role-based hierarchy
- ❌ Explicit team boundaries
- ❌ Cross-team protocols

**LangGraph:**
- ✅ Stateful workflows
- ✅ Durable execution
- ✅ Graph-based orchestration
- ❌ Built-in hierarchy patterns
- ❌ Team concepts

**AutoGen:**
- ✅ Multi-agent conversation
- ✅ Group chat patterns
- ❌ Explicit hierarchy
- ❌ Team organization

### 6.2 What Our Design Adds

1. **Explicit Hierarchy**
   - Parent-child relationships
   - Relationship tracking
   - Hierarchy visualization

2. **Team Management**
   - Team creation/management
   - Team boundaries
   - Cross-team collaboration

3. **Unified System**
   - Integrates with existing patterns
   - Extends TeammateManager
   - Builds on heliosShield coordination

---

## 7. Recommendations

### 7.1 Adopt from Frameworks

1. **CrewAI Patterns**
   - Manager coordination
   - Hierarchical process
   - Role-based agents
   - Delegation support

2. **MetaGPT Patterns**
   - SOP-driven workflows
   - Role-based hierarchy
   - Artifact-based coordination

3. **LangGraph Patterns**
   - Stateful workflows
   - Durable execution
   - Graph-based visualization

### 7.2 Extend with Our Design

1. **Explicit Relationships**
   - Parent-child tracking
   - Relationship types
   - Hierarchy visualization

2. **Team Management**
   - Team creation API
   - Team boundaries
   - Cross-team protocols

3. **Integration**
   - Extend TeammateManager
   - Use heliosShield coordination
   - Leverage file-based IPC

---

## 8. Next Steps

1. **Complete Web Research**
   - Academic papers on hierarchies
   - Production system deep dives
   - Best practices compilation

2. **Synthesize Findings**
   - Compare local vs web research
   - Identify unique patterns
   - Validate design decisions

3. **Update Design**
   - Incorporate best practices
   - Address identified gaps
   - Create unified architecture

---

**Status**: Web research in progress. Framework analysis complete.
