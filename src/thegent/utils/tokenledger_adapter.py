"""Tokenledger adapter for thegent.

Fetches benchmark data from tokenledger CLI/HTTP service and provides
a unified interface for routing decisions.

Usage:
    from thegent.utils.tokenledger_adapter import TokenledgerAdapter

    adapter = TokenledgerAdapter()
    benchmark = adapter.get_benchmark("gpt-4o")
    quality = benchmark.intelligence_index / 100.0 if benchmark else fallback
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass

_log = logging.getLogger(__name__)

# Default tokenledger CLI path
DEFAULT_TOKENLEDGER_PATH = "tokenledger"

# Cache TTL in seconds
CACHE_TTL_SECONDS = 3600  # 1 hour


@dataclass
class BenchmarkData:
    """Benchmark data for a model from tokenledger."""

    model_id: str
    provider: str | None = None

    # Quality metrics
    intelligence_index: float | None = None
    coding_index: float | None = None

    # Performance metrics
    speed_tps: float | None = None  # Tokens per second
    latency_ttft_ms: float | None = None  # Time to first token

    # Cost metrics
    price_input_per_1m: float | None = None  # USD per 1M input tokens
    price_output_per_1m: float | None = None  # USD per 1M output tokens

    # Context
    context_window_tokens: int | None = None

    # Metadata
    confidence: float = 0.0
    source: str = "unknown"

    def get_quality_score(self) -> float | None:
        """Get normalized quality score (0-1)."""
        if self.intelligence_index is not None:
            return self.intelligence_index / 100.0
        return None

    def get_cost_per_1k(self) -> float | None:
        """Get cost per 1K tokens."""
        if self.price_input_per_1m is not None:
            return self.price_input_per_1m
        return None

    def get_latency_ms(self) -> int | None:
        """Get latency in milliseconds."""
        if self.latency_ttft_ms is not None:
            return int(self.latency_ttft_ms)
        return None


@dataclass
class TokenledgerConfig:
    """Configuration for tokenledger adapter."""

    # Path to tokenledger CLI
    cli_path: str = DEFAULT_TOKENLEDGER_PATH

    # Enable/disable tokenledger integration
    enabled: bool = True

    # Cache TTL in seconds
    cache_ttl: int = CACHE_TTL_SECONDS

    # Fallback to hardcoded values on error
    fallback_on_error: bool = True


class TokenledgerAdapter:
    """Adapter for fetching benchmark data from tokenledger.

    This adapter:
    1. Calls tokenledger CLI to get benchmark data
    2. Caches results for performance
    3. Falls back to hardcoded values on error
    """

    def __init__(self, config: TokenledgerConfig | None = None):
        self.config = config or TokenledgerConfig()
        self._cache: dict[str, BenchmarkData] = {}
        self._available: bool | None = None

    def is_available(self) -> bool:
        """Check if tokenledger CLI is available."""
        if self._available is not None:
            return self._available

        # Check if CLI exists
        if shutil.which(self.config.cli_path):
            self._available = True
            return True

        self._available = False
        return False

    def get_benchmark(self, model_id: str) -> BenchmarkData | None:
        """Get benchmark data for a model.

        Args:
            model_id: Model identifier (e.g., "gpt-4o", "claude-3-5-sonnet")

        Returns:
            BenchmarkData if available, None otherwise
        """
        if not self.config.enabled:
            return None

        # Check cache
        if model_id in self._cache:
            return self._cache[model_id]

        # Try to fetch from tokenledger
        if self.is_available():
            data = self._fetch_from_cli(model_id)
            if data:
                self._cache[model_id] = data
                return data

        return None

    def get_all_benchmarks(self) -> list[BenchmarkData]:
        """Get all available benchmarks."""
        if not self.is_available():
            return []

        # Would call tokenledger to get all benchmarks
        # For now, return empty list
        return []

    def refresh(self) -> bool:
        """Refresh benchmark data cache."""
        self._cache.clear()
        return True

    def _fetch_from_cli(self, model_id: str) -> BenchmarkData | None:
        """Fetch benchmark data from tokenledger CLI.

        Args:
            model_id: Model identifier

        Returns:
            BenchmarkData if successful, None otherwise
        """
        try:
            result = subprocess.run(
                [self.config.cli_path, "benchmark", "get", model_id, "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                _log.debug(f"Tokenledger CLI error: {result.stderr}")
                return None

            data = json.loads(result.stdout)
            return self._parse_benchmark_data(data)

        except subprocess.TimeoutExpired:
            _log.warning(f"Tokenledger CLI timeout for {model_id}")
            return None
        except json.JSONDecodeError as e:
            _log.warning(f"Tokenledger CLI JSON error: {e}")
            return None
        except Exception as e:
            _log.warning(f"Tokenledger CLI error: {e}")
            return None

    def _parse_benchmark_data(self, data: dict) -> BenchmarkData:
        """Parse benchmark data from JSON response."""
        return BenchmarkData(
            model_id=data.get("model_id", ""),
            provider=data.get("provider"),
            intelligence_index=data.get("intelligence_index"),
            coding_index=data.get("coding_index"),
            speed_tps=data.get("speed_tps"),
            latency_ttft_ms=data.get("latency_ttft_ms"),
            price_input_per_1m=data.get("price_input_per_1m"),
            price_output_per_1m=data.get("price_output_per_1m"),
            context_window_tokens=data.get("context_window_tokens"),
            confidence=data.get("confidence", 0.0),
            source=data.get("source", "tokenledger"),
        )

    def get_quality_score(self, model_id: str, fallback: float = 0.5) -> float:
        """Get quality score for a model with fallback.

        Args:
            model_id: Model identifier
            fallback: Fallback value if not found

        Returns:
            Quality score (0-1)
        """
        data = self.get_benchmark(model_id)
        if data:
            quality = data.get_quality_score()
            if quality is not None:
                return quality
        return fallback

    def get_cost_per_1k(self, model_id: str, fallback: float = 0.01) -> float:
        """Get cost per 1K tokens for a model with fallback.

        Args:
            model_id: Model identifier
            fallback: Fallback value if not found

        Returns:
            Cost per 1K tokens in USD
        """
        data = self.get_benchmark(model_id)
        if data:
            cost = data.get_cost_per_1k()
            if cost is not None:
                return cost
        return fallback

    def get_latency_ms(self, model_id: str, fallback: int = 2000) -> int:
        """Get latency in ms for a model with fallback.

        Args:
            model_id: Model identifier
            fallback: Fallback value if not found

        Returns:
            Latency in milliseconds
        """
        data = self.get_benchmark(model_id)
        if data:
            latency = data.get_latency_ms()
            if latency is not None:
                return latency
        return fallback


# Global adapter instance
_adapter: TokenledgerAdapter | None = None


def get_adapter() -> TokenledgerAdapter:
    """Get the global tokenledger adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = TokenledgerAdapter()
    return _adapter


def get_benchmark(model_id: str) -> BenchmarkData | None:
    """Convenience function to get benchmark data."""
    return get_adapter().get_benchmark(model_id)


def get_quality_score(model_id: str, fallback: float = 0.5) -> float:
    """Convenience function to get quality score."""
    return get_adapter().get_quality_score(model_id, fallback)


def get_cost_per_1k(model_id: str, fallback: float = 0.01) -> float:
    """Convenience function to get cost per 1K tokens."""
    return get_adapter().get_cost_per_1k(model_id, fallback)


def get_latency_ms(model_id: str, fallback: int = 2000) -> int:
    """Convenience function to get latency."""
    return get_adapter().get_latency_ms(model_id, fallback)
