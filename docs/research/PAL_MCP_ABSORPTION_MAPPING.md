<DONE>
# PAL-MCP Absorption Mapping for thegent Hexagonal Split

**Quick reference**: Which PAL-MCP files/patterns map to which thegent modules.

---

## File Extraction Matrix

| PAL-MCP Source                                | Target Module                 | Thegent File                   | Purpose                                    | Effort |
| --------------------------------------------- | ----------------------------- | ------------------------------ | ------------------------------------------ | ------ |
| `tools/consensus.py`                          | infrastructure/orchestration  | `consensus_engine.py`          | Multi-model debate orchestration           | Medium |
| `tools/clink.py`                              | infrastructure/orchestration  | `subagent_spawner.py`          | CLI subagent isolation + spawning          | Medium |
| `docs/context-revival.md`                     | infrastructure/context        | `revival_handler.py`           | Cross-session continuity                   | High   |
| `systemprompts/consensus_prompt.py`           | docs/reference/system_prompts | `consensus_prompt.md`          | Debate stance structure                    | Low    |
| `systemprompts/codereview_prompt.py`          | docs/reference/system_prompts | `codereview_prompt.md`         | Multi-angle inspection                     | Low    |
| `systemprompts/planner_prompt.py`             | docs/reference/system_prompts | `planner_prompt.md`            | WBS decomposition                          | Low    |
| `systemprompts/refactor_prompt.py`            | docs/reference/system_prompts | `refactor_prompt.md`           | Code transformation                        | Low    |
| `systemprompts/secaudit_prompt.py`            | docs/reference/system_prompts | `secaudit_prompt.md`           | Security analysis                          | Low    |
| `infrastructure/providers/gemini_provider.py` | infrastructure/providers      | `gemini_provider.py` (enhance) | Add thinking modes + context window tuning | Low    |
| (new)                                         | infrastructure/providers      | `grok_provider.py`             | X.AI Grok integration                      | Low    |
| (new)                                         | infrastructure/providers      | `ollama_provider.py`           | Local LLM support                          | Low    |
| (new)                                         | infrastructure/providers      | `openrouter_provider.py`       | Meta-provider (50+ models)                 | Low    |
| (new)                                         | infrastructure/providers      | `provider_auto_selector.py`    | Task-based model selection matrix          | Medium |
| `tools/apilookup.py`                          | application/tools             | `api_lookup_tool.py`           | Real-time API documentation                | Low    |

---

## Domain Model Additions

### 1. Consensus Request/Response

```python
# src/domain/models/orchestration.py

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path


class StanceType(str, Enum):
    SUPPORTIVE = "supportive"
    CRITICAL = "critical"
    NEUTRAL = "neutral"


class ThinkingDepth(int, Enum):
    MINIMAL = 128
    LIGHT = 1024
    MEDIUM = 8192
    HEAVY = 32768


@dataclass
class ConsensusRequest:
    """Multi-model debate request"""

    decision_topic: str
    stances: Dict[str, StanceType]  # model_name → stance
    thinking_depth: ThinkingDepth = ThinkingDepth.MEDIUM
    context_files: List[Path] = None
    focus_areas: List[str] = None  # e.g., ["security", "performance"]
    max_tokens_per_response: int = 2000


@dataclass
class ConsensusResult:
    """Multi-model debate result"""

    model_responses: Dict[str, str]  # model_name → response
    synthesis: str  # Combined recommendation
    confidence: float  # 0.0-1.0 agreement level
    thinking_tokens_used: int
```

### 2. Subagent Spawn Request/Response

```python
# src/domain/models/orchestration.py (continued)

from enum import Enum


class IsolationMode(str, Enum):
    FRESH_CONTEXT = "fresh_context"
    WORKTREE = "worktree"
    DOCKER = "docker"


@dataclass
class SubagentSpawnRequest:
    """CLI subagent isolation request"""

    tool_name: str
    persona: str  # e.g., "code_reviewer", "security_auditor"
    context_budget: int  # Max tokens for isolated context
    timeout_seconds: int = 600
    isolation_mode: IsolationMode = IsolationMode.FRESH_CONTEXT
    output_format: str = "json"  # or "text", "markdown"


@dataclass
class SubagentResult:
    """Subagent execution result"""

    tool_name: str
    persona: str
    result: str
    tokens_used: int
    execution_time_seconds: float
    success: bool
    error_message: Optional[str] = None
```

### 3. Context Revival Trigger

```python
# src/domain/models/context.py


@dataclass
class ContextRevivalTrigger:
    """Detect & trigger cross-session continuity"""

    session_id: str
    prior_session_id: str
    detected_context_reset: bool
    tokens_in_history: int
    preferred_summarizer_model: str = "gemini-2.0"  # 1M context


@dataclass
class ContextSummary:
    """Revival summary returned to current session"""

    summary_text: str
    key_decisions: List[str]
    implementation_status: str
    constraints_and_tradeoffs: List[str]
    tokens_used: int
```

---

## Application Layer Use Cases

### 1. Consensus Orchestrator Use Case

```python
# src/application/orchestration/consensus_use_case.py

from domain.models.orchestration import ConsensusRequest, ConsensusResult
from infrastructure.orchestration.consensus_engine import ConsensusEngine


class ConsensusUseCase:
    def __init__(self, engine: ConsensusEngine, provider_registry: ProviderRegistry):
        self.engine = engine
        self.providers = provider_registry

    async def execute(self, request: ConsensusRequest) -> ConsensusResult:
        """
        Execute multi-model consensus debate.

        1. Validate stances (pro/con/neutral assignment)
        2. Prepare context (files, focus areas)
        3. Route to each model with stance prompt
        4. Collect responses
        5. Synthesize findings
        """
        # Implementation details...
        pass

    async def validate_request(self, request: ConsensusRequest) -> None:
        """Validate request is executable (all models available, etc.)"""
        pass

    async def synthesize_results(self, responses: Dict[str, str]) -> str:
        """Combine multi-model responses into unified recommendation"""
        pass
```

### 2. Subagent Orchestrator Use Case

```python
# src/application/orchestration/subagent_use_case.py

from domain.models.orchestration import SubagentSpawnRequest, SubagentResult
from infrastructure.orchestration.subagent_spawner import SubagentSpawner


class SubagentOrchestratorUseCase:
    def __init__(self, spawner: SubagentSpawner):
        self.spawner = spawner

    async def spawn_and_track(self, request: SubagentSpawnRequest) -> SubagentResult:
        """
        Spawn isolated CLI subagent for specialized task.

        1. Create isolation boundary (fresh context / worktree / container)
        2. Launch CLI process
        3. Pass tool invocation spec
        4. Monitor execution (timeout, resource usage)
        5. Collect result + cleanup
        """
        pass

    async def spawn_multiple(self, requests: List[SubagentSpawnRequest]) -> List[SubagentResult]:
        """Spawn multiple subagents in parallel (max 3 concurrent)"""
        pass

    async def enforce_isolation(self, request: SubagentSpawnRequest) -> None:
        """Prevent context pollution: validate budget, timeout, resource limits"""
        pass
```

### 3. Context Revival Use Case

```python
# src/application/context/context_revival_use_case.py

from domain.models.context import ContextRevivalTrigger, ContextSummary
from infrastructure.context.revival_handler import ContextRevivalHandler


class ContextRevivalUseCase:
    def __init__(self, handler: ContextRevivalHandler):
        self.handler = handler

    async def trigger_if_reset(self, session: AgentSession) -> Optional[ContextSummary]:
        """
        Check if context reset detected. If so, trigger revival.

        1. Compare current token usage vs prior session
        2. If reset detected, query Redis for conversation history
        3. Route to summarizer model (Gemini)
        4. Return summary to current session
        """
        pass

    async def detect_reset(self, session: AgentSession) -> bool:
        """Model inference: Has context window reset?"""
        pass

    async def synthesize_history(self, prior_conversation: List[Dict]) -> ContextSummary:
        """Use Gemini (1M context) to summarize full conversation"""
        pass

    async def store_conversation(self, session_id: str, messages: List[Dict]) -> None:
        """Store conversation in Redis for future revival"""
        pass
```

---

## Infrastructure Layer: New Modules

### 1. Consensus Engine

```python
# src/infrastructure/orchestration/consensus_engine.py

from typing import Dict, List, Optional
from domain.models.orchestration import ConsensusRequest, StanceType, ThinkingDepth
from infrastructure.providers.base_provider import BaseProvider


class ConsensusEngine:
    """Multi-model debate orchestrator"""

    def __init__(self, provider_registry: ProviderRegistry):
        self.providers = provider_registry

    async def orchestrate_debate(self, request: ConsensusRequest) -> Dict[str, str]:
        """
        Route each model with its assigned stance.
        Returns dict of model_name → response.
        """
        tasks = []
        for model_name, stance in request.stances.items():
            prompt = self._build_stance_prompt(request.decision_topic, stance, request.focus_areas)
            task = self.providers.invoke(
                model_name,
                prompt,
                max_tokens=request.max_tokens_per_response,
                thinking_budget=request.thinking_depth.value,
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        return dict(zip(request.stances.keys(), responses))

    def _build_stance_prompt(self, topic: str, stance: StanceType, focus_areas: Optional[List[str]]) -> str:
        """Build prompt with stance instructions"""
        template = """You are participating in a structured debate.

Topic: {topic}

Your assigned stance: {stance}

If your stance is SUPPORTIVE, argue for the proposal.
If your stance is CRITICAL, argue against the proposal.
If your stance is NEUTRAL, present both sides objectively.

Focus areas to address:
{focus_areas}

Provide a clear, well-reasoned response."""

        return template.format(
            topic=topic,
            stance=stance.value,
            focus_areas="\n".join(focus_areas or []),
        )

    async def synthesize(self, responses: Dict[str, str]) -> str:
        """Combine responses into unified recommendation"""
        # Use Gemini or Claude to synthesize
        pass
```

### 2. Subagent Spawner

```python
# src/infrastructure/orchestration/subagent_spawner.py

import asyncio
import subprocess
from typing import Optional
from domain.models.orchestration import (
    SubagentSpawnRequest,
    SubagentResult,
    IsolationMode,
)


class SubagentSpawner:
    """Launch isolated CLI subagents"""

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def spawn(self, request: SubagentSpawnRequest) -> SubagentResult:
        """Spawn isolated subagent process"""
        async with self.semaphore:
            try:
                start_time = time.time()

                # Create isolation boundary based on mode
                if request.isolation_mode == IsolationMode.FRESH_CONTEXT:
                    result = await self._spawn_fresh_context(request)
                elif request.isolation_mode == IsolationMode.WORKTREE:
                    result = await self._spawn_worktree(request)
                elif request.isolation_mode == IsolationMode.DOCKER:
                    result = await self._spawn_docker(request)

                execution_time = time.time() - start_time

                return SubagentResult(
                    tool_name=request.tool_name,
                    persona=request.persona,
                    result=result,
                    tokens_used=0,  # Would be tracked by subagent
                    execution_time_seconds=execution_time,
                    success=True,
                )
            except asyncio.TimeoutError:
                return SubagentResult(
                    tool_name=request.tool_name,
                    persona=request.persona,
                    result="",
                    tokens_used=0,
                    execution_time_seconds=request.timeout_seconds,
                    success=False,
                    error_message=f"Timeout after {request.timeout_seconds}s",
                )
            except Exception as e:
                return SubagentResult(
                    tool_name=request.tool_name,
                    persona=request.persona,
                    result="",
                    tokens_used=0,
                    execution_time_seconds=0,
                    success=False,
                    error_message=str(e),
                )

    async def _spawn_fresh_context(self, request: SubagentSpawnRequest) -> str:
        """Spawn subagent with fresh context window"""
        # Launch isolated process
        proc = subprocess.Popen(
            ["codex-cli", "--fresh-context", f"--budget={request.context_budget}"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                asyncio.to_thread(proc.communicate, input=request.tool_name),
                timeout=request.timeout_seconds,
            )
            return stdout
        except asyncio.TimeoutError:
            proc.kill()
            raise

    async def _spawn_worktree(self, request: SubagentSpawnRequest) -> str:
        """Spawn subagent on git worktree (isolated branch)"""
        # Create worktree, launch agent on branch
        pass

    async def _spawn_docker(self, request: SubagentSpawnRequest) -> str:
        """Spawn subagent in Docker container"""
        # Build + launch container with tool spec
        pass
```

### 3. Context Revival Handler

```python
# src/infrastructure/context/revival_handler.py

import json
from typing import List, Dict, Optional
from domain.models.context import ContextRevivalTrigger, ContextSummary
from infrastructure.storage.redis_client import RedisClient
from infrastructure.providers.base_provider import BaseProvider


class ContextRevivalHandler:
    """Cross-session context continuity via history synthesis"""

    def __init__(self, redis: RedisClient, providers: ProviderRegistry):
        self.redis = redis
        self.providers = providers

    async def detect_reset(self, session_id: str, current_token_count: int) -> bool:
        """
        Detect context reset by comparing current vs prior token counts.

        Logic:
        - If current < prior/2, likely context was reset
        - Or model reports explicit reset signal
        """
        prior_key = f"session:{session_id}:max_tokens"
        prior_tokens = await self.redis.get(prior_key) or 0
        return current_token_count < int(prior_tokens) / 2

    async def store_conversation(self, session_id: str, messages: List[Dict]) -> None:
        """Store conversation in Redis for retrieval after reset"""
        key = f"session:{session_id}:conversation_history"
        await self.redis.set(
            key,
            json.dumps(messages),
            ex=86400 * 7,  # 7 day TTL
        )

    async def retrieve_conversation(self, session_id: str) -> Optional[List[Dict]]:
        """Retrieve prior conversation from Redis"""
        key = f"session:{session_id}:conversation_history"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def trigger_revival(self, trigger: ContextRevivalTrigger) -> ContextSummary:
        """Detect reset & synthesize prior context via summarizer model"""
        # 1. Retrieve conversation history
        prior_conversation = await self.retrieve_conversation(trigger.prior_session_id)
        if not prior_conversation:
            return ContextSummary(
                summary_text="No prior conversation found.",
                key_decisions=[],
                implementation_status="",
                constraints_and_tradeoffs=[],
                tokens_used=0,
            )

        # 2. Use summarizer model (Gemini) to synthesize
        summary_prompt = self._build_summary_prompt(prior_conversation)
        response = await self.providers.invoke(
            trigger.preferred_summarizer_model,
            summary_prompt,
            max_tokens=2000,
        )

        # 3. Parse response into structured summary
        summary = self._parse_summary(response)
        await self.store_conversation(trigger.session_id, prior_conversation)  # Update current session
        return summary

    def _build_summary_prompt(self, conversation: List[Dict]) -> str:
        """Build prompt for Gemini to summarize conversation"""
        conv_text = "\n".join([f"{msg['role']}: {msg['content'][:500]}" for msg in conversation])
        return f"""You are a context revival assistant. A developer's session was interrupted.

Here is the full prior conversation history:

{conv_text}

Please provide a concise summary (1-2 paragraphs) of:
1. Key architectural decisions made
2. Current implementation status
3. Constraints and tradeoffs considered
4. Next steps

Format as JSON:
{{
    "summary": "...",
    "key_decisions": ["..."],
    "implementation_status": "...",
    "constraints": ["..."]
}}"""

    def _parse_summary(self, response: str) -> ContextSummary:
        """Parse Gemini response into ContextSummary"""
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            data = {}

        return ContextSummary(
            summary_text=data.get("summary", ""),
            key_decisions=data.get("key_decisions", []),
            implementation_status=data.get("implementation_status", ""),
            constraints_and_tradeoffs=data.get("constraints", []),
            tokens_used=0,  # Would track actual tokens
        )
```

---

## Provider Extensions

### 1. Grok Provider

```python
# src/infrastructure/providers/grok_provider.py

from infrastructure.providers.base_provider import BaseProvider
from openai import AsyncOpenAI  # Grok uses OpenAI-compatible API


class GrokProvider(BaseProvider):
    """X.AI Grok model provider"""

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
        )
        self.model_name = "grok-2"

    async def invoke(self, prompt: str, max_tokens: int = 2000, thinking_budget: int = 0, **kwargs) -> str:
        """Invoke Grok model"""
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    @property
    def capabilities(self) -> Dict[str, any]:
        return {
            "context_window": 128000,
            "supports_vision": False,
            "supports_thinking": False,
            "cost_per_1m_input": 2.0,
            "cost_per_1m_output": 10.0,
            "specialization": "fast_inference",
        }
```

### 2. Provider Auto-Selector

```python
# src/infrastructure/providers/provider_auto_selector.py

from typing import Dict
from enum import Enum


class TaskType(str, Enum):
    REASONING = "reasoning"
    CODING = "coding"
    FORMATTING = "formatting"
    CREATIVE = "creative"


class ProviderAutoSelector:
    """Auto-select best model for task based on capabilities"""

    # Model decision matrix: (task_type, context_size, budget) → model
    DECISION_MATRIX = {
        (TaskType.REASONING, "large", "high"): "gemini-2.0",  # 1M context
        (TaskType.REASONING, "large", "medium"): "claude-opus-4.6",
        (TaskType.REASONING, "large", "low"): "grok-2",
        (TaskType.REASONING, "medium", "high"): "o3-mini",
        (TaskType.REASONING, "medium", "low"): "grok-2",
        (TaskType.CODING, "large", "high"): "claude-opus-4.6",
        (TaskType.CODING, "large", "low"): "gpt-5-mini",
        (TaskType.CODING, "medium", "high"): "claude-sonnet-4.5",
        (TaskType.CODING, "medium", "low"): "gpt-5-mini",
        (TaskType.FORMATTING, "any", "any"): "gpt-5-mini",  # cheap + fast
    }

    def select(
        self,
        task_type: TaskType,
        context_size: int,
        budget: str = "medium",
        user_override: Optional[str] = None,
    ) -> str:
        """Select model based on task characteristics"""
        if user_override:
            return user_override

        size_bucket = self._bucket_context_size(context_size)
        key = (task_type, size_bucket, budget)

        return self.DECISION_MATRIX.get(key, "claude-sonnet-4.5")  # fallback

    def _bucket_context_size(self, tokens: int) -> str:
        """Bucket context size for decision matrix"""
        if tokens > 100000:
            return "large"
        elif tokens > 50000:
            return "medium"
        else:
            return "small"
```

---

## MCP Tool Registration

### New MCP Tools for thegent

```python
# src/thegent/mcp/mcp_consensus_tool.py

from mcp.server import Server
from mcp.types import Tool, TextContent
from application.orchestration.consensus_use_case import ConsensusUseCase


def register_consensus_tool(server: Server, use_case: ConsensusUseCase):
    """Register consensus MCP tool"""

    @server.call_tool()
    async def consensus(
        topic: str,
        stances: Dict[str, str],  # JSON: {"gpt-5": "supportive", "gemini": "critical"}
        focus_areas: Optional[str] = None,  # Comma-separated
        thinking_depth: str = "medium",
    ) -> TextContent:
        """Multi-model consensus debate tool"""
        request = ConsensusRequest(
            decision_topic=topic,
            stances={k: StanceType(v) for k, v in stances.items()},
            thinking_depth=ThinkingDepth[thinking_depth.upper()],
            focus_areas=focus_areas.split(",") if focus_areas else [],
        )
        result = await use_case.execute(request)
        return TextContent(type="text", text=f"Debate Results:\n{json.dumps(result, indent=2)}")

    server.register_tool(
        Tool(
            name="consensus",
            description="Multi-model debate to reach structured consensus",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Decision topic"},
                    "stances": {
                        "type": "object",
                        "description": 'JSON dict: model name → stance ("supportive"/"critical"/"neutral")',
                    },
                    "focus_areas": {
                        "type": "string",
                        "description": "Comma-separated focus areas (security, performance, cost)",
                    },
                    "thinking_depth": {
                        "type": "string",
                        "enum": ["minimal", "light", "medium", "heavy"],
                    },
                },
                "required": ["topic", "stances"],
            },
        )
    )


# src/thegent/mcp/mcp_clink_tool.py


def register_clink_tool(server: Server, use_case: SubagentOrchestratorUseCase):
    """Register clink (CLI subagent) MCP tool"""

    @server.call_tool()
    async def clink(
        tool_name: str,
        persona: str,
        context_budget: int = 32000,
        timeout_seconds: int = 600,
    ) -> TextContent:
        """Spawn isolated CLI subagent for specialized task"""
        request = SubagentSpawnRequest(
            tool_name=tool_name,
            persona=persona,
            context_budget=context_budget,
            timeout_seconds=timeout_seconds,
        )
        result = await use_case.spawn_and_track(request)
        return TextContent(type="text", text=f"Subagent Result:\n{json.dumps(result.dict(), indent=2)}")

    server.register_tool(
        Tool(
            name="clink",
            description="Spawn isolated CLI subagent (Codex, Gemini CLI, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Tool to invoke (codereview, secaudit, etc.)",
                    },
                    "persona": {
                        "type": "string",
                        "description": "Agent role (reviewer, security_auditor, etc.)",
                    },
                    "context_budget": {
                        "type": "integer",
                        "description": "Max tokens for isolated context",
                    },
                    "timeout_seconds": {"type": "integer"},
                },
                "required": ["tool_name", "persona"],
            },
        )
    )
```

---

## System Prompts to Extract/Create

Create in `docs/reference/system_prompts/`:

1. **consensus_prompt.md** — Setup debate structure, stance clarity
2. **codereview_prompt.md** — Multi-angle code inspection guidelines
3. **planner_prompt.md** — WBS breakdown, phased approach
4. **refactor_prompt.md** — Code transformation rules, patterns
5. **secaudit_prompt.md** — Security analysis (OWASP/CWE mapping)
6. **testgen_prompt.md** — Test case generation strategy
7. **debug_prompt.md** — Incident root cause analysis
8. **context_revival_prompt.md** — Session history summarization

Each should include:

- Purpose
- Input format / constraints
- Output structure
- Example interactions
- Cost estimates

---

## Testing Strategy

### Unit Tests

```
tests/unit/orchestration/
├── test_consensus_engine.py       # Route stances, synthesize
├── test_subagent_spawner.py       # Process isolation, IPC
└── test_provider_auto_selector.py # Task → model mapping

tests/unit/infrastructure/providers/
├── test_grok_provider.py
├── test_ollama_provider.py
└── test_openrouter_provider.py

tests/unit/context/
└── test_revival_handler.py        # Detect reset, synthesize
```

### Integration Tests

```
tests/integration/
├── test_consensus_workflow.py     # Real Gemini + OpenAI calls
├── test_subagent_spawning.py      # Actual CLI launch
└── test_context_revival_e2e.py    # Redis + model calls
```

### E2E Tests

```
tests/e2e/
└── test_multi_model_orchestration.py  # Full workflow: consensus → clink → context-revival
```

---

## Dependencies to Add

### Python packages

```
# pyproject.toml additions

[dependencies]
# New provider libraries
x-ai-sdk>=1.0.0          # For Grok
ollama>=0.1.0            # For local LLMs
openrouter>=1.0.0        # For meta-provider
redis>=5.0.0             # For context history

# Enhanced existing
google-generativeai>=0.5.0  # Add thinking modes support
```

---

## Deployment & Configuration

### Environment Variables

```bash
# New provider keys
export XAI_API_KEY="..."           # X.AI Grok
export OPENROUTER_API_KEY="..."    # OpenRouter
export OLLAMA_API_URL="http://localhost:11434"  # Local LLMs

# Feature flags
export ENABLE_CONTEXT_REVIVAL=true
export ENABLE_SUBAGENT_SPAWNING=true
export REDIS_URL="redis://localhost:6379"

# Cost tracking
export TRACK_MULTI_MODEL_COSTS=true
```

### Docker Configuration

Add to existing docker-compose.yml:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  ollama: # Optional: for local LLM support
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama

volumes:
  redis_data:
  ollama_models:
```

---

## Rollout Phases

### Phase 1: Foundation (Week 1)

- [ ] Create domain models (consensus, subagent, context-revival)
- [ ] Setup system prompts framework
- [ ] Add Grok, Ollama, OpenRouter provider skeletons
- [ ] Create unit test scaffolding

### Phase 2: Workflows (Week 2)

- [ ] Implement ConsensusEngine
- [ ] Implement SubagentSpawner
- [ ] Implement ContextRevivalHandler
- [ ] Unit tests pass (80%+ coverage)

### Phase 3: Integration (Week 3)

- [ ] MCP tool registration (consensus, clink, context-revival)
- [ ] Provider integration tests
- [ ] Cost tracking + monitoring
- [ ] Redis integration

### Phase 4: Polish (Week 4)

- [ ] E2E tests (real provider calls)
- [ ] Documentation + examples
- [ ] Performance optimization
- [ ] Agent persona definitions

---

## Success Criteria

- [ ] Consensus debates work across 3+ models
- [ ] Subagents can spawn isolated Codex CLI instances
- [ ] Context revival recovers prior session knowledge
- [ ] All 7 providers auto-route based on task/cost
- [ ] 100% unit test coverage (core logic)
- [ ] Integration tests pass (real API calls)
- [ ] Cost tracking within 5% accuracy
- [ ] Documentation complete + examples working
