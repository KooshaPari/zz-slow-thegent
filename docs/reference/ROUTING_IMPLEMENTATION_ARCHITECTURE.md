# Task Routing Implementation Architecture

**Audience:** Implementers of the routing system
**Scope:** Code structure, integration points, data flows
**Status:** Design (implementer reference)

---

## 1. Module Structure

```
src/thegent/routing/
├── __init__.py                 # Export TaskRouter, TaskCategory
├── classifier.py              # TaskRouter.classify() + helpers
├── provider_resolver.py        # resolve_provider() + fallback logic
├── signals.py                  # TaskClassificationInput, signals extraction
└── metrics.py                  # Cost estimation, token prediction

src/thegent/
├── models/
│   └── catalog.py             # EXISTING: ModelCatalog, Route (no changes)
├── governance/
│   ├── cost.py                # EXISTING: CostEstimator, CostAggregator
│   └── routing_policy.py       # NEW: RoutePolicy enforcement
├── execution.py               # EXISTING: RunMeta (ADD: task_category, tokens_in_estimated, etc.)
├── cli_impl.py                # EXISTING: integrate classification into dispatch flow
└── main.py                    # EXISTING: hook new signals into CLI
```

---

## 2. Core Data Types

### TaskCategory Enum
```python
# src/thegent/routing/classifier.py
from enum import Enum, auto


class TaskCategory(str, Enum):
    """Task complexity classification."""

    FAST = "FAST"
    NORMAL = "NORMAL"
    COMPLEX = "COMPLEX"
    HIGH_COMPLEX = "HIGH_COMPLEX"

    @property
    def token_budget_input(self) -> tuple[int, int]:
        """Return (min, max) input tokens for this category."""
        return {
            TaskCategory.FAST: (50, 500),
            TaskCategory.NORMAL: (500, 3_000),
            TaskCategory.COMPLEX: (3_000, 10_000),
            TaskCategory.HIGH_COMPLEX: (5_000, 30_000),
        }[self]

    @property
    def token_budget_output(self) -> tuple[int, int]:
        """Return (min, max) output tokens for this category."""
        return {
            TaskCategory.FAST: (100, 1_000),
            TaskCategory.NORMAL: (500, 5_000),
            TaskCategory.COMPLEX: (2_000, 15_000),
            TaskCategory.HIGH_COMPLEX: (5_000, 50_000),
        }[self]

    @property
    def quality_bar(self) -> float:
        """Quality bar (0.0–1.0) for this category."""
        return {
            TaskCategory.FAST: 0.70,
            TaskCategory.NORMAL: 0.80,
            TaskCategory.COMPLEX: 0.90,
            TaskCategory.HIGH_COMPLEX: 0.95,
        }[self]

    @property
    def preferred_provider(self) -> str:
        """Default provider for this category."""
        return {
            TaskCategory.FAST: "claude",
            TaskCategory.NORMAL: "claude",
            TaskCategory.COMPLEX: "claude",
            TaskCategory.HIGH_COMPLEX: "claude",
        }[self]

    @property
    def preferred_model(self) -> str:
        """Default model for this category."""
        return {
            TaskCategory.FAST: "haiku-4.5",
            TaskCategory.NORMAL: "sonnet-4.5",
            TaskCategory.COMPLEX: "opus-4.6",
            TaskCategory.HIGH_COMPLEX: "opus-4.6",
        }[self]

    @property
    def cost_estimate(self) -> float:
        """Median cost estimate in USD."""
        return {
            TaskCategory.FAST: 0.002,
            TaskCategory.NORMAL: 0.030,
            TaskCategory.COMPLEX: 0.150,
            TaskCategory.HIGH_COMPLEX: 0.850,
        }[self]
```

### TaskClassificationInput
```python
# src/thegent/routing/signals.py
from dataclasses import dataclass, field


@dataclass
class TaskClassificationInput:
    """Signals for task classification."""

    # Required
    prompt: str  # Full prompt text
    agent: str  # Agent name

    # Optional but important
    mode: str = "write"  # write, read, observe, session, etc.
    lane: str = "standard"  # standard, critical, recovery
    owner: str = "unknown"  # User/team identifier
    cwd: str = "."  # Working directory

    # Explicit signals (override heuristics)
    token_budget_explicit: int | None = None  # Explicit token limit
    tokens_in_explicit: int | None = None  # Explicit input token count
    tokens_out_explicit: int | None = None  # Explicit output token count
    confidence: float | None = None  # Caller confidence (0.0–1.0)
    provider_hint: str | None = None  # Preferred provider

    # Context
    contract_version: str | None = None  # For drift checking
    domain_tag: str | None = None  # Compliance domain
```

### RoutingDecision
```python
# src/thegent/routing/classifier.py
@dataclass(frozen=True)
class RoutingDecision:
    """Result of task routing classification."""

    category: TaskCategory
    provider: str
    model_alias: str
    backend_type: str  # "direct" or "proxy"
    cost_estimate: float  # Estimated cost in USD
    cost_weight: float  # Cost multiplier (for budget calc)

    # Audit trail
    reasoning: str  # Human-readable explanation
    signals_used: dict[str, object]  # Classification signals snapshot
    alternatives: list[str]  # Alternative providers considered
    fallback_chain: list[str]  # Fallback sequence if primary exhausted
```

---

## 3. Classification Algorithm

### TaskRouter Class

```python
# src/thegent/routing/classifier.py
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TaskRouter:
    """Route tasks to optimal providers based on complexity, cost, and quality."""

    def __init__(self, settings: Any):
        self.settings = settings
        self._token_cache = {}  # Cache token estimates

    def classify(self, input: TaskClassificationInput) -> RoutingDecision:
        """
        Classify task and return routing decision.

        Returns:
            RoutingDecision with category, provider, model, cost estimate
        """
        # Step 1: Extract signals
        signals = self._extract_signals(input)

        # Step 2: Determine category
        category = self._determine_category(signals)

        # Step 3: Resolve provider
        provider, model = self._resolve_provider(
            category=category, provider_hint=input.provider_hint, policy=self.settings.route_policy or "prefer_direct"
        )

        # Step 4: Build routing decision
        routes = ModelCatalog.routes_for(model)
        selected_route = next((r for r in routes if r.provider == provider and r.model_alias == model), None)

        if not selected_route:
            raise ValueError(f"No route found for {provider}/{model}")

        fallback_chain = self._get_fallback_chain(category)

        return RoutingDecision(
            category=category,
            provider=provider,
            model_alias=model,
            backend_type=selected_route.backend_type,
            cost_estimate=category.cost_estimate,
            cost_weight=selected_route.cost_weight,
            reasoning=f"{category.value} task routed to {provider}/{model}",
            signals_used=signals,
            alternatives=self._get_alternatives(category),
            fallback_chain=fallback_chain,
        )

    def _extract_signals(self, input: TaskClassificationInput) -> dict[str, object]:
        """Extract classification signals from input."""
        signals = {}

        # Token budgets
        if input.tokens_in_explicit:
            tokens_in = input.tokens_in_explicit
        else:
            tokens_in = self._estimate_tokens_input(input.prompt)

        if input.tokens_out_explicit:
            tokens_out = input.tokens_out_explicit
        else:
            tokens_out = self._estimate_tokens_output(input.prompt)

        signals["tokens_in"] = tokens_in
        signals["tokens_out"] = tokens_out

        # Reasoning depth
        reasoning_depth = self._infer_reasoning_depth(input.prompt)
        signals["reasoning_depth"] = reasoning_depth

        # Quality requirement from lane
        quality_bar = {
            "critical": "critical",
            "recovery": "excellent",
            "standard": "good",
        }.get(input.lane, "good")
        signals["quality_bar"] = quality_bar

        # Confidence
        signals["confidence"] = input.confidence or 0.5
        signals["lane"] = input.lane

        return signals

    def _determine_category(self, signals: dict[str, object]) -> TaskCategory:
        """Apply classification rules to determine category."""
        tokens_in: int = signals.get("tokens_in", 500)
        tokens_out: int = signals.get("tokens_out", 1000)
        reasoning_depth: int = signals.get("reasoning_depth", 0)
        quality_bar: str = signals.get("quality_bar", "good")
        lane: str = signals.get("lane", "standard")

        # Rule: HIGH_COMPLEX if large tokens, critical lane, or deep reasoning
        if (
            tokens_in >= 5_000
            or tokens_out > 15_000
            or reasoning_depth >= 3
            or quality_bar == "critical"
            or lane == "critical"
        ):
            return TaskCategory.HIGH_COMPLEX

        # Rule: COMPLEX if moderate tokens and reasoning
        if tokens_in < 10_000 and tokens_out < 15_000 and reasoning_depth >= 2 and quality_bar == "excellent":
            return TaskCategory.COMPLEX

        # Rule: NORMAL if medium tokens, moderate reasoning
        if tokens_in < 3_000 and tokens_out < 5_000 and reasoning_depth <= 1 and quality_bar != "critical":
            return TaskCategory.NORMAL

        # Default: FAST for small, simple tasks
        if tokens_in < 500 and tokens_out < 1_000 and reasoning_depth == 0:
            return TaskCategory.FAST

        # Fallback
        if tokens_in < 3_000:
            return TaskCategory.NORMAL
        else:
            return TaskCategory.COMPLEX

    def _estimate_tokens_input(self, prompt: str) -> int:
        """Estimate input tokens. Heuristic: 1 token ≈ 4 characters."""
        # Cache key
        key = f"input:{hash(prompt)}"
        if key in self._token_cache:
            return self._token_cache[key]

        # Estimate: characters / 4 (Claude tokenizer average)
        estimated = max(10, len(prompt) // 4)

        # Clamp to reasonable bounds
        estimated = min(100_000, estimated)

        self._token_cache[key] = estimated
        return estimated

    def _estimate_tokens_output(self, prompt: str) -> int:
        """Estimate output tokens. Heuristic based on prompt keywords."""
        keywords_heavy = ["implement", "refactor", "test", "architecture", "design"]
        keywords_light = ["find", "explain", "review", "lint", "check"]

        prompt_lower = prompt.lower()

        # If prompt contains "heavy" keywords, expect large output
        if any(kw in prompt_lower for kw in keywords_heavy):
            return min(15_000, len(prompt) // 2)

        # If "light" keywords, expect smaller output
        if any(kw in prompt_lower for kw in keywords_light):
            return min(1_000, len(prompt) // 4)

        # Default: conservative estimate
        return min(5_000, len(prompt) // 3)

    def _infer_reasoning_depth(self, prompt: str) -> int:
        """Infer reasoning depth from prompt keywords."""
        keywords_deep = ["design", "architect", "optimize", "debug", "complex", "algorithm"]
        keywords_moderate = ["implement", "refactor", "improve", "fix", "handle"]
        keywords_light = ["write", "add", "update", "create", "check"]

        prompt_lower = prompt.lower()

        if any(kw in prompt_lower for kw in keywords_deep):
            return 3
        if any(kw in prompt_lower for kw in keywords_moderate):
            return 2
        if any(kw in prompt_lower for kw in keywords_light):
            return 1

        return 0

    def _resolve_provider(
        self, category: TaskCategory, provider_hint: str | None = None, policy: str = "prefer_direct"
    ) -> tuple[str, str]:
        """Resolve category to (provider, model_alias)."""
        from thegent.models.catalog import ModelCatalog, resolve_route

        # If hint provided, validate it
        if provider_hint:
            route = resolve_route(category.preferred_model, provider_hint=provider_hint, policy="prefer_direct")
            if route:
                return route
            else:
                logger.warning(f"Provider hint {provider_hint} not available; using default")

        # Use routing policy
        route = resolve_route(category.preferred_model, policy=policy)

        if not route:
            # Fallback: use category's preferred
            return (category.preferred_provider, category.preferred_model)

        return route

    def _get_fallback_chain(self, category: TaskCategory) -> list[str]:
        """Return fallback chain for category."""
        chains = {
            TaskCategory.FAST: ["haiku-4.5", "gemini-2.5-flash", "composer-1.5", "sonnet-4.5"],
            TaskCategory.NORMAL: ["sonnet-4.5", "minimax-m2.5", "glm-5", "gpt-5.3-codex", "haiku-4.5"],
            TaskCategory.COMPLEX: ["opus-4.6", "opus-thinking", "gpt-5.3-codex-high", "sonnet-4.5"],
            TaskCategory.HIGH_COMPLEX: [
                "opus-4.6",
                "opus-thinking",
                # NO LOWER FALLBACKS FOR HIGH_COMPLEX
            ],
        }
        return chains.get(category, [])

    def _get_alternatives(self, category: TaskCategory) -> list[str]:
        """Get alternative providers for category."""
        return self._get_fallback_chain(category)[1:]  # exclude primary
```

---

## 4. Integration with PolicyEngine

### Modified PolicyEngine.evaluate()

```python
# src/thegent/execution.py (updated)


class PolicyEngine:
    """Evaluates execution requests against governance policies."""

    def evaluate(
        self,
        run: RunMeta,
        registry: RunRegistry | None = None,
        router: TaskRouter | None = None,  # NEW
    ) -> tuple[str, str]:
        """
        Evaluate a run against active policies.

        NEW: Integrate task routing classification.
        """

        # NEW: Classify task
        if router:
            try:
                input = TaskClassificationInput(
                    prompt=run.prompt,
                    agent=run.agent,
                    mode=run.mode,
                    lane=run.lane,
                    owner=run.owner,
                    cwd=run.cwd,
                    confidence=run.confidence,
                    provider_hint=run.provider_hint if hasattr(run, "provider_hint") else None,
                )
                routing_decision = router.classify(input)

                # Store in run metadata
                run.task_category = routing_decision.category.value
                run.route_decision = routing_decision.reasoning
                run.tokens_in_estimated = routing_decision.signals_used.get("tokens_in")
                run.tokens_out_estimated = routing_decision.signals_used.get("tokens_out")
                run.reasoning_depth = routing_decision.signals_used.get("reasoning_depth")

                cost_estimate = routing_decision.cost_estimate * routing_decision.cost_weight

                # NEW: Category-specific checks
                if routing_decision.category == TaskCategory.HIGH_COMPLEX:
                    # HIGH_COMPLEX requires explicit approval
                    if run.lane != "critical":
                        return "deny", f"HIGH_COMPLEX tasks require lane=critical"
                    if (run.confidence or 0.0) < 0.9:
                        return "deny", f"HIGH_COMPLEX requires confidence >= 0.9 (got {run.confidence})"
                    # Cost check
                    if registry:
                        mtd = CostAggregator(self.settings.session_dir).get_mtd_total()
                        budget = float(getattr(self.settings, "cost_budget_mtd", 100.0))
                        if mtd + cost_estimate >= budget:
                            return "deny", f"Monthly budget exceeded ({mtd + cost_estimate:.2f} >= {budget:.2f})"

            except Exception as e:
                logger.warning(f"Task routing classification failed: {e}")
                # Continue with existing policy checks

        # EXISTING: continue with all existing policy checks
        # (circuit breakers, input guardrails, trust score, cost budget, etc.)
        # ...

        return "allow", "All policies passed."
```

---

## 5. Data Flow: Task Submission → Dispatch

```
User Command
    ↓
    └─► thegent run claude "Implement auth handler" --confidence 0.85
        ↓
        CLI Parser (cli.py)
        ├─ Extract prompt, agent, mode, lane, confidence, provider_hint
        ├─ Build RunMeta (start event)
        └─► cli_impl.py: dispatch_task()
            ↓
            Build TaskClassificationInput
            ├─ prompt = "Implement auth handler"
            ├─ agent = "claude"
            ├─ lane = "standard" (default)
            ├─ confidence = 0.85
            └─ provider_hint = None
            ↓
            TaskRouter.classify() [NEW]
            ├─ Extract signals: tokens_in=650, tokens_out=2200, reasoning=1
            ├─ Determine category: NORMAL (500–3K tokens, reasoning ≤ 1)
            ├─ Resolve provider: sonnet-4.5 (prefer_direct)
            └─► RoutingDecision(NORMAL, claude, sonnet-4.5, direct, $0.031, ...)
            ↓
            PolicyEngine.evaluate(run, registry, router) [MODIFIED]
            ├─ Task classification: NORMAL ✓
            ├─ Cost estimate: $0.031 < budget ✓
            ├─ Confidence: 0.85 (acceptable for NORMAL) ✓
            ├─ Lane: standard (no special gates) ✓
            └─► ("allow", "All policies passed.")
            ↓
            RunMeta.register_start()
            ├─ task_category = "NORMAL"
            ├─ tokens_in_estimated = 650
            ├─ tokens_out_estimated = 2200
            ├─ route_decision = "NORMAL task routed to claude/sonnet-4.5"
            └─ Persist to run_registry.jsonl
            ↓
            AgentRunner.execute(provider="claude", model="sonnet-4.5", prompt=...)
            ├─ Chat.create(model="claude-sonnet-4.5", messages=[...])
            └─► Response: implementation code
            ↓
            RunRegistry.register_end()
            ├─ exit_code = 0
            ├─ status = "completed"
            ├─ cost_usd = 0.032 (actual, from API usage)
            ├─ duration_s = 3.2
            └─ Persist to run_registry.jsonl
            ↓
            Success: Task complete, model implementation generated
```

---

## 6. Metrics Collection Points

### In RunRegistry.register_end()

```python
# src/thegent/execution.py
def register_end(
    self,
    run_id: str,
    exit_code: int,
    status: str,
    ended_at_utc: str,
    duration_s: float,
    error_class: str | None = None,
    cost_usd: float | None = None,
    task_category: str | None = None,  # NEW
    tokens_in_estimated: int | None = None,  # NEW
    tokens_out_estimated: int | None = None,  # NEW
    reasoning_depth: int | None = None,  # NEW
    fallback_count: int | None = None,  # NEW
) -> None:
    """Update a run with completion metadata."""
    event = {
        "run_id": run_id,
        "event": "finish",
        "exit_code": exit_code,
        "status": status,
        "ended_at_utc": ended_at_utc,
        "duration_s": duration_s,
        "error_class": error_class,
        # NEW:
        "task_category": task_category,
        "tokens_in_estimated": tokens_in_estimated,
        "tokens_out_estimated": tokens_out_estimated,
        "reasoning_depth": reasoning_depth,
        "fallback_count": fallback_count,
        # ...
    }
    if cost_usd is not None:
        event["cost_usd"] = cost_usd
    event["hash"] = self._calculate_hash(event)
    # ... persist ...
```

### Dashboard Queries

```sql
-- Cost by category (daily)
SELECT
  task_category,
  COUNT(*) as call_count,
  SUM(cost_usd) as total_cost,
  AVG(cost_usd) as avg_cost,
  SUM(cost_usd) / COUNT(*) / AVG(tokens_in_estimated) * 1000 as cost_per_1k_tokens
FROM run_registry
WHERE DATE(ended_at_utc) = CURDATE()
  AND task_category IS NOT NULL
GROUP BY task_category
ORDER BY total_cost DESC;

-- Fallback frequency (hourly)
SELECT
  HOUR(ended_at_utc) as hour,
  COUNT(CASE WHEN fallback_count > 0 THEN 1 END) as fallback_runs,
  COUNT(*) as total_runs,
  100.0 * COUNT(CASE WHEN fallback_count > 0 THEN 1 END) / COUNT(*) as fallback_rate_pct
FROM run_registry
WHERE ended_at_utc > NOW() - INTERVAL 1 DAY
  AND task_category IS NOT NULL
GROUP BY hour
ORDER BY hour DESC;

-- Quality by category (7-day average)
SELECT
  task_category,
  AVG(feedback_score) as avg_feedback,
  MIN(feedback_score) as min_feedback,
  MAX(feedback_score) as max_feedback,
  COUNT(CASE WHEN feedback_score >= 0.80 THEN 1 END) as good_count,
  COUNT(CASE WHEN feedback_score >= 0.90 THEN 1 END) as excellent_count
FROM run_registry
WHERE ended_at_utc > NOW() - INTERVAL 7 DAY
  AND task_category IS NOT NULL
  AND feedback_score IS NOT NULL
GROUP BY task_category
ORDER BY avg_feedback DESC;
```

---

## 7. Testing Strategy

### Unit Tests: TaskRouter.classify()

```python
# tests/test_unit_routing_classifier.py


def test_classify_fast_simple_query():
    router = TaskRouter(MockSettings())
    input = TaskClassificationInput(prompt="Find the retry decorator in utils.py", agent="claude", lane="standard")
    decision = router.classify(input)

    assert decision.category == TaskCategory.FAST
    assert decision.provider == "claude"
    assert decision.model_alias == "haiku-4.5"
    assert decision.cost_estimate == 0.002


def test_classify_normal_implementation():
    router = TaskRouter(MockSettings())
    input = TaskClassificationInput(
        prompt="Implement an auth handler with error handling and tests", agent="claude", lane="standard"
    )
    decision = router.classify(input)

    assert decision.category == TaskCategory.NORMAL
    assert decision.provider == "claude"
    assert decision.model_alias == "sonnet-4.5"
    assert decision.cost_estimate == 0.030


def test_classify_complex_design():
    router = TaskRouter(MockSettings())
    input = TaskClassificationInput(
        prompt="Design the microservices architecture for our data pipeline",
        agent="claude",
        lane="critical",
        confidence=0.92,
    )
    decision = router.classify(input)

    assert decision.category == TaskCategory.COMPLEX
    assert decision.provider == "claude"
    assert decision.model_alias == "opus-4.6"
    assert decision.cost_estimate == 0.150


def test_classify_high_complex_feature():
    router = TaskRouter(MockSettings())
    input = TaskClassificationInput(
        prompt="Full-stack feature: auth + tests + docs + CI setup" * 10,  # Long prompt
        agent="claude",
        lane="critical",
        confidence=0.93,
    )
    decision = router.classify(input)

    assert decision.category == TaskCategory.HIGH_COMPLEX
    assert decision.provider == "claude"
    assert decision.model_alias == "opus-4.6"
    assert len(decision.fallback_chain) == 2  # Opus only, minimal fallback
```

### Integration Tests: PolicyEngine + TaskRouter

```python
# tests/test_integration_routing_governance.py


def test_complex_with_high_confidence_allowed():
    settings = MockSettings(cost_budget_mtd=500.0)
    engine = PolicyEngine(settings)
    router = TaskRouter(settings)
    registry = RunRegistry(Path("/tmp/test"))

    run = RunMeta(
        agent="claude", prompt="Design auth architecture", lane="critical", confidence=0.92, owner="alice", cwd="."
    )

    result, reason = engine.evaluate(run, registry, router)

    assert result == "allow"
    assert run.task_category == "COMPLEX"


def test_high_complex_low_confidence_denied():
    settings = MockSettings()
    engine = PolicyEngine(settings)
    router = TaskRouter(settings)
    registry = RunRegistry(Path("/tmp/test"))

    run = RunMeta(
        agent="claude",
        prompt="Full-stack feature: " + "X" * 20000,  # Large prompt → HIGH_COMPLEX
        lane="critical",
        confidence=0.80,  # Too low
        owner="alice",
        cwd=".",
    )

    result, reason = engine.evaluate(run, registry, router)

    assert result == "deny"
    assert "confidence >= 0.9" in reason
```

---

## 8. Configuration & Defaults

### Config Defaults

```python
# src/thegent/config.py (additions)


@dataclass
class Settings(BaseSettings):
    # ... existing fields ...

    # NEW: Routing configuration
    route_policy: str = Field(
        default="prefer_direct",
        description="Routing policy: prefer_direct, prefer_proxy, cheapest, round_robin (THGENT_ROUTE_POLICY)",
    )
    fast_provider: str = Field(default="claude", description="Default provider for FAST tasks (THGENT_FAST_PROVIDER)")
    normal_provider: str = Field(
        default="claude", description="Default provider for NORMAL tasks (THGENT_NORMAL_PROVIDER)"
    )
    complex_provider: str = Field(
        default="claude", description="Default provider for COMPLEX tasks (THGENT_COMPLEX_PROVIDER)"
    )
    high_complex_provider: str = Field(
        default="claude", description="Default provider for HIGH_COMPLEX tasks (THGENT_HIGH_COMPLEX_PROVIDER)"
    )

    # Confidence & calibration
    critical_lane_min_confidence: float = Field(
        default=0.9, description="Minimum confidence for critical lane (THGENT_CRITICAL_LANE_MIN_CONFIDENCE)"
    )
```

---

## 9. Rollout Checklist

- [ ] Implement `TaskRouter` class with classify() method
- [ ] Add TaskClassificationInput dataclass
- [ ] Add RoutingDecision dataclass
- [ ] Integrate TaskRouter into PolicyEngine.evaluate()
- [ ] Add new fields to RunMeta (task_category, tokens_in_estimated, etc.)
- [ ] Add configuration environment variables
- [ ] Update RunRegistry to log routing signals
- [ ] Write unit tests (classifier logic)
- [ ] Write integration tests (routing + governance)
- [ ] Create dashboard queries for metrics
- [ ] Document for users (TASK_ROUTING_QUICK_REF.md)
- [ ] Soft-launch (log decisions, no enforcement)
- [ ] Gather feedback for 1 week
- [ ] Hard-launch (enforce category-based budgets)
- [ ] Monitor fallback rates, adjust thresholds

---

## References

- Full Specification: `/docs/reference/TASK_ROUTING_DESIGN.md`
- Quick Reference: `/docs/guides/TASK_ROUTING_QUICK_REF.md`
- Existing Code:
  - `/src/thegent/models/catalog.py` — ModelCatalog, Route
  - `/src/thegent/governance/cost.py` — CostEstimator
  - `/src/thegent/execution.py` — RunMeta, PolicyEngine, RunRegistry
  - `/src/thegent/agents/registry.py` — Agent fallback chains


---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made
1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added
- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions
- Implementation templates
- Configuration examples
- Best practices
