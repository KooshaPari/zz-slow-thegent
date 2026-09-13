"""Unified benchmark store with tokenledger integration.

Provides a unified interface for benchmark data that:
1. Tries tokenledger first for dynamic data
2. Falls back to hardcoded values
3. Maintains backward compatibility with existing QUALITY_PROXY

Usage:
    from thegent.utils.benchmark_store import BenchmarkStore

    store = BenchmarkStore()
    quality = store.get_quality("gpt-4o")  # Returns 0.85
    cost = store.get_cost("gpt-4o")  # Returns 0.005
"""

from __future__ import annotations

import logging

from thegent.utils.tokenledger_adapter import (
    BenchmarkData,
    TokenledgerAdapter,
    TokenledgerConfig,
)

_log = logging.getLogger(__name__)

# Hardcoded fallback values (from original pareto_router.py)
QUALITY_PROXY: dict[str, float] = {
    "claude-opus-4.6": 0.95,
    "claude-opus-4.6-1m": 0.96,
    "claude-sonnet-4.6": 0.88,
    "claude-haiku-4.5": 0.75,
    "gpt-5.3-codex-high": 0.92,
    "gpt-5.3-codex": 0.82,
    "claude-4.5-opus-high-thinking": 0.94,
    "claude-4.5-opus-high": 0.92,
    "claude-4.5-sonnet-thinking": 0.85,
    "claude-4-sonnet": 0.80,
    "gpt-4o": 0.85,
    "gpt-5.1-codex": 0.80,
    "gemini-3-flash": 0.78,
    "gemini-3.1-pro": 0.90,
    "gemini-2.5-flash": 0.76,
    "gemini-2.0-flash": 0.72,
    "glm-5": 0.78,
    "minimax-m2.5": 0.75,
    "deepseek-v3.2": 0.80,
    "composer-1.5": 0.82,
    "composer-1": 0.78,
    "roo-default": 0.70,
    "kilo-default": 0.70,
}

COST_PER_1K_PROXY: dict[str, float] = {
    "claude-opus-4.6": 0.015,
    "claude-opus-4.6-1m": 0.015,
    "claude-sonnet-4.6": 0.003,
    "claude-haiku-4.5": 0.00025,
    "gpt-5.3-codex-high": 0.020,
    "gpt-5.3-codex": 0.010,
    "claude-4.5-opus-high-thinking": 0.025,
    "claude-4.5-opus-high": 0.015,
    "claude-4.5-sonnet-thinking": 0.005,
    "claude-4-sonnet": 0.003,
    "gpt-4o": 0.005,
    "gpt-5.1-codex": 0.008,
    "gemini-3-flash": 0.00015,
    "gemini-3.1-pro": 0.007,
    "gemini-2.5-flash": 0.0001,
    "gemini-2.0-flash": 0.0001,
    "glm-5": 0.001,
    "minimax-m2.5": 0.001,
    "deepseek-v3.2": 0.0005,
    "composer-1.5": 0.002,
    "composer-1": 0.001,
    "roo-default": 0.0,
    "kilo-default": 0.0,
}

LATENCY_MS_PROXY: dict[str, int] = {
    "claude-opus-4.6": 4000,
    "claude-opus-4.6-1m": 5000,
    "claude-sonnet-4.6": 2000,
    "claude-haiku-4.5": 800,
    "gpt-5.3-codex-high": 6000,
    "gpt-5.3-codex": 3000,
    "claude-4.5-opus-high-thinking": 8000,
    "claude-4.5-opus-high": 5000,
    "claude-4.5-sonnet-thinking": 4000,
    "claude-4-sonnet": 2500,
    "gpt-4o": 2000,
    "gpt-5.1-codex": 3000,
    "gemini-3-flash": 600,
    "gemini-3.1-pro": 3000,
    "gemini-2.5-flash": 500,
    "gemini-2.0-flash": 400,
    "glm-5": 1500,
    "minimax-m2.5": 1200,
    "deepseek-v3.2": 1000,
    "composer-1.5": 2000,
    "composer-1": 1500,
    "roo-default": 1000,
    "kilo-default": 1000,
}


class BenchmarkStore:
    """Unified benchmark store with tokenledger integration.

    Tries tokenledger first, then falls back to hardcoded values.
    """

    def __init__(
        self,
        tokenledger_config: TokenledgerConfig | None = None,
        use_tokenledger: bool = True,
    ):
        self._use_tokenledger = use_tokenledger
        self._tokenledger: TokenledgerAdapter | None = None

        if use_tokenledger:
            self._tokenledger = TokenledgerAdapter(tokenledger_config)

    @property
    def tokenledger(self) -> TokenledgerAdapter | None:
        """Get the tokenledger adapter."""
        return self._tokenledger

    def get_quality(self, model_id: str) -> float | None:
        """Get quality score for a model.

        Args:
            model_id: Model identifier

        Returns:
            Quality score (0-1) or None if not found
        """
        # Try tokenledger first
        if self._tokenledger:
            data = self._tokenledger.get_benchmark(model_id)
            if data:
                quality = data.get_quality_score()
                if quality is not None:
                    return quality

        # Fallback to hardcoded
        return QUALITY_PROXY.get(model_id)

    def get_cost(self, model_id: str) -> float | None:
        """Get cost per 1K tokens for a model.

        Args:
            model_id: Model identifier

        Returns:
            Cost per 1K tokens in USD or None if not found
        """
        # Try tokenledger first
        if self._tokenledger:
            data = self._tokenledger.get_benchmark(model_id)
            if data:
                cost = data.get_cost_per_1k()
                if cost is not None:
                    return cost

        # Fallback to hardcoded
        return COST_PER_1K_PROXY.get(model_id)

    def get_latency(self, model_id: str) -> int | None:
        """Get latency in ms for a model.

        Args:
            model_id: Model identifier

        Returns:
            Latency in milliseconds or None if not found
        """
        # Try tokenledger first
        if self._tokenledger:
            data = self._tokenledger.get_benchmark(model_id)
            if data:
                latency = data.get_latency_ms()
                if latency is not None:
                    return latency

        # Fallback to hardcoded
        return LATENCY_MS_PROXY.get(model_id)

    def get_benchmark(self, model_id: str) -> BenchmarkData | None:
        """Get full benchmark data for a model.

        Args:
            model_id: Model identifier

        Returns:
            BenchmarkData or None if not found
        """
        # Try tokenledger first
        if self._tokenledger:
            data = self._tokenledger.get_benchmark(model_id)
            if data:
                return data

        # Build from hardcoded values
        quality = QUALITY_PROXY.get(model_id)
        cost = COST_PER_1K_PROXY.get(model_id)
        latency = LATENCY_MS_PROXY.get(model_id)

        if quality is not None or cost is not None:
            return BenchmarkData(
                model_id=model_id,
                intelligence_index=quality * 100 if quality else None,
                price_input_per_1m=cost,
                latency_ttft_ms=float(latency) if latency else None,
                confidence=0.5,
                source="fallback",
            )

        return None

    def refresh(self) -> bool:
        """Refresh benchmark data from tokenledger."""
        if self._tokenledger:
            return self._tokenledger.refresh()
        return True

    def get_all_models(self) -> list[str]:
        """Get all known model IDs."""
        # Combine hardcoded and tokenledger models
        models = set(QUALITY_PROXY.keys())

        if self._tokenledger:
            for data in self._tokenledger.get_all_benchmarks():
                models.add(data.model_id)

        return list(models)


# Global store instance
_store: BenchmarkStore | None = None


def get_store() -> BenchmarkStore:
    """Get the global benchmark store instance."""
    global _store
    if _store is None:
        _store = BenchmarkStore()
    return _store


def get_quality(model_id: str) -> float | None:
    """Convenience function to get quality score."""
    return get_store().get_quality(model_id)


def get_cost(model_id: str) -> float | None:
    """Convenience function to get cost."""
    return get_store().get_cost(model_id)


def get_latency(model_id: str) -> int | None:
    """Convenience function to get latency."""
    return get_store().get_latency(model_id)
