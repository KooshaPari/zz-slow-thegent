<DONE>
# Advanced Agent Orchestration and Optimization Patterns

Comprehensive research on production patterns from academic literature, engineering blogs, and open-source frameworks implementing multi-agent systems, context optimization, streaming, performance tuning, and benchmarking.

---

## 1. Subagent Orchestration Patterns

### 1.1 Sequential vs Parallel Execution

**Sequential Execution: Task Pipeline Pattern**

Best when tasks have strict dependencies (reasoning chains where each step needs previous results).

```python
# Sequential orchestration using LangGraph
from langgraph.graph import StateGraph, START
from typing_extensions import TypedDict


class State(TypedDict):
    query: str
    analysis: str
    decision: str
    result: str


def analyze_input(state: State) -> State:
    """First step: analyze the query"""
    state["analysis"] = f"Analysis of: {state['query']}"
    return state


def make_decision(state: State) -> State:
    """Second step: make decision based on analysis"""
    state["decision"] = f"Decision from: {state['analysis']}"
    return state


def execute_result(state: State) -> State:
    """Third step: execute based on decision"""
    state["result"] = f"Result from: {state['decision']}"
    return state


# Build sequential graph
graph = StateGraph(State)
graph.add_node("analyze", analyze_input)
graph.add_node("decide", make_decision)
graph.add_node("execute", execute_result)

graph.add_edge(START, "analyze")
graph.add_edge("analyze", "decide")
graph.add_edge("decide", "execute")

compiled = graph.compile()
result = compiled.invoke({"query": "What is 2+2?"})
```

**Tradeoffs:**
- ✅ Deterministic, composable, easy to debug
- ✅ Natural for reasoning chains (chain-of-thought)
- ❌ Slower for independent tasks
- ❌ Cannot exploit parallelism

---

**Parallel Execution: Fan-Out Pattern**

Use when multiple subagents can work independently on the same problem.

```python
# Parallel orchestration: multiple experts on same task
import asyncio
from typing import List


class Agent:
    def __init__(self, name: str, specialty: str):
        self.name = name
        self.specialty = specialty

    async def analyze(self, query: str) -> str:
        """Simulate agent thinking"""
        await asyncio.sleep(0.1)  # Simulated work
        return f"{self.name} ({self.specialty}): Analysis of '{query}'"


async def parallel_analysis(query: str) -> List[str]:
    """Launch multiple agents in parallel"""
    agents = [Agent("Alice", "Code"), Agent("Bob", "Testing"), Agent("Charlie", "Architecture")]

    # Fan-out: launch all in parallel
    tasks = [agent.analyze(query) for agent in agents]
    results = await asyncio.gather(*tasks)  # Wait for all

    return results


# Usage
results = asyncio.run(parallel_analysis("Design a new API"))
for result in results:
    print(result)
```

**Tradeoffs:**
- ✅ Exploits independent parallelism
- ✅ Fast for embarrassingly parallel problems
- ❌ Harder to coordinate results
- ❌ Requires aggregation/consensus logic

---

**Hybrid: Directed Acyclic Graph (DAG) Pattern**

Modern approach combining sequential + parallel execution based on dependencies.

```python
# DAG orchestration: dependencies determine parallelism
from dataclasses import dataclass
from typing import Dict, Set, Callable, Any


@dataclass
class Task:
    name: str
    func: Callable
    depends_on: Set[str] = None

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = set()


class DAGOrchestrator:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.results: Dict[str, Any] = {}

    def add_task(self, task: Task):
        self.tasks[task.name] = task

    async def execute(self):
        """Execute DAG respecting dependencies"""
        completed = set()

        while len(completed) < len(self.tasks):
            # Find tasks ready to run (all deps completed)
            ready = [
                name for name, task in self.tasks.items() if name not in completed and task.depends_on <= completed
            ]

            if not ready:
                raise ValueError("Circular dependency detected")

            # Run ready tasks in parallel
            tasks = [asyncio.create_task(self._run_task(name)) for name in ready]
            await asyncio.gather(*tasks)
            completed.update(ready)

    async def _run_task(self, name: str):
        task = self.tasks[name]
        print(f"Executing {name}...")
        self.results[name] = await task.func(self.results)


# Usage
async def example():
    # Build tasks with dependencies
    #    fetch_data
    #   /          \
    # analyze    validate
    #   \        /
    #    combine

    dag = DAGOrchestrator()

    dag.add_task(Task("fetch_data", lambda results: "raw_data"))
    dag.add_task(Task("analyze", lambda results: f"analysis of {results.get('fetch_data')}"))
    dag.add_task(Task("validate", lambda results: f"validation of {results.get('fetch_data')}"))
    dag.add_task(
        Task(
            "combine",
            lambda results: f"combined: {results.get('analyze')} + {results.get('validate')}",
            depends_on={"analyze", "validate"},
        )
    )

    await dag.execute()
    print(dag.results)
```

**Tradeoffs:**
- ✅ Optimal: runs only necessary parallelism
- ✅ Works for complex workflows
- ❌ Requires explicit dependency specification
- ❌ Harder to debug circular dependencies

---

### 1.2 Work Stealing and Load Balancing

**Work Stealing: Queue-Based Load Distribution**

When one worker is idle, it can "steal" work from busier workers' queues.

```python
import asyncio
from collections import deque
from typing import Optional, Callable, Any


class WorkStealingScheduler:
    def __init__(self, num_workers: int = 4):
        self.workers = [deque() for _ in range(num_workers)]
        self.num_workers = num_workers

    def enqueue_task(self, task: Callable, worker_id: int = None):
        """
        Enqueue task. If worker_id not specified, use least-loaded worker.
        """
        if worker_id is None:
            # Use load balancing: assign to least-loaded queue
            worker_id = min(range(self.num_workers), key=lambda i: len(self.workers[i]))

        self.workers[worker_id].append(task)

    async def work_steal_loop(self, worker_id: int):
        """Worker loop with work-stealing capability"""
        my_queue = self.workers[worker_id]

        while True:
            # Try to get work from own queue
            if my_queue:
                task = my_queue.popleft()
                print(f"Worker {worker_id} executing task from own queue")
                await task()
            else:
                # Work stealing: find another worker with tasks
                victim = None
                max_load = 0
                for other_id in range(self.num_workers):
                    if other_id != worker_id and len(self.workers[other_id]) > max_load:
                        max_load = len(self.workers[other_id])
                        victim = other_id

                if victim is not None:
                    # Steal half of victim's tasks
                    stolen_count = len(self.workers[victim]) // 2
                    for _ in range(stolen_count):
                        my_queue.append(self.workers[victim].popleft())
                    print(f"Worker {worker_id} stole {stolen_count} tasks from {victim}")
                else:
                    # No work available
                    await asyncio.sleep(0.01)


class LoadBalancer:
    """Alternative: centralized load balancing with cost awareness"""

    def __init__(self, num_workers: int = 4):
        self.workers = [{"queue": [], "cost": 0} for _ in range(num_workers)]

    def enqueue_with_cost(self, task: Callable, estimated_cost: float):
        """Assign to worker with lowest total cost"""
        cheapest = min(range(len(self.workers)), key=lambda i: self.workers[i]["cost"])
        self.workers[cheapest]["queue"].append(task)
        self.workers[cheapest]["cost"] += estimated_cost

    def rebalance(self):
        """Periodically rebalance when costs diverge"""
        total_cost = sum(w["cost"] for w in self.workers)
        target_cost = total_cost / len(self.workers)

        for worker in self.workers:
            if worker["cost"] > target_cost * 1.5:
                # This worker is overloaded; mark for migration
                worker["migrate"] = True
```

**Tradeoffs:**
- ✅ Prevents worker starvation
- ✅ Better throughput than static assignment
- ❌ Adds coordination overhead
- ❌ Cache locality suffers (tasks move between workers)
- ❌ Requires synchronization (lock-free queues help)

---

### 1.3 Communication Patterns

**Message Passing: Publish-Subscribe Pattern**

Decoupled agent communication via event streams.

```python
# Event-driven multi-agent coordination
from dataclasses import dataclass
from typing import Callable, List
import asyncio


@dataclass
class Event:
    event_type: str
    data: dict
    source: str


class EventBus:
    def __init__(self):
        self.subscribers: dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe handler to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    async def publish(self, event: Event):
        """Publish event to all subscribers"""
        if event.event_type in self.subscribers:
            # Fire and forget (or gather for sync)
            tasks = [handler(event) for handler in self.subscribers[event.event_type]]
            await asyncio.gather(*tasks, return_exceptions=True)


class Agent:
    def __init__(self, name: str, bus: EventBus):
        self.name = name
        self.bus = bus
        self.state = {}
        # Subscribe to relevant events
        self.bus.subscribe("data_ready", self.on_data_ready)
        self.bus.subscribe("result", self.on_result)

    async def on_data_ready(self, event: Event):
        """Handle incoming data"""
        print(f"{self.name} received data from {event.source}: {event.data}")
        self.state["input"] = event.data

        # Process and emit result
        result = f"Processed: {event.data['content']}"
        await self.bus.publish(Event("result", {"result": result}, self.name))

    async def on_result(self, event: Event):
        """Handle results from other agents"""
        if event.source != self.name:
            print(f"{self.name} sees result from {event.source}")


# Usage
async def example():
    bus = EventBus()

    agents = [Agent("DataProcessor", bus), Agent("Analyzer", bus), Agent("Aggregator", bus)]

    # Trigger workflow
    await bus.publish(Event("data_ready", {"content": "raw_input"}, "Source"))
    await asyncio.sleep(0.1)  # Let async tasks complete
```

**Shared State Pattern: State Dictionary**

Direct shared state for tightly-coupled agent interactions.

```python
class SharedStateCoordinator:
    def __init__(self):
        self.state = {
            "data": None,
            "analysis": None,
            "decision": None,
            "locks": {},  # For coordination
        }

    def agent1_process(self):
        """Agent 1: fetch and store data"""
        self.state["data"] = "fetched_data"
        print(f"Agent 1: stored data = {self.state['data']}")

    def agent2_analyze(self):
        """Agent 2: wait for data, then analyze"""
        while self.state["data"] is None:
            pass  # Spin (bad) - should use Event instead

        self.state["analysis"] = f"Analysis of {self.state['data']}"
        print(f"Agent 2: analysis = {self.state['analysis']}")

    def agent3_decide(self):
        """Agent 3: wait for analysis, then decide"""
        while self.state["analysis"] is None:
            pass

        self.state["decision"] = "Decision based on analysis"
        print(f"Agent 3: decision = {self.state['decision']}")
```

**Tradeoffs:**
| Pattern | Latency | Coupling | Ordering | Ordering |
|---------|---------|----------|----------|----------|
| Event Bus (Async) | ⭐⭐⭐⭐ (Low latency) | ⭐⭐⭐⭐ (Decoupled) | ⭐⭐ (Eventually consistent) | ⭐⭐⭐ |
| Shared State | ⭐⭐⭐⭐⭐ (Instant) | ⭐ (Tightly coupled) | ⭐⭐⭐⭐⭐ (Sequential) | ⭐ |
| Message Queue | ⭐⭐⭐ (Medium) | ⭐⭐⭐ (Loose) | ⭐⭐⭐ (FIFO) | ⭐⭐⭐ |

---

### 1.4 Agent Pooling and Recycling

**Connection Pool Pattern: Reuse Agent Instances**

```python
from typing import Optional
import asyncio


class AgentPool:
    """Manage pool of reusable agent instances"""

    def __init__(self, agent_factory, pool_size: int = 4):
        self.factory = agent_factory
        self.pool_size = pool_size
        self.available: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        self.in_use = 0

    async def initialize(self):
        """Create initial agents"""
        for _ in range(self.pool_size):
            agent = await self.factory()
            await self.available.put(agent)

    async def acquire(self) -> "Agent":
        """Get an agent from pool (wait if none available)"""
        agent = await self.available.get()
        self.in_use += 1
        return agent

    async def release(self, agent: "Agent"):
        """Return agent to pool"""
        self.in_use -= 1
        await self.available.put(agent)

    async def context_manager(self):
        """Use with 'async with' for automatic release"""
        agent = await self.acquire()
        try:
            return agent
        finally:
            await self.release(agent)


# Usage
class LLMAgent:
    def __init__(self, model: str):
        self.model = model
        self.context = ""  # State to persist

    async def reset(self):
        """Reset agent for reuse"""
        self.context = ""

    async def process(self, task: str) -> str:
        return f"Result from {self.model}: {task}"


async def example():
    pool = AgentPool(lambda: LLMAgent("gpt-4"), pool_size=4)
    await pool.initialize()

    async def worker(task_id: int):
        agent = await pool.acquire()
        try:
            result = await agent.process(f"Task {task_id}")
            print(result)
        finally:
            await agent.release(agent)

    # 20 tasks using only 4 agents
    await asyncio.gather(*[worker(i) for i in range(20)])
```

**Dynamic Agent Spawning: Scale on Demand**

```python
class DynamicAgentOrchestrator:
    def __init__(self, min_agents: int = 2, max_agents: int = 16):
        self.min_agents = min_agents
        self.max_agents = max_agents
        self.agents = []
        self.queue_length = 0
        self.target_utilization = 0.7  # Keep queue/agents ratio

    def spawn_agent(self) -> "Agent":
        """Spawn a new agent (up to max)"""
        if len(self.agents) < self.max_agents:
            agent = Agent()
            self.agents.append(agent)
            print(f"Spawned agent #{len(self.agents)}")
            return agent
        return None

    def reap_agent(self) -> bool:
        """Kill an idle agent (above minimum)"""
        if len(self.agents) > self.min_agents:
            agent = self.agents.pop()
            print(f"Reaped agent, now {len(self.agents)} agents")
            return True
        return False

    async def adjust_pool(self):
        """Monitor and adjust pool size dynamically"""
        while True:
            utilization = self.queue_length / max(len(self.agents), 1)

            if utilization > self.target_utilization:
                # Spawn more agents
                self.spawn_agent()
            elif utilization < self.target_utilization / 2:
                # Kill idle agents
                self.reap_agent()

            await asyncio.sleep(5)  # Check every 5 seconds
```

**Tradeoffs:**
- ✅ Reduces agent creation overhead
- ✅ Amortizes LLM API calls
- ❌ Requires careful state reset to avoid context leakage
- ❌ Maximum pool size limits scalability

---

### 1.5 Dynamic Agent Spawning Strategies

**Strategies based on recent research (AgentConductor, AdaptOrch):**

```python
# Topology-aware spawning
class AdaptiveOrchestrator:
    """
    Based on research papers AdaptOrch and AgentConductor:
    - Parallel topology: no dependencies, spawn all agents
    - Sequential topology: 1 agent waits, others spawned in pipeline
    - Hierarchical topology: spawn manager + worker agents
    - Hybrid: mix based on task analysis
    """

    @staticmethod
    def analyze_task(task_spec: dict) -> str:
        """Analyze task dependencies to pick topology"""
        dependencies = task_spec.get("dependencies", [])
        num_subtasks = task_spec.get("num_subtasks", 1)

        if not dependencies:
            return "parallel"  # No deps → all in parallel
        elif len(dependencies) == 1:
            return "sequential"  # Linear chain
        else:
            return "hierarchical"  # DAG → manager + workers

    async def spawn_for_topology(self, topology: str, task: dict) -> list:
        """Spawn agents according to topology"""
        agents = []

        if topology == "parallel":
            # Create one agent per independent subtask
            for subtask in task["subtasks"]:
                agents.append(Agent(subtask))

        elif topology == "sequential":
            # Create pipeline of agents, each processes sequentially
            for step in task["steps"]:
                agents.append(Agent(step, input_queue=agents[-1].output if agents else None))

        elif topology == "hierarchical":
            # Create manager + workers for complex DAG
            manager = Agent("manager", orchestrator=self)
            for worker_task in task["parallel_subtasks"]:
                agents.append(Agent(worker_task, manager=manager))
            agents.insert(0, manager)

        return agents
```

---

## 2. Context Window Optimization

### 2.1 Sliding Window Technique

Process long sequences by maintaining only relevant recent context.

```python
from collections import deque
from typing import List


class SlidingWindowContextManager:
    def __init__(self, max_tokens: int = 4096, overlap: int = 256):
        """
        max_tokens: maximum context window size
        overlap: tokens to carry forward between windows
        """
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.context_history = deque()
        self.current_window = ""

    def add_content(self, text: str, estimate_tokens: int = None):
        """Add new content and manage sliding window"""
        if estimate_tokens is None:
            estimate_tokens = len(text.split()) // 4  # Rough estimate

        # Add to current window
        current_size = len(self.current_window.split()) // 4

        if current_size + estimate_tokens > self.max_tokens:
            # Window full - slide forward
            self._slide_window()

        self.current_window += text + "\n"

    def _slide_window(self):
        """Keep overlap tokens, remove oldest content"""
        lines = self.current_window.split("\n")

        # Calculate which lines to keep (overlap)
        overlap_lines = int(self.overlap / 4)  # Rough token-to-line ratio

        # Archive oldest lines
        archived = "\n".join(lines[:-overlap_lines])
        self.context_history.append(archived)

        # Keep overlap for continuity
        self.current_window = "\n".join(lines[-overlap_lines:])

    def get_context(self) -> str:
        """Get current relevant context for LLM"""
        return self.current_window

    def retrieve_history(self, query: str) -> str:
        """Retrieve relevant historical context (BM25, semantic search)"""
        # Simplified: could use semantic similarity
        # Real implementation would use vector DB
        return list(self.context_history)[-1] if self.context_history else ""


# Usage
manager = SlidingWindowContextManager(max_tokens=2048, overlap=256)
for chunk in long_document.split("\n\n"):
    manager.add_content(chunk)
context = manager.get_context()
```

---

### 2.2 Hierarchical Context Management

**Multi-level context: Summary → Detail**

```python
from typing import Optional


class HierarchicalContextManager:
    def __init__(self):
        self.levels = {
            0: "",  # Summary level
            1: "",  # Intermediate detail
            2: "",  # Full detail
        }

    async def build_hierarchy(self, full_content: str):
        """Build context hierarchy from full content"""
        # Level 2: Full content
        self.levels[2] = full_content

        # Level 1: Intermediate (remove examples, keep structure)
        self.levels[1] = self._extract_intermediate(full_content)

        # Level 0: Summary (key points only)
        self.levels[0] = await self._summarize(full_content)

    def get_context(self, detail_level: int = 2) -> str:
        """Get context at appropriate detail level"""
        return self.levels[detail_level]

    def _extract_intermediate(self, content: str) -> str:
        """Remove verbose examples, keep structure"""
        lines = content.split("\n")
        # Filter out code blocks, examples
        filtered = [line for line in lines if not line.startswith("```") and not line.startswith("Example:")]
        return "\n".join(filtered)

    async def _summarize(self, content: str) -> str:
        """Generate summary using LLM or extractive methods"""
        # Simplified: extract first N lines + key sentences
        sentences = content.split(". ")
        summary = ". ".join(sentences[:3]) + "..."
        return summary

    def switch_level(self, new_level: int):
        """Dynamically adjust detail as needed"""
        if len(self.get_context(new_level).split()) > self.max_tokens:
            return self.switch_level(new_level - 1)
        return self.get_context(new_level)
```

---

### 2.3 Context Compression and Summarization

**Extractive and abstractive compression:**

```python
from typing import List
import json


class ContextCompressor:
    """Reduce context size while preserving critical information"""

    @staticmethod
    def extractive_compression(text: str, ratio: float = 0.3) -> str:
        """Keep most important sentences"""
        sentences = text.split(". ")
        # Simple: keep first (ratio) of sentences
        # Better: use TF-IDF or LLM scoring
        keep_count = max(1, int(len(sentences) * ratio))
        return ". ".join(sentences[:keep_count])

    @staticmethod
    async def abstractive_compression(text: str, target_tokens: int = 256) -> str:
        """Use LLM to generate summary (better quality)"""
        # Pseudo-code: actual LLM call
        summary = await llm.summarize(text, target_tokens=target_tokens)
        return summary

    @staticmethod
    def semantic_compression(tokens: List[str], embeddings) -> List[str]:
        """Keep semantically diverse tokens, remove redundant ones"""
        # Iterate: for each new token, if similar to existing, skip
        kept = []
        threshold = 0.85  # Similarity threshold

        for token in tokens:
            is_redundant = any(similarity(token, existing) > threshold for existing in kept)
            if not is_redundant:
                kept.append(token)

        return kept

    @staticmethod
    def json_compression(data: dict) -> dict:
        """Compress structured data by removing low-signal fields"""
        # Remove: null values, empty arrays, default values
        compressed = {k: v for k, v in data.items() if v not in (None, [], {}, "", 0, False)}
        return compressed


# Usage
original = "Long document text... " * 1000
compressed = ContextCompressor.extractive_compression(original, ratio=0.2)
```

---

### 2.4 Memory-Efficient Patterns

**Streaming + windowed processing:**

```python
class StreamingContextProcessor:
    """Process documents without holding entire context in memory"""

    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.buffer = ""
        self.results = []

    async def process_stream(self, stream):
        """Process streaming input chunk by chunk"""
        async for chunk in stream:
            self.buffer += chunk

            # When buffer is large enough, process and slide
            while len(self.buffer) >= self.chunk_size:
                window = self.buffer[: self.chunk_size]
                result = await self.process_window(window)
                self.results.append(result)

                # Slide with overlap
                self.buffer = self.buffer[self.chunk_size - self.overlap :]

    async def process_window(self, window: str):
        """Process single window without keeping full context"""
        # Could call LLM on this window
        return f"Processed: {window[:50]}..."
```

---

### 2.5 Multi-Turn Conversation Handling

**Managing conversation history efficiently:**

```python
from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = None
    tokens: int = 0


class ConversationManager:
    def __init__(self, max_window_tokens: int = 4096, keep_system: bool = True):
        self.max_window_tokens = max_window_tokens
        self.keep_system = keep_system
        self.system_prompt = ""
        self.messages: List[Message] = []

    def add_message(self, role: str, content: str):
        """Add message and auto-truncate if needed"""
        msg = Message(role, content, datetime.now(), len(content.split()))
        self.messages.append(msg)
        self._enforce_window()

    def _enforce_window(self):
        """Keep messages within context window"""
        # Always keep system prompt
        base_tokens = len(self.system_prompt.split())
        available = self.max_window_tokens - base_tokens

        current = 0
        keep_from = 0

        # Iterate from most recent backwards
        for i in range(len(self.messages) - 1, -1, -1):
            current += self.messages[i].tokens
            if current > available:
                keep_from = i + 1
                break

        # Discard old messages (but log them)
        if keep_from > 0:
            discarded = self.messages[:keep_from]
            print(f"Discarded {len(discarded)} old messages to fit window")

        self.messages = self.messages[keep_from:]

    def get_context(self) -> List[dict]:
        """Get formatted context for LLM"""
        context = []

        if self.keep_system:
            context.append({"role": "system", "content": self.system_prompt})

        for msg in self.messages:
            context.append({"role": msg.role, "content": msg.content})

        return context

    def summarize_old_messages(self, keep_recent: int = 5):
        """Summarize older messages to recover tokens"""
        if len(self.messages) <= keep_recent:
            return

        old = self.messages[:-keep_recent]
        summary = f"[Previous conversation summary: Discussed {len(old)} exchanges about ...]"

        # Replace old messages with summary
        self.messages = [
            Message("system", summary, old[0].timestamp, len(summary.split())),
            *self.messages[-keep_recent:],
        ]
```

**Tradeoff Summary:**
| Technique | Token Savings | Quality Impact | Complexity |
|-----------|---------------|----------------|-----------|
| Sliding Window | 60-70% | Minimal (with overlap) | Low |
| Hierarchical | 70-80% | Moderate (loses detail) | Medium |
| Summarization | 80-90% | High (abstractive better) | High |
| Message Culling | 40-50% | Low (loses history) | Low |

---

## 3. Streaming and Real-Time Capabilities

### 3.1 Token-by-Token Streaming

**Incremental output with backpressure:**

```python
import asyncio
from typing import AsyncGenerator


class TokenStreamer:
    def __init__(self, backpressure_threshold: int = 10):
        self.token_queue: asyncio.Queue = asyncio.Queue()
        self.backpressure_threshold = backpressure_threshold

    async def stream_tokens(self) -> AsyncGenerator[str, None]:
        """Stream tokens with backpressure handling"""
        while True:
            # Backpressure: slow down producer if queue gets large
            if self.token_queue.qsize() > self.backpressure_threshold:
                await asyncio.sleep(0.01)

            try:
                token = self.token_queue.get_nowait()
                yield token
            except asyncio.QueueEmpty:
                # Check if stream is done
                if self.is_complete:
                    break
                await asyncio.sleep(0.001)

    async def add_token(self, token: str):
        """Producer: add tokens to stream"""
        await self.token_queue.put(token)

    # Mock LLM streaming
    async def mock_llm_stream(self):
        """Simulate LLM producing tokens"""
        response = "The quick brown fox jumps over the lazy dog"
        for token in response.split():
            await self.add_token(token + " ")
            await asyncio.sleep(0.05)  # Simulate network delay
        self.is_complete = True


# Usage
async def example():
    streamer = TokenStreamer()

    # Start LLM in background
    llm_task = asyncio.create_task(streamer.mock_llm_stream())

    # Consume stream
    async for token in streamer.stream_tokens():
        print(token, end="", flush=True)

    await llm_task
    print()
```

---

### 3.2 Partial Result Handling

**Work with incomplete results in real-time:**

```python
from enum import Enum
from dataclasses import dataclass


class ResultStatus(Enum):
    PARTIAL = "partial"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class PartialResult:
    status: ResultStatus
    content: str
    confidence: float = 1.0
    error: str = None


class PartialResultHandler:
    """Handle streaming results as they arrive"""

    def __init__(self, on_partial=None, on_complete=None):
        self.on_partial = on_partial
        self.on_complete = on_complete
        self.accumulated = ""

    async def process_chunk(self, chunk: str):
        """Process incoming chunk"""
        self.accumulated += chunk

        # Check if we have complete units
        while "\n" in self.accumulated:
            line, self.accumulated = self.accumulated.split("\n", 1)

            result = PartialResult(
                status=ResultStatus.PARTIAL,
                content=line,
                confidence=0.8,  # Partial confidence lower
            )

            if self.on_partial:
                await self.on_partial(result)

        # Emit final result
        if self.is_stream_done:
            result = PartialResult(status=ResultStatus.COMPLETE, content=self.accumulated, confidence=1.0)
            if self.on_complete:
                await self.on_complete(result)


# Usage: UI can render partial results immediately
async def on_partial(result):
    print(f"[Partial] {result.content} (confidence: {result.confidence})")


async def on_complete(result):
    print(f"[Complete] {result.content}")


handler = PartialResultHandler(on_partial, on_complete)
```

---

### 3.3 Backpressure Mechanisms

**Flow control: slow producer, prevent consumer overflow:**

```python
class BackpressureManager:
    """Prevent memory overflow when producer > consumer"""

    def __init__(self, max_buffer: int = 100):
        self.max_buffer = max_buffer
        self.buffer = asyncio.Queue(maxsize=max_buffer)
        self.paused = False

    async def produce(self, item):
        """Producer: add item, auto-pause if full"""
        if self.buffer.full():
            self.paused = True
            print("⚠️  Buffer full, pausing producer")

        await self.buffer.put(item)

        # Signal producer to resume if we drop below threshold
        if self.buffer.qsize() < self.max_buffer * 0.5:
            self.paused = False

    async def consume(self):
        """Consumer: pull items, signal producer when ready"""
        while True:
            item = await self.buffer.get()
            yield item
            self.buffer.task_done()


# HTTP streaming with backpressure
async def stream_response(request, handler):
    """HTTP response streaming with backpressure"""
    backpressure = BackpressureManager(max_buffer=50)

    # Start producer in background
    producer_task = asyncio.create_task(handler.produce_stream(backpressure.produce))

    async def response_generator():
        async for item in backpressure.consume():
            yield item + "\n"

    return response_generator()
```

---

### 3.4 Incremental Rendering

**Update UI/display as data arrives:**

```python
class IncrementalRenderer:
    """Update output incrementally (web, terminal, etc)"""

    def __init__(self, render_fn=None):
        self.render_fn = render_fn or print
        self.buffer = ""
        self.line_num = 0

    async def append(self, chunk: str):
        """Append chunk and render lines"""
        self.buffer += chunk

        # Render complete lines immediately
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            self.render_fn(f"{self.line_num}: {line}")
            self.line_num += 1

    async def finish(self):
        """Render remaining buffer"""
        if self.buffer:
            self.render_fn(f"{self.line_num}: {self.buffer}")


# Web streaming example
@app.post("/stream")
async def stream_endpoint():
    renderer = IncrementalRenderer(render_fn=lambda x: send_to_client(x))

    async for chunk in llm.stream_response(user_query):
        await renderer.append(chunk)

    await renderer.finish()
    return {"status": "complete"}
```

---

### 3.5 Live Progress Updates

**Real-time status for long-running operations:**

```python
import time
from typing import Callable, Optional
from dataclasses import dataclass


@dataclass
class Progress:
    current: int
    total: int
    percent: float = 0.0
    rate: float = 0.0  # items/sec
    eta_seconds: int = 0
    message: str = ""

    def __post_init__(self):
        self.percent = 100 * self.current / self.total if self.total else 0
        if self.rate > 0:
            remaining = self.total - self.current
            self.eta_seconds = int(remaining / self.rate)


class ProgressTracker:
    def __init__(self, total: int, update_callback: Callable[[Progress], None]):
        self.total = total
        self.current = 0
        self.update_callback = update_callback
        self.start_time = time.time()
        self.last_update = self.start_time

    async def update(self, increment: int = 1, message: str = ""):
        """Update progress"""
        self.current += increment
        now = time.time()

        # Only update UI every N updates (to avoid thrashing)
        if now - self.last_update > 0.1:  # 100ms updates
            elapsed = now - self.start_time
            rate = self.current / elapsed if elapsed > 0 else 0

            progress = Progress(current=self.current, total=self.total, rate=rate, message=message)

            await self.update_callback(progress)
            self.last_update = now


# Usage
async def process_items(items):
    async def on_progress(p: Progress):
        print(
            f"\r[{p.percent:3.0f}%] {p.current}/{p.total} ({p.rate:.1f}/s, ETA: {p.eta_seconds}s) - {p.message}",
            end="",
            flush=True,
        )

    tracker = ProgressTracker(len(items), on_progress)

    for i, item in enumerate(items):
        # Process item
        await process(item)
        await tracker.update(1, f"Processing {item.name}")

    print()  # Final newline
```

---

## 4. Performance Optimization Techniques

### 4.1 Caching Strategies

**Exact Match Cache (Traditional):**

```python
from functools import lru_cache
import hashlib
import json


class ExactMatchCache:
    """Cache responses for identical prompts"""

    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _key(self, prompt: str, model: str) -> str:
        """Generate cache key"""
        content = f"{model}:{prompt}".encode()
        return hashlib.md5(content).hexdigest()

    def get(self, prompt: str, model: str):
        """Retrieve cached response"""
        key = self._key(prompt, model)
        if key in self.cache:
            self.hits += 1
            return self.cache[key]

        self.misses += 1
        return None

    def set(self, prompt: str, model: str, response: str):
        """Cache response"""
        if len(self.cache) >= self.max_size:
            # LRU eviction
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        key = self._key(prompt, model)
        self.cache[key] = response

    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
```

**Semantic Cache (Embedding-based):**

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class SemanticCache:
    """Cache based on semantic similarity, not exact match"""

    def __init__(self, embedding_model, similarity_threshold: float = 0.85):
        self.embedding_model = embedding_model
        self.threshold = similarity_threshold
        self.cache = {}
        self.embeddings = {}

    async def get(self, prompt: str):
        """Find cached response for semantically similar prompt"""
        # Embed query
        query_embedding = await self.embedding_model.embed(prompt)

        # Compare to cached prompts
        for cached_prompt, cached_response in self.cache.items():
            cached_embedding = self.embeddings[cached_prompt]

            similarity = cosine_similarity([query_embedding], [cached_embedding])[0][0]

            if similarity > self.threshold:
                print(f"✓ Semantic cache hit (sim={similarity:.3f})")
                return cached_response

        return None

    async def set(self, prompt: str, response: str):
        """Cache with embedding"""
        embedding = await self.embedding_model.embed(prompt)
        self.cache[prompt] = response
        self.embeddings[prompt] = embedding


# Usage
semantic_cache = SemanticCache(embedding_model=your_embedder)

# "What is 2+2?" and "Compute 2 + 2" → same cache hit
result = await semantic_cache.get("Compute 2 plus 2")
if not result:
    result = await llm.query("Compute 2 plus 2")
    await semantic_cache.set("Compute 2 plus 2", result)
```

**Hierarchical Cache (L1/L2):**

```python
class HierarchicalCache:
    """L1 (fast, small) + L2 (slower, large)"""

    def __init__(self, l1_size: int = 100, l2_size: int = 10000):
        self.l1 = {}  # In-memory, fast
        self.l2 = {}  # Disk or Redis, slower but larger
        self.l1_size = l1_size
        self.l2_size = l2_size

    def get(self, key: str):
        """Check L1, then L2"""
        # Check fast cache first
        if key in self.l1:
            return self.l1[key]

        # Check slow cache
        if key in self.l2:
            # Promote to L1
            value = self.l2[key]
            self._promote_to_l1(key, value)
            return value

        return None

    def set(self, key: str, value: str):
        """Set in L1 (push to L2 if needed)"""
        self.l1[key] = value

        # Overflow to L2
        if len(self.l1) > self.l1_size:
            oldest = next(iter(self.l1))
            self.l2[oldest] = self.l1.pop(oldest)

    def _promote_to_l1(self, key: str, value):
        """Promote from L2 to L1"""
        self.l1[key] = value
        del self.l2[key]

        # Evict from L1 if full
        if len(self.l1) > self.l1_size:
            oldest = next(iter(self.l1))
            del self.l1[oldest]
```

**Tradeoffs:**
| Cache Type | Hit Rate | Speed | Memory | Complexity |
|-----------|----------|-------|--------|-----------|
| Exact Match | 20-40% | Instant | Medium | Low |
| Semantic | 60-80% | ~100ms lookup | Medium | High |
| Hierarchical | 40-70% | Fast (L1) | Large | High |
| Prompt Cache (Claude) | 85%+ | Instant | Offloaded | Very Low |

---

### 4.2 Prefetching and Speculation

**Speculative Decoding: predict next tokens**

```python
class SpeculativeDecoder:
    """Use smaller, faster model to predict next tokens"""

    def __init__(self, main_model, draft_model, num_speculative_tokens: int = 5):
        self.main = main_model
        self.draft = draft_model
        self.num_spec = num_speculative_tokens

    async def decode_speculative(self, prompt: str):
        """
        1. Draft model generates N tokens quickly
        2. Main model validates in parallel
        3. If validation fails, discard & re-sample
        """
        context = prompt

        while True:
            # Step 1: Draft model generates speculative tokens
            draft_tokens = []
            draft_probs = []

            for _ in range(self.num_spec):
                token, prob = await self.draft.predict_next(context)
                draft_tokens.append(token)
                draft_probs.append(prob)
                context += token

            # Step 2: Main model validates all tokens in ONE pass
            main_probs = await self.main.validate_sequence(prompt, draft_tokens)

            # Step 3: Check if tokens match (high probability in main model)
            matches = sum(
                1
                for draft_p, main_p in zip(draft_probs, main_probs)
                if abs(draft_p - main_p) < 0.1  # Similar probability
            )

            if matches == self.num_spec:
                # All speculated tokens accepted! Done.
                yield "".join(draft_tokens)
                return
            else:
                # Reject divergent token, backtrack
                context = prompt + "".join(draft_tokens[:matches])
                yield "".join(draft_tokens[: matches + 1])
```

**Prefetch for Batch Queries:**

```python
class BatchPrefetcher:
    """Prefetch results for likely next queries"""

    def __init__(self, llm_model):
        self.model = llm_model
        self.prefetch_queue = asyncio.Queue()
        self.prefetch_cache = {}

    async def start_prefetching(self):
        """Background task: prefetch likely queries"""
        while True:
            try:
                query = self.prefetch_queue.get_nowait()
                result = await self.model.query(query)
                self.prefetch_cache[query] = result
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.01)

    async def query(self, user_query: str):
        """User query (hits prefetch cache if lucky)"""
        # Check if prefetched
        if user_query in self.prefetch_cache:
            print("✓ Prefetch hit!")
            return self.prefetch_cache.pop(user_query)

        # Otherwise, fetch + prefetch likely next queries
        result = await self.model.query(user_query)

        # Predict likely follow-ups and prefetch
        follow_ups = self._predict_follow_ups(user_query, result)
        for query in follow_ups:
            self.prefetch_queue.put_nowait(query)

        return result

    def _predict_follow_ups(self, query: str, result: str) -> list:
        """Heuristic: predict likely follow-up queries"""
        # Could use: user history, question type, etc.
        follow_ups = [f"{query} (continued)", f"Explain {query}", f"Example of {query}"]
        return follow_ups
```

---

### 4.3 Batching and Request Coalescing

**Dynamic Batching: group requests for efficiency**

```python
import time
from typing import List, Coroutine


class DynamicBatcher:
    """Batch requests to reduce LLM API calls"""

    def __init__(self, batch_timeout: float = 0.1, max_batch_size: int = 32):
        self.batch_timeout = batch_timeout
        self.max_batch_size = max_batch_size
        self.pending = []
        self.batch_ready = asyncio.Event()

    async def add_request(self, request: dict) -> str:
        """Add request to batch"""
        future = asyncio.Future()
        self.pending.append({"request": request, "future": future})

        # Trigger batch if full
        if len(self.pending) >= self.max_batch_size:
            self.batch_ready.set()
        else:
            # Or wait for timeout
            asyncio.create_task(self._timeout_trigger())

        return await future

    async def _timeout_trigger(self):
        """Wait for batch timeout, then trigger"""
        await asyncio.sleep(self.batch_timeout)
        if self.pending:
            self.batch_ready.set()

    async def process_batches(self):
        """Background: process batches as they're ready"""
        while True:
            await self.batch_ready.wait()

            # Process current batch
            batch = self.pending[:]
            self.pending = []
            self.batch_ready.clear()

            # Make single API call
            requests = [item["request"] for item in batch]
            results = await llm.batch_query(requests)

            # Resolve futures
            for item, result in zip(batch, results):
                item["future"].set_result(result)


# Usage
batcher = DynamicBatcher(batch_timeout=0.1)
asyncio.create_task(batcher.process_batches())

# Calls arrive individually but get batched
result1 = await batcher.add_request({"query": "What is 2+2?"})
result2 = await batcher.add_request({"query": "What is 3+3?"})
# Both processed in single API call!
```

---

### 4.4 Resource Pooling

Already covered in **Agent Pooling** section. Key patterns:
- Connection pools (reuse HTTP connections)
- Object pools (avoid allocation overhead)
- Thread pools (for I/O operations)
- Memory pools (preallocate buffers)

---

### 4.5 GC Optimization for Long-Running Agents

**Memory management for extended operations:**

```python
import gc
import psutil


class AgentMemoryManager:
    """Optimize garbage collection for long-running agents"""

    def __init__(self, memory_threshold_mb: int = 1000):
        self.threshold = memory_threshold_mb * 1024 * 1024
        self.process = psutil.Process()
        self.collections = 0

    async def monitor_memory(self):
        """Periodically check and optimize memory"""
        while True:
            rss = self.process.memory_info().rss

            if rss > self.threshold:
                print(f"⚠️  Memory usage: {rss / 1024 / 1024:.0f}MB (threshold: {self.threshold / 1024 / 1024:.0f}MB)")

                # Optimize
                self._optimize_memory()

            await asyncio.sleep(5)  # Check every 5 seconds

    def _optimize_memory(self):
        """Perform memory optimization"""
        # Disable GC, collect, re-enable (more efficient)
        gc.disable()
        collected = gc.collect()  # Manual collect
        gc.enable()

        self.collections += 1
        print(f"GC collected {collected} objects ({self.collections} total collections)")

    async def clear_agent_cache(self, agent):
        """Periodically clear agent internal caches"""
        agent.clear_cache()
        gc.collect()
```

**Streaming to avoid memory accumulation:**

```python
class StreamingLLMResponse:
    """Don't load entire response into memory"""

    async def stream_large_response(self, query: str):
        """Stream response token by token"""
        async with llm.stream(query) as response:
            async for chunk in response:
                yield chunk
                # Don't accumulate in memory!

    async def process_with_streaming(self, query: str):
        """Process response chunks as they arrive"""
        token_count = 0

        async for token in self.stream_large_response(query):
            # Process token immediately
            await self.handle_token(token)
            token_count += 1

            # Yield control periodically
            if token_count % 100 == 0:
                await asyncio.sleep(0)  # Let event loop run
```

---

## 5. Benchmarking and Profiling

### 5.1 Agent Quality Metrics

**Multi-dimensional evaluation framework:**

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TaskDifficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3
    COMPETITION = 4  # State-of-art level


@dataclass
class AgentEvalResult:
    task_id: str
    task_difficulty: TaskDifficulty
    success: bool
    accuracy: float  # 0-1
    latency_ms: float
    cost_tokens: int
    reasoning_steps: int

    def score(self) -> float:
        """Composite score: accuracy * difficulty - penalty"""
        base = self.accuracy * self.task_difficulty.value

        # Penalize slow responses
        latency_penalty = min(0.1, self.latency_ms / 10000)

        # Penalize inefficient reasoning
        efficiency_penalty = min(0.1, (self.reasoning_steps - 3) / 10)

        return base * (1 - latency_penalty - efficiency_penalty)


class AgentBenchmark:
    """Evaluate agent quality across dimensions"""

    def __init__(self, test_suite: list):
        self.tests = test_suite
        self.results = []

    async def run_benchmark(self, agent, num_runs: int = 3) -> dict:
        """Run agent against all tests"""
        for test in self.tests:
            for run in range(num_runs):
                result = await self._run_single_test(agent, test)
                self.results.append(result)

        return self._aggregate_results()

    async def _run_single_test(self, agent, test) -> AgentEvalResult:
        """Run single test with metrics"""
        import time

        start = time.time()
        start_tokens = agent.token_count()

        response = await agent.process(test["query"])

        latency = (time.time() - start) * 1000
        tokens_used = agent.token_count() - start_tokens

        # Grade response
        accuracy = self._grade_response(response, test["expected"])

        return AgentEvalResult(
            task_id=test["id"],
            task_difficulty=test.get("difficulty", TaskDifficulty.MEDIUM),
            success=accuracy > 0.9,
            accuracy=accuracy,
            latency_ms=latency,
            cost_tokens=tokens_used,
            reasoning_steps=self._count_reasoning_steps(agent),
        )

    def _aggregate_results(self) -> dict:
        """Compute aggregate metrics"""
        return {
            "accuracy": np.mean([r.accuracy for r in self.results]),
            "latency_p50": np.percentile([r.latency_ms for r in self.results], 50),
            "latency_p95": np.percentile([r.latency_ms for r in self.results], 95),
            "success_rate": sum(1 for r in self.results if r.success) / len(self.results),
            "avg_tokens": np.mean([r.cost_tokens for r in self.results]),
            "avg_score": np.mean([r.score() for r in self.results]),
        }
```

---

### 5.2 Latency vs Accuracy Tradeoffs

**Pareto frontier analysis:**

```python
import matplotlib.pyplot as plt
from typing import List, Tuple


class LatencyAccuracyAnalysis:
    """Find optimal tradeoff between speed and quality"""

    @staticmethod
    def pareto_frontier(agents: List[tuple]) -> List[tuple]:
        """
        agents: List of (name, latency, accuracy)
        Returns: Non-dominated solutions
        """
        # Sort by latency
        sorted_agents = sorted(agents, key=lambda x: x[1])

        frontier = []
        max_accuracy = 0

        for name, latency, accuracy in sorted_agents:
            if accuracy >= max_accuracy:
                frontier.append((name, latency, accuracy))
                max_accuracy = accuracy

        return frontier

    @staticmethod
    def plot_tradeoff(agents: List[tuple]):
        """Visualize latency-accuracy tradeoff"""
        names, latencies, accuracies = zip(*agents)

        plt.scatter(latencies, accuracies, s=100)

        # Highlight Pareto frontier
        frontier = LatencyAccuracyAnalysis.pareto_frontier(agents)
        frontier_names, frontier_lats, frontier_accs = zip(*frontier)

        plt.plot(frontier_lats, frontier_accs, "r--", label="Pareto Frontier")

        for name, lat, acc in agents:
            plt.annotate(name, (lat, acc))

        plt.xlabel("Latency (ms)")
        plt.ylabel("Accuracy")
        plt.title("Agent Tradeoff Analysis")
        plt.legend()
        plt.show()


# Usage
agents = [
    ("gpt-4 (full)", 5000, 0.95),
    ("gpt-3.5 (fast)", 500, 0.80),
    ("gpt-4 (10% sample)", 800, 0.92),
    ("local-llm (4bit)", 200, 0.70),
]

frontier = LatencyAccuracyAnalysis.pareto_frontier(agents)
LatencyAccuracyAnalysis.plot_tradeoff(agents)
```

---

### 5.3 Cost Optimization Metrics

**Analyze cost efficiency:**

```python
@dataclass
class CostMetrics:
    cost_per_query: float
    tokens_per_query: int
    accuracy: float
    latency_ms: float

    def cost_efficiency_score(self) -> float:
        """Cost per unit of quality"""
        return self.cost_per_query / (self.accuracy + 0.01)

    def throughput(self) -> float:
        """Queries per second"""
        return 1000 / self.latency_ms if self.latency_ms > 0 else 0

    def cost_per_success(self, success_rate: float) -> float:
        """Cost to get one successful answer"""
        return self.cost_per_query / success_rate


class CostAnalyzer:
    """Compare cost across different strategies"""

    @staticmethod
    async def analyze_routing_costs(agents: dict, queries: list):
        """
        agents: {"agent_name": Agent}
        Returns: Cost analysis for each agent
        """
        results = {}

        for agent_name, agent in agents.items():
            total_cost = 0
            total_tokens = 0
            total_accuracy = 0
            total_latency = 0

            for query in queries:
                cost = agent.cost_per_query()
                tokens = agent.tokens_per_query(query)
                accuracy = await agent.evaluate(query)
                latency = await agent.measure_latency(query)

                total_cost += cost
                total_tokens += tokens
                total_accuracy += accuracy
                total_latency += latency

            n = len(queries)
            results[agent_name] = CostMetrics(
                cost_per_query=total_cost / n,
                tokens_per_query=total_tokens // n,
                accuracy=total_accuracy / n,
                latency_ms=total_latency / n,
            )

        return results

    @staticmethod
    def recommend_agent(cost_metrics: dict, priority: str = "cost"):
        """Recommend agent based on optimization priority"""
        if priority == "cost":
            return min(cost_metrics.items(), key=lambda x: x[1].cost_efficiency_score())[0]
        elif priority == "accuracy":
            return max(cost_metrics.items(), key=lambda x: x[1].accuracy)[0]
        elif priority == "speed":
            return max(cost_metrics.items(), key=lambda x: x[1].throughput())[0]
```

---

### 5.4 Throughput Benchmarking

**Measure requests per second under load:**

```python
import asyncio
import time
from typing import Callable


class ThroughputBenchmark:
    """Measure sustained throughput under load"""

    async def benchmark(self, query_generator: Callable, duration_seconds: int = 60, max_concurrent: int = 32):
        """
        Benchmark agent throughput

        Returns:
            queries_per_second: Sustained rate
            p99_latency: 99th percentile latency
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        latencies = []
        query_count = 0

        start_time = time.time()

        async def query_with_limit():
            nonlocal query_count
            async with semaphore:
                query = query_generator()

                t0 = time.time()
                result = await self.agent.process(query)
                latency = (time.time() - t0) * 1000

                latencies.append(latency)
                query_count += 1

        # Launch queries continuously for duration
        tasks = []
        while time.time() - start_time < duration_seconds:
            tasks.append(asyncio.create_task(query_with_limit()))

            # Limit task growth
            if len(tasks) > 1000:
                done, tasks = asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

        elapsed = time.time() - start_time
        qps = query_count / elapsed
        p99_latency = np.percentile(latencies, 99)

        return {
            "queries_per_second": qps,
            "total_queries": query_count,
            "p50_latency_ms": np.percentile(latencies, 50),
            "p95_latency_ms": np.percentile(latencies, 95),
            "p99_latency_ms": p99_latency,
            "max_latency_ms": max(latencies),
        }
```

---

### 5.5 Comparative Analysis Methodologies

**A/B testing framework:**

```python
from enum import Enum
from scipy import stats


class ABTestResult(Enum):
    VARIANT_A_BETTER = "A"
    VARIANT_B_BETTER = "B"
    NO_SIGNIFICANT_DIFFERENCE = "none"


class ABTester:
    """Compare two agent implementations"""

    @staticmethod
    async def ab_test(agent_a, agent_b, test_cases: list, significance_level: float = 0.05):
        """
        Run A/B test with statistical significance
        """
        metrics_a = await ABTester._evaluate_agent(agent_a, test_cases)
        metrics_b = await ABTester._evaluate_agent(agent_b, test_cases)

        # Accuracy comparison
        t_stat, p_value = stats.ttest_ind(metrics_a["accuracies"], metrics_b["accuracies"])

        if p_value < significance_level:
            if metrics_a["mean_accuracy"] > metrics_b["mean_accuracy"]:
                winner = ABTestResult.VARIANT_A_BETTER
            else:
                winner = ABTestResult.VARIANT_B_BETTER
        else:
            winner = ABTestResult.NO_SIGNIFICANT_DIFFERENCE

        return {
            "winner": winner,
            "p_value": p_value,
            "agent_a": {
                "accuracy": metrics_a["mean_accuracy"],
                "latency": metrics_a["mean_latency"],
            },
            "agent_b": {
                "accuracy": metrics_b["mean_accuracy"],
                "latency": metrics_b["mean_latency"],
            },
        }

    @staticmethod
    async def _evaluate_agent(agent, test_cases: list) -> dict:
        """Evaluate single agent"""
        accuracies = []
        latencies = []

        for test in test_cases:
            start = time.time()
            result = await agent.process(test["query"])
            latency = time.time() - start

            accuracy = similarity(result, test["expected"])

            accuracies.append(accuracy)
            latencies.append(latency)

        return {
            "accuracies": accuracies,
            "latencies": latencies,
            "mean_accuracy": np.mean(accuracies),
            "mean_latency": np.mean(latencies),
        }
```

---

## 6. Agent Routing and Selection

### 6.1 Cost-Based Routing

**Route to cheapest agent that meets requirements:**

```python
from dataclasses import dataclass
from typing import List


@dataclass
class AgentProfile:
    name: str
    model: str
    cost_per_token: float
    latency_ms: float
    accuracy: float
    specialties: List[str]  # e.g., ["coding", "math"]


class CostBasedRouter:
    def __init__(self, agents: List[AgentProfile]):
        self.agents = agents

    def route(self, query: str, estimated_tokens: int = 100, required_accuracy: float = 0.9) -> AgentProfile:
        """
        Find cheapest agent that:
        1. Meets accuracy requirement
        2. Handles query specialty (if relevant)
        """
        candidates = [agent for agent in self.agents if agent.accuracy >= required_accuracy]

        if not candidates:
            # Fallback: most accurate agent
            return max(self.agents, key=lambda x: x.accuracy)

        # Among qualified agents, pick cheapest
        cheapest = min(candidates, key=lambda x: x.cost_per_token * estimated_tokens)

        return cheapest


# Usage
agents = [
    AgentProfile("gpt-4", "gpt-4", 0.00003, 4000, 0.95, ["code", "math"]),
    AgentProfile("gpt-3.5", "gpt-3.5-turbo", 0.000001, 500, 0.80, ["general"]),
    AgentProfile("local", "llama-13b", 0.000000, 100, 0.60, ["general"]),
]

router = CostBasedRouter(agents)
best_agent = router.route("Write Python code", estimated_tokens=200)
print(f"Selected: {best_agent.name}")  # Likely gpt-4 for coding
```

---

### 6.2 Capability-Based Selection

**Route based on agent specialization:**

```python
from typing import Dict, Set


class CapabilityMatcher:
    def __init__(self, agents: Dict[str, Set[str]]):
        """
        agents: {"agent_name": {"math", "coding", "writing"}}
        """
        self.agents = agents

    def find_specialists(self, required_capabilities: Set[str]) -> List[str]:
        """Find agents with all required capabilities"""
        specialists = [
            name
            for name, capabilities in self.agents.items()
            if required_capabilities <= capabilities  # Subset check
        ]
        return specialists

    def find_best_match(self, required: Set[str]) -> str:
        """Find agent with best capability match"""
        match_scores = {}

        for name, capabilities in self.agents.items():
            # Intersection: how many required capabilities does agent have?
            match = len(required & capabilities)
            match_scores[name] = match

        return max(match_scores, key=match_scores.get)


# Usage
agents = {
    "math_bot": {"math", "reasoning"},
    "code_bot": {"coding", "debugging", "testing"},
    "general_bot": {"writing", "reasoning", "general"},
}

matcher = CapabilityMatcher(agents)
query_type = {"math", "reasoning"}

# Find specialists
specialists = matcher.find_specialists(query_type)
print(f"Specialists for {query_type}: {specialists}")  # ["math_bot"]

# Find best match for partial requirements
best = matcher.find_best_match({"math", "debugging"})
print(f"Best match: {best}")  # Could be code_bot or math_bot
```

---

### 6.3 Load-Based Balancing

**Route to least-loaded agent:**

```python
import time
from collections import deque


class LoadBalancer:
    def __init__(self, agents: List[str]):
        self.agents = agents
        self.active_tasks = {agent: 0 for agent in agents}
        self.recent_latencies = {agent: deque(maxlen=100) for agent in agents}

    def select_agent(self) -> str:
        """Pick agent with lowest load"""
        # Consider both current load and recent latency
        scores = {}

        for agent in self.agents:
            current_load = self.active_tasks[agent]
            avg_latency = (
                sum(self.recent_latencies[agent]) / len(self.recent_latencies[agent])
                if self.recent_latencies[agent]
                else 0
            )

            # Score: lower is better
            scores[agent] = current_load + (avg_latency / 1000)  # Normalize latency

        return min(scores, key=scores.get)

    async def execute_task(self, task, agent=None):
        """Execute task on selected agent"""
        if agent is None:
            agent = self.select_agent()

        self.active_tasks[agent] += 1

        try:
            start = time.time()
            result = await self._run_on_agent(agent, task)
            latency = (time.time() - start) * 1000

            self.recent_latencies[agent].append(latency)
            return result
        finally:
            self.active_tasks[agent] -= 1
```

---

### 6.4 Specialization Patterns

**Route to specialized expert agents:**

```python
class SpecialistRouter:
    def __init__(self):
        self.specialists = {
            "code": CodeExpertAgent(),
            "math": MathExpertAgent(),
            "reasoning": ReasoningExpertAgent(),
            "general": GeneralAgent(),
        }

    async def route(self, query: str) -> str:
        """Classify query and route to specialist"""

        # Classify query type
        query_type = await self._classify_query(query)

        if query_type in self.specialists:
            agent = self.specialists[query_type]
        else:
            # Multi-specialist for complex queries
            agent = self.specialists["general"]

        return await agent.process(query)

    async def _classify_query(self, query: str) -> str:
        """Use lightweight classifier (or heuristics)"""
        query_lower = query.lower()

        if any(keyword in query_lower for keyword in ["code", "python", "javascript"]):
            return "code"
        elif any(keyword in query_lower for keyword in ["math", "calculate", "equation"]):
            return "math"
        elif any(keyword in query_lower for keyword in ["think", "reason", "logic"]):
            return "reasoning"
        else:
            return "general"
```

---

### 6.5 Multi-Model Fallback Strategies

**Graceful degradation with fallback chain:**

```python
class FallbackRouter:
    def __init__(self, models: List[str], fallback_order: List[str] = None):
        """
        models: List of available model names
        fallback_order: Priority order for fallback (default: models list)
        """
        self.models = models
        self.fallback_order = fallback_order or models
        self.model_status = {model: "available" for model in models}

    async def query_with_fallback(self, query: str, required_quality: float = 0.8):
        """
        Try primary model, fallback to others if it fails
        """

        for model in self.fallback_order:
            if self.model_status[model] != "available":
                continue

            try:
                result = await self._query_model(model, query)

                # Check quality
                quality = self._assess_quality(result)

                if quality >= required_quality:
                    return {
                        "result": result,
                        "model": model,
                        "quality": quality,
                    }

            except Exception as e:
                print(f"Model {model} failed: {e}")
                self.model_status[model] = "error"
                # Continue to next fallback

        # All models exhausted
        raise RuntimeError("All fallback models failed")

    async def _query_model(self, model: str, query: str):
        """Query specific model"""
        # Implementation depends on model provider
        pass

    def _assess_quality(self, result: str) -> float:
        """Rate response quality (0-1)"""
        # Heuristic: longer, more detailed responses score higher
        length_score = min(1.0, len(result.split()) / 100)
        return length_score
```

---

## Summary: Pattern Selection Guide

| Problem | Best Pattern | Why |
|---------|-------------|-----|
| Task dependencies | DAG Orchestration | Optimal parallelism |
| Many independent tasks | Work Stealing | Prevents starvation |
| Tight agent coupling | Shared State | Low latency |
| Loose agent coupling | Event Bus | Decoupled, scalable |
| Long documents | Sliding Window | Memory efficient |
| Chat applications | Multi-turn Manager | Conversation history |
| High cost sensitivity | Semantic Cache | 80%+ hit rate possible |
| Latency critical | Prompt Cache | Instant hits |
| Fast inference | Speculative Decoding | 2-3x speedup |
| Variable load | Dynamic Spawning | Cost effective |
| Quality-cost tradeoff | Cost-based Routing | Optimal choices |
| Complex queries | Specialist Routing | Expert answers |
| Reliability critical | Fallback Chain | Graceful degradation |

---

## Key Research References

**Academic Papers:**
- **AgentConductor** (arXiv:2602.17100) - RL-optimized topology selection
- **AdaptOrch** (arXiv:2602.16873) - Dynamic canonical topologies
- **ThunderAgent** (arXiv:2602.13692) - 1.5-3.6x throughput improvements
- **Agent Communication Protocol** (arXiv:2602.15055) - Federated agent coordination

**Frameworks:**
- LangGraph - Graph-based orchestration with stateful execution
- AutoGen - Message-passing multi-agent architecture
- LangChain - Streaming and component architecture

**Optimization Techniques:**
- Prompt Caching (Claude, OpenAI) - 85%+ cache hit rates
- Semantic Caching - 60-80% hit rates with similarity matching
- Speculative Decoding - 2-3x latency reduction
- Work Stealing - Prevents load imbalance in parallel workloads
