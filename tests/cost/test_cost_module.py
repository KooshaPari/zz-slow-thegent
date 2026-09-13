"""Unit tests for the cost/ module.

Tests aggregator.py, tracker.py, budget_alerts.py, cost_quality_optimization.py,
aggregators.py, and aggregator_controller.py.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thegent.cost.aggregator import CostAggregator, CostEstimator
from thegent.cost.aggregator_controller import BudgetTier, CostController, UsageSnapshot
from thegent.cost.aggregators import BudgetAlert as SimpleBudgetAlert
from thegent.cost.aggregators import CostCap, CostTracker
from thegent.cost.budget_alerts import BudgetAlertSystem, BudgetConfig
from thegent.cost.cost_quality_optimization import CostQualityOptimizer
from thegent.cost.tracker import CostEntry, RunCostTracker, get_run_cost_tracker

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# CostEstimator Tests
# ---------------------------------------------------------------------------


class TestCostEstimator:
    """Tests for CostEstimator."""

    def test_estimate_with_known_model(self) -> None:
        """Test cost estimation with a known model from pricing table."""
        estimator = CostEstimator()
        cost = estimator.estimate(model="claude-sonnet-4.5", tokens_total=1_000_000)
        assert cost == 3.00

    def test_estimate_with_tokens_only(self) -> None:
        """Test cost estimation using token count only."""
        estimator = CostEstimator()
        cost = estimator.estimate(tokens_total=1_000_000)
        assert cost == 2.00  # $2/MTok fallback

    def test_estimate_with_prompt_length_only(self) -> None:
        """Test cost estimation using prompt length fallback."""
        estimator = CostEstimator()
        cost = estimator.estimate(prompt_length=1000)
        expected = ((1000 * 1.5 + 500) / 1_000_000.0) * 2.0
        assert cost == expected

    def test_estimate_zero_tokens_and_prompt(self) -> None:
        """Test estimation with zero tokens and prompt returns fallback."""
        estimator = CostEstimator()
        cost = estimator.estimate(model="unknown-model", tokens_total=0, prompt_length=0)
        expected = (500 / 1_000_000.0) * 2.0
        assert cost == expected

    def test_estimate_with_metadata_pricing(self) -> None:
        """Test estimation falls back to metadata pricing."""
        estimator = CostEstimator()

        with patch("thegent.cost.aggregator.get_model_metadata") as mock_meta:
            mock_meta.return_value = {"cost_per_mtok": 5.0}
            cost = estimator.estimate(model="test-model", tokens_total=1_000_000)
            assert cost == 5.00

    def test_estimate_metadata_failure_fallback(self) -> None:
        """Test estimation falls back when metadata lookup fails."""
        estimator = CostEstimator()

        with patch("thegent.cost.aggregator.get_model_metadata") as mock_meta:
            mock_meta.side_effect = Exception("Metadata unavailable")
            cost = estimator.estimate(model="unknown", tokens_total=1_000_000)
            assert cost == 2.00  # Falls back to $2/MTok

    def test_estimate_unknown_model_uses_fallback(self) -> None:
        """Test unknown model uses fallback pricing."""
        estimator = CostEstimator()
        cost = estimator.estimate(model="completely-unknown-model", tokens_total=500_000)
        assert cost == 2.00  # $2/MTok fallback

    def test_estimate_case_sensitive_pricing(self) -> None:
        """Test case-sensitive model pricing lookup."""
        estimator = CostEstimator()
        cost_lower = estimator.estimate(model="minimax-m2.5", tokens_total=1_000_000)
        cost_upper = estimator.estimate(model="MiniMax-M2.5", tokens_total=1_000_000)
        assert cost_lower == cost_upper == 0.40


# ---------------------------------------------------------------------------
# CostAggregator Tests
# ---------------------------------------------------------------------------


class TestCostAggregator:
    """Tests for CostAggregator."""

    def test_daily_total_no_registry(self, tmp_path: Path) -> None:
        """Test daily total returns 0 when registry doesn't exist."""
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("owner") == 0.0

    def test_daily_total_empty_registry(self, tmp_path: Path) -> None:
        """Test daily total returns 0 with empty registry."""
        registry = tmp_path / "run_registry.jsonl"
        registry.write_text("", encoding="utf-8")
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("owner") == 0.0

    def test_daily_total_with_valid_entries(self, tmp_path: Path) -> None:
        """Test daily total sums cost_usd from finish events."""
        registry = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC).isoformat()
        registry.write_text(
            json.dumps(
                {
                    "event": "finish",
                    "cost_usd": 1.5,
                    "ended_at_utc": now,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("owner") == 1.5

    def test_daily_total_excludes_old_entries(self, tmp_path: Path) -> None:
        """Test daily total excludes entries older than cutoff."""
        registry = tmp_path / "run_registry.jsonl"
        old_date = (datetime.now(UTC) - timedelta(days=5)).isoformat()
        registry.write_text(
            json.dumps(
                {
                    "event": "finish",
                    "cost_usd": 10.0,
                    "ended_at_utc": old_date,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("owner", days=1) == 0.0

    def test_daily_total_uses_timestamp_field(self, tmp_path: Path) -> None:
        """Test daily total falls back to timestamp field."""
        registry = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC).isoformat()
        registry.write_text(
            json.dumps(
                {
                    "event": "finish",
                    "cost_usd": 2.5,
                    "timestamp": now,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("owner") == 2.5

    def test_daily_total_ignores_non_finish_events(self, tmp_path: Path) -> None:
        """Test daily total ignores non-finish events."""
        registry = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC).isoformat()
        registry.write_text(
            json.dumps(
                {
                    "event": "start",
                    "cost_usd": 100.0,
                    "ended_at_utc": now,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("owner") == 0.0

    def test_daily_total_handles_invalid_json(self, tmp_path: Path) -> None:
        """Test daily total handles malformed JSON lines."""
        registry = tmp_path / "run_registry.jsonl"
        registry.write_text('{"event": "finish", "cost_usd": 1.0}\nnot-json\n', encoding="utf-8")
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("owner") == 1.0

    def test_daily_total_handles_missing_cost(self, tmp_path: Path) -> None:
        """Test daily total handles entries without cost_usd."""
        registry = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC).isoformat()
        registry.write_text(
            json.dumps(
                {
                    "event": "finish",
                    "ended_at_utc": now,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("owner") == 0.0

    def test_daily_total_negative_cost(self, tmp_path: Path) -> None:
        """Test daily total handles negative costs (refunds)."""
        registry = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC).isoformat()
        registry.write_text(
            json.dumps(
                {
                    "event": "finish",
                    "cost_usd": -5.0,
                    "ended_at_utc": now,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("owner") == -5.0

    def test_daily_total_multiple_entries(self, tmp_path: Path) -> None:
        """Test daily total sums multiple entries."""
        registry = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC).isoformat()
        registry.write_text(
            json.dumps({"event": "finish", "cost_usd": 1.0, "ended_at_utc": now}) + "\n",
            encoding="utf-8",
        )
        registry.open("a", encoding="utf-8").write(
            json.dumps({"event": "finish", "cost_usd": 2.0, "ended_at_utc": now}) + "\n"
        )
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("owner") == 3.0

    def test_mtd_total_no_registry(self, tmp_path: Path) -> None:
        """Test MTD total returns 0 when registry doesn't exist."""
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.get_mtd_total() == 0.0

    def test_mtd_total_current_month_only(self, tmp_path: Path) -> None:
        """Test MTD total only includes current month."""
        registry = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC)
        current_month = now.strftime("%Y-%m")
        last_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

        registry.write_text(
            json.dumps(
                {
                    "event": "finish",
                    "cost_usd": 5.0,
                    "ended_at_utc": f"{current_month}-15T00:00:00+00:00",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        registry.open("a", encoding="utf-8").write(
            json.dumps(
                {
                    "event": "finish",
                    "cost_usd": 10.0,
                    "ended_at_utc": f"{last_month}-15T00:00:00+00:00",
                }
            )
            + "\n"
        )
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.get_mtd_total() == 5.0

    def test_category_mtd_total(self, tmp_path: Path) -> None:
        """Test category MTD total filters by task_category."""
        registry = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC)
        current_month = now.strftime("%Y-%m")

        registry.write_text(
            json.dumps(
                {
                    "event": "finish",
                    "cost_usd": 3.0,
                    "task_category": "fast",
                    "ended_at_utc": f"{current_month}-15T00:00:00+00:00",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        registry.open("a", encoding="utf-8").write(
            json.dumps(
                {
                    "event": "finish",
                    "cost_usd": 7.0,
                    "task_category": "complex",
                    "ended_at_utc": f"{current_month}-16T00:00:00+00:00",
                }
            )
            + "\n"
        )
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.get_category_mtd_total("fast") == 3.0
        assert agg.get_category_mtd_total("complex") == 7.0

    def test_category_mtd_case_insensitive(self, tmp_path: Path) -> None:
        """Test category MTD is case-insensitive."""
        registry = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC)
        current_month = now.strftime("%Y-%m")

        registry.write_text(
            json.dumps(
                {
                    "event": "finish",
                    "cost_usd": 4.0,
                    "task_category": "FAST",
                    "ended_at_utc": f"{current_month}-15T00:00:00+00:00",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.get_category_mtd_total("fast") == 4.0

    def test_all_categories_mtd(self, tmp_path: Path) -> None:
        """Test all categories MTD returns dict for all categories."""
        agg = CostAggregator(session_dir=tmp_path)
        result = agg.get_all_categories_mtd()
        assert isinstance(result, dict)
        assert set(result.keys()) == {"fast", "normal", "complex", "high_complex"}


# ---------------------------------------------------------------------------
# CostEntry and RunCostTracker Tests
# ---------------------------------------------------------------------------


class TestCostEntry:
    """Tests for CostEntry dataclass."""

    def test_cost_entry_creation(self) -> None:
        """Test basic CostEntry creation."""
        entry = CostEntry(
            timestamp="2024-01-01T00:00:00Z",
            provider="openai",
            model="gpt-4",
            input_tokens=100,
            output_tokens=200,
            cost_usd=0.01,
            run_id="run-123",
        )
        assert entry.provider == "openai"
        assert entry.cost_usd == 0.01
        assert entry.task_id is None

    def test_cost_entry_with_task_id(self) -> None:
        """Test CostEntry with optional task_id."""
        entry = CostEntry(
            timestamp="2024-01-01T00:00:00Z",
            provider="anthropic",
            model="claude-3",
            input_tokens=500,
            output_tokens=1000,
            cost_usd=0.05,
            run_id="run-456",
            task_id="task-789",
        )
        assert entry.task_id == "task-789"


class TestRunCostTracker:
    """Tests for RunCostTracker."""

    def test_init_creates_cost_dir(self, tmp_path: Path) -> None:
        """Test tracker creates cost directory on init."""
        RunCostTracker(cost_dir=tmp_path)
        assert tmp_path.exists()
        assert tmp_path.is_dir()

    def test_start_run(self, tmp_path: Path) -> None:
        """Test starting a new run."""
        tracker = RunCostTracker(cost_dir=tmp_path)
        tracker.start_run("run-123")
        assert tracker.current_run == "run-123"
        assert tracker.run_entries == []

    def test_record_entry(self, tmp_path: Path) -> None:
        """Test recording cost entries."""
        tracker = RunCostTracker(cost_dir=tmp_path)
        tracker.start_run("run-123")
        entry = CostEntry(
            timestamp="2024-01-01T00:00:00Z",
            provider="openai",
            model="gpt-4",
            input_tokens=100,
            output_tokens=200,
            cost_usd=0.01,
            run_id="run-123",
        )
        tracker.record_entry(entry)
        assert len(tracker.run_entries) == 1

    def test_end_run_without_active_run(self, tmp_path: Path) -> None:
        """Test ending run without active run returns empty dict."""
        tracker = RunCostTracker(cost_dir=tmp_path)
        result = tracker.end_run()
        assert result == {}

    def test_end_run_with_entries(self, tmp_path: Path) -> None:
        """Test ending run aggregates and saves entries."""
        tracker = RunCostTracker(cost_dir=tmp_path)
        tracker.start_run("run-123")
        entry = CostEntry(
            timestamp="2024-01-01T00:00:00Z",
            provider="openai",
            model="gpt-4",
            input_tokens=100,
            output_tokens=200,
            cost_usd=0.01,
            run_id="run-123",
        )
        tracker.record_entry(entry)
        result = tracker.end_run()

        assert result["run_id"] == "run-123"
        assert result["total_cost_usd"] == 0.01
        assert result["total_input_tokens"] == 100
        assert result["total_output_tokens"] == 200
        assert tracker.current_run is None
        assert tracker.run_entries == []

    def test_end_run_multiple_entries(self, tmp_path: Path) -> None:
        """Test ending run with multiple entries sums costs."""
        tracker = RunCostTracker(cost_dir=tmp_path)
        tracker.start_run("run-456")
        entries = [
            CostEntry(
                timestamp="2024-01-01T00:00:00Z",
                provider="openai",
                model="gpt-4",
                input_tokens=100,
                output_tokens=200,
                cost_usd=0.01,
                run_id="run-456",
            ),
            CostEntry(
                timestamp="2024-01-01T00:00:01Z",
                provider="anthropic",
                model="claude-3",
                input_tokens=500,
                output_tokens=1000,
                cost_usd=0.05,
                run_id="run-456",
            ),
        ]
        for e in entries:
            tracker.record_entry(e)
        result = tracker.end_run()

        assert result["total_cost_usd"] == 0.06
        assert result["total_input_tokens"] == 600
        assert result["total_output_tokens"] == 1200
        assert "openai" in result["providers"]
        assert "anthropic" in result["providers"]

    def test_end_run_saves_files(self, tmp_path: Path) -> None:
        """Test end_run saves run summary and appends to aggregate."""
        tracker = RunCostTracker(cost_dir=tmp_path)
        tracker.start_run("run-789")
        entry = CostEntry(
            timestamp="2024-01-01T00:00:00Z",
            provider="openai",
            model="gpt-4",
            input_tokens=100,
            output_tokens=200,
            cost_usd=0.01,
            run_id="run-789",
        )
        tracker.record_entry(entry)
        tracker.end_run()

        run_file = tmp_path / "run-789.json"
        assert run_file.exists()

        aggregate_file = tmp_path / "aggregate.jsonl"
        assert aggregate_file.exists()

    def test_run_summary_format(self, tmp_path: Path) -> None:
        """Test run summary JSON structure."""
        tracker = RunCostTracker(cost_dir=tmp_path)
        tracker.start_run("run-test")
        entry = CostEntry(
            timestamp="2024-01-01T00:00:00Z",
            provider="openai",
            model="gpt-4",
            input_tokens=100,
            output_tokens=200,
            cost_usd=0.01,
            run_id="run-test",
        )
        tracker.record_entry(entry)
        result = tracker.end_run()

        assert "run_id" in result
        assert "total_cost_usd" in result
        assert "total_input_tokens" in result
        assert "total_output_tokens" in result
        assert "providers" in result
        assert "ended_at" in result

    def test_aggregate_by_model(self, tmp_path: Path) -> None:
        """Test costs are aggregated by model within provider."""
        tracker = RunCostTracker(cost_dir=tmp_path)
        tracker.start_run("run-models")
        entries = [
            CostEntry(
                timestamp="2024-01-01T00:00:00Z",
                provider="openai",
                model="gpt-4",
                input_tokens=100,
                output_tokens=200,
                cost_usd=0.01,
                run_id="run-models",
            ),
            CostEntry(
                timestamp="2024-01-01T00:00:01Z",
                provider="openai",
                model="gpt-4",
                input_tokens=150,
                output_tokens=300,
                cost_usd=0.015,
                run_id="run-models",
            ),
        ]
        for e in entries:
            tracker.record_entry(e)
        result = tracker.end_run()

        assert result["providers"]["openai"]["models"]["gpt-4"]["calls"] == 2
        assert result["providers"]["openai"]["models"]["gpt-4"]["cost_usd"] == 0.025


class TestGetRunCostTracker:
    """Tests for get_run_cost_tracker global function."""

    def test_returns_tracker_instance(self) -> None:
        """Test global function returns RunCostTracker instance."""
        tracker = get_run_cost_tracker()
        assert isinstance(tracker, RunCostTracker)

    def test_singleton_behavior(self) -> None:
        """Test global function returns same instance."""
        tracker1 = get_run_cost_tracker()
        tracker2 = get_run_cost_tracker()
        assert tracker1 is tracker2


# ---------------------------------------------------------------------------
# BudgetConfig Tests
# ---------------------------------------------------------------------------


class TestBudgetConfig:
    """Tests for BudgetConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = BudgetConfig()
        assert config.hourly_limit_usd == 10.0
        assert config.daily_limit_usd == 100.0
        assert config.run_limit_usd == 5.0
        assert config.warning_threshold == 0.8

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = BudgetConfig(
            hourly_limit_usd=20.0,
            daily_limit_usd=200.0,
            run_limit_usd=10.0,
            warning_threshold=0.9,
        )
        assert config.hourly_limit_usd == 20.0
        assert config.daily_limit_usd == 200.0
        assert config.run_limit_usd == 10.0
        assert config.warning_threshold == 0.9


# ---------------------------------------------------------------------------
# BudgetAlertSystem Tests
# ---------------------------------------------------------------------------


class TestBudgetAlertSystem:
    """Tests for BudgetAlertSystem."""

    def test_init_defaults(self, tmp_path: Path) -> None:
        """Test initialization with defaults."""
        system = BudgetAlertSystem(cost_dir=tmp_path)
        assert system.cost_dir == tmp_path
        assert isinstance(system.config, BudgetConfig)

    def test_init_with_custom_config(self, tmp_path: Path) -> None:
        """Test initialization with custom config."""
        config = BudgetConfig(hourly_limit_usd=50.0)
        system = BudgetAlertSystem(cost_dir=tmp_path, config=config)
        assert system.config.hourly_limit_usd == 50.0

    def test_from_settings(self, tmp_path: Path) -> None:
        """Test creating system from settings object."""
        settings = MagicMock()
        settings.budget_hourly_limit = 25.0
        settings.budget_daily_limit = 250.0
        settings.budget_run_limit = 12.5
        settings.budget_warning_threshold = 0.85

        system = BudgetAlertSystem.from_settings(settings)
        assert system.config.hourly_limit_usd == 25.0
        assert system.config.daily_limit_usd == 250.0
        assert system.config.run_limit_usd == 12.5
        assert system.config.warning_threshold == 0.85

    def test_from_settings_fallback_on_error(self, tmp_path: Path) -> None:
        """Test from_settings falls back when settings have invalid values."""
        settings = MagicMock()
        settings.budget_hourly_limit = "invalid"
        settings.budget_daily_limit = 200.0
        settings.budget_run_limit = 5.0
        settings.budget_warning_threshold = 0.8

        system = BudgetAlertSystem.from_settings(settings)
        assert system.config == BudgetConfig()

    def test_check_budget_ok(self, tmp_path: Path) -> None:
        """Test check_budget returns OK when under threshold."""
        config = BudgetConfig(warning_threshold=0.8)
        system = BudgetAlertSystem(cost_dir=tmp_path, config=config)
        level, blocking = system.check_budget(1.0, "run")
        assert level == "OK"
        assert blocking is False

    def test_check_budget_warn(self, tmp_path: Path) -> None:
        """Test check_budget returns WARN when at warning threshold."""
        config = BudgetConfig(run_limit_usd=10.0, warning_threshold=0.8)
        system = BudgetAlertSystem(cost_dir=tmp_path, config=config)
        level, blocking = system.check_budget(8.1, "run")
        assert level == "WARN"
        assert blocking is False

    def test_check_budget_block(self, tmp_path: Path) -> None:
        """Test check_budget returns BLOCK when at or over limit."""
        config = BudgetConfig(run_limit_usd=10.0)
        system = BudgetAlertSystem(cost_dir=tmp_path, config=config)
        level, blocking = system.check_budget(10.0, "run")
        assert level == "BLOCK"
        assert blocking is True

    def test_check_budget_over_limit(self, tmp_path: Path) -> None:
        """Test check_budget returns BLOCK when over limit."""
        config = BudgetConfig(daily_limit_usd=100.0)
        system = BudgetAlertSystem(cost_dir=tmp_path, config=config)
        level, blocking = system.check_budget(150.0, "daily")
        assert level == "BLOCK"
        assert blocking is True

    def test_check_budget_zero_limit(self, tmp_path: Path) -> None:
        """Test check_budget with zero limit."""
        config = BudgetConfig(run_limit_usd=0.0)
        system = BudgetAlertSystem(cost_dir=tmp_path, config=config)
        level, blocking = system.check_budget(0.0, "run")
        assert level == "BLOCK"
        assert blocking is True

    def test_check_budget_unknown_context(self, tmp_path: Path) -> None:
        """Test check_budget falls back to run_limit for unknown context."""
        config = BudgetConfig(run_limit_usd=5.0)
        system = BudgetAlertSystem(cost_dir=tmp_path, config=config)
        level, blocking = system.check_budget(6.0, "unknown")
        assert level == "BLOCK"
        assert blocking is True

    def test_get_hourly_spend_no_file(self, tmp_path: Path) -> None:
        """Test hourly spend returns 0 when file doesn't exist."""
        system = BudgetAlertSystem(cost_dir=tmp_path)
        assert system.get_hourly_spend() == 0.0

    def test_get_hourly_spend_with_entries(self, tmp_path: Path) -> None:
        """Test hourly spend sums recent entries."""
        aggregate = tmp_path / "aggregate.jsonl"
        now = datetime.now(UTC).isoformat()
        aggregate.write_text(
            json.dumps({"total_cost": 5.0, "timestamp": now}) + "\n",
            encoding="utf-8",
        )
        system = BudgetAlertSystem(cost_dir=tmp_path)
        assert system.get_hourly_spend() == 5.0

    def test_get_hourly_spend_excludes_old(self, tmp_path: Path) -> None:
        """Test hourly spend excludes entries older than 1 hour."""
        aggregate = tmp_path / "aggregate.jsonl"
        old_time = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        aggregate.write_text(
            json.dumps({"total_cost": 100.0, "timestamp": old_time}) + "\n",
            encoding="utf-8",
        )
        system = BudgetAlertSystem(cost_dir=tmp_path)
        assert system.get_hourly_spend() == 0.0

    def test_get_hourly_spend_handles_invalid_json(self, tmp_path: Path) -> None:
        """Test hourly spend handles malformed JSON."""
        aggregate = tmp_path / "aggregate.jsonl"
        now = datetime.now(UTC).isoformat()
        aggregate.write_text(
            json.dumps({"total_cost": 5.0, "timestamp": now}) + "\n" + "not-valid-json\n",
            encoding="utf-8",
        )
        system = BudgetAlertSystem(cost_dir=tmp_path)
        assert system.get_hourly_spend() == 5.0

    def test_get_daily_spend_no_file(self, tmp_path: Path) -> None:
        """Test daily spend returns 0 when file doesn't exist."""
        system = BudgetAlertSystem(cost_dir=tmp_path)
        assert system.get_daily_spend() == 0.0

    def test_get_daily_spend_with_entries(self, tmp_path: Path) -> None:
        """Test daily spend sums today's entries."""
        aggregate = tmp_path / "aggregate.jsonl"
        now = datetime.now(UTC).isoformat()
        aggregate.write_text(
            json.dumps({"total_cost": 10.0, "timestamp": now}) + "\n",
            encoding="utf-8",
        )
        system = BudgetAlertSystem(cost_dir=tmp_path)
        assert system.get_daily_spend() == 10.0

    def test_get_daily_spend_excludes_yesterday(self, tmp_path: Path) -> None:
        """Test daily spend excludes yesterday's entries."""
        aggregate = tmp_path / "aggregate.jsonl"
        yesterday = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        aggregate.write_text(
            json.dumps({"total_cost": 50.0, "timestamp": yesterday}) + "\n",
            encoding="utf-8",
        )
        system = BudgetAlertSystem(cost_dir=tmp_path)
        assert system.get_daily_spend() == 0.0

    def test_get_daily_spend_handles_invalid_json(self, tmp_path: Path) -> None:
        """Test daily spend handles malformed JSON."""
        aggregate = tmp_path / "aggregate.jsonl"
        now = datetime.now(UTC).isoformat()
        aggregate.write_text(
            json.dumps({"total_cost": 10.0, "timestamp": now}) + "\n" + "bad-json\n",
            encoding="utf-8",
        )
        system = BudgetAlertSystem(cost_dir=tmp_path)
        assert system.get_daily_spend() == 10.0


class TestBudgetAlertSystemAlias:
    """Tests for BudgetAlerts alias."""

    def test_budget_alerts_is_budget_alert_system(self) -> None:
        """Test BudgetAlerts is an alias for BudgetAlertSystem."""
        from thegent.cost.budget_alerts import BudgetAlerts

        assert BudgetAlerts is BudgetAlertSystem


# ---------------------------------------------------------------------------
# CostQualityOptimizer Tests
# ---------------------------------------------------------------------------


class TestCostQualityOptimizer:
    """Tests for CostQualityOptimizer."""

    def test_init(self) -> None:
        """Test optimizer initialization."""
        optimizer = CostQualityOptimizer()
        assert optimizer.models == {}
        assert optimizer.routing_history == []

    def test_register_model(self) -> None:
        """Test registering a model."""
        optimizer = CostQualityOptimizer()
        optimizer.register_model("gpt-4", cost_per_token=0.0001, quality_score=0.9)
        assert "gpt-4" in optimizer.models
        assert optimizer.models["gpt-4"]["cost_per_token"] == 0.0001
        assert optimizer.models["gpt-4"]["quality_score"] == 0.9

    def test_route_request_no_models(self) -> None:
        """Test routing with no registered models returns default."""
        optimizer = CostQualityOptimizer()
        result = optimizer.route_request(task_complexity=0.5)
        assert result == "default"

    def test_route_request_single_model(self) -> None:
        """Test routing with single model returns that model."""
        optimizer = CostQualityOptimizer()
        optimizer.register_model("gpt-4", cost_per_token=0.0001, quality_score=0.9)
        result = optimizer.route_request(task_complexity=0.5)
        assert result == "gpt-4"

    def test_route_request_filters_by_quality(self) -> None:
        """Test routing filters by quality threshold."""
        optimizer = CostQualityOptimizer()
        optimizer.register_model("cheap-model", cost_per_token=0.00001, quality_score=0.5)
        optimizer.register_model("good-model", cost_per_token=0.0001, quality_score=0.9)

        result = optimizer.route_request(task_complexity=0.5, quality_threshold=0.8)
        assert result == "good-model"

    def test_route_request_falls_back_when_no_match(self) -> None:
        """Test routing falls back to highest quality when no match."""
        optimizer = CostQualityOptimizer()
        optimizer.register_model("low-quality", cost_per_token=0.00001, quality_score=0.3)
        optimizer.register_model("medium-quality", cost_per_token=0.00005, quality_score=0.6)

        result = optimizer.route_request(task_complexity=0.5, quality_threshold=0.8)
        assert result in ("low-quality", "medium-quality")

    def test_route_request_respects_max_cost(self) -> None:
        """Test routing respects max cost constraint."""
        optimizer = CostQualityOptimizer()
        optimizer.register_model("expensive", cost_per_token=0.001, quality_score=0.95)
        optimizer.register_model("cheap", cost_per_token=0.0001, quality_score=0.8)

        result = optimizer.route_request(task_complexity=0.5, quality_threshold=0.5, max_cost=0.1)
        assert result == "cheap"

    def test_route_request_tracks_history(self) -> None:
        """Test routing records history."""
        optimizer = CostQualityOptimizer()
        optimizer.register_model("gpt-4", cost_per_token=0.0001, quality_score=0.9)
        optimizer.route_request(task_complexity=0.5, quality_threshold=0.7)
        assert len(optimizer.routing_history) == 1
        assert optimizer.routing_history[0]["model"] == "gpt-4"
        assert optimizer.routing_history[0]["task_complexity"] == 0.5

    def test_route_request_best_cost_quality_ratio(self) -> None:
        """Test routing selects best cost/quality ratio."""
        optimizer = CostQualityOptimizer()
        optimizer.register_model("efficient", cost_per_token=0.00005, quality_score=0.8)
        optimizer.register_model("inefficient", cost_per_token=0.0001, quality_score=0.8)
        optimizer.register_model("wasteful", cost_per_token=0.0002, quality_score=0.9)

        result = optimizer.route_request(task_complexity=0.5, quality_threshold=0.5)
        assert result == "efficient"

    def test_get_routing_stats_empty(self) -> None:
        """Test routing stats with no history."""
        optimizer = CostQualityOptimizer()
        stats = optimizer.get_routing_stats()
        assert stats == {}

    def test_get_routing_stats_with_history(self) -> None:
        """Test routing stats calculation."""
        optimizer = CostQualityOptimizer()
        optimizer.register_model("model-a", cost_per_token=0.0001, quality_score=0.9)
        optimizer.register_model("model-b", cost_per_token=0.00005, quality_score=0.8)

        optimizer.route_request(task_complexity=0.3, quality_threshold=0.5)
        optimizer.route_request(task_complexity=0.5, quality_threshold=0.5)
        optimizer.route_request(task_complexity=0.7, quality_threshold=0.5)

        stats = optimizer.get_routing_stats()
        assert stats["total_routes"] == 3
        assert stats["model_distribution"]["model-a"] == 1
        assert stats["model_distribution"]["model-b"] == 2


# ---------------------------------------------------------------------------
# Aggregators Tests (CostCap, CostTracker, SimpleBudgetAlert)
# ---------------------------------------------------------------------------


class TestCostCap:
    """Tests for CostCap."""

    def test_check_within_limit(self) -> None:
        """Test check returns True when under cap."""
        cap = CostCap(max_cost=10.0)
        assert cap.check(5.0) is True

    def test_check_at_limit(self) -> None:
        """Test check returns True when at cap."""
        cap = CostCap(max_cost=10.0)
        assert cap.check(10.0) is True

    def test_check_over_limit(self) -> None:
        """Test check returns False when over cap."""
        cap = CostCap(max_cost=10.0)
        assert cap.check(10.1) is False

    def test_check_zero_max(self) -> None:
        """Test check with zero max cost."""
        cap = CostCap(max_cost=0.0)
        assert cap.check(0.0) is True
        assert cap.check(0.1) is False

    def test_check_negative_cost(self) -> None:
        """Test check with negative cost (refund)."""
        cap = CostCap(max_cost=10.0)
        assert cap.check(-5.0) is True


class TestCostTracker:
    """Tests for CostTracker."""

    def test_start_session(self) -> None:
        """Test starting a session."""
        tracker = CostTracker()
        tracker.start_session("session-1")
        assert tracker.get_session_cost("session-1") == 0.0

    def test_record_cost(self) -> None:
        """Test recording costs."""
        tracker = CostTracker()
        tracker.start_session("session-1")
        tracker.record_cost("session-1", 5.0)
        assert tracker.get_session_cost("session-1") == 5.0

    def test_record_cost_multiple(self) -> None:
        """Test recording multiple costs."""
        tracker = CostTracker()
        tracker.start_session("session-1")
        tracker.record_cost("session-1", 5.0)
        tracker.record_cost("session-1", 3.0)
        assert tracker.get_session_cost("session-1") == 8.0

    def test_get_session_cost_unknown(self) -> None:
        """Test getting cost for unknown session."""
        tracker = CostTracker()
        assert tracker.get_session_cost("unknown") == 0.0

    def test_is_within_budget_true(self) -> None:
        """Test within budget check returns True."""
        tracker = CostTracker()
        tracker.start_session("session-1")
        tracker.record_cost("session-1", 5.0)
        assert tracker.is_within_budget("session-1", 10.0) is True

    def test_is_within_budget_false(self) -> None:
        """Test within budget check returns False."""
        tracker = CostTracker()
        tracker.start_session("session-1")
        tracker.record_cost("session-1", 15.0)
        assert tracker.is_within_budget("session-1", 10.0) is False

    def test_record_cost_negative(self) -> None:
        """Test recording negative cost (refund)."""
        tracker = CostTracker()
        tracker.start_session("session-1")
        tracker.record_cost("session-1", 10.0)
        tracker.record_cost("session-1", -3.0)
        assert tracker.get_session_cost("session-1") == 7.0


class TestSimpleBudgetAlert:
    """Tests for SimpleBudgetAlert."""

    def test_init_default_threshold(self) -> None:
        """Test default threshold."""
        alert = SimpleBudgetAlert()
        assert alert.threshold == 0.8

    def test_init_custom_threshold(self) -> None:
        """Test custom threshold."""
        alert = SimpleBudgetAlert(threshold=0.5)
        assert alert.threshold == 0.5

    def test_set_budget(self) -> None:
        """Test setting budget."""
        alert = SimpleBudgetAlert()
        alert.set_budget(100.0)
        assert alert._budget == 100.0

    def test_should_alert_above_threshold(self) -> None:
        """Test alert triggers above threshold."""
        alert = SimpleBudgetAlert(threshold=0.8)
        alert.set_budget(100.0)
        assert alert.should_alert(85.0) is True

    def test_should_alert_at_threshold(self) -> None:
        """Test alert triggers at threshold."""
        alert = SimpleBudgetAlert(threshold=0.8)
        alert.set_budget(100.0)
        assert alert.should_alert(80.0) is True

    def test_should_alert_below_threshold(self) -> None:
        """Test alert doesn't trigger below threshold."""
        alert = SimpleBudgetAlert(threshold=0.8)
        alert.set_budget(100.0)
        assert alert.should_alert(50.0) is False

    def test_should_alert_zero_budget(self) -> None:
        """Test alert doesn't trigger with zero budget."""
        alert = SimpleBudgetAlert(threshold=0.8)
        alert.set_budget(0.0)
        assert alert.should_alert(100.0) is False

    def test_should_alert_negative_budget(self) -> None:
        """Test alert doesn't trigger with negative budget."""
        alert = SimpleBudgetAlert(threshold=0.8)
        alert.set_budget(-10.0)
        assert alert.should_alert(50.0) is False


# ---------------------------------------------------------------------------
# AggregatorController Tests (BudgetTier, UsageSnapshot, CostController)
# ---------------------------------------------------------------------------


class TestBudgetTier:
    """Tests for BudgetTier enum."""

    def test_tier_values(self) -> None:
        """Test all tier values exist."""
        assert BudgetTier.NORMAL.value == "normal"
        assert BudgetTier.CAUTIOUS.value == "cautious"
        assert BudgetTier.RESTRICTED.value == "restricted"
        assert BudgetTier.HALTED.value == "halted"


class TestUsageSnapshot:
    """Tests for UsageSnapshot."""

    def test_default_values(self) -> None:
        """Test default usage snapshot."""
        snapshot = UsageSnapshot()
        assert snapshot.calls_used == 0
        assert snapshot.calls_limit == 20
        assert snapshot.per_dimension == {}
        assert snapshot.per_agent == {}

    def test_utilization_pct_calculation(self) -> None:
        """Test utilization percentage calculation."""
        snapshot = UsageSnapshot(calls_used=10, calls_limit=20)
        assert snapshot.utilization_pct == 50.0

    def test_utilization_pct_zero_limit(self) -> None:
        """Test utilization with zero limit returns 100."""
        snapshot = UsageSnapshot(calls_used=0, calls_limit=0)
        assert snapshot.utilization_pct == 100.0

    def test_utilization_pct_full(self) -> None:
        """Test full utilization."""
        snapshot = UsageSnapshot(calls_used=20, calls_limit=20)
        assert snapshot.utilization_pct == 100.0

    def test_utilization_pct_over(self) -> None:
        """Test over utilization."""
        snapshot = UsageSnapshot(calls_used=25, calls_limit=20)
        assert snapshot.utilization_pct == 125.0


class TestCostController:
    """Tests for CostController."""

    def test_init_default_values(self, tmp_path: Path) -> None:
        """Test controller initialization defaults."""
        controller = CostController(session_dir=tmp_path)
        assert controller._calls_used == 0
        assert controller._calls_limit == 20
        assert controller._tiers == {}

    def test_init_loads_health_targets(self, tmp_path: Path) -> None:
        """Test controller loads health targets."""
        health_file = tmp_path / "health_targets.json"
        health_file.write_text(
            json.dumps(
                {
                    "budget": {
                        "daily_agent_calls": 50,
                        "tiers": {"custom": "tier"},
                    }
                }
            ),
            encoding="utf-8",
        )
        controller = CostController(session_dir=tmp_path, health_targets_path=health_file)
        assert controller._calls_limit == 50

    def test_init_handles_missing_health_targets(self, tmp_path: Path) -> None:
        """Test controller handles missing health targets file."""
        controller = CostController(session_dir=tmp_path, health_targets_path=tmp_path / "nonexistent.json")
        assert controller._calls_limit == 20

    def test_record_call_increments_counters(self, tmp_path: Path) -> None:
        """Test recording a call increments all counters."""
        controller = CostController(session_dir=tmp_path)
        controller.record_call("dimension-a", "agent-x", cost_usd=0.05)
        assert controller._calls_used == 1
        assert controller._per_dimension["dimension-a"] == 1
        assert controller._per_agent["agent-x"] == 1

    def test_record_call_multiple(self, tmp_path: Path) -> None:
        """Test multiple call recording."""
        controller = CostController(session_dir=tmp_path)
        controller.record_call("dim-a", "agent-1")
        controller.record_call("dim-a", "agent-1")
        controller.record_call("dim-b", "agent-2")

        assert controller._calls_used == 3
        assert controller._per_dimension["dim-a"] == 2
        assert controller._per_dimension["dim-b"] == 1
        assert controller._per_agent["agent-1"] == 2
        assert controller._per_agent["agent-2"] == 1

    def test_get_today_usage(self, tmp_path: Path) -> None:
        """Test getting today's usage snapshot."""
        controller = CostController(session_dir=tmp_path)
        controller.record_call("dim-a", "agent-1")
        controller.record_call("dim-b", "agent-2")

        snapshot = controller.get_today_usage()
        assert snapshot.calls_used == 2
        assert snapshot.calls_limit == 20
        assert snapshot.per_dimension == {"dim-a": 1, "dim-b": 1}
        assert snapshot.per_agent == {"agent-1": 1, "agent-2": 1}

    def test_get_tier_normal(self, tmp_path: Path) -> None:
        """Test NORMAL tier at low utilization."""
        controller = CostController(session_dir=tmp_path)
        for _ in range(5):
            controller.record_call("dim", "agent")
        assert controller.get_tier() == BudgetTier.NORMAL

    def test_get_tier_cautious(self, tmp_path: Path) -> None:
        """Test CAUTIOUS tier at 50%+ utilization."""
        controller = CostController(session_dir=tmp_path)
        for _ in range(12):
            controller.record_call("dim", "agent")
        assert controller.get_tier() == BudgetTier.CAUTIOUS

    def test_get_tier_restricted(self, tmp_path: Path) -> None:
        """Test RESTRICTED tier at 80%+ utilization."""
        controller = CostController(session_dir=tmp_path)
        for _ in range(17):
            controller.record_call("dim", "agent")
        assert controller.get_tier() == BudgetTier.RESTRICTED

    def test_get_tier_halted(self, tmp_path: Path) -> None:
        """Test HALTED tier at 95%+ utilization."""
        controller = CostController(session_dir=tmp_path)
        for _ in range(19):
            controller.record_call("dim", "agent")
        assert controller.get_tier() == BudgetTier.HALTED

    def test_calls_remaining(self, tmp_path: Path) -> None:
        """Test calls remaining calculation."""
        controller = CostController(session_dir=tmp_path)
        for _ in range(15):
            controller.record_call("dim", "agent")
        assert controller.calls_remaining() == 5

    def test_calls_remaining_at_limit(self, tmp_path: Path) -> None:
        """Test calls remaining at limit."""
        controller = CostController(session_dir=tmp_path)
        for _ in range(20):
            controller.record_call("dim", "agent")
        assert controller.calls_remaining() == 0

    def test_calls_remaining_over_limit(self, tmp_path: Path) -> None:
        """Test calls remaining doesn't go negative."""
        controller = CostController(session_dir=tmp_path)
        for _ in range(25):
            controller.record_call("dim", "agent")
        assert controller.calls_remaining() == 0

    def test_can_spawn_normal_tier(self, tmp_path: Path) -> None:
        """Test can_spawn returns True in NORMAL tier."""
        controller = CostController(session_dir=tmp_path)
        assert controller.can_spawn() is True

    def test_can_spawn_cautious_tier(self, tmp_path: Path) -> None:
        """Test can_spawn returns True in CAUTIOUS tier."""
        controller = CostController(session_dir=tmp_path)
        for _ in range(12):
            controller.record_call("dim", "agent")
        assert controller.can_spawn() is True

    def test_can_spawn_restricted_tier(self, tmp_path: Path) -> None:
        """Test can_spawn returns True in RESTRICTED tier."""
        controller = CostController(session_dir=tmp_path)
        for _ in range(17):
            controller.record_call("dim", "agent")
        assert controller.can_spawn() is True

    def test_can_spawn_halted_tier(self, tmp_path: Path) -> None:
        """Test can_spawn returns False in HALTED tier."""
        controller = CostController(session_dir=tmp_path)
        for _ in range(19):
            controller.record_call("dim", "agent")
        assert controller.can_spawn() is False

    def test_can_spawn_with_estimate(self, tmp_path: Path) -> None:
        """Test can_spawn with estimated calls."""
        controller = CostController(session_dir=tmp_path)
        for _ in range(18):
            controller.record_call("dim", "agent")
        assert controller.can_spawn(estimated_calls=2) is False
        assert controller.can_spawn(estimated_calls=1) is True


# ---------------------------------------------------------------------------
# Edge Case Tests
# ---------------------------------------------------------------------------


class TestCostEdgeCases:
    """Tests for edge cases across cost module."""

    def test_aggregator_handles_overflow_cost(self, tmp_path: Path) -> None:
        """Test aggregator handles very large costs."""
        registry = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC).isoformat()
        registry.write_text(
            json.dumps(
                {
                    "event": "finish",
                    "cost_usd": 1e15,
                    "ended_at_utc": now,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        agg = CostAggregator(session_dir=tmp_path)
        result = agg.daily_total("owner")
        assert result == 1e15

    def test_aggregator_handles_extreme_negative_cost(self, tmp_path: Path) -> None:
        """Test aggregator handles extreme negative costs."""
        registry = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC).isoformat()
        registry.write_text(
            json.dumps(
                {
                    "event": "finish",
                    "cost_usd": -1e15,
                    "ended_at_utc": now,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        agg = CostAggregator(session_dir=tmp_path)
        result = agg.daily_total("owner")
        assert result == -1e15

    def test_tracker_handles_zero_cost_entries(self, tmp_path: Path) -> None:
        """Test tracker handles zero-cost entries."""
        tracker = RunCostTracker(cost_dir=tmp_path)
        tracker.start_run("run-zero")
        entry = CostEntry(
            timestamp="2024-01-01T00:00:00Z",
            provider="free-provider",
            model="free-model",
            input_tokens=0,
            output_tokens=0,
            cost_usd=0.0,
            run_id="run-zero",
        )
        tracker.record_entry(entry)
        result = tracker.end_run()
        assert result["total_cost_usd"] == 0.0

    def test_tracker_handles_missing_provider_model(self, tmp_path: Path) -> None:
        """Test tracker handles entries with missing fields."""
        tracker = RunCostTracker(cost_dir=tmp_path)
        tracker.start_run("run-missing")

        entry_dict = {
            "timestamp": "2024-01-01T00:00:00Z",
            "provider": "",
            "model": "",
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "run_id": "run-missing",
        }
        entry = CostEntry(**entry_dict)
        tracker.record_entry(entry)
        result = tracker.end_run()
        assert result["total_cost_usd"] == 0.0
        assert "" in result["providers"]

    def test_budget_alert_zero_threshold(self, tmp_path: Path) -> None:
        """Test budget alert with zero threshold."""
        config = BudgetConfig(warning_threshold=0.0)
        system = BudgetAlertSystem(cost_dir=tmp_path, config=config)
        level, blocking = system.check_budget(0.01, "run")
        assert level == "WARN"
        assert blocking is False

    def test_budget_alert_full_threshold(self, tmp_path: Path) -> None:
        """Test budget alert with 100% threshold."""
        config = BudgetConfig(run_limit_usd=10.0, warning_threshold=1.0)
        system = BudgetAlertSystem(cost_dir=tmp_path, config=config)
        level, _blocking = system.check_budget(9.9, "run")
        assert level == "OK"
        level, _blocking = system.check_budget(10.0, "run")
        assert level == "BLOCK"

    def test_optimizer_handles_zero_quality(self) -> None:
        """Test optimizer handles zero quality score."""
        optimizer = CostQualityOptimizer()
        optimizer.register_model("zero-quality", cost_per_token=0.0001, quality_score=0.0)
        result = optimizer.route_request(task_complexity=0.5, quality_threshold=0.0)
        assert result == "zero-quality"

    def test_optimizer_handles_zero_cost(self) -> None:
        """Test optimizer handles zero cost."""
        optimizer = CostQualityOptimizer()
        optimizer.register_model("free", cost_per_token=0.0, quality_score=0.5)
        optimizer.register_model("paid", cost_per_token=0.001, quality_score=0.9)
        result = optimizer.route_request(task_complexity=0.5, quality_threshold=0.3)
        assert result == "free"

    def test_cost_controller_zero_limit_from_config(self, tmp_path: Path) -> None:
        """Test controller with zero daily calls limit from config."""
        health_file = tmp_path / "health_targets.json"
        health_file.write_text(
            json.dumps(
                {
                    "budget": {
                        "daily_agent_calls": 0,
                        "tiers": {},
                    }
                }
            ),
            encoding="utf-8",
        )
        controller = CostController(session_dir=tmp_path, health_targets_path=health_file)
        assert controller._calls_limit == 0
        assert controller.get_tier() == BudgetTier.HALTED

    def test_usage_snapshot_negative_calls(self) -> None:
        """Test usage snapshot with negative calls (edge case)."""
        snapshot = UsageSnapshot(calls_used=-5, calls_limit=20)
        assert snapshot.utilization_pct == -25.0
