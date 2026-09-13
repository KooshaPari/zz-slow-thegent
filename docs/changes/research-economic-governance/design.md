# Economic Governance Technical Design

**Status**: Design Phase
**Work Item**: WP-5003
**Design Date**: 2026-02-18
**Architect**: thegent team

---

## 1. System Overview

### Design Goals
1. **Cost efficiency**: Route tasks to best cost-to-value provider
2. **Quality preservation**: Maintain >95% reliability through scoring
3. **Transparency**: Audit trail for all routing decisions
4. **Extensibility**: Add new providers/metrics without changes

### Key Design Patterns
- **Provider Strategy**: Pluggable provider scoring
- **Fallback Chain**: Graceful degradation on provider failure
- **Circuit Breaker**: Protect against cascading failures
- **Decision Record**: Immutable audit trail

---

## 2. Core Components

### 2.1 Provider Scoring System

#### Location
```
thegent/src/thegent/governance/
├── scoring.py          # Core scoring logic
├── providers.py        # Provider definitions
└── metrics.py          # Metric collection
```

#### Interface

```python
# thegent/src/thegent/governance/scoring.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ProviderMetrics:
    """Measured provider performance"""

    provider_id: str
    reliability: float  # 0.0-1.0 (uptime/success rate)
    latency_p99: float  # milliseconds
    cost_per_1m_tokens: float  # USD
    last_updated: float  # Unix timestamp
    sample_size: int  # Measurements in score


@dataclass
class ProviderScore:
    """Normalized provider score"""

    provider_id: str
    reliability_score: float  # 0-10
    latency_score: float  # 0-10 (lower latency = higher score)
    cost_score: float  # 0-10 (lower cost = higher score)
    composite_score: float  # Weighted average
    timestamp: float


class ProviderScorer(ABC):
    """Abstract scorer for extensibility"""

    @abstractmethod
    def score(self, metrics: ProviderMetrics) -> ProviderScore:
        """Compute score from metrics"""
        pass

    @abstractmethod
    def normalize(self, raw_value: float, metric_type: str) -> float:
        """Normalize metric to 0-10 scale"""
        pass


class DefaultProviderScorer(ProviderScorer):
    """Standard provider scorer with configurable weights"""

    # Weights (sum to 1.0)
    RELIABILITY_WEIGHT = 0.4
    LATENCY_WEIGHT = 0.2
    COST_WEIGHT = 0.4

    # Normalization baselines
    BASELINE_LATENCY_MS = 250  # 250ms = score 5
    BASELINE_COST_PER_1M = 0.15  # $0.15/1M = score 5

    def score(self, metrics: ProviderMetrics) -> ProviderScore:
        """Compute composite score"""
        reliability_score = metrics.reliability * 10
        latency_score = self._normalize_latency(metrics.latency_p99)
        cost_score = self._normalize_cost(metrics.cost_per_1m_tokens)

        composite = (
            reliability_score * self.RELIABILITY_WEIGHT
            + latency_score * self.LATENCY_WEIGHT
            + cost_score * self.COST_WEIGHT
        )

        return ProviderScore(
            provider_id=metrics.provider_id,
            reliability_score=reliability_score,
            latency_score=latency_score,
            cost_score=cost_score,
            composite_score=composite,
            timestamp=time.time(),
        )

    def _normalize_latency(self, latency_ms: float) -> float:
        """Lower latency = higher score"""
        ratio = latency_ms / self.BASELINE_LATENCY_MS
        # Inverse relationship: score = 10 / (1 + ratio)
        return 10.0 / (1.0 + (ratio - 1.0) * 0.5)

    def _normalize_cost(self, cost: float) -> float:
        """Lower cost = higher score"""
        ratio = cost / self.BASELINE_COST_PER_1M
        # Inverse relationship: score = 10 / (1 + ratio)
        return 10.0 / (1.0 + (ratio - 1.0) * 0.5)
```

#### Provider Registry

```python
# thegent/src/thegent/governance/providers.py

from typing import Dict, Optional
from enum import Enum


class ProviderType(Enum):
    DIRECT = "direct"
    PROXY = "proxy"


@dataclass
class ProviderConfig:
    """Provider configuration"""

    provider_id: str
    name: str
    provider_type: ProviderType
    api_endpoint: str
    auth_method: str  # "api_key", "oauth", etc.
    cost_per_1m_tokens: float
    max_rpm: int  # Requests per minute
    max_tpm: int  # Tokens per minute
    fallback_order: List[str]  # Preferred fallback providers


class ProviderRegistry:
    """Centralized provider configuration"""

    _registry: Dict[str, ProviderConfig] = {}
    _scorer: ProviderScorer = DefaultProviderScorer()

    @classmethod
    def register(cls, config: ProviderConfig):
        """Register a provider"""
        cls._registry[config.provider_id] = config

    @classmethod
    def get(cls, provider_id: str) -> Optional[ProviderConfig]:
        """Get provider config"""
        return cls._registry.get(provider_id)

    @classmethod
    def list_providers(cls) -> List[ProviderConfig]:
        """List all providers"""
        return list(cls._registry.values())

    @classmethod
    def get_fallback_order(cls, provider_id: str) -> List[str]:
        """Get fallback chain for provider"""
        config = cls.get(provider_id)
        return config.fallback_order if config else []


# Initialize registry with built-in providers
_BUILTIN_PROVIDERS = [
    ProviderConfig(
        provider_id="gemini-flash",
        name="Google Gemini 3 Flash",
        provider_type=ProviderType.DIRECT,
        api_endpoint="https://generativelanguage.googleapis.com",
        auth_method="api_key",
        cost_per_1m_tokens=0.10,
        max_rpm=1500,
        max_tpm=1000000,
        fallback_order=["claude-haiku", "gpt-4o-mini"],
    ),
    ProviderConfig(
        provider_id="claude-haiku",
        name="Anthropic Claude Haiku 4.5",
        provider_type=ProviderType.DIRECT,
        api_endpoint="https://api.anthropic.com",
        auth_method="api_key",
        cost_per_1m_tokens=0.25,
        max_rpm=1000,
        max_tpm=500000,
        fallback_order=["gemini-flash", "gpt-4o-mini"],
    ),
    # ... more providers
]

for provider_config in _BUILTIN_PROVIDERS:
    ProviderRegistry.register(provider_config)
```

### 2.2 Value Estimator

#### Location
```
thegent/src/thegent/governance/
├── value.py  # Value estimation
└── task_classifier.py  # Task classification
```

#### Interface

```python
# thegent/src/thegent/governance/value.py

from dataclasses import dataclass
from enum import Enum


class TaskComplexity(Enum):
    TRIVIAL = 1
    SIMPLE = 3
    MODERATE = 5
    COMPLEX = 7
    VERY_COMPLEX = 10


class BusinessImpact(Enum):
    NONE = 0
    LOW = 2
    MEDIUM = 5
    HIGH = 8
    CRITICAL = 10


class UserPriority(Enum):
    STANDARD = 1
    ELEVATED = 3
    URGENT = 8
    BLOCKING = 10


@dataclass
class TaskValue:
    """Estimated task value"""

    complexity: float  # 1-10
    business_impact: float  # 0-10
    user_priority: float  # 1-10
    estimated_value: float  # Composite
    confidence: float  # 0.0-1.0 (confidence in estimate)


class ValueEstimator:
    """Estimate task value for cost-to-value routing"""

    # Weights for value components
    COMPLEXITY_WEIGHT = 0.3
    BUSINESS_IMPACT_WEIGHT = 0.5
    PRIORITY_WEIGHT = 0.2

    def estimate(self, task) -> TaskValue:
        """Estimate value of task"""
        complexity = self._estimate_complexity(task)
        business_impact = self._estimate_business_impact(task)
        user_priority = self._estimate_user_priority(task)

        value = (
            complexity * self.COMPLEXITY_WEIGHT
            + business_impact * self.BUSINESS_IMPACT_WEIGHT
            + user_priority * self.PRIORITY_WEIGHT
        )

        confidence = self._estimate_confidence(task)

        return TaskValue(
            complexity=complexity,
            business_impact=business_impact,
            user_priority=user_priority,
            estimated_value=value,
            confidence=confidence,
        )

    def _estimate_complexity(self, task) -> float:
        """Estimate task complexity (1-10)"""
        # Factors: lines of code, number of files, dependencies, etc.
        if hasattr(task, "complexity_hint"):
            return task.complexity_hint

        # Default: analyze task type
        task_type = task.get("type", "unknown")
        return {
            "trivial_fix": 1,
            "simple_refactor": 3,
            "feature_addition": 7,
            "system_design": 10,
        }.get(task_type, 5)

    def _estimate_business_impact(self, task) -> float:
        """Estimate business impact (0-10)"""
        # Factors: user-facing, revenue impact, compliance, etc.
        if hasattr(task, "business_impact"):
            return task.business_impact

        business_category = task.get("business_category", "internal")
        return {
            "internal": 2,
            "user_experience": 6,
            "revenue": 8,
            "compliance": 9,
            "security": 10,
        }.get(business_category, 2)

    def _estimate_user_priority(self, task) -> float:
        """Estimate user priority (1-10)"""
        if hasattr(task, "priority"):
            return task.priority

        return 1  # Standard priority by default

    def _estimate_confidence(self, task) -> float:
        """Estimate confidence in value estimate (0-1)"""
        # Higher confidence for standard task types with explicit hints
        if hasattr(task, "complexity_hint") and hasattr(task, "business_impact"):
            return 0.9
        return 0.6  # Lower confidence for inferred values
```

### 2.3 Cost Estimator

#### Location
```
thegent/src/thegent/governance/cost.py
```

#### Interface

```python
# thegent/src/thegent/governance/cost.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class TokenEstimate:
    """Estimated token usage"""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    confidence: float  # 0.0-1.0


@dataclass
class CostEstimate:
    """Estimated task cost"""

    provider_id: str
    token_estimate: TokenEstimate
    cost_usd: float
    confidence: float


class CostEstimator:
    """Estimate task cost for given provider"""

    # Token estimation multipliers by task type
    TOKEN_ESTIMATES = {
        "trivial_fix": (100, 50),  # (input, output)
        "simple_refactor": (300, 150),
        "feature_addition": (1000, 500),
        "system_design": (2000, 1000),
    }

    def estimate(
        self,
        task,
        provider_id: str,
    ) -> CostEstimate:
        """Estimate cost for task on given provider"""
        # Get provider pricing
        provider_config = ProviderRegistry.get(provider_id)
        if not provider_config:
            raise ValueError(f"Unknown provider: {provider_id}")

        # Estimate tokens
        token_estimate = self._estimate_tokens(task)

        # Calculate cost
        cost_usd = token_estimate.total_tokens / 1_000_000 * provider_config.cost_per_1m_tokens

        return CostEstimate(
            provider_id=provider_id,
            token_estimate=token_estimate,
            cost_usd=cost_usd,
            confidence=token_estimate.confidence,
        )

    def _estimate_tokens(self, task) -> TokenEstimate:
        """Estimate token usage"""
        task_type = task.get("type", "unknown")

        if task_type in self.TOKEN_ESTIMATES:
            input_est, output_est = self.TOKEN_ESTIMATES[task_type]
        else:
            # Default estimate
            input_est, output_est = 500, 250

        # Adjust based on task size hints
        if hasattr(task, "size_multiplier"):
            input_est *= task.size_multiplier
            output_est *= task.size_multiplier

        total = input_est + output_est
        confidence = 0.75  # Moderate confidence in estimate

        return TokenEstimate(
            input_tokens=input_est,
            output_tokens=output_est,
            total_tokens=total,
            confidence=confidence,
        )
```

### 2.4 Cost-Aware Router

#### Location
```
thegent/src/thegent/governance/router.py
```

#### Interface

```python
# thegent/src/thegent/governance/router.py

from dataclasses import dataclass
from typing import List, Optional
import logging


@dataclass
class RoutingDecision:
    """Decision made by router"""

    selected_provider: str
    candidate_providers: List[str]
    cost_to_value_ratio: float
    cost_estimates: Dict[str, CostEstimate]
    value_estimate: TaskValue
    fallback_chain: List[str]
    decision_rationale: str
    timestamp: float


class CostAwareRouter:
    """Route tasks to providers based on cost-to-value ratio"""

    def __init__(
        self,
        value_estimator: Optional[ValueEstimator] = None,
        cost_estimator: Optional[CostEstimator] = None,
        scorer: Optional[ProviderScorer] = None,
    ):
        self.value_estimator = value_estimator or ValueEstimator()
        self.cost_estimator = cost_estimator or CostEstimator()
        self.scorer = scorer or DefaultProviderScorer()
        self.logger = logging.getLogger(__name__)
        self._decision_log: List[RoutingDecision] = []

    def route(self, task) -> RoutingDecision:
        """Select best provider for task"""
        try:
            # Estimate task value
            value_estimate = self.value_estimator.estimate(task)

            # Get candidate providers
            candidates = ProviderRegistry.list_providers()

            # Estimate cost for each provider
            cost_estimates = {}
            for provider in candidates:
                try:
                    cost_est = self.cost_estimator.estimate(task, provider.provider_id)
                    cost_estimates[provider.provider_id] = cost_est
                except Exception as e:
                    self.logger.warning(f"Failed to estimate cost for {provider.provider_id}: {e}")

            # Calculate cost-to-value ratios
            ratios = {}
            for provider_id, cost_est in cost_estimates.items():
                if value_estimate.estimated_value > 0:
                    ratio = cost_est.cost_usd / value_estimate.estimated_value
                    ratios[provider_id] = ratio

            # Select provider with best (lowest) ratio
            if ratios:
                selected_provider = min(ratios.items(), key=lambda x: x[1])[0]
                best_ratio = ratios[selected_provider]
            else:
                # Fallback: select highest-scoring provider
                selected_provider = self._select_by_score(candidates)
                best_ratio = float("inf")

            # Get fallback chain
            fallback_chain = ProviderRegistry.get_fallback_order(selected_provider)

            # Create decision record
            decision = RoutingDecision(
                selected_provider=selected_provider,
                candidate_providers=[p.provider_id for p in candidates],
                cost_to_value_ratio=best_ratio,
                cost_estimates=cost_estimates,
                value_estimate=value_estimate,
                fallback_chain=fallback_chain,
                decision_rationale=self._build_rationale(selected_provider, ratios, value_estimate),
                timestamp=time.time(),
            )

            # Log decision
            self._decision_log.append(decision)
            self.logger.info(f"Routing decision: {selected_provider} (ratio={best_ratio:.4f})")

            return decision

        except Exception as e:
            self.logger.error(f"Routing error: {e}")
            # Fallback: highest-scoring provider
            candidates = ProviderRegistry.list_providers()
            selected_provider = self._select_by_score(candidates)

            return RoutingDecision(
                selected_provider=selected_provider,
                candidate_providers=[p.provider_id for p in candidates],
                cost_to_value_ratio=0.0,
                cost_estimates={},
                value_estimate=TaskValue(0, 0, 0, 0, 0),
                fallback_chain=ProviderRegistry.get_fallback_order(selected_provider),
                decision_rationale=f"Fallback due to error: {e}",
                timestamp=time.time(),
            )

    def _select_by_score(self, providers: List[ProviderConfig]) -> str:
        """Select highest-scoring provider"""
        best_score = -1
        best_provider = None

        for provider in providers:
            # Fetch recent metrics (from Supermemory L3)
            metrics = self._get_provider_metrics(provider.provider_id)
            score = self.scorer.score(metrics)

            if score.composite_score > best_score:
                best_score = score.composite_score
                best_provider = provider.provider_id

        return best_provider or providers[0].provider_id

    def _get_provider_metrics(self, provider_id: str) -> ProviderMetrics:
        """Get recent metrics for provider (from Supermemory L3)"""
        # TODO: Integrate with Supermemory L3
        # For now, return default metrics
        return ProviderMetrics(
            provider_id=provider_id,
            reliability=0.95,
            latency_p99=250,
            cost_per_1m_tokens=0.15,
            last_updated=time.time(),
            sample_size=1000,
        )

    def _build_rationale(
        self,
        selected: str,
        ratios: Dict[str, float],
        value: TaskValue,
    ) -> str:
        """Build human-readable rationale"""
        if not ratios:
            return "Selected by score (cost estimation unavailable)"

        ratio = ratios[selected]
        return (
            f"Selected {selected} with cost-to-value ratio {ratio:.4f}. "
            f"Task value: {value.estimated_value:.2f}, "
            f"Confidence: {value.confidence:.1%}"
        )

    def get_decision_log(self) -> List[RoutingDecision]:
        """Get routing decision audit trail"""
        return self._decision_log.copy()
```

---

## 3. Integration Architecture

### 3.1 System Context

```
┌──────────────────────────────┐
│  Pareto Router (WP-1004)     │
│  ├─ Task Classification      │
│  ├─ Risk Assessment          │
│  └─ Route Selection (80/20)  │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  Economic Governance (WP-5003)       │ ◄─── THIS MODULE
│  ├─ Value Estimation                │
│  ├─ Cost Estimation                 │
│  ├─ Provider Scoring                │
│  └─ Cost-Aware Router               │
└────────────┬─────────────────────────┘
             │
    ┌────────┴────────┬─────────────┐
    ▼                 ▼             ▼
┌─────────┐    ┌────────────┐  ┌─────────┐
│Lifecycle│    │ The Gent   │  │Fallback │
│ Loop    │    │ Loop       │  │Providers│
└─────────┘    └────────────┘  └─────────┘
```

### 3.2 Data Flow

```
Task Input
  │
  ├─► Value Estimator
  │   ├─ Complexity analysis
  │   ├─ Business impact assessment
  │   └─ Priority check
  │
  ├─► Cost Estimator (for each provider)
  │   ├─ Token estimation
  │   ├─ Provider pricing lookup
  │   └─ Cost calculation
  │
  ├─► Provider Scorer
  │   ├─ Reliability normalization
  │   ├─ Latency normalization
  │   ├─ Cost normalization
  │   └─ Score aggregation
  │
  ├─► Cost-to-Value Calculation
  │   └─ Select provider with best ratio
  │
  └─► Audit Log Entry
      └─ Record decision with rationale
```

### 3.3 Integration with Supermemory

```python
# Store provider metrics in L3 Knowledge Graph
async def store_provider_metrics(self, metrics: ProviderMetrics):
    await supermemory_client.store_knowledge(
        entity=f"provider:{metrics.provider_id}",
        relationships=[
            Relationship(
                type="has_reliability",
                value=metrics.reliability,
            ),
            Relationship(
                type="has_latency_p99",
                value=metrics.latency_p99,
            ),
            Relationship(
                type="has_cost",
                value=metrics.cost_per_1m_tokens,
            ),
        ],
    )


# Query provider scores
async def get_provider_metrics(self, provider_id: str) -> ProviderMetrics:
    nodes = await supermemory_client.query_knowledge(f"provider:{provider_id}")
    return self._parse_metrics(nodes)
```

---

## 4. Error Handling & Fallback

### 4.1 Fallback Strategy

**Chain**: Primary → Fallback1 → Fallback2 → Default

```python
async def execute_with_fallback(
    self,
    task,
    decision: RoutingDecision,
) -> Result:
    """Execute task with fallback chain"""
    providers_to_try = [decision.selected_provider] + decision.fallback_chain

    for provider_id in providers_to_try:
        try:
            result = await execute_on_provider(provider_id, task)
            return result
        except ProviderUnavailableError:
            logger.info(f"Provider {provider_id} unavailable, trying next")
            continue
        except ProviderRateLimitError:
            logger.info(f"Provider {provider_id} rate limited, trying next")
            continue
        except Exception as e:
            logger.error(f"Provider {provider_id} error: {e}")
            continue

    # All providers failed
    raise AllProvidersFailedError(f"All providers failed for task: {task}")
```

### 4.2 Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Cost estimation fails | Try/catch | Use default estimate |
| Value estimation fails | Confidence check | Use default value |
| Provider unavailable | HTTP error | Fallback to next provider |
| Rate limit hit | 429 response | Retry with backoff |
| Metric lookup fails | Exception | Use cached metrics |

---

## 5. Data Structures

### 5.1 Configuration File

```yaml
# config/governance.yaml
providers:
  gemini-flash:
    cost_per_1m_tokens: 0.10
    reliability_baseline: 0.95
    latency_p99_baseline: 200
  claude-haiku:
    cost_per_1m_tokens: 0.25
    reliability_baseline: 0.98
    latency_p99_baseline: 300

scoring:
  reliability_weight: 0.4
  latency_weight: 0.2
  cost_weight: 0.4
  baseline_latency_ms: 250
  baseline_cost_per_1m: 0.15

value_estimation:
  complexity_weight: 0.3
  business_impact_weight: 0.5
  priority_weight: 0.2

routing:
  enable_cost_aware: true
  fallback_strategy: "score_based"
  max_retries: 3
  retry_backoff: "exponential"
```

### 5.2 Audit Log Schema

```python
@dataclass
class AuditLogEntry:
    timestamp: float
    task_id: str
    selected_provider: str
    cost_estimate: float
    value_estimate: float
    cost_to_value_ratio: float
    decision_rationale: str
    fallback_used: bool
    execution_time_ms: float
    actual_cost: Optional[float] = None
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

```python
def test_value_estimator():
    """Test value estimation"""
    estimator = ValueEstimator()
    task = {"type": "feature_addition", "priority": 5}
    value = estimator.estimate(task)
    assert 5 < value.estimated_value < 8


def test_cost_estimator():
    """Test cost estimation"""
    estimator = CostEstimator()
    task = {"type": "simple_refactor"}
    cost = estimator.estimate(task, "gemini-flash")
    assert cost.cost_usd < 0.01  # Should be cheap


def test_router_selects_best_ratio():
    """Test router selects provider with best ratio"""
    router = CostAwareRouter()
    task = {"type": "trivial_fix"}
    decision = router.route(task)
    assert decision.selected_provider == "gemini-flash"  # Cheapest
```

### 6.2 Integration Tests

- Test with live provider APIs
- Test fallback chain execution
- Test cost prediction accuracy
- Test routing decision logging

### 6.3 Performance Tests

- <5ms provider selection
- <10ms cost estimation per provider
- <1ms audit log write

---

## 7. Deployment Checklist

- [ ] Provider registry populated
- [ ] Supermemory integration functional
- [ ] Audit logging configured
- [ ] Performance baselines established
- [ ] Fallback chain tested
- [ ] Cost tracking implemented
- [ ] Monitoring dashboards created

---

## See Also

- [Proposal](./proposal.md) — Business rationale
- [Tasks](./tasks.md) — Implementation tasks
- [SESSION_RESEARCH_FRAGMENTS_EXPANDED.md](../../research/SESSION_RESEARCH_FRAGMENTS_EXPANDED.md#3-economic-governance) — Research
