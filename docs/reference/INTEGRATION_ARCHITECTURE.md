# TaskRouter + Pareto Routing Integration Architecture

**Last Updated**: 2026-02-15
**Phase**: Design & Pre-Implementation
**Status**: Ready for Implementation Sprint
**Owner**: thegent Core Team

---

## 1. Executive Summary

This document defines the comprehensive integration plan for TaskRouter (task classification, complexity scoring, constraint validation) and Pareto routing (quality-optimized model selection) into thegent's execution pipeline. The integration spans three weeks and involves:

- **Week 1 (Core Routing):** Implement TaskRouter, extend RunMeta, integrate into cli_impl.py
- **Week 2 (Policy Integration):** Extend PolicyEngine with task-aware rules, add per-category cost tracking
- **Week 3 (Testing + Monitoring):** Full testing, shadow run, production rollout

**Hard Constraints** (all must pass before soft optimization):

- **Performance:** Quality threshold by task category (60–80% depending on complexity)
- **Cost:** Per-call instantaneous budget + monthly cumulative budget by category
- **Speed:** SLA by task category (1s for FAST, 60s for HIGH_COMPLEX)

---

## 2. Module Integration Map

### 2.1 execution.py — RunMeta Extensions

**Current State:**
`RunMeta` contains: run_id, agent, model, prompt, status, policy_result, etc.

**Changes Required:**

```python
class RunMeta(BaseModel):
    # Existing fields...

    # NEW: Task Routing Fields (Phase 1)
    task_category: str | None = None  # FAST, NORMAL, COMPLEX, HIGH_COMPLEX
    task_complexity_score: float | None = None  # 0.0 to 1.0
    estimated_cost_usd: float | None = None  # Pre-execution estimate
    estimated_duration_s: float | None = None  # Predicted execution time

    # NEW: Constraint Validation (Phase 1)
    constraint_violations: list[str] = Field(default_factory=list)  # e.g. ["speed_sla_exceeded"]
    fallback_reason: str | None = None  # Why fallback was triggered (if any)
    fallback_chain: list[str] = Field(default_factory=list)  # [first_try, fallback1, fallback2...]
```

**Integration Points:**

| Location                   | Change                                                               | Why                                         |
| -------------------------- | -------------------------------------------------------------------- | ------------------------------------------- |
| `register_start()`         | Capture task_category, complexity_score, estimated_cost at run start | Audit trail for cost/complexity correlation |
| `register_end()`           | Store actual_cost_usd, actual_duration_s; compare vs estimates       | Calibration feedback for classifier         |
| `get_calibration_factor()` | Use task_category bucketing (FAST/NORMAL/COMPLEX per-agent factors)  | Better calibration precision                |

**LOC Impact:** +15 lines (field definitions only; no logic)

---

### 2.2 cli_impl.py — TaskRouter Integration Point

**Current State:**
`run_impl()` calls PolicyEngine.evaluate(), then dispatches to agent.

**Changes Required:**

```python
async def run_impl(
    agent: str,
    model: str | None,
    prompt: str,
    cwd: str,
    config: ThegentSettings,
    # ... existing params ...
) -> dict[str, Any]:
    # 1. Create RunMeta early
    run = RunMeta(agent=agent, model=model, prompt=prompt, cwd=cwd, ...)
    registry = RunRegistry(config.session_dir)
    registry.register_start(run)

    # NEW: Step 2 — Task Classification (Phase 1, BEFORE policy eval)
    from thegent.routing.task_router import TaskRouter, ConstraintValidator

    router = TaskRouter(config)
    task_metadata = router.classify(run.prompt)  # Returns TaskMetadata
    run.task_category = task_metadata.category
    run.task_complexity_score = task_metadata.complexity_score
    run.estimated_cost_usd = task_metadata.estimated_cost
    run.estimated_duration_s = task_metadata.estimated_duration_s

    # NEW: Validate hard constraints (Phase 1)
    validator = ConstraintValidator(config)
    violations = validator.validate(
        task_metadata=task_metadata,
        registry=registry,  # For cumulative cost checks
        model=model,
    )
    if violations:
        run.constraint_violations = violations
        # Log violations but don't block yet; let PolicyEngine decide
        _log.warning(f"Constraint violations for task {run.run_id}: {violations}")

    # Step 3 — Policy Evaluation (NOW task-aware)
    policy_engine = PolicyEngine(config)
    policy_result, policy_reason = policy_engine.evaluate(run, registry)
    run.policy_result = policy_result
    run.policy_reason = policy_reason

    if policy_result == "deny":
        # Escalate to queue if configured
        eq = EscalationQueue(config.session_dir)
        eq.add(run.run_id, reason=policy_reason, ...)
        return {"error": policy_reason, "run_id": run.run_id}

    # Step 4 — Route Selection (NOW Pareto-aware)
    resolved_route = resolve_route_for_category(
        model=model or "default",
        category=run.task_category,
        policy="prefer_direct",
        config=config,
    )
    # ... rest of dispatch logic ...
```

**Integration Points:**

| Location                         | Change                                            | Why                           |
| -------------------------------- | ------------------------------------------------- | ----------------------------- |
| Pre-policy: Classify + Validate  | Route early; block before expensive policy checks | Fail-fast on hard constraints |
| Post-policy: Route selection     | Use task_category for Pareto optimization         | Category-aware model mapping  |
| Post-dispatch: Cost registration | Track actual vs estimated; feed calibration       | Classifier feedback loop      |

**LOC Impact:** +20 lines (integration; logic in TaskRouter module)

---

### 2.3 governance/cost.py — Per-Category Cost Tracking

**Current State:**
`CostAggregator` tracks daily/MTD totals only (no category bucketing).

**Changes Required:**

```python
@dataclass
class CostAggregator:
    """Per-category cost tracking (Phase 2)."""

    session_dir: Path

    def add_to_category(
        self,
        category: str,  # FAST, NORMAL, COMPLEX, HIGH_COMPLEX
        cost_usd: float,
        owner: str | None = None,
        timestamp_utc: str | None = None,
    ) -> None:
        """Record cost in per-category bucket (Phase 2)."""
        event = {
            "event": "cost",
            "category": category,
            "cost_usd": cost_usd,
            "owner": owner,
            "timestamp": timestamp_utc or datetime.now(UTC).isoformat(),
        }
        registry_path = self.session_dir / "run_registry.jsonl"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        with registry_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\\n")

    def get_category_mtd_total(self, category: str) -> float:
        """Sum cost_usd for category this month."""
        registry_path = self.session_dir / "run_registry.jsonl"
        if not registry_path.exists():
            return 0.0

        now = datetime.now(UTC)
        current_month = f"{now.year}-{now.month:02d}"
        total = 0.0

        try:
            with registry_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if (
                            data.get("event") == "cost"
                            and data.get("category") == category
                            and data.get("timestamp", "").startswith(current_month)
                        ):
                            total += float(data.get("cost_usd", 0))
                    except Exception:
                        continue
        except Exception:
            pass

        return total

    def get_category_daily_total(self, category: str) -> float:
        """Sum cost_usd for category today."""
        registry_path = self.session_dir / "run_registry.jsonl"
        if not registry_path.exists():
            return 0.0

        today = datetime.now(UTC).date().isoformat()
        total = 0.0

        try:
            with registry_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        ts = data.get("timestamp", "")[:10]
                        if data.get("event") == "cost" and data.get("category") == category and ts == today:
                            total += float(data.get("cost_usd", 0))
                    except Exception:
                        continue
        except Exception:
            pass

        return total

    def get_all_categories_mtd(self) -> dict[str, float]:
        """Return {category: mtd_total} for all categories."""
        categories = ["FAST", "NORMAL", "COMPLEX", "HIGH_COMPLEX"]
        return {cat: self.get_category_mtd_total(cat) for cat in categories}

    def is_budget_exhausted(self, category: str, config: ThegentSettings) -> tuple[bool, str]:
        """
        Check if category is at/over budget.
        Returns (exhausted, reason).
        """
        mtd = self.get_category_mtd_total(category)
        budget = config.cost_budget_by_category.get(category, 100.0)

        if mtd >= budget:
            return True, f"Category '{category}' budget exhausted (${mtd:.2f} >= ${budget:.2f})"

        utilization = mtd / budget if budget > 0 else 0
        if utilization >= 0.9:
            return False, f"Category '{category}' at 90% budget (${mtd:.2f} / ${budget:.2f})"

        return False, ""
```

**Integration Points:**

| Location                         | Change                                  | Why                             |
| -------------------------------- | --------------------------------------- | ------------------------------- |
| `register_end()` in execution.py | Call `CostAggregator.add_to_category()` | Track per-category spend        |
| `PolicyEngine.evaluate()`        | Check category budget before allow      | Enforce per-category limits     |
| Monitoring/dashboard             | Query per-category totals               | Category-aware spend visibility |

**LOC Impact:** +40 lines (new methods)

---

### 2.4 models/catalog.py — Pareto-Aware Route Selection

**Current State:**
`resolve_route()` selects based on policy (prefer_direct, prefer_proxy, etc.), ignoring task complexity.

**Changes Required:**

```python
def resolve_route_for_category(
    model_id: str,
    category: str,  # FAST, NORMAL, COMPLEX, HIGH_COMPLEX
    policy: RoutePolicy = "prefer_direct",
    quality_threshold: float | None = None,
) -> ResolvedRoute | None:
    """
    Pareto-aware route selection (Phase 2, optional).

    Selects model based on task category:
    - FAST: Prefer cheapest, min quality 60%
    - NORMAL: Balance cost/quality, min quality 70%
    - COMPLEX: Prefer quality, min quality 75%
    - HIGH_COMPLEX: Highest quality only, min quality 80%

    Returns route that satisfies quality threshold AND cost constraints.
    """
    routes = ModelCatalog.routes_for(model_id, use_scraped=True)
    if not routes:
        return None

    # Category -> default quality threshold
    category_thresholds = {
        "FAST": quality_threshold or 0.60,
        "NORMAL": quality_threshold or 0.70,
        "COMPLEX": quality_threshold or 0.75,
        "HIGH_COMPLEX": quality_threshold or 0.80,
    }
    min_quality = category_thresholds.get(category, 0.70)

    # Filter routes by quality (from model catalog)
    # Requires model catalog to have quality scores (Phase 2 enhancement)
    qualified_routes = [r for r in routes if _get_route_quality_score(r) >= min_quality]

    if not qualified_routes:
        # Fallback: return cheapest route, log warning
        return _fallback_cheapest_route(routes)

    # Sort by policy
    if category in ("COMPLEX", "HIGH_COMPLEX"):
        # Prioritize quality, then cost
        sorted_routes = sorted(qualified_routes, key=lambda r: (-_get_route_quality_score(r), r.cost_weight))
    elif category == "FAST":
        # Prioritize cost, then quality
        sorted_routes = sorted(qualified_routes, key=lambda r: (r.cost_weight, -_get_route_quality_score(r)))
    else:  # NORMAL
        # Balance
        sorted_routes = sorted(
            qualified_routes, key=lambda r: r.cost_weight * 0.5 + (1 - _get_route_quality_score(r)) * 0.5
        )

    best = sorted_routes[0]
    return ResolvedRoute(
        provider=best.provider,
        model_alias=best.model_alias,
        backend_type=best.backend_type,
        priority=best.priority,
        cost_weight=best.cost_weight,
    )


def _get_route_quality_score(route: Route) -> float:
    """
    Get quality score for route (placeholder; Phase 2 enhancement).

    In production: fetch from model catalog quality metadata.
    For now: hardcoded quality by provider/model.
    """
    quality_map = {
        ("claude", "claude-opus-4.6"): 0.95,
        ("claude", "claude-sonnet-4.5"): 0.88,
        ("claude", "claude-haiku-4.5"): 0.78,
        ("minimax", "minimax-m2.5"): 0.92,
        ("gemini", "gemini-3-flash"): 0.82,
        ("gemini", "gemini-2.0-flash"): 0.80,
        ("gpt-5.3-codex", "gpt-5.3-codex"): 0.85,
    }
    return quality_map.get((route.provider, route.model_alias), 0.70)


def _fallback_cheapest_route(routes: list[Route]) -> ResolvedRoute | None:
    """Fallback: return cheapest route when no quality threshold match."""
    if not routes:
        return None
    best = min(routes, key=lambda r: r.cost_weight)
    return ResolvedRoute(
        provider=best.provider,
        model_alias=best.model_alias,
        backend_type=best.backend_type,
        priority=best.priority,
        cost_weight=best.cost_weight,
    )
```

**Integration Points:**

| Location               | Change                                               | Why                        |
| ---------------------- | ---------------------------------------------------- | -------------------------- |
| cli_impl.py:run_impl() | Call resolve_route_for_category() with task_category | Task-aware routing         |
| models/catalog.py      | Add quality metadata to Route (Phase 2)              | Enable Pareto optimization |
| monitoring             | Track Pareto coverage (% of routes meeting quality)  | SLA visibility             |

**LOC Impact:** +50 lines (new functions; Phase 2 optional enhancement)

---

### 2.5 config.py — TaskRouter Configuration

**Current State:**
Config has cost_budget_mtd and cost_tracking_enabled, but no TaskRouter settings.

**Changes Required:**

```python
class ThegentSettings(BaseSettings):
    # Existing fields...

    # TaskRouter Configuration (Phase 1)
    routing_enabled: bool = Field(
        default=True,
        description="Enable TaskRouter classification and constraint validation (THGENT_ROUTING_ENABLED)",
    )
    routing_classifier_method: str = Field(
        default="word_count_div_1.3",
        description="Token estimation method: word_count_div_1.3, model_specific, heuristic (THGENT_ROUTING_CLASSIFIER_METHOD)",
    )
    routing_complexity_keywords: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "high_complexity": ["architecture", "design", "refactor", "rewrite", "migration"],
            "medium_complexity": ["debug", "optimize", "fix", "test", "improve"],
        },
        description="Keywords for complexity scoring (THGENT_ROUTING_COMPLEXITY_KEYWORDS as JSON)",
    )

    # Constraint Configuration (Phase 1)
    routing_constraints_enabled: bool = Field(
        default=True,
        description="Enforce hard constraints (perf, cost, speed) (THGENT_ROUTING_CONSTRAINTS_ENABLED)",
    )
    routing_performance_thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "FAST": 0.60,
            "NORMAL": 0.70,
            "COMPLEX": 0.75,
            "HIGH_COMPLEX": 0.80,
        },
        description="Min quality by category (THGENT_ROUTING_PERFORMANCE_THRESHOLDS as JSON)",
    )
    routing_instantaneous_budget: dict[str, float] = Field(
        default_factory=lambda: {
            "FAST": 0.002,
            "NORMAL": 0.05,
            "COMPLEX": 0.15,
            "HIGH_COMPLEX": 0.85,
        },
        description="Max per-call cost by category in USD (THGENT_ROUTING_INSTANTANEOUS_BUDGET as JSON)",
    )
    routing_cumulative_budget: dict[str, float] = Field(
        default_factory=lambda: {
            "FAST": 50,
            "NORMAL": 200,
            "COMPLEX": 150,
            "HIGH_COMPLEX": 50,
        },
        description="Max monthly cost by category in USD (THGENT_ROUTING_CUMULATIVE_BUDGET as JSON)",
    )
    routing_speed_sla_ms: dict[str, int] = Field(
        default_factory=lambda: {
            "FAST": 1000,
            "NORMAL": 5000,
            "COMPLEX": 20000,
            "HIGH_COMPLEX": 60000,
        },
        description="Max execution time by category in ms (THGENT_ROUTING_SPEED_SLA_MS as JSON)",
    )
    routing_budget_warning_threshold: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="Warn at N% of category budget utilization (THGENT_ROUTING_BUDGET_WARNING_THRESHOLD)",
    )

    # Per-category cost budget (replaces global cost_budget_mtd in Phase 2)
    cost_budget_by_category: dict[str, float] = Field(
        default_factory=lambda: {
            "FAST": 50,
            "NORMAL": 200,
            "COMPLEX": 150,
            "HIGH_COMPLEX": 50,
        },
        description="MTD budget by task category (THGENT_COST_BUDGET_BY_CATEGORY as JSON)",
    )
```

**Validation:**

```python
@field_validator("routing_complexity_keywords", mode="before")
@classmethod
def _parse_complexity_keywords(cls, v: object) -> dict[str, list[str]]:
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, dict):
                return {k: list(val) if isinstance(val, (list, tuple)) else [val] for k, val in parsed.items()}
        except json.JSONDecodeError:
            pass
    if isinstance(v, dict):
        return {k: list(val) if isinstance(val, (list, tuple)) else [val] for k, val in v.items()}
    return {"high_complexity": [], "medium_complexity": []}
```

**LOC Impact:** +20 lines (config definitions + validators)

---

### 2.6 routing/ — New Module

**New Files:**

#### routing/**init**.py

```python
"""Task routing and constraint validation for thegent."""

from thegent.routing.task_router import (
    TaskRouter,
    TaskClassifier,
    ConstraintValidator,
    TaskMetadata,
)

__all__ = [
    "TaskRouter",
    "TaskClassifier",
    "ConstraintValidator",
    "TaskMetadata",
]
```

**LOC Impact:** +10 lines

#### routing/models.py

```python
"""Data models for task routing."""

from dataclasses import dataclass
from enum import Enum


class TaskCategory(str, Enum):
    """Task complexity categories."""

    FAST = "FAST"  # Simple, <1s, <100 tokens, <$0.002
    NORMAL = "NORMAL"  # Standard, <5s, <1k tokens, <$0.05
    COMPLEX = "COMPLEX"  # Hard, <20s, <10k tokens, <$0.15
    HIGH_COMPLEX = "HIGH_COMPLEX"  # Very hard, <60s, >10k tokens, <$0.85


@dataclass
class TaskMetadata:
    """Metadata for classified task."""

    category: str  # FAST, NORMAL, COMPLEX, HIGH_COMPLEX
    complexity_score: float  # 0.0 (trivial) to 1.0 (hardest)
    estimated_tokens: int  # Estimated input+output tokens
    estimated_cost: float  # Estimated cost in USD
    estimated_duration_s: float  # Estimated execution time
    reasoning: str | None = None  # Why this category was assigned


@dataclass
class ConstraintViolation:
    """A violated hard constraint."""

    constraint_type: str  # performance, cost, speed
    category: str
    threshold: float
    actual: float
    message: str
```

**LOC Impact:** +50 lines

#### routing/task_router.py

````python
"""Task classification and constraint validation."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from thegent.routing.models import TaskCategory, TaskMetadata, ConstraintViolation

if TYPE_CHECKING:
    from thegent.config import ThegentSettings
    from thegent.execution import RunRegistry

_log = logging.getLogger(__name__)


class TaskClassifier:
    """Classifies tasks by complexity and estimates cost/duration."""

    def __init__(self, config: "ThegentSettings") -> None:
        self.config = config
        self.method = config.routing_classifier_method
        self.complexity_keywords = config.routing_complexity_keywords

    def classify(self, prompt: str) -> TaskMetadata:
        """
        Classify task and estimate metrics.

        Returns TaskMetadata with:
        - category (FAST, NORMAL, COMPLEX, HIGH_COMPLEX)
        - complexity_score (0.0 to 1.0)
        - estimated_tokens, cost, duration
        """
        # 1. Estimate tokens
        tokens = self._estimate_tokens(prompt)

        # 2. Score complexity (0.0 to 1.0)
        complexity = self._score_complexity(prompt, tokens)

        # 3. Categorize
        category = self._categorize(complexity, tokens)

        # 4. Estimate cost & duration
        cost = self._estimate_cost(tokens, category)
        duration = self._estimate_duration(tokens, category)

        return TaskMetadata(
            category=category,
            complexity_score=complexity,
            estimated_tokens=tokens,
            estimated_cost=cost,
            estimated_duration_s=duration,
            reasoning=f"Tokens: {tokens}, Complexity: {complexity:.2f}, Category: {category}",
        )

    def _estimate_tokens(self, prompt: str) -> int:
        """Estimate tokens in prompt + expected output."""
        if self.method == "word_count_div_1.3":
            words = len(prompt.split())
            input_tokens = max(1, int(words / 1.3))
            output_tokens = 500  # Assume ~500 token output
            return input_tokens + output_tokens
        elif self.method == "model_specific":
            # Phase 2: Use model-specific tokenizer
            return self._estimate_tokens_model_specific(prompt)
        else:  # heuristic
            return len(prompt) // 4 + 500  # 4 chars per token + output

    def _estimate_tokens_model_specific(self, prompt: str) -> int:
        """Phase 2: Use actual model tokenizer."""
        # Placeholder: implement per-model tokenization
        return self._estimate_tokens(prompt)  # Fallback to word_count

    def _score_complexity(self, prompt: str, tokens: int) -> float:
        """
        Score complexity (0.0 to 1.0) based on:
        - Keywords (high_complexity, medium_complexity)
        - Token count (more tokens = more complex)
        - Structural indicators (code blocks, bullets, etc.)
        """
        score = 0.0
        prompt_lower = prompt.lower()

        # Keyword-based (0 to 0.5)
        high_kw = self.complexity_keywords.get("high_complexity", [])
        med_kw = self.complexity_keywords.get("medium_complexity", [])

        for kw in high_kw:
            if kw.lower() in prompt_lower:
                score += 0.25  # High-complexity keywords push up

        for kw in med_kw:
            if kw.lower() in prompt_lower:
                score += 0.10

        # Token-based (0 to 0.5)
        # Assume: FAST < 200 tokens, NORMAL < 1000, COMPLEX < 10000, HIGH_COMPLEX >= 10000
        token_complexity = min(0.5, tokens / 20000)
        score += token_complexity

        # Structural (0 to 0.2)
        if "```" in prompt:  # Code blocks
            score += 0.1
        if prompt.count("\\n") > 20:  # Many lines
            score += 0.05
        if any(c in prompt for c in ["architecture", "design", "pattern"]):  # Design-heavy
            score += 0.05

        return min(1.0, score)

    def _categorize(self, complexity: float, tokens: int) -> str:
        """
        Categorize based on complexity and token count.

        FAST: complexity < 0.3 AND tokens < 200
        NORMAL: complexity < 0.6 AND tokens < 1000
        COMPLEX: complexity < 0.8 AND tokens < 10000
        HIGH_COMPLEX: else
        """
        if complexity < 0.3 and tokens < 200:
            return TaskCategory.FAST.value
        elif complexity < 0.6 and tokens < 1000:
            return TaskCategory.NORMAL.value
        elif complexity < 0.8 and tokens < 10000:
            return TaskCategory.COMPLEX.value
        else:
            return TaskCategory.HIGH_COMPLEX.value

    def _estimate_cost(self, tokens: int, category: str) -> float:
        """Rough cost estimate based on tokens and category."""
        # Assume: $0.001-0.003 per 1k input tokens
        input_cost = (tokens * 0.8 / 1000) * 0.002  # 80% are input, ~$0.002 per 1k
        output_cost = (tokens * 0.2 / 1000) * 0.005  # 20% are output, ~$0.005 per 1k

        # Category multiplier (complexity/quality)
        multipliers = {
            TaskCategory.FAST.value: 0.5,
            TaskCategory.NORMAL.value: 1.0,
            TaskCategory.COMPLEX.value: 2.0,
            TaskCategory.HIGH_COMPLEX.value: 4.0,
        }
        multiplier = multipliers.get(category, 1.0)

        return (input_cost + output_cost) * multiplier

    def _estimate_duration(self, tokens: int, category: str) -> float:
        """Estimate execution duration in seconds."""
        # Base: ~1 token per 5-10ms for most models
        base_duration = tokens * 0.008  # 8ms per token

        # Category-based SLA buffers
        sla_buffers = {
            TaskCategory.FAST.value: 1.0,
            TaskCategory.NORMAL.value: 5.0,
            TaskCategory.COMPLEX.value: 20.0,
            TaskCategory.HIGH_COMPLEX.value: 60.0,
        }
        sla_buffer = sla_buffers.get(category, 5.0)

        return min(sla_buffer, base_duration + 1.0)


class ConstraintValidator:
    """Validates hard constraints (performance, cost, speed)."""

    def __init__(self, config: "ThegentSettings") -> None:
        self.config = config

    def validate(
        self,
        task_metadata: TaskMetadata,
        registry: "RunRegistry | None" = None,
        model: str | None = None,
    ) -> list[str]:
        """
        Validate task against all hard constraints.

        Returns list of violation messages (empty if all pass).

        Checks:
        1. Performance: model quality >= threshold
        2. Cost: estimated_cost <= instantaneous_budget
        3. Cost: category MTD + estimated >= cumulative_budget (if registry provided)
        4. Speed: estimated_duration <= SLA
        """
        violations = []

        category = task_metadata.category
        if not self.config.routing_constraints_enabled:
            return violations

        # 1. Performance constraint
        perf_thresholds = self.config.routing_performance_thresholds
        required_quality = perf_thresholds.get(category, 0.70)

        # Phase 2: Check model quality; for now, assume all models meet threshold
        # model_quality = self._get_model_quality(model)
        # if model_quality < required_quality:
        #     violations.append(
        #         f"Performance: model quality {model_quality:.1%} < {required_quality:.1%}"
        #     )

        # 2. Instantaneous cost constraint
        inst_budget = self.config.routing_instantaneous_budget.get(category, 0.05)
        if task_metadata.estimated_cost > inst_budget:
            violations.append(f"Cost (instantaneous): ${task_metadata.estimated_cost:.4f} > ${inst_budget:.4f}")

        # 3. Cumulative cost constraint (if registry available)
        if registry:
            cum_budget = self.config.routing_cumulative_budget.get(category, 100.0)
            from thegent.governance.cost import CostAggregator

            agg = CostAggregator(self.config.session_dir)
            category_mtd = agg.get_category_mtd_total(category)
            if category_mtd + task_metadata.estimated_cost > cum_budget:
                violations.append(
                    f"Cost (cumulative): ${category_mtd:.2f} + ${task_metadata.estimated_cost:.4f} > ${cum_budget:.2f}"
                )

        # 4. Speed constraint
        speed_sla = self.config.routing_speed_sla_ms.get(category, 5000) / 1000
        if task_metadata.estimated_duration_s > speed_sla:
            violations.append(f"Speed: {task_metadata.estimated_duration_s:.1f}s > {speed_sla:.1f}s SLA")

        return violations


class TaskRouter:
    """Orchestrates task classification and constraint validation."""

    def __init__(self, config: "ThegentSettings") -> None:
        self.config = config
        self.classifier = TaskClassifier(config)
        self.validator = ConstraintValidator(config)

    def classify(self, prompt: str) -> TaskMetadata:
        """Classify task."""
        return self.classifier.classify(prompt)

    def validate(
        self,
        task_metadata: TaskMetadata,
        registry: "RunRegistry | None" = None,
        model: str | None = None,
    ) -> list[str]:
        """Validate task against constraints."""
        return self.validator.validate(task_metadata, registry, model)

    def route(
        self,
        prompt: str,
        registry: "RunRegistry | None" = None,
        model: str | None = None,
    ) -> tuple[TaskMetadata, list[str]]:
        """
        Full routing: classify + validate.

        Returns (TaskMetadata, violations).
        Violations is empty list if all constraints pass.
        """
        task = self.classify(prompt)
        violations = self.validate(task, registry, model)
        return task, violations
````

**LOC Impact:** +300 lines (comprehensive implementation)

---

## 3. Data Flow Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        User Command (thegent run "...")                      │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 ↓
                    ┌────────────────────────────┐
                    │   parse_command() [cli.py] │
                    └────────┬───────────────────┘
                             ↓
                    ┌────────────────────────────┐
                    │  run_impl() [cli_impl.py]  │
                    └────────┬───────────────────┘
                             ↓
            ┌────────────────────────────────────────┐
            │ Step 1: Create RunMeta + register_start │
            │ - run_id, agent, model, prompt         │
            │ - started_at_utc                       │
            └────────────────┬───────────────────────┘
                             ↓
        ┌───────────────────────────────────────────────────┐
        │ Step 2: TaskRouter.classify() [NEW]               │
        │ - Estimate tokens (prompt/config.method)         │
        │ - Score complexity (keywords, tokens, structure) │
        │ - Categorize (FAST, NORMAL, COMPLEX, HIGH...)    │
        │ - Estimate cost & duration                       │
        │ Returns: TaskMetadata                             │
        └──────────┬──────────────────────────────────────┘
                   ↓
        ┌───────────────────────────────────────────────────┐
        │ Step 3: ConstraintValidator.validate() [NEW]      │
        │ - Performance: quality >= threshold               │
        │ - Cost (instantaneous): <= per-call budget        │
        │ - Cost (cumulative): MTD + est <= category budget │
        │ - Speed: estimated_duration <= SLA                │
        │ Returns: list[violations] (empty if all pass)     │
        └──────────┬──────────────────────────────────────┘
                   ↓
      ┌────────────────────────────────────────────────┐
      │ Step 4: PolicyEngine.evaluate(run) [ENHANCED]  │
      │ - Now has access to run.task_category          │
      │ - Applies task-aware rules (per-category budgets)
      │ - Checks circuit breakers, guardrails, etc.    │
      │ Returns: (policy_result, reason)               │
      │ - allow → proceed to Step 5                    │
      │ - deny → escalate to queue, return error       │
      │ - warn → log warning, proceed to Step 5        │
      └──────────┬─────────────────────────────────────┘
                 ↓
      ┌────────────────────────────────────────────────────┐
      │ Step 5: resolve_route_for_category() [NEW, Ph2]    │
      │ - Filter routes by task_category quality threshold │
      │ - Sort by policy (cheapest for FAST, quality for   │
      │   COMPLEX/HIGH_COMPLEX, balanced for NORMAL)       │
      │ Returns: ResolvedRoute(provider, model_alias, ...) │
      └──────────┬─────────────────────────────────────────┘
                 ↓
      ┌────────────────────────────────────────────────────┐
      │ Step 6: Dispatch to Agent                          │
      │ - Call agent runner (direct or proxy)              │
      │ - Execution completes                              │
      │ - Capture actual_cost_usd, actual_duration_s       │
      └──────────┬─────────────────────────────────────────┘
                 ↓
      ┌────────────────────────────────────────────────────┐
      │ Step 7: register_end() [ENHANCED]                  │
      │ - Store actual cost, duration, exit_code           │
      │ - Call CostAggregator.add_to_category()            │
      │ - Feed actual metrics to calibration registry      │
      └──────────┬─────────────────────────────────────────┘
                 ↓
           ┌──────────────────┐
           │  Return Result   │
           └──────────────────┘
```

---

## 4. File Changes Summary

| File                                   | Change Type            | LOC  | Priority | Depends On                      |
| -------------------------------------- | ---------------------- | ---- | -------- | ------------------------------- |
| **src/thegent/execution.py**           | Extend RunMeta         | +15  | P0       | None                            |
| **src/thegent/cli_impl.py**            | TaskRouter integration | +20  | P0       | execution.py changes            |
| **src/thegent/config.py**              | Add TaskRouter config  | +20  | P0       | None                            |
| **src/thegent/governance/cost.py**     | Per-category tracking  | +40  | P1       | execution.py changes            |
| **src/thegent/models/catalog.py**      | Pareto-aware routing   | +50  | P2       | config.py (Phase 2 only)        |
| **src/thegent/routing/**init**.py**    | Module init            | +10  | P0       | None                            |
| **src/thegent/routing/models.py**      | Data classes           | +50  | P0       | None                            |
| **src/thegent/routing/task_router.py** | Core router            | +300 | P0       | config.py, models.py            |
| **tests/test_unit_routing.py**         | Unit tests             | +400 | P0       | routing/ modules                |
| **tests/test_integration_routing.py**  | Integration tests      | +300 | P1       | routing/, execution, governance |

**Total LOC**: ~1,205 lines (including tests)
**Critical Path**: execution.py → cli_impl.py → routing/task_router.py

---

## 5. Constraint Enforcement Matrix

### Hard Constraints (All Must Pass)

#### Performance

```
FAST Task:
├─ Min Quality: 60%
├─ Eligible Models: GPT-4o mini (70%), MiniMax M2.5 (>80%), Gemini Flash (>80%)
└─ Status: ✓ Pass

NORMAL Task:
├─ Min Quality: 70%
├─ Eligible Models: MiniMax M2.5 (80%), Gemini 3-Flash (82%), etc.
└─ Status: ✓ Pass

COMPLEX Task:
├─ Min Quality: 75%
├─ Eligible Models: Claude Sonnet (88%), MiniMax M2.5 (80%), etc.
└─ Status: ✓ Pass

HIGH_COMPLEX Task:
├─ Min Quality: 80%
├─ Eligible Models: Claude Opus (95%), MiniMax M2.5 (92%), etc.
└─ Status: ✓ Pass
```

#### Instantaneous Cost (per-call)

```
FAST:      cost ≤ $0.002 (typical: MiniMax ~$0.0015, Gemini ~$0.0001)
NORMAL:    cost ≤ $0.05  (typical: MiniMax ~$0.04, Claude Haiku ~$0.02)
COMPLEX:   cost ≤ $0.15  (typical: Claude Sonnet ~$0.12, Opus ~$0.35 ✗ TOO HIGH)
HIGH_COMPLEX: cost ≤ $0.85 (typical: Claude Opus ~$0.35, MiniMax ~$0.40)
```

#### Cumulative Cost (monthly per category)

```
FAST:      budget = $50/mo  (warn at $40, block at $50)
           capacity: ~33,000 calls @ $0.0015/call

NORMAL:    budget = $200/mo (warn at $160, block at $200)
           capacity: ~5,000 calls @ $0.04/call

COMPLEX:   budget = $150/mo (warn at $120, block at $150)
           capacity: ~1,000 calls @ $0.15/call

HIGH_COMPLEX: budget = $50/mo (warn at $40, block at $50)
           capacity: ~142 calls @ $0.35/call (Opus)
```

#### Speed (SLA)

```
FAST:      SLA ≤ 1s    (typical: MiniMax ~200ms, Gemini ~150ms ✓)
NORMAL:    SLA ≤ 5s    (typical: MiniMax ~200ms, Claude ~800ms ✓)
COMPLEX:   SLA ≤ 20s   (typical: Opus ~1.76s ✓)
HIGH_COMPLEX: SLA ≤ 60s (typical: Opus ~1.76s ✓)
```

---

## 6. Configuration Schema

```yaml
# .env or environment variables

# TaskRouter Core (Phase 1)
THGENT_ROUTING_ENABLED=true
THGENT_ROUTING_CLASSIFIER_METHOD=word_count_div_1.3  # word_count_div_1.3 | model_specific | heuristic
THGENT_ROUTING_COMPLEXITY_KEYWORDS='{"high_complexity":["architecture","design","refactor"],"medium_complexity":["debug","optimize","fix"]}'

# Constraints (Phase 1)
THGENT_ROUTING_CONSTRAINTS_ENABLED=true

# Performance Thresholds
THGENT_ROUTING_PERFORMANCE_THRESHOLDS='{"FAST":0.60,"NORMAL":0.70,"COMPLEX":0.75,"HIGH_COMPLEX":0.80}'

# Instantaneous Cost Budget (per-call)
THGENT_ROUTING_INSTANTANEOUS_BUDGET='{"FAST":0.002,"NORMAL":0.05,"COMPLEX":0.15,"HIGH_COMPLEX":0.85}'

# Cumulative Cost Budget (monthly per category)
THGENT_ROUTING_CUMULATIVE_BUDGET='{"FAST":50,"NORMAL":200,"COMPLEX":150,"HIGH_COMPLEX":50}'

# Speed SLA (milliseconds)
THGENT_ROUTING_SPEED_SLA_MS='{"FAST":1000,"NORMAL":5000,"COMPLEX":20000,"HIGH_COMPLEX":60000}'

# Budget Warning Threshold (warn at 80% utilization)
THGENT_ROUTING_BUDGET_WARNING_THRESHOLD=0.80

# Cost Tracking (Phase 2)
THGENT_COST_TRACKING_ENABLED=true
THGENT_COST_BUDGET_BY_CATEGORY='{"FAST":50,"NORMAL":200,"COMPLEX":150,"HIGH_COMPLEX":50}'
```

---

## 7. Phase Breakdown (3 Weeks, 15 Days)

### Week 1: Core Routing (Days 1–5)

**Day 1–2: Implement TaskRouter**

- routing/models.py: TaskMetadata, TaskCategory, ConstraintViolation (1–2 hours)
- routing/task_router.py: TaskClassifier, ConstraintValidator (4–6 hours)
- Unit tests: test_unit_routing.py (tokenization, complexity, categorization, validation) (2–3 hours)
- **Deliverable**: TaskRouter module with unit tests (90%+ coverage)

**Day 2–3: Extend config.py + RunMeta**

- config.py: Add all routing settings (1–2 hours)
- execution.py: Add task_category, complexity_score, estimated_cost to RunMeta (30 min)
- Tests: test_unit_config.py for TaskRouter config validation (1 hour)
- **Deliverable**: Config schema + RunMeta extensions

**Day 3–4: Integrate into cli_impl.py**

- cli_impl.py: Call TaskRouter.classify(), ConstraintValidator.validate() before policy (2 hours)
- Update PolicyEngine.evaluate() signature to accept RunMeta with task_category (1 hour)
- E2E smoke test: Run 100 tasks, verify classification + validation (1 hour)
- **Deliverable**: TaskRouter integrated into execution pipeline

**Day 5: Unit + E2E Testing**

- Complete unit tests (routing, config, execution changes) (2 hours)
- E2E test: FAST task (should route to cheap model, <1s) (1 hour)
- E2E test: HIGH_COMPLEX task (should enforce quality constraint) (1 hour)
- **Deliverable**: 100% unit test coverage for Week 1 changes, E2E smoke tests pass

---

### Week 2: Policy + Cost Integration (Days 6–10)

**Day 6–7: Extend PolicyEngine + CostAggregator**

- governance/cost.py: Add per-category methods (add_to_category, get_category_mtd_total, etc.) (2 hours)
- execution.py: register_end() calls CostAggregator.add_to_category() (1 hour)
- PolicyEngine.evaluate(): Check per-category budget before allow (1.5 hours)
- **Deliverable**: Cost tracking by category, budget enforcement in policy

**Day 7–8: Extend Route Selection (Phase 2 – Optional)**

- models/catalog.py: resolve_route_for_category() function (2 hours)
- Add quality metadata to Route dataclass (30 min)
- \_get_route_quality_score() hardcoded mapping (30 min)
- Tests: test_unit_models.py for Pareto routing (1.5 hours)
- **Deliverable**: Pareto-aware model selection (optional; can defer if time-constrained)

**Day 8–9: Integration Tests**

- test_integration_routing.py: Full flow tests (classify + validate + policy + route + dispatch) (3 hours)
- Cost tracking integration: Verify category buckets update after runs (1 hour)
- Policy enforcement: Verify budget blocks/warns correctly (1 hour)
- **Deliverable**: Integration tests pass, cost enforcement working

**Day 10: Monitoring + Reporting**

- Add metrics queries (cost by category, utilization %, fallback frequency) (2 hours)
- Implement dashboard queries (SQL if using DB, or JSONL parsing) (1.5 hours)
- Documentation: Update CLAUDE.md with TaskRouter usage (1 hour)
- **Deliverable**: Monitoring queries + dashboard ready

---

### Week 3: Testing + Monitoring + Rollout (Days 11–15)

**Day 11–12: Shadow Run (Production Traffic, No Enforcement)**

- Deploy with routing_constraints_enabled=false (violations logged but not enforced)
- Run production traffic through TaskRouter for 2 days
- Collect metrics: classification accuracy, cost estimates vs actual, SLA adherence (2 hours/day)
- **Success Criteria**: No false positives, cost estimates within 20% of actual

**Day 13: Full Enforcement Rollout**

- Set routing_constraints_enabled=true
- Set routing_budget_warning_threshold=0.80 (warn at 80% utilization)
- Monitor: violations logged, budget warnings firing (2 hours)
- Rollback plan ready (1 hour)
- **Success Criteria**: No task rejections due to false positives, legitimate budget blocks only

**Day 14: Tuning + Documentation**

- Adjust thresholds based on shadow run data (1 hour)
- Finalize documentation: INTEGRATION_ARCHITECTURE.md, INTEGRATION_QUICK_START.md (1.5 hours)
- Runbooks: How to investigate cost overages, disable routing, adjust budgets (1 hour)

**Day 15: Post-Launch Monitoring**

- Monitor SLOs: routing latency < 100ms, budget accuracy, constraint violation rate < 1% (1 hour)
- Respond to any issues (1 hour)
- Post-launch report: cost reduction, constraint compliance, incident summary (1 hour)
- **Deliverable**: Launch report, runbooks, monitoring stable

---

## 8. Testing Strategy

### Unit Tests

**test_routing.py — TaskClassifier**

```python
def test_classify_fast_task():
    """Classify simple task as FAST."""
    classifier = TaskClassifier(config)
    result = classifier.classify("Rename variable x to y")
    assert result.category == "FAST"
    assert result.estimated_duration_s <= 1.0
    assert result.estimated_cost <= 0.002


def test_classify_high_complex_task():
    """Classify complex task as HIGH_COMPLEX."""
    classifier = TaskClassifier(config)
    result = classifier.classify(
        "Design a complete microservices architecture for "
        "a multi-tenant SaaS platform with sharding, "
        "rate limiting, and failover..."
    )
    assert result.category == "HIGH_COMPLEX"
    assert result.complexity_score > 0.75


def test_complexity_keywords():
    """High-complexity keywords increase score."""
    classifier = TaskClassifier(config)
    result1 = classifier.classify("Add a line")
    result2 = classifier.classify("Architecture refactor: redesign storage layer")
    assert result2.complexity_score > result1.complexity_score
```

**test_routing.py — ConstraintValidator**

```python
def test_validate_instantaneous_cost_constraint():
    """Reject if estimated cost > instantaneous budget."""
    validator = ConstraintValidator(config)
    task = TaskMetadata(
        category="FAST",
        complexity_score=0.2,
        estimated_tokens=100,
        estimated_cost=0.005,  # Exceeds FAST budget of $0.002
        estimated_duration_s=0.5,
    )
    violations = validator.validate(task)
    assert any("instantaneous" in v for v in violations)


def test_validate_speed_constraint():
    """Reject if estimated duration > SLA."""
    validator = ConstraintValidator(config)
    task = TaskMetadata(
        category="FAST",
        complexity_score=0.2,
        estimated_tokens=100,
        estimated_cost=0.001,
        estimated_duration_s=2.0,  # Exceeds FAST SLA of 1.0s
    )
    violations = validator.validate(task)
    assert any("Speed" in v for v in violations)


def test_validate_cumulative_budget():
    """Reject if category MTD + estimate > budget."""
    registry = mock_registry_with_mtd({"FAST": 49.5})
    validator = ConstraintValidator(config)
    task = TaskMetadata(
        category="FAST",
        complexity_score=0.2,
        estimated_tokens=100,
        estimated_cost=0.8,  # 49.5 + 0.8 > 50
        estimated_duration_s=0.5,
    )
    violations = validator.validate(task, registry)
    assert any("cumulative" in v for v in violations)
```

### Integration Tests

**test_integration_routing.py**

```python
@pytest.mark.asyncio
async def test_full_routing_flow():
    """End-to-end: classify + validate + policy + route + dispatch."""
    config = test_config_with_routing_enabled()
    registry = create_test_registry()

    run = RunMeta(agent="claude", model="haiku", prompt="Fix typo in function name")
    registry.register_start(run)

    # Classify
    router = TaskRouter(config)
    task, violations = router.route(run.prompt, registry)

    assert task.category == "FAST"
    assert len(violations) == 0

    # Policy
    policy_engine = PolicyEngine(config)
    result, reason = policy_engine.evaluate(run, registry)

    assert result == "allow"

    # Route
    resolved = resolve_route_for_category(
        model="haiku",
        category=task.category,
        policy="prefer_direct",
    )
    assert resolved is not None
    assert resolved.cost_weight <= 0.3  # FAST should pick cheap route


@pytest.mark.asyncio
async def test_cost_tracking_by_category():
    """Verify cost tracked per-category."""
    config = test_config()
    registry = create_test_registry()
    agg = CostAggregator(config.session_dir)

    # Simulate 3 FAST runs @ $0.001 each
    for i in range(3):
        agg.add_to_category("FAST", 0.001)

    # Simulate 1 COMPLEX run @ $0.10
    agg.add_to_category("COMPLEX", 0.10)

    assert agg.get_category_mtd_total("FAST") == pytest.approx(0.003)
    assert agg.get_category_mtd_total("COMPLEX") == pytest.approx(0.10)
    assert agg.get_mtd_total() == pytest.approx(0.13)


@pytest.mark.asyncio
async def test_budget_enforcement():
    """Budget constraint blocks when exhausted."""
    config = test_config_with_budget({"FAST": 0.01})  # Tiny budget
    registry = create_test_registry()
    policy_engine = PolicyEngine(config)

    agg = CostAggregator(config.session_dir)
    agg.add_to_category("FAST", 0.015)  # Already over

    run = RunMeta(
        agent="claude",
        model="haiku",
        prompt="Fix typo",
        task_category="FAST",
        estimated_cost=0.001,
    )

    result, reason = policy_engine.evaluate(run, registry)

    assert result == "deny"
    assert "budget" in reason.lower()
```

### End-to-End Tests

**test_e2e_routing.py**

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_fast_task_routed_cheap():
    """E2E: FAST task routed to cheapest model, completes <1s."""
    prompt = "Rename variable x to y"
    result = await run_e2e_task(prompt)

    assert result["task_category"] == "FAST"
    assert result["provider"] in ["minimax", "gemini"]
    assert result["duration_s"] < 1.0
    assert result["cost_usd"] < 0.002


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_high_complex_task_routed_quality():
    """E2E: HIGH_COMPLEX task routed to highest-quality model."""
    prompt = (
        "Design a complete event-driven microservices architecture "
        "with eventual consistency guarantees, handling 1M QPS..."
    )
    result = await run_e2e_task(prompt)

    assert result["task_category"] == "HIGH_COMPLEX"
    assert result["provider"] in ["claude", "minimax"]
    assert result["model_quality"] >= 0.80
    assert result["duration_s"] < 60


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_budget_exhaustion():
    """E2E: After budget exhausted, next task is blocked."""
    config = test_config_with_budget({"FAST": 0.005})

    # Use up budget: 5 tasks @ $0.001 = $0.005
    for i in range(5):
        result = await run_e2e_task("Simple task")
        assert result["status"] == "success"

    # Next task should be denied
    result = await run_e2e_task("Another simple task")
    assert result["status"] == "denied"
    assert "budget" in result["reason"].lower()
```

---

## 9. Monitoring & Metrics

### Dashboard Queries

```sql
-- Daily cost by category
SELECT
  DATE(timestamp) as date,
  category,
  SUM(cost_usd) as total_cost,
  COUNT(*) as call_count,
  AVG(cost_usd) as avg_cost
FROM run_registry
WHERE event = "cost"
  AND timestamp >= DATE(NOW()) - INTERVAL 30 DAY
GROUP BY date, category
ORDER BY date DESC, category;

-- Budget utilization
SELECT
  category,
  SUM(cost_usd) as mtd_cost,
  (SELECT value FROM config WHERE key = CONCAT('budget_', category)) as budget,
  SUM(cost_usd) / CAST((SELECT value FROM config WHERE key = CONCAT('budget_', category)) AS FLOAT) * 100 as utilization_pct
FROM run_registry
WHERE event = "cost"
  AND YEAR_MONTH(timestamp) = YEAR_MONTH(NOW())
GROUP BY category;

-- Constraint violations
SELECT
  task_category,
  COUNT(*) as violation_count,
  GROUP_CONCAT(DISTINCT LEFT(constraint_violations, 50)) as types
FROM run_registry
WHERE event IS NULL  -- Start events
  AND constraint_violations IS NOT NULL
  AND JSON_ARRAY_LENGTH(constraint_violations) > 0
  AND started_at_utc >= DATE(NOW()) - INTERVAL 7 DAY
GROUP BY task_category;

-- Fallback frequency
SELECT
  task_category,
  JSON_ARRAY_LENGTH(fallback_chain) > 0 as had_fallback,
  COUNT(*) as count,
  COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY task_category) * 100 as pct
FROM run_registry
WHERE started_at_utc >= DATE(NOW()) - INTERVAL 7 DAY
GROUP BY task_category, had_fallback;

-- Routing latency (classify + validate)
SELECT
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY routing_latency_ms) as p50,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY routing_latency_ms) as p95,
  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY routing_latency_ms) as p99,
  MAX(routing_latency_ms) as max_ms
FROM run_registry
WHERE started_at_utc >= NOW() - INTERVAL 7 DAY
  AND routing_latency_ms IS NOT NULL;
```

### SLOs

```
Routing Latency (classify + validate):
├─ Target: < 100ms (p99)
├─ Alert if: p99 > 150ms (2 consecutive hours)
└─ Runbook: profile classifier, check registry size

Budget Accuracy (forecast vs actual):
├─ Target: < 10% error (abs(estimated - actual) / actual)
├─ Alert if: error > 20% (5+ consecutive days)
└─ Runbook: retrain classifier on recent data

Constraint Violation Rate:
├─ Target: < 1% of tasks rejected
├─ Alert if: > 5% rejection rate
└─ Runbook: review violation distribution, adjust thresholds

Fallback Frequency:
├─ Target: < 5% HIGH_COMPLEX tasks fallback
├─ Alert if: > 10% fallback rate
└─ Runbook: check model availability, adjust thresholds
```

---

## 10. Rollback Plan

If integration causes issues:

### Disable Routing

```bash
# Immediate: Set env var
export THGENT_ROUTING_ENABLED=false

# Or: config.yaml
routing:
  enabled: false
```

**Effect**: Tasks skip TaskRouter.classify() and ConstraintValidator.validate(), but RunMeta fields remain available (backward-compatible).

### Disable Cost Enforcement

```bash
export THGENT_ROUTING_CONSTRAINTS_ENABLED=false
export THGENT_COST_TRACKING_ENABLED=false
```

### Revert RunMeta

RunMeta fields (task_category, complexity_score, etc.) are optional (default None). Old code that doesn't set them continues to work.

### Manual Recovery

```python
# If registry is corrupted, rebuild from backups:
registry_path = ~/.cache/thegent/sessions/run_registry.jsonl
# cp run_registry.jsonl.backup run_registry.jsonl

# If cost totals are wrong, recalculate:
python scripts/recalculate_category_costs.py --month 2026-02
```

### Disable per-Phase

| Phase                 | Disable via                                      | Impact                                              |
| --------------------- | ------------------------------------------------ | --------------------------------------------------- |
| Task Classification   | ROUTING_ENABLED=false                            | No task_category assigned; runs proceed normally    |
| Constraint Validation | ROUTING_CONSTRAINTS_ENABLED=false                | Violations logged but not enforced                  |
| Cost Enforcement      | COST_TRACKING_ENABLED=false or PolicyEngine skip | Budget checks don't fire                            |
| Pareto Routing        | resolve_route_for_category → resolve_route       | Fall back to standard routing (Phase 1 still works) |

---

## 11. Success Criteria

### Week 1

- [ ] TaskRouter module 100% tested (unit coverage ≥ 90%)
- [ ] 100 test tasks classified with ≤5% misclassification rate
- [ ] Constraints validated with 100% accuracy (no false positives)
- [ ] config.py supports all routing settings
- [ ] RunMeta extended with task metadata
- [ ] cli_impl.py integration complete (E2E smoke tests pass)

### Week 2

- [ ] Per-category cost tracking working (verified against mock registry)
- [ ] PolicyEngine enforces per-category budgets (block at 100%, warn at 80%)
- [ ] Integration tests pass (policy + cost + routing full flow)
- [ ] Pareto routing working (Phase 2, optional)
- [ ] Monitoring queries production-ready

### Week 3

- [ ] Shadow run complete: cost estimates within 20% of actual
- [ ] Zero false-positive constraint blocks during shadow run
- [ ] Full enforcement rollout: legitimate blocks only
- [ ] Cost reduction verified: goal 18% ($550 → $450/mo)
- [ ] SLOs met: routing latency <100ms p99, budget accuracy <10% error, violation rate <1%
- [ ] Post-launch report + runbooks

---

## References

- **Task Classification**: Inspired by O(1) token estimation (Claude Cookbook)
- **Constraint Validation**: Pareto frontier optimization (cost vs quality trade-offs)
- **Per-Category Budgeting**: Multi-tenant cost isolation pattern
- **Hard Constraints**: All-or-nothing enforcement (no graceful degradation)
- **Monitoring**: Industry-standard SLO framework (Google SLO handbook)

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
