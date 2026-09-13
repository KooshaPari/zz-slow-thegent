"""Unit tests for enhanced LiteLLM routing modules.

Tests for cost_tracker, alerting, donut_adapter, and enhanced router features.
"""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 -- Path used in pytest fixture type hints
from unittest.mock import patch

import orjson as json

# ============================================================================
# Cost Tracker Tests
# ============================================================================


class TestCostTracker:
    """Tests for CostTracker class."""

    def test_track_single_call(self, tmp_path: Path) -> None:
        """Test tracking a single LLM call."""
        from thegent.utils.routing_impl.cost_tracker import CostTracker

        tracker = CostTracker(log_path=tmp_path / "costs.jsonl")
        entry = tracker.track(
            provider="openai",
            model="gpt-4o",
            usage={"prompt_tokens": 100, "completion_tokens": 50},
            cost=0.005,
            latency_ms=500.0,
        )

        assert entry.provider == "openai"
        assert entry.model == "gpt-4o"
        assert entry.input_tokens == 100
        assert entry.output_tokens == 50
        assert entry.cost_usd == 0.005
        assert tracker.get_daily_spend() == 0.005

    def test_budget_exceeded(self, tmp_path: Path) -> None:
        """Test budget exceeded detection."""
        from thegent.utils.routing_impl.cost_tracker import CostTracker

        tracker = CostTracker(log_path=tmp_path / "costs.jsonl", daily_budget=0.01)

        # First call within budget
        tracker.track(
            provider="openai",
            model="gpt-4o",
            usage={"prompt_tokens": 100, "completion_tokens": 50},
            cost=0.005,
            latency_ms=500.0,
        )
        assert not tracker.is_over_budget()

        # Second call exceeds budget
        tracker.track(
            provider="openai",
            model="gpt-4o",
            usage={"prompt_tokens": 100, "completion_tokens": 50},
            cost=0.006,
            latency_ms=500.0,
        )
        assert tracker.is_over_budget()

    def test_get_stats(self, tmp_path: Path) -> None:
        """Test getting statistics summary."""
        from thegent.utils.routing_impl.cost_tracker import CostTracker

        tracker = CostTracker(log_path=tmp_path / "costs.jsonl", daily_budget=1.0)

        tracker.track("openai", "gpt-4o", {"prompt_tokens": 100, "completion_tokens": 50}, 0.005, 500.0)
        tracker.track("anthropic", "claude-sonnet-4.5", {"prompt_tokens": 200, "completion_tokens": 100}, 0.010, 600.0)

        stats = tracker.get_stats()
        assert stats.total_calls == 2
        assert stats.total_cost_usd == 0.015
        assert stats.daily_spend_usd == 0.015
        assert stats.total_tokens == 450  # 100+50+200+100
        assert "gpt-4o" in stats.requests_by_model
        assert "claude-sonnet-4.5" in stats.requests_by_model

    def test_log_file_written(self, tmp_path: Path) -> None:
        """Test that cost entries are written to JSONL file."""
        from thegent.utils.routing_impl.cost_tracker import CostTracker

        log_path = tmp_path / "costs.jsonl"
        tracker = CostTracker(log_path=log_path)

        tracker.track("openai", "gpt-4o", {"prompt_tokens": 100, "completion_tokens": 50}, 0.005, 500.0)

        assert log_path.exists()
        content = log_path.read_text()
        assert "gpt-4o" in content
        assert "openai" in content

        # Verify valid JSON
        lines = content.strip().split("\n")
        entry = json.loads(lines[0])
        assert entry["model"] == "gpt-4o"


class TestCostTrackerGlobals:
    """Tests for global cost tracker functions."""

    def test_get_cost_tracker_singleton(self) -> None:
        """Test that get_cost_tracker returns singleton."""
        from thegent.utils.routing_impl import cost_tracker

        cost_tracker.reset_cost_tracker()
        tracker1 = cost_tracker.get_cost_tracker()
        tracker2 = cost_tracker.get_cost_tracker()
        assert tracker1 is tracker2
        cost_tracker.reset_cost_tracker()


# ============================================================================
# Alerting Tests
# ============================================================================


class TestAlert:
    """Tests for Alert dataclass."""

    def test_alert_to_json(self) -> None:
        """Test alert serialization."""
        from thegent.utils.routing_impl.alerting import Alert

        alert = Alert(
            alert_type="budget_exceeded",
            severity="critical",
            message="Daily budget exceeded: $10.00 / $5.00",
            data={"daily_spend": 10.0, "budget": 5.0},
        )

        result = alert.to_json()
        assert result["alert_type"] == "budget_exceeded"
        assert result["severity"] == "critical"
        assert result["data"]["daily_spend"] == 10.0


class TestAlertManager:
    """Tests for AlertManager class."""

    def test_severity_threshold_filtering(self) -> None:
        """Test that low severity alerts are filtered."""
        from thegent.utils.routing_impl.alerting import AlertManager

        manager = AlertManager(webhook_url="http://example.com/webhook", min_severity="warning")

        # Info alert should be filtered
        assert not manager._should_send("info")

        # Warning should pass
        assert manager._should_send("warning")

        # Critical should pass
        assert manager._should_send("critical")

    def test_pending_alerts_without_webhook(self) -> None:
        """Test that alerts are queued when no webhook configured."""
        from thegent.utils.routing_impl.alerting import AlertManager

        manager = AlertManager(webhook_url=None)
        manager.send_alert(manager.alert_budget_exceeded(daily_spend=10.0, budget=5.0))

        pending = manager.get_pending_alerts()
        assert len(pending) >= 1
        assert pending[0].alert_type == "budget_exceeded"

    def test_alert_budget_exceeded(self) -> None:
        """Test budget exceeded alert creation."""
        from thegent.utils.routing_impl.alerting import AlertManager

        manager = AlertManager(webhook_url=None)
        alert = manager.alert_budget_exceeded(daily_spend=10.0, budget=5.0)

        assert alert.alert_type == "budget_exceeded"
        assert alert.severity == "critical"
        assert "exceeded" in alert.message.lower()

    def test_alert_high_latency(self) -> None:
        """Test high latency alert creation."""
        from thegent.utils.routing_impl.alerting import AlertManager

        manager = AlertManager(webhook_url=None)
        alert = manager.alert_high_latency(
            model="gpt-4o",
            latency_ms=2000.0,
            threshold_ms=500.0,
            provider="openai",
        )

        assert alert.alert_type == "high_latency"
        assert alert.severity == "warning"
        assert "gpt-4o" in alert.message

    def test_alert_provider_error(self) -> None:
        """Test provider error alert creation."""
        from thegent.utils.routing_impl.alerting import AlertManager

        manager = AlertManager(webhook_url=None)
        alert = manager.alert_provider_error(
            provider="openai",
            error="Rate limit exceeded",
            model="gpt-4o",
            is_rate_limit=True,
        )

        assert alert.alert_type == "provider_error"
        assert alert.severity == "warning"  # Rate limit = warning
        assert "openai" in alert.message

    def test_alert_provider_error_critical(self) -> None:
        """Test critical provider error alert."""
        from thegent.utils.routing_impl.alerting import AlertManager

        manager = AlertManager(webhook_url=None)
        alert = manager.alert_provider_error(
            provider="openai",
            error="Internal server error",
            model="gpt-4o",
            is_rate_limit=False,
        )

        assert alert.severity == "critical"  # Non-rate-limit = critical


class TestAlertManagerGlobals:
    """Tests for global alert manager functions."""

    def test_get_alert_manager_singleton(self) -> None:
        """Test that get_alert_manager returns singleton."""
        from thegent.utils.routing_impl import alerting

        alerting.reset_alert_manager()
        manager1 = alerting.get_alert_manager()
        manager2 = alerting.get_alert_manager()
        assert manager1 is manager2
        alerting.reset_alert_manager()


# ============================================================================
# Donut Adapter Tests
# ============================================================================


class TestRoutingStats:
    """Tests for RoutingStats dataclass."""

    def test_routing_stats_defaults(self) -> None:
        """Test default values."""
        from thegent.utils.routing_impl.donut_adapter import RoutingStats

        stats = RoutingStats()
        assert stats.total_requests == 0
        assert stats.total_cost_usd == 0.0
        assert stats.errors == 0


class TestRoutingDonutAdapter:
    """Tests for RoutingDonutAdapter class."""

    def test_read_model_preference_from_queue(self, tmp_path: Path) -> None:
        """Test reading model preference from queue file."""
        from thegent.utils.routing_impl.donut_adapter import RoutingDonutAdapter

        queue_path = tmp_path / "prompt_queue.jsonl"
        queue_path.write_text(
            json.dumps(
                {
                    "ts": "2026-02-16T00:00:00Z",
                    "prompt": "Test prompt",
                    "preferred_model": "claude-opus-4.6",
                }
            ).decode()
            + "\n"
        )

        adapter = RoutingDonutAdapter(queue_path=queue_path)
        preference = adapter.read_model_preference_from_queue()

        assert preference == "claude-opus-4.6"

    def test_read_model_preference_empty_queue(self, tmp_path: Path) -> None:
        """Test reading from non-existent queue returns None."""
        from thegent.utils.routing_impl.donut_adapter import RoutingDonutAdapter

        adapter = RoutingDonutAdapter(queue_path=tmp_path / "nonexistent.jsonl")
        preference = adapter.read_model_preference_from_queue()

        assert preference is None

    def test_record_request(self) -> None:
        """Test recording a routing request."""
        from thegent.utils.routing_impl.donut_adapter import RoutingDonutAdapter

        adapter = RoutingDonutAdapter()
        adapter.record_request(
            model="gpt-4o",
            provider="openai",
            category="normal",
            tokens=1000,
            cost_usd=0.01,
        )

        stats = adapter.get_stats()
        assert stats.total_requests == 1
        assert stats.requests_by_model["gpt-4o"] == 1
        assert stats.requests_by_provider["openai"] == 1
        assert stats.total_tokens == 1000
        assert stats.total_cost_usd == 0.01

    def test_harvest_on_stop(self, tmp_path: Path) -> None:
        """Test harvesting stats on stop."""
        from thegent.utils.routing_impl.donut_adapter import RoutingDonutAdapter

        harvest_path = tmp_path / "routing_harvest.jsonl"
        adapter = RoutingDonutAdapter(harvest_path=harvest_path)

        adapter.record_request("gpt-4o", "openai", "normal", 1000, 0.01)
        entry = adapter.harvest_on_stop()

        assert entry["type"] == "routing_harvest"
        assert entry["stats"]["total_requests"] == 1
        assert harvest_path.exists()

    def test_get_team_router_config(self) -> None:
        """Test getting team router config."""
        from thegent.utils.routing_impl.donut_adapter import RoutingDonutAdapter

        adapter = RoutingDonutAdapter()
        config = adapter.get_team_router_config()

        assert "policies" in config
        assert "cheapest" in config["policies"]
        assert "default_policy" in config
        assert "queue_path" in config
        assert "harvest_path" in config


class TestDonutAdapterGlobals:
    """Tests for global Donut adapter functions."""

    def test_get_donut_adapter_singleton(self) -> None:
        """Test that get_donut_adapter returns singleton."""
        from thegent.utils.routing_impl import donut_adapter

        donut_adapter._adapter = None
        adapter1 = donut_adapter.get_donut_adapter()
        adapter2 = donut_adapter.get_donut_adapter()
        assert adapter1 is adapter2
        donut_adapter._adapter = None


# ============================================================================
# Enhanced Router Tests
# ============================================================================


class TestContextWindowValidation:
    """Tests for context window validation."""

    def test_get_context_window_known_model(self) -> None:
        """Test getting context window for known models."""
        from thegent.utils.routing_impl.litellm_router import get_context_window

        assert get_context_window("claude-opus-4.6") == 200000
        assert get_context_window("gpt-4o") == 128000
        assert get_context_window("gemini-3-flash") == 1000000

    def test_get_context_window_unknown_model(self) -> None:
        """Test getting context window for unknown models returns default."""
        from thegent.utils.routing_impl.litellm_router import get_context_window

        assert get_context_window("unknown-model") == 8192  # Default

    def test_validate_context_window_within_limit(self) -> None:
        """Test validation when prompt fits."""
        from thegent.utils.routing_impl.litellm_router import validate_context_window

        # 5000 tokens should fit in any model's context window
        assert validate_context_window("gpt-4o", 5000)

    def test_validate_context_window_exceeds_limit(self) -> None:
        """Test validation when prompt exceeds limit."""
        from thegent.utils.routing_impl.litellm_router import validate_context_window

        # 500000 tokens exceeds gpt-4o's context (128K * 0.75 = 96K effective)
        assert not validate_context_window("gpt-4o", 500000)


class TestFallbackChains:
    """Tests for fallback chain building."""

    def test_build_fallback_chains(self) -> None:
        """Test that fallback chains are built correctly in LiteLLM format."""
        from thegent.utils.routing_impl.litellm_router import build_fallback_chains

        chains = build_fallback_chains()

        # Should return a list of dicts
        assert isinstance(chains, list)
        assert len(chains) > 0

        # Each entry should be a dict mapping model -> list of fallbacks
        for entry in chains:
            assert isinstance(entry, dict)
            for fallbacks in entry.values():
                assert isinstance(fallbacks, list)
                assert len(fallbacks) >= 1

        # Check specific model fallbacks exist
        model_names = [next(iter(entry.keys())) for entry in chains]
        assert "claude-opus-4.6" in model_names
        assert "deepseek-v3.2" in model_names


class TestRoutingResult:
    """Tests for RoutingResult dataclass."""

    def test_routing_result_defaults(self) -> None:
        """Test default values."""
        from thegent.utils.routing_impl.litellm_router import RoutingResult

        result = RoutingResult(success=True, model="gpt-4o", provider="openai")

        assert result.success is True
        assert result.response is None
        assert result.latency_ms == 0.0
        assert result.is_fallback is False
        assert result.is_cached is False


class TestRouterConfig:
    """Tests for RouterConfig dataclass."""

    def test_router_config_defaults(self) -> None:
        """Test default values."""
        from thegent.utils.routing_impl.litellm_router import RouterConfig

        config = RouterConfig()

        assert config.routing_policy == "cheapest"
        assert config.timeout == 300
        assert config.enable_cache is True
        assert config.cache_type == "in-memory"
        assert config.fallback_enabled is True


class TestEnhancedRouterGlobals:
    """Tests for global enhanced router functions."""

    def test_get_enhanced_router_singleton(self) -> None:
        """Test that get_enhanced_router returns singleton."""
        from thegent.utils.routing_impl import litellm_router

        # Mock the model list to avoid catalog dependency issues
        mock_model_list = [
            {
                "model_name": "gpt-4o",
                "litellm_params": {
                    "model": "openai/gpt-4o",
                    "api_key": "test-key",
                },
            }
        ]

        with patch.object(litellm_router, "build_litellm_model_list", return_value=mock_model_list):
            litellm_router.reset_enhanced_router()
            router1 = litellm_router.get_enhanced_router()
            router2 = litellm_router.get_enhanced_router()
            assert router1 is router2
            litellm_router.reset_enhanced_router()


# ============================================================================
# Config Enhanced Settings Tests
# ============================================================================


class TestLiteLLMEnhancedConfig:
    """Tests for enhanced LiteLLM configuration settings."""

    def test_litellm_enable_cache_default(self) -> None:
        """Test cache is enabled by default."""
        from thegent.config import ThegentSettings

        settings = ThegentSettings()
        assert settings.litellm_enable_cache is True

    def test_litellm_cache_type_default(self) -> None:
        """Test default cache type is in-memory."""
        from thegent.config import ThegentSettings

        settings = ThegentSettings()
        assert settings.litellm_cache_type == "in-memory"

    def test_litellm_cooldown_time_default(self) -> None:
        """Test default cooldown time."""
        from thegent.config import ThegentSettings

        settings = ThegentSettings()
        assert settings.litellm_cooldown_time == 60

    def test_litellm_enable_streaming_default(self) -> None:
        """Test streaming is enabled by default."""
        from thegent.config import ThegentSettings

        settings = ThegentSettings()
        assert settings.litellm_enable_streaming is True

    def test_litellm_enable_cost_tracking_default(self) -> None:
        """Test cost tracking is enabled by default."""
        from thegent.config import ThegentSettings

        settings = ThegentSettings()
        assert settings.litellm_enable_cost_tracking is True

    def test_litellm_cost_budget_default(self) -> None:
        """Test cost budget is None by default."""
        from thegent.config import ThegentSettings

        settings = ThegentSettings()
        assert settings.litellm_cost_budget is None

    def test_litellm_latency_threshold_default(self) -> None:
        """Test default latency threshold."""
        from thegent.config import ThegentSettings

        settings = ThegentSettings()
        assert settings.litellm_latency_threshold_ms == 500.0

    def test_litellm_context_window_validation_default(self) -> None:
        """Test context window validation is enabled by default."""
        from thegent.config import ThegentSettings

        settings = ThegentSettings()
        assert settings.litellm_context_window_validation is True

    def test_litellm_fallback_enabled_default(self) -> None:
        """Test fallback is enabled by default."""
        from thegent.config import ThegentSettings

        settings = ThegentSettings()
        assert settings.litellm_fallback_enabled is True
