"""
Provider Registry (Task 2.1.2)

Extensible registry with built-in provider configurations.
Supports provider lookup, fallback chains, and cost efficiency ordering.
"""

from dataclasses import dataclass, field

from governance.scoring import DefaultProviderScorer, ProviderMetrics, ProviderScore


@dataclass
class ProviderConfig:
    """Provider configuration and characteristics"""

    provider_id: str
    name: str
    cost_per_1m_tokens: float
    reliability: float  # 0.0-1.0
    latency_p99_ms: int
    fallback_chain: list[str] = field(default_factory=list)  # Ordered fallback providers

    def to_metrics(self) -> ProviderMetrics:
        """Convert to ProviderMetrics for scoring"""
        return ProviderMetrics(
            reliability=self.reliability,
            latency_p99=self.latency_p99_ms,
            cost_per_1m_tokens=self.cost_per_1m_tokens,
        )


class ProviderRegistry:
    """
    Extensible provider registry with scoring and fallback support.

    Supports:
    - Provider lookup by ID
    - Fallback chain resolution
    - Cost-efficiency ordering
    - Provider scoring via DefaultProviderScorer
    """

    def __init__(self, scorer: DefaultProviderScorer | None = None) -> None:
        """
        Initialize registry with optional custom scorer.

        Args:
            scorer: Custom ProviderScorer instance (defaults to DefaultProviderScorer)
        """
        self.scorer = scorer or DefaultProviderScorer()
        self.providers: dict[str, ProviderConfig] = {}
        self._scores_cache: dict[str, ProviderScore] = {}

        # Initialize with built-in providers
        self._register_builtin_providers()

    def _register_builtin_providers(self) -> None:
        """Register built-in providers with realistic configs"""
        builtin = [
            ProviderConfig(
                provider_id="gemini-flash",
                name="Google Gemini Flash",
                cost_per_1m_tokens=0.10,
                reliability=0.95,
                latency_p99_ms=200,
                fallback_chain=["gpt-4o-mini", "claude-haiku", "claude-opus"],
            ),
            ProviderConfig(
                provider_id="claude-haiku",
                name="Anthropic Claude Haiku",
                cost_per_1m_tokens=0.25,
                reliability=0.98,
                latency_p99_ms=300,
                fallback_chain=["gemini-flash", "gpt-4o-mini", "claude-sonnet"],
            ),
            ProviderConfig(
                provider_id="gpt-4o-mini",
                name="OpenAI GPT-4o Mini",
                cost_per_1m_tokens=0.15,
                reliability=0.97,
                latency_p99_ms=250,
                fallback_chain=["gemini-flash", "claude-haiku", "gpt-4"],
            ),
            ProviderConfig(
                provider_id="claude-sonnet",
                name="Anthropic Claude Sonnet",
                cost_per_1m_tokens=3.00,
                reliability=0.99,
                latency_p99_ms=350,
                fallback_chain=["claude-haiku", "gpt-4", "gemini-pro"],
            ),
            ProviderConfig(
                provider_id="claude-opus",
                name="Anthropic Claude Opus",
                cost_per_1m_tokens=15.0,
                reliability=0.99,
                latency_p99_ms=500,
                fallback_chain=["claude-sonnet", "gpt-4", "claude-haiku"],
            ),
            ProviderConfig(
                provider_id="gpt-4",
                name="OpenAI GPT-4",
                cost_per_1m_tokens=30.0,
                reliability=0.98,
                latency_p99_ms=400,
                fallback_chain=["gpt-4-turbo", "claude-opus", "claude-sonnet"],
            ),
        ]

        for config in builtin:
            self.register(config)

    def register(self, config: ProviderConfig) -> None:
        """
        Register a provider configuration.

        Args:
            config: ProviderConfig with provider details

        Raises:
            ValueError: If provider_id already registered
        """
        if config.provider_id in self.providers:
            raise ValueError(f"Provider '{config.provider_id}' already registered")

        self.providers[config.provider_id] = config
        # Invalidate cache when new provider added
        self._scores_cache.clear()

    def get(self, provider_id: str) -> ProviderConfig | None:
        """
        Get provider configuration by ID.

        Args:
            provider_id: Provider identifier

        Returns:
            ProviderConfig if found, None otherwise
        """
        return self.providers.get(provider_id)

    def list_providers(self) -> list[ProviderConfig]:
        """
        List all registered providers.

        Returns:
            List of all registered ProviderConfig objects
        """
        return list(self.providers.values())

    def get_fallback_order(self, provider_id: str) -> list[str]:
        """
        Get ordered fallback chain for a provider.

        Args:
            provider_id: Primary provider ID

        Returns:
            List of provider IDs in fallback order (including primary at index 0)

        Raises:
            ValueError: If provider not found
        """
        provider = self.get(provider_id)
        if not provider:
            raise ValueError(f"Provider '{provider_id}' not found")

        # Return: [primary, ...fallbacks], filtering out any missing providers
        chain = [provider_id]
        for fallback_id in provider.fallback_chain:
            if self.get(fallback_id):  # Only include if registered
                chain.append(fallback_id)

        return chain

    def get_cost_efficient_order(self) -> list[str]:
        """
        Get providers ordered by cost efficiency (lowest cost first).

        Returns:
            List of provider IDs sorted by cost (ascending)
        """
        sorted_providers = sorted(
            self.providers.items(),
            key=lambda item: item[1].cost_per_1m_tokens,
        )
        return [provider_id for provider_id, _ in sorted_providers]

    def get_score(self, provider_id: str) -> ProviderScore:
        """
        Get composite score for a provider (with caching).

        Args:
            provider_id: Provider identifier

        Returns:
            ProviderScore with composite and component scores

        Raises:
            ValueError: If provider not found
        """
        if provider_id in self._scores_cache:
            return self._scores_cache[provider_id]

        provider = self.get(provider_id)
        if not provider:
            raise ValueError(f"Provider '{provider_id}' not found")

        metrics = provider.to_metrics()
        score = self.scorer.score(provider_id, metrics)
        self._scores_cache[provider_id] = score

        return score

    def get_ranked_providers(self) -> list[tuple[str, ProviderScore]]:
        """
        Get all providers ranked by composite score (highest first).

        Returns:
            List of (provider_id, ProviderScore) tuples sorted by score descending
        """
        scores = [(provider_id, self.get_score(provider_id)) for provider_id in self.providers]
        scores.sort(key=lambda item: item[1].composite_score, reverse=True)
        return scores

    def validate_fallback_chains(self) -> dict[str, list[str]]:
        """
        Validate that all fallback providers are registered.

        Returns:
            Dict mapping provider_id to list of missing fallback providers
        """
        missing = {}
        for provider_id, config in self.providers.items():
            missing_for_provider = [fb for fb in config.fallback_chain if fb not in self.providers]
            if missing_for_provider:
                missing[provider_id] = missing_for_provider

        return missing
