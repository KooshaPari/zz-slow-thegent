# Hexagonal Split: Absorption & Implementation Checklist

**Status:** Ready for execution
**Created:** 2026-02-23
**Owner:** Implementation Team
**Phases:** 5 (8+ weeks)

---

## Phase 1: Foundation & Protocol (Weeks 1-2)

### Research & Planning

- [ ] Read PAL-MCP server.py (entry point)
- [ ] Read PAL-MCP providers/ directory
- [ ] Read PAL-MCP systemprompts/ directory
- [ ] Review ACP protocol spec (GitHub repo)
- [ ] Review AgentAPI routing patterns
- [ ] Map thegent agent types to PAL-MCP roles
- [ ] Document architecture decisions in ADR

### Dependency Setup

- [ ] Add mcp>=1.0.0 to pyproject.toml
- [ ] Add google-genai>=1.19.0 to pyproject.toml
- [ ] Add openai>=1.55.2 to pyproject.toml
- [ ] Add pydantic>=2.0.0 to pyproject.toml
- [ ] Test imports (smoke test)
- [ ] Document dependencies in DEPENDENCIES.md

### Proof of Concept

- [ ] Create skeleton multi-model provider registry
- [ ] Wire up Gemini API (test)
- [ ] Wire up OpenAI API (test)
- [ ] Create simple test: "Ask two models, compare responses"
- [ ] Document findings in CONVERSATION_DUMP

**Deliverable:** PRD for multi-model orchestration, dependency audit passed

---

## Phase 2: Multi-Model Conversation Threading (Weeks 3-4)

### Core Implementation

- [ ] Design conversation state schema (database/in-memory)
- [ ] Implement message history storage per thread
- [ ] Implement model switching (mid-conversation)
- [ ] Implement context passing between models
- [ ] Add context window management (track tokens)
- [ ] Implement context revival (when model resets)

### Provider Pattern

- [ ] Create ProviderBase abstract class
- [ ] Implement GeminiProvider
- [ ] Implement OpenAIProvider
- [ ] Implement OpenRouterProvider
- [ ] Create ProviderRegistry with factory pattern
- [ ] Add provider fallback logic (if primary unavailable)

### Testing

- [ ] Unit tests: conversation state management
- [ ] Integration tests: model switching
- [ ] Integration tests: context passing
- [ ] E2E test: multi-turn conversation across 2 models
- [ ] Performance test: token counting accuracy
- [ ] Coverage: >=80%

### Documentation

- [ ] Document provider interface
- [ ] Document conversation threading API
- [ ] Add code examples (codereview workflow)
- [ ] Update ARCHITECTURE.md

**Deliverable:** Working multi-model conversations, 80%+ test coverage

---

## Phase 3: Subagent Spawning & Role Specialization (Weeks 5-6)

### Subagent Lifecycle

- [ ] Design subagent spawn interface
- [ ] Implement spawn() with role parameter
- [ ] Implement isolate() (separate context)
- [ ] Implement execute() (run in isolation)
- [ ] Implement collect_results() (gather outputs)
- [ ] Implement synthesize() (merge results to parent)
- [ ] Add parent-child tracking (for debugging)

### Role Specialization

- [ ] Define system prompts: planner
- [ ] Define system prompts: codereviewer
- [ ] Define system prompts: debugger
- [ ] Define system prompts: docwriter
- [ ] Create role registry
- [ ] Allow custom roles (extensible)

### Workflow Orchestration

- [ ] Design DAG validator (ensure no cycles)
- [ ] Implement codereview workflow: walk code → analyze → collect issues
- [ ] Implement planner workflow: break down tasks
- [ ] Implement implement workflow: execute tasks
- [ ] Implement precommit workflow: final validation
- [ ] Add confidence tracking (exploring → low → medium → high → certain)

### Testing

- [ ] Unit tests: DAG validation
- [ ] Unit tests: role system prompt injection
- [ ] Integration tests: spawn + execute + collect
- [ ] Integration tests: workflow sequences
- [ ] E2E test: full codereview workflow (3 subagents)
- [ ] Coverage: >=80%

### Documentation

- [ ] Document subagent lifecycle
- [ ] Document role specialization
- [ ] Document workflow creation
- [ ] Add examples (planner, codereviewer)
- [ ] Update ARCHITECTURE.md

**Deliverable:** Working subagents, workflow orchestration, 80%+ test coverage

---

## Phase 4: Consensus & Advanced Workflows (Weeks 7-8)

### Consensus Workflows

- [ ] Design consensus mechanism (collect opinions)
- [ ] Implement multi-model consensus
- [ ] Implement conflict resolution (when models disagree)
- [ ] Implement confidence scoring (weight by model)
- [ ] Add explanation collection (why each model chose X)

### Advanced Patterns

- [ ] Implement token limit bypass (use different models for different limits)
- [ ] Implement context injection (from PAL-MCP patterns)
- [ ] Implement CLI-to-CLI bridging (clink-like)
- [ ] Add vision capabilities (for model analysis)
- [ ] Add local model support (Ollama, Llama)

### Error Handling & Recovery

- [ ] Handle model API timeouts (retry logic)
- [ ] Handle context window overflow
- [ ] Handle subagent failures (graceful degradation)
- [ ] Handle conversation state corruption
- [ ] Add monitoring/alerting

### Testing

- [ ] Integration tests: consensus workflows
- [ ] Integration tests: token limit bypass
- [ ] Chaos tests: API failures, timeouts
- [ ] Load tests: concurrent subagents
- [ ] Coverage: >=80%

**Deliverable:** Advanced workflows, error handling, production-ready

---

## Phase 5: Integration Layer & ACP Adoption (Weeks 9-10)

### AgentAPI Extension

- [ ] Design HTTP routing for thegent agents
- [ ] Implement /agents endpoint (list available agents)
- [ ] Implement /agents/{id}/execute endpoint
- [ ] Implement request/response adapter (normalize formats)
- [ ] Add CLI abstraction layer (Codex, Claude Code, Gemini)
- [ ] Add usage tracking (for governance)

### ACP Protocol Integration (Planned for Future)

- [ ] Review ACP spec (not critical path yet)
- [ ] Create type definitions matching ACP
- [ ] Plan WebSocket transport layer
- [ ] Document integration plan
- [ ] Schedule for v2 (after MVP)

### Context7 Documentation Injection (Optional Phase 6)

- [ ] Research documentation sources (APIs, docs, examples)
- [ ] Implement library docs fetching
- [ ] Implement version detection
- [ ] Add validation layer (against live APIs)
- [ ] Integrate with agent prompts

### Tool Governance (From AiBridge)

- [ ] Create MCP tool registry
- [ ] Implement tool versioning
- [ ] Add tool deprecation tracking
- [ ] Implement request interception (for policies)
- [ ] Add usage tracking

### Testing

- [ ] Integration tests: HTTP routing
- [ ] Integration tests: adapter patterns
- [ ] E2E tests: CLI tool bridging
- [ ] Performance tests: routing overhead
- [ ] Coverage: >=80%

**Deliverable:** Production-ready integration layer, CLI bridging works

---

## Phase 6+: Refinement & Scaling

### Performance Optimization

- [ ] Profile token counting
- [ ] Optimize context passing
- [ ] Cache frequently-used outputs
- [ ] Implement request batching
- [ ] Measure latency per model

### Deployment & Ops

- [ ] Docker image building
- [ ] Kubernetes manifests
- [ ] Health check endpoints
- [ ] Monitoring/observability (metrics, logs)
- [ ] Runbook documentation

### Documentation

- [ ] User guide: how to use multi-model orchestration
- [ ] Developer guide: adding new workflows
- [ ] Operator guide: deployment, scaling, monitoring
- [ ] API reference (auto-generated from code)
- [ ] Architecture decision records

### Quality Assurance

- [ ] Full regression test suite
- [ ] Performance benchmarks
- [ ] Security audit (token handling, API keys)
- [ ] Dependency audit (vulnerabilities)
- [ ] Documentation audit (completeness)

---

## Code Organization Targets

```
src/thegent/orchestration/
├── __init__.py
├── providers/
│   ├── __init__.py
│   ├── base.py                 # ProviderBase abstract class
│   ├── gemini.py               # GeminiProvider
│   ├── openai.py               # OpenAIProvider
│   ├── openrouter.py           # OpenRouterProvider
│   └── registry.py             # ProviderRegistry factory
├── conversation/
│   ├── __init__.py
│   ├── state.py                # ConversationState, MessageHistory
│   ├── thread.py               # ConversationThread
│   └── context.py              # ContextWindow, token counting
├── subagents/
│   ├── __init__.py
│   ├── base.py                 # SubagentBase
│   ├── lifecycle.py            # spawn, isolate, execute, collect
│   ├── roles.py                # Role definitions, specialization
│   └── registry.py             # SubagentRegistry
├── workflows/
│   ├── __init__.py
│   ├── base.py                 # WorkflowBase
│   ├── dag.py                  # DAG validation
│   ├── codereview.py           # CodeReviewWorkflow
│   ├── planner.py              # PlannerWorkflow
│   ├── implement.py            # ImplementWorkflow
│   └── precommit.py            # PrecommitWorkflow
├── consensus/
│   ├── __init__.py
│   ├── engine.py               # ConsensusEngine
│   ├── conflict.py             # ConflictResolution
│   └── scoring.py              # ConfidenceScoring
└── integration/
    ├── __init__.py
    ├── http_routing.py         # HTTP API, AgentAPI patterns
    ├── acp_protocol.py         # ACP integration (future)
    └── context7_injection.py   # Docs injection (future)
```

---

## Key Files to Study (Research Phase)

### PAL-MCP Server (Local or GitHub)

```
/tmp/pal-mcp/
├── server.py                   # Entry point (small, readable)
├── providers/                  # Multi-provider pattern
│   ├── gemini_provider.py     # Study this
│   ├── openai_provider.py     # Study this
│   └── registry.py             # Factory pattern
├── systemprompts/              # Role specialization
│   ├── planner_prompt.py
│   ├── codereview_prompt.py
│   └── __init__.py
├── clink/                      # CLI bridging (future reference)
│   ├── agents/
│   ├── parsers/
│   └── models.py
└── pyproject.toml              # Dependencies
```

### Coder Ecosystem

```
/tmp/agentapi/                  # Go HTTP routing
/tmp/acp/                       # Rust protocol reference
```

---

## Success Criteria per Phase

| Phase | Criterion             | Acceptance                                        |
| ----- | --------------------- | ------------------------------------------------- |
| 1     | Dependencies working  | All imports successful                            |
| 2     | Multi-model threading | Ask 2 models, get 2 responses, context carries    |
| 3     | Subagent spawning     | Spawn agent, runs in isolation, results collected |
| 4     | Consensus             | 3 models vote, conflict resolution works          |
| 5     | HTTP integration      | AgentAPI routes requests correctly                |
| 6     | Deployment ready      | Docker image runs, K8s manifests work             |

---

## Blocked By / Dependencies

- [ ] ACP v1.0 stable (for Phase 5 ACP integration, not critical path)
- [ ] PAL-MCP API stability (monitor for breaking changes)
- [ ] Thegent core foundation (agents, hooks, dispatch) — assuming done

---

## Known Risks & Mitigations

| Risk                    | Likelihood | Impact | Mitigation                         |
| ----------------------- | ---------- | ------ | ---------------------------------- |
| PAL-MCP API changes     | Medium     | High   | Pin versions, test frequently      |
| Token limit issues      | Medium     | Medium | Test per-provider, document limits |
| Subagent complexity     | Medium     | Medium | Require DAG validation, clear docs |
| State corruption        | Low        | High   | Durable storage, recovery tests    |
| Performance degradation | Low        | Medium | Profiling, caching, benchmarks     |

---

## Sign-Off & Handoff

**Phase Completion Sign-Off Template:**

```markdown
Phase X: [Name]

- [ ] All tasks completed
- [ ] Test coverage >=80%
- [ ] Documentation updated
- [ ] Deliverables working
- [ ] Risks mitigated
- [ ] Ready for next phase

Signed: **\*\***\_\_\_**\*\*** Date: **\*\***\_\_**\*\***
```

---

## Appendix: PAL-MCP Pattern Examples to Extract

### 1. Multi-Provider Factory (Python)

```python
class ProviderRegistry:
    def get_provider(self, provider_name: str, model: str):
        if provider_name == "gemini":
            return GeminiProvider(model)
        elif provider_name == "openai":
            return OpenAIProvider(model)
        # ...
```

### 2. Conversation State

```python
class ConversationThread:
    def __init__(self, thread_id: str):
        self.messages = []  # Full history
        self.models_used = set()

    def add_message(self, role, content, model):
        self.messages.append(
            {
                "role": role,
                "content": content,
                "model": model,  # Track which model sent this
                "timestamp": now(),
            }
        )
```

### 3. Subagent Spawning

```python
def spawn_subagent(role: str, parent_thread: ConversationThread):
    subagent = Subagent(role=role)
    # Isolated context (doesn't see parent's full history)
    subagent.context = parent_thread.summarize_for_role(role)
    return subagent
```

### 4. Workflow Sequencing

```python
class CodeReviewWorkflow:
    async def execute(self):
        # Step 1: Analyze code (Gemini)
        analysis = await self.analyze_code_with_gemini()
        # Step 2: Peer review (O3)
        feedback = await self.review_with_o3(analysis)
        # Step 3: Synthesize (Claude)
        final = await self.synthesize_with_claude(feedback)
        return final
```

---

**For updates, see:** `/docs/research/HEXAGONAL_SPLIT_PROJECT_RESEARCH_20260223.md`
