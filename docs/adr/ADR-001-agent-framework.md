# ADR-001: Agent Framework Architecture

**Date**: 2026-04-02  
**Status**: Accepted  
**Deciders**: Agent

## Context

thegent requires an agent architecture for managing dotfiles and executing environment configuration tasks. The system needs to:

1. Execute user commands in a structured way
2. Support multi-step workflows (detect OS → install packages → configure shell)
3. Integrate with sandboxing for security
4. Scale from simple tasks to complex multi-tenant scenarios

## Decision Drivers

- **Performance**: Agent startup and execution speed
- **Control**: Granular control over agent behavior
- **Ecosystem**: Integration with existing tools
- **Security**: Sandboxing integration capability
- **Maintainability**: Code complexity and team expertise

## Options Considered

### Option A: CrewAI (Role-Based Framework)

**Pros**:

- Intuitive role-based model (perfect for "dotfiles manager" role)
- YAML configuration support (fits thegent's config-driven approach)
- Fast execution (5.76x faster than LangGraph per benchmarks)
- 100,000+ certified developers, strong documentation
- Built-in task delegation patterns

**Cons**:

- Python dependency (thegent is primarily Rust/Go)
- Less granular control than custom implementation
- Limited to Python ecosystem
- Newer project (less proven than LangChain)

**Performance**: 300-800ms cold start, low resource overhead

### Option B: LangGraph (State Machine Framework)

**Pros**:

- Explicit control flow via state machines
- State persistence for long workflows
- Better for complex, multi-step processes
- Part of LangChain ecosystem (integration)

**Cons**:

- Steep learning curve
- More boilerplate code required
- LangChain dependency (large)
- Overkill for simple dotfiles tasks

**Performance**: Higher overhead due to LangChain abstraction

### Option C: Custom Implementation (Hybrid Approach)

**Pros**:

- Full control over architecture
- Native language (Rust/Go)
- Optimized for thegent's specific use cases
- No external dependencies
- Can incorporate patterns from CrewAI/LangGraph

**Cons**:

- Development time investment
- Maintenance burden
- No community ecosystem

**Performance**: Fastest possible (native implementation)

### Option D: Temporal (Durable Execution)

**Pros**:

- Durable execution (survives crashes)
- Workflow replay capability
- Production-grade reliability

**Cons**:

- Heavy infrastructure (requires Temporal server)
- Overkill for dotfiles management
- Go/Java/TS focused

**Decision**: Rejected for current scope (too heavy)

## Decision

**Adopt Option C with Option A patterns**: Build a custom agent framework in Rust that implements CrewAI's role-based patterns while maintaining LangGraph's state machine control flow.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│              thegent Agent Architecture                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │                  Agent Definition                     ││
│  │                                                      ││
│  │  pub struct Agent {                                  ││
│  │      role: Role,           // "dotfiles_manager"   ││
│  │      goal: String,         // "Configure env"       ││
│  │      backstory: String,    // Context for LLM      ││
│  │      tools: Vec<Tool>,     // Available actions    ││
│  │      llm: Box<dyn LLM>,    // LLM backend          ││
│  │  }                                                  ││
│  │                                                      ││
│  │  impl Agent {                                        ││
│  │      pub async fn execute(&self, task: Task)       ││
│  │          -> Result<Output> {                          ││
│  │          // Pattern from CrewAI                     ││
│  │      }                                              ││
│  │  }                                                  ││
│  └─────────────────────────────────────────────────────┘│
│                          │                               │
│  ┌───────────────────────▼─────────────────────────────┐│
│  │                 Task Orchestration                  ││
│  │  (LangGraph-inspired state machine)                   ││
│  │                                                      ││
│  │  pub enum TaskState {                                ││
│  │      Pending,                                        ││
│  │      InProgress { step: usize },                     ││
│  │      AwaitingInput,                                  ││
│  │      Completed(Output),                              ││
│  │      Failed(Error),                                  ││
│  │  }                                                  ││
│  │                                                      ││
│  │  pub struct TaskGraph {                              ││
│  │      nodes: Vec<TaskNode>,                           ││
│  │      edges: Vec<(usize, usize)>, // step transitions││
│  │      current: usize,                                 ││
│  │  }                                                  ││
│  └─────────────────────────────────────────────────────┘│
│                          │                               │
│  ┌───────────────────────▼─────────────────────────────┐│
│  │                  Tool System                        ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  ││
│  │  │ Install │ │ Symlink │ │  Exec   │ │  Detect │  ││
│  │  │ Package │ │  Config │ │ Command │ │   OS    │  ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘  ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Language Choice

| Component            | Language | Rationale                                   |
| -------------------- | -------- | ------------------------------------------- |
| Agent core           | Rust     | Performance, safety, existing thegent stack |
| Tool implementations | Rust     | Sandboxing integration                      |
| LLM integration      | Rust     | `llm` crate ecosystem                       |
| Configuration        | TOML     | thegent standard                            |

## Consequences

### Positive

- **Optimal performance**: Native Rust implementation
- **Full control**: No framework limitations
- **CrewAI patterns**: Proven role-based model
- **State machine reliability**: LangGraph-inspired control flow
- **Language alignment**: Fits thegent's Rust stack

### Negative

- **Development time**: ~2-3 weeks for core implementation
- **Maintenance burden**: No upstream updates
- **Documentation**: Must write our own

### Migration Path

**Phase 1**: Core agent framework (roles, tasks, tools)
**Phase 2**: State machine orchestration
**Phase 3**: LLM integration layer
**Phase 4**: Multi-agent coordination

## Implementation Notes

```rust
// Core trait definitions

pub trait Agent: Send + Sync {
    fn role(&self) -> &Role;
    fn execute(&self, task: Task) -> BoxFuture<Result<Output>>;
}

pub trait Tool: Send + Sync {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    fn execute(&self, input: Input) -> BoxFuture<Result<Output>>;
}

pub struct Task {
    pub description: String,
    pub expected_output: String,
    pub tools: Vec<Box<dyn Tool>>,
    pub context: HashMap<String, Value>,
}
```

## References

- CrewAI: https://github.com/crewAIInc/crewAI
- LangGraph: https://github.com/langchain-ai/langgraph
- thegent SOTA Research: `docs/research/AGENT_FRAMEWORKS_SOTA.md`

---

_This ADR will be updated as implementation progresses_
