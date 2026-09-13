"""
Provider Metrics Collection (Task 2.1.3)

Infrastructure to collect and update provider performance metrics.
Supports latency p99 calculation, success rate tracking, and storage.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class ExecutionResult:
    """Single execution result for metrics collection"""

    provider_id: str
    timestamp: datetime
    success: bool
    latency_ms: float
    tokens_input: int
    tokens_output: int
    error_msg: str | None = None


@dataclass
class ProviderMetricsSnapshot:
    """Current snapshot of provider metrics"""

    provider_id: str
    timestamp: datetime
    success_count: int
    failure_count: int
    latency_samples: list[float] = field(default_factory=list)
    latency_p99: float = 0.0
    latency_p95: float = 0.0
    latency_p50: float = 0.0
    success_rate: float = 0.0
    avg_tokens_input: float = 0.0
    avg_tokens_output: float = 0.0

    def to_dict(self) -> dict:
        """Convert to serializable dict"""
        return {
            "provider_id": self.provider_id,
            "timestamp": self.timestamp.isoformat(),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "latency_p99": self.latency_p99,
            "latency_p95": self.latency_p95,
            "latency_p50": self.latency_p50,
            "success_rate": self.success_rate,
            "avg_tokens_input": self.avg_tokens_input,
            "avg_tokens_output": self.avg_tokens_output,
        }


class ProviderMetricsCollector:
    """
    Collect and aggregate provider performance metrics.

    Supports:
    - Recording execution results (success/error, latency, tokens)
    - Calculating latency p99, p95, p50
    - Calculating success rate
    - Storing metrics in local cache or external store
    - Querying metrics within <50ms
    """

    # Local cache directory
    CACHE_DIR = Path("var/provider_metrics")

    def __init__(self, storage_backend: str = "local") -> None:
        """
        Initialize metrics collector.

        Args:
            storage_backend: "local" (default) or "supermemory" (when available)
        """
        self.storage_backend = storage_backend
        self.results: dict[str, list[ExecutionResult]] = {}
        self.metrics_cache: dict[str, ProviderMetricsSnapshot] = {}
        self.last_update: dict[str, datetime] = {}

        # Ensure cache directory exists
        if storage_backend == "local":
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    async def record_execution(self, result: ExecutionResult) -> None:
        """
        Record a single execution result asynchronously.

        Args:
            result: ExecutionResult with execution metrics
        """
        provider_id = result.provider_id

        if provider_id not in self.results:
            self.results[provider_id] = []

        self.results[provider_id].append(result)

        # Invalidate cache for this provider
        if provider_id in self.metrics_cache:
            del self.metrics_cache[provider_id]

        # Store to persistent backend (async, non-blocking)
        asyncio.create_task(self._persist_result(result))

    async def _persist_result(self, result: ExecutionResult) -> None:
        """
        Persist result to storage backend (async).

        Args:
            result: ExecutionResult to persist
        """
        if self.storage_backend == "local":
            await self._persist_local(result)
        # TODO: elif self.storage_backend == "supermemory": await persist_to_supermemory(result)

    async def _persist_local(self, result: ExecutionResult) -> None:
        """
        Persist result to local JSONL file (non-blocking).

        Args:
            result: ExecutionResult to write
        """
        date_str = result.timestamp.strftime("%Y-%m-%d")
        logfile = self.CACHE_DIR / f"metrics_{date_str}.jsonl"

        # Prepare JSON line
        line = (
            json.dumps(
                {
                    "provider_id": result.provider_id,
                    "timestamp": result.timestamp.isoformat(),
                    "success": result.success,
                    "latency_ms": result.latency_ms,
                    "tokens_input": result.tokens_input,
                    "tokens_output": result.tokens_output,
                    "error_msg": result.error_msg,
                }
            )
            + "\n"
        )

        # Append to file (this should be <1ms latency)
        try:
            async with asyncio.Lock():
                with open(logfile, "a") as f:
                    f.write(line)
        except Exception:
            # Log but don't fail - metrics collection shouldn't break execution
            pass

    def get_metrics(self, provider_id: str, window_hours: int = 24) -> ProviderMetricsSnapshot | None:
        """
        Get current metrics snapshot for a provider.

        Must complete within <50ms.

        Args:
            provider_id: Provider identifier
            window_hours: Look back window (default 24 hours)

        Returns:
            ProviderMetricsSnapshot if metrics exist, None otherwise
        """
        # Check cache first
        if provider_id in self.metrics_cache:
            return self.metrics_cache[provider_id]

        # Collect from in-memory results
        if provider_id not in self.results or len(self.results[provider_id]) == 0:
            return None

        # Filter by time window
        cutoff = datetime.now() - timedelta(hours=window_hours)
        recent_results = [r for r in self.results[provider_id] if r.timestamp >= cutoff]

        if len(recent_results) == 0:
            return None

        # Calculate metrics
        snapshot = self._calculate_metrics(provider_id, recent_results)

        # Cache result
        self.metrics_cache[provider_id] = snapshot
        self.last_update[provider_id] = datetime.now()

        return snapshot

    def _calculate_metrics(
        self,
        provider_id: str,
        results: list[ExecutionResult],
    ) -> ProviderMetricsSnapshot:
        """
        Calculate metrics from execution results.

        Args:
            provider_id: Provider identifier
            results: List of ExecutionResult objects

        Returns:
            ProviderMetricsSnapshot with calculated metrics
        """
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        success_rate = success_count / len(results) if results else 0.0

        # Latency calculations (from successful executions)
        latencies = sorted([r.latency_ms for r in results if r.success])

        if len(latencies) > 0:
            p99_idx = max(0, int(len(latencies) * 0.99) - 1)
            p95_idx = max(0, int(len(latencies) * 0.95) - 1)
            p50_idx = max(0, int(len(latencies) * 0.50) - 1)

            latency_p99 = latencies[p99_idx]
            latency_p95 = latencies[p95_idx]
            latency_p50 = latencies[p50_idx]
        else:
            latency_p99 = latency_p95 = latency_p50 = 0.0

        # Token averages
        if len(results) > 0:
            avg_tokens_input = sum(r.tokens_input for r in results) / len(results)
            avg_tokens_output = sum(r.tokens_output for r in results) / len(results)
        else:
            avg_tokens_input = avg_tokens_output = 0.0

        return ProviderMetricsSnapshot(
            provider_id=provider_id,
            timestamp=datetime.now(),
            success_count=success_count,
            failure_count=failure_count,
            latency_samples=latencies[:100],  # Keep up to 100 samples
            latency_p99=latency_p99,
            latency_p95=latency_p95,
            latency_p50=latency_p50,
            success_rate=success_rate,
            avg_tokens_input=avg_tokens_input,
            avg_tokens_output=avg_tokens_output,
        )

    def get_all_providers_metrics(self) -> dict[str, ProviderMetricsSnapshot]:
        """
        Get metrics for all providers with recent executions.

        Returns:
            Dict mapping provider_id to ProviderMetricsSnapshot
        """
        metrics = {}
        for provider_id in self.results:
            snapshot = self.get_metrics(provider_id)
            if snapshot:
                metrics[provider_id] = snapshot
        return metrics

    def load_historical_metrics(self, date: str) -> dict[str, ProviderMetricsSnapshot]:
        """
        Load historical metrics from persistent storage for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Dict mapping provider_id to aggregated metrics for that date
        """
        logfile = self.CACHE_DIR / f"metrics_{date}.jsonl"

        if not logfile.exists():
            return {}

        results_by_provider: dict[str, list[ExecutionResult]] = {}

        try:
            with open(logfile) as f:
                for line in f:
                    if not line.strip():
                        continue

                    data = json.loads(line)
                    result = ExecutionResult(
                        provider_id=data["provider_id"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        success=data["success"],
                        latency_ms=data["latency_ms"],
                        tokens_input=data["tokens_input"],
                        tokens_output=data["tokens_output"],
                        error_msg=data.get("error_msg"),
                    )

                    if result.provider_id not in results_by_provider:
                        results_by_provider[result.provider_id] = []

                    results_by_provider[result.provider_id].append(result)
        except Exception:
            return {}

        # Aggregate metrics per provider
        metrics = {}
        for provider_id, results in results_by_provider.items():
            metrics[provider_id] = self._calculate_metrics(provider_id, results)

        return metrics
