"""AUDIT-N+49: governance/cost_controller hardening spec (SOTA pass-33).

15 invariants FR-GOV-CC-001..015 covering CostController init,
record_call, get_today_usage, get_tier, can_spawn, calls_remaining,
and _persist.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Module-level import check
# ---------------------------------------------------------------------------


class TestModuleImport:
    """FR-GOV-CC-001: Module imports cleanly."""

    def test_import_cost_controller(self) -> None:
        from thegent.governance.cost_controller import CostController

        assert CostController is not None

    def test_import_budget_tier(self) -> None:
        from thegent.governance.cost_controller import BudgetTier

        assert BudgetTier.NORMAL == "normal"
        assert BudgetTier.HALTED == "halted"

    def test_import_daily_usage(self) -> None:
        from thegent.governance.cost_controller import DailyUsage

        usage = DailyUsage(date="2025-01-01")
        assert usage.calls_used == 0
        assert usage.calls_limit == 20


# ---------------------------------------------------------------------------
# Init & path-traversal guards
# ---------------------------------------------------------------------------


def _make_health_targets(tmp: Path, *, daily: int = 20, tiers: dict | None = None) -> Path:
    """Create a minimal health-targets.json for testing."""
    tiers = tiers or {
        "normal": {"max_utilization_pct": 50},
        "cautious": {"max_utilization_pct": 80},
        "restricted": {"max_utilization_pct": 95},
    }
    p = tmp / "health_targets.json"
    p.write_text(json.dumps({"budget": {"daily_agent_calls": daily, "tiers": tiers}}))
    return p


class TestInitGuards:
    """FR-GOV-CC-002: Path-traversal guard rejects relative paths."""

    def test_rejects_relative_session_dir(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path)
        with pytest.raises(ValueError, match="relative"):
            CostController(session_dir=Path("relative/path"), health_targets_path=ht)

    def test_rejects_relative_health_targets(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        with pytest.raises(ValueError, match="relative"):
            CostController(session_dir=tmp_path, health_targets_path=Path("relative/ht.json"))

    def test_accepts_absolute_paths(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        assert ctrl._daily_limit == 20


class TestInitConfig:
    """FR-GOV-CC-003: Config loading and tier parsing."""

    def test_loads_daily_limit(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path, daily=50)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        assert ctrl._daily_limit == 50

    def test_tiers_sorted_ascending(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import BudgetTier, CostController

        ht = _make_health_targets(tmp_path)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        pcts = [p for _, p in ctrl._tier_thresholds]
        assert pcts == sorted(pcts)
        names = [t for t, _ in ctrl._tier_thresholds]
        assert BudgetTier.NORMAL in names

    def test_missing_health_file_falls_back(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ctrl = CostController(
            session_dir=tmp_path,
            health_targets_path=tmp_path / "nonexistent.json",
        )
        # Should not raise; graceful fallback
        assert ctrl._daily_limit >= 0


class TestRecordCall:
    """FR-GOV-CC-004: record_call increments counters correctly."""

    def test_single_record(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        ctrl.record_call("dim-a", "agent-x")
        usage = ctrl.get_today_usage()
        assert usage.calls_used == 1
        assert usage.per_dimension["dim-a"] == 1
        assert usage.per_agent["agent-x"] == 1

    def test_multiple_records_same_dimension(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        ctrl.record_call("dim-a", "agent-1")
        ctrl.record_call("dim-a", "agent-1")
        ctrl.record_call("dim-b", "agent-2")
        usage = ctrl.get_today_usage()
        assert usage.calls_used == 3
        assert usage.per_dimension["dim-a"] == 2
        assert usage.per_dimension["dim-b"] == 1

    def test_record_with_cost_usd(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        # Should not raise with cost_usd kwarg
        ctrl.record_call("dim", "agent", cost_usd=0.05)
        assert ctrl.get_today_usage().calls_used == 1


class TestGetTodayUsage:
    """FR-GOV-CC-005: get_today_usage returns fresh DailyUsage."""

    def test_no_file_returns_fresh(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        usage = ctrl.get_today_usage()
        assert usage.calls_used == 0
        assert usage.calls_limit == 20

    def test_loads_from_jsonl(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path, daily=30)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        ctrl.record_call("d", "a")
        usage = ctrl.get_today_usage()
        assert usage.calls_used == 1
        assert usage.calls_limit == 30

    def test_corrupted_jsonl_returns_fresh(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        # Write garbage to the JSONL
        ctrl._usage_path.parent.mkdir(parents=True, exist_ok=True)
        ctrl._usage_path.write_text("NOT-JSON\n{broken\n")
        # Should gracefully return fresh usage
        usage = ctrl.get_today_usage()
        assert usage.calls_used == 0


class TestGetTier:
    """FR-GOV-CC-006: get_tier returns correct BudgetTier."""

    def test_normal_at_low_utilization(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import BudgetTier, CostController

        ht = _make_health_targets(tmp_path)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        for _ in range(5):
            ctrl.record_call("d", "a")
        assert ctrl.get_tier() == BudgetTier.NORMAL

    def test_halted_at_zero_limit(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import BudgetTier, CostController

        ht = _make_health_targets(tmp_path, daily=0)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        assert ctrl.get_tier() == BudgetTier.HALTED


class TestCanSpawn:
    """FR-GOV-CC-007: can_spawn returns correct boolean."""

    def test_can_spawn_when_not_halted(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        assert ctrl.can_spawn() is True

    def test_cannot_spawn_when_halted(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path, daily=0)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        assert ctrl.can_spawn() is False

    def test_can_spawn_insufficient_budget(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path, daily=2)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        ctrl.record_call("d", "a")
        ctrl.record_call("d", "a")
        assert ctrl.can_spawn(estimated_calls=1) is False


class TestCallsRemaining:
    """FR-GOV-CC-008: calls_remaining returns non-negative count."""

    def test_fresh_remaining(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path, daily=10)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        assert ctrl.calls_remaining() == 10

    def test_after_records(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path, daily=10)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        for _ in range(7):
            ctrl.record_call("d", "a")
        assert ctrl.calls_remaining() == 3

    def test_does_not_go_negative(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path, daily=3)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        for _ in range(10):
            ctrl.record_call("d", "a")
        assert ctrl.calls_remaining() == 0


class TestPersist:
    """FR-GOV-CC-009: _persist writes JSONL correctly."""

    def test_persists_and_reloads(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        ctrl.record_call("d", "a")
        # Verify file exists and has content
        assert ctrl._usage_path.exists()
        lines = ctrl._usage_path.read_text().strip().splitlines()
        assert len(lines) >= 1
        data = json.loads(lines[-1])
        assert data["calls_used"] == 1

    def test_preserves_other_days(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        # Manually write an old-day record
        ctrl._usage_dir.mkdir(parents=True, exist_ok=True)
        old_record = json.dumps({"date": "2020-01-01", "calls_used": 5, "calls_limit": 20})
        ctrl._usage_path.write_text(old_record + "\n")
        # Record a new call
        ctrl.record_call("d", "a")
        lines = ctrl._usage_path.read_text().strip().splitlines()
        # Old record should still be there
        dates = [json.loads(l)["date"] for l in lines]
        assert "2020-01-01" in dates


class TestTraceAnnotation:
    """FR-GOV-CC-010: Module has @trace AUDIT-N+44 annotations."""

    def test_module_docstring_has_trace(self) -> None:
        import thegent.governance.cost_controller as mod

        doc = mod.__doc__ or ""
        assert "AUDIT-N+49" in doc or "@trace" in doc or "FR-GOV-CC-" in doc


# ---------------------------------------------------------------------------
# DailyUsage model
# ---------------------------------------------------------------------------


class TestDailyUsageModel:
    """FR-GOV-CC-011: DailyUsage pydantic model."""

    def test_default_per_dimension(self) -> None:
        from thegent.governance.cost_controller import DailyUsage

        usage = DailyUsage(date="2025-06-01")
        assert usage.per_dimension == {}
        assert usage.per_agent == {}

    def test_custom_calls_limit(self) -> None:
        from thegent.governance.cost_controller import DailyUsage

        usage = DailyUsage(date="2025-06-01", calls_limit=50)
        assert usage.calls_limit == 50


class TestBudgetTierEnum:
    """FR-GOV-CC-012: BudgetTier enum coverage."""

    def test_all_tiers_exist(self) -> None:
        from thegent.governance.cost_controller import BudgetTier

        assert set(BudgetTier) == {
            BudgetTier.NORMAL,
            BudgetTier.CAUTIOUS,
            BudgetTier.RESTRICTED,
            BudgetTier.HALTED,
        }

    def test_tier_values_are_strings(self) -> None:
        from thegent.governance.cost_controller import BudgetTier

        for tier in BudgetTier:
            assert isinstance(tier.value, str)


class TestEdgeCases:
    """FR-GOV-CC-013..015: Edge cases and error handling."""

    def test_empty_tiers_config(self, tmp_path: Path) -> None:
        """Empty tiers dict in health targets produces no thresholds."""
        from thegent.governance.cost_controller import CostController

        p = tmp_path / "health_targets.json"
        p.write_text(json.dumps({"budget": {"daily_agent_calls": 20, "tiers": {}}}))
        ctrl = CostController(session_dir=tmp_path, health_targets_path=p)
        assert ctrl._tier_thresholds == []

    def test_malformed_json_falls_back_to_defaults(self, tmp_path: Path) -> None:
        """Malformed JSON in health targets triggers graceful fallback."""
        from thegent.governance.cost_controller import CostController

        ht = tmp_path / "bad.json"
        ht.write_text("{not valid json")
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        # Falls back to default 20/day
        assert ctrl._daily_limit == 20

    def test_usage_path_property(self, tmp_path: Path) -> None:
        from thegent.governance.cost_controller import CostController

        ht = _make_health_targets(tmp_path)
        ctrl = CostController(session_dir=tmp_path, health_targets_path=ht)
        assert ctrl.usage_path == ctrl._usage_path
        assert ctrl.usage_path.suffix == ".jsonl"
