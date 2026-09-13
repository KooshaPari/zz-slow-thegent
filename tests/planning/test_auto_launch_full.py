"""Comprehensive tests for thegent.planning.auto_launch module."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCheckAgentThrottle:
    """Tests for check_agent_throttle function."""

    def test_ok_when_count_zero(self) -> None:
        """Zero agents returns ok status."""
        from thegent.planning.auto_launch import check_agent_throttle

        result = check_agent_throttle(count=0)
        assert result.action == "ok"

    def test_ok_when_below_warn(self) -> None:
        """Count below warn threshold returns ok."""
        from thegent.planning.auto_launch import check_agent_throttle

        result = check_agent_throttle(count=10, warn_at=20)
        assert result.action == "ok"

    def test_warn_at_threshold(self) -> None:
        """Count at warn threshold returns warn."""
        from thegent.planning.auto_launch import check_agent_throttle

        result = check_agent_throttle(count=20, warn_at=20)
        assert result.action == "warn"

    def test_warn_above_threshold(self) -> None:
        """Count above warn but below throttle returns warn."""
        from thegent.planning.auto_launch import check_agent_throttle

        result = check_agent_throttle(count=30, warn_at=20, throttle_at=50)
        assert result.action == "warn"

    def test_throttle_at_threshold(self) -> None:
        """Count at throttle threshold returns throttle."""
        from thegent.planning.auto_launch import check_agent_throttle

        result = check_agent_throttle(count=50, warn_at=20, throttle_at=50)
        assert result.action == "throttle"

    def test_throttle_above_threshold(self) -> None:
        """Count above throttle but below hard_stop returns throttle."""
        from thegent.planning.auto_launch import check_agent_throttle

        result = check_agent_throttle(count=60, warn_at=20, throttle_at=50, hard_stop_at=80)
        assert result.action == "throttle"

    def test_hard_stop_at_threshold(self) -> None:
        """Count at hard_stop threshold returns hard_stop."""
        from thegent.planning.auto_launch import check_agent_throttle

        result = check_agent_throttle(count=80, warn_at=20, throttle_at=50, hard_stop_at=80)
        assert result.action == "hard_stop"

    def test_hard_stop_above_threshold(self) -> None:
        """Count above hard_stop returns hard_stop."""
        from thegent.planning.auto_launch import check_agent_throttle

        result = check_agent_throttle(count=100, warn_at=20, throttle_at=50, hard_stop_at=80)
        assert result.action == "hard_stop"

    def test_message_in_result(self) -> None:
        """Result includes a non-empty message."""
        from thegent.planning.auto_launch import check_agent_throttle

        result = check_agent_throttle(count=0)
        assert isinstance(result.message, str)
        assert len(result.message) > 0

    def test_count_and_limit_in_result(self) -> None:
        """Result includes correct count and limit."""
        from thegent.planning.auto_launch import check_agent_throttle

        result = check_agent_throttle(count=25, warn_at=20, throttle_at=50)
        assert result.count == 25
        assert result.limit == 20


class TestGetActiveAgentCount:
    """Tests for get_active_agent_count function."""

    def test_returns_non_negative(self) -> None:
        """Function returns non-negative integer."""
        from thegent.planning.auto_launch import get_active_agent_count

        with patch("thegent.cli.commands.impl.ps_impl", side_effect=Exception("mock")):
            with patch("psutil.process_iter", return_value=[]):
                count = get_active_agent_count()
        assert isinstance(count, int)
        assert count >= 0

    def test_empty_sessions_and_no_processes(self) -> None:
        """Zero sessions and zero processes returns zero."""
        from thegent.planning.auto_launch import get_active_agent_count

        with patch("thegent.cli.commands.impl.ps_impl", return_value=[]):
            with patch("psutil.process_iter", return_value=[]):
                count = get_active_agent_count()
        assert count == 0

    def test_ps_impl_exception_fallback(self) -> None:
        """Exception from ps_impl falls back to psutil."""
        from thegent.planning.auto_launch import get_active_agent_count

        fake_proc = MagicMock()
        fake_proc.pid = 1234
        fake_proc.info = {"pid": 1234, "name": "claude", "cmdline": ["claude"]}

        with patch("thegent.cli.commands.impl.ps_impl", side_effect=RuntimeError("error")):
            with patch("psutil.process_iter", return_value=[fake_proc]):
                count = get_active_agent_count()
        assert count == 1


class TestIsAgentProcess:
    """Tests for _is_agent_process helper."""

    def test_claude_agent_detected(self) -> None:
        """Process named 'claude' is detected as agent."""
        from thegent.planning.auto_launch import _is_agent_process

        assert _is_agent_process("claude", []) is True

    def test_codex_agent_detected(self) -> None:
        """Process named 'codex' is detected as agent."""
        from thegent.planning.auto_launch import _is_agent_process

        assert _is_agent_process("codex", []) is True

    def test_random_process_not_agent(self) -> None:
        """Random process is not detected as agent."""
        from thegent.planning.auto_launch import _is_agent_process

        assert _is_agent_process("firefox", []) is False

    def test_agent_cmdline_detected(self) -> None:
        """Process with agent cmdline keyword is detected."""
        from thegent.planning.auto_launch import _is_agent_process

        assert _is_agent_process("python", ["--bg"]) is True

    def test_run_agent_cmdline_detected(self) -> None:
        """Process with 'run-agent' cmdline is detected."""
        from thegent.planning.auto_launch import _is_agent_process

        assert _is_agent_process("python", ["run-agent"]) is True


class TestSampleResources:
    """Tests for sample_resources function."""

    def test_returns_resource_sample(self) -> None:
        """Function returns a ResourceSample."""
        from thegent.planning.auto_launch import sample_resources

        result = sample_resources()
        assert hasattr(result, "cpu_count")
        assert hasattr(result, "load_1m")
        assert hasattr(result, "fd_used")
        assert hasattr(result, "fd_limit")
        assert hasattr(result, "mem_rss_mb")
        assert hasattr(result, "mem_available_mb")

    def test_cpu_count_positive(self) -> None:
        """CPU count is positive."""
        from thegent.planning.auto_launch import sample_resources

        result = sample_resources()
        assert result.cpu_count >= 1


class TestComputeDynamicLimit:
    """Tests for compute_dynamic_limit function."""

    def test_returns_tuple(self) -> None:
        """Function returns tuple of (limit, metadata)."""
        from thegent.planning.auto_launch import _ResourceSample, compute_dynamic_limit

        resources = _ResourceSample(
            cpu_count=4,
            load_1m=0.5,
            fd_used=50,
            fd_limit=1024,
            mem_rss_mb=200,
            mem_available_mb=8000,
        )
        limit, metadata = compute_dynamic_limit(resources)
        assert isinstance(limit, int)
        assert isinstance(metadata, dict)

    def test_limit_within_bounds(self) -> None:
        """Limit is between 1 and 100."""
        from thegent.planning.auto_launch import _ResourceSample, compute_dynamic_limit

        resources = _ResourceSample(
            cpu_count=4,
            load_1m=0.5,
            fd_used=50,
            fd_limit=1024,
            mem_rss_mb=200,
            mem_available_mb=8000,
        )
        limit, _ = compute_dynamic_limit(resources)
        assert 1 <= limit <= 100

    def test_metadata_contains_factors(self) -> None:
        """Metadata contains factor values."""
        from thegent.planning.auto_launch import _ResourceSample, compute_dynamic_limit

        resources = _ResourceSample(
            cpu_count=4,
            load_1m=0.5,
            fd_used=50,
            fd_limit=1024,
            mem_rss_mb=200,
            mem_available_mb=8000,
        )
        _, metadata = compute_dynamic_limit(resources)
        assert "load_factor" in metadata
        assert "fd_factor" in metadata
        assert "mem_factor" in metadata
        assert "combined_factor" in metadata


class TestAutoLaunchSystemInit:
    """Tests for AutoLaunchSystem initialization."""

    def test_init_with_defaults(self) -> None:
        """System initializes with default None values."""
        from thegent.planning.auto_launch import AutoLaunchSystem

        system = AutoLaunchSystem()
        assert system.db is None
        assert system.rbac_manager is None

    def test_init_with_custom_values(self) -> None:
        """System initializes with provided values."""
        from thegent.planning.auto_launch import AutoLaunchSystem

        db = MagicMock()
        rbac = MagicMock()
        system = AutoLaunchSystem(db=db, rbac_manager=rbac)
        assert system.db is db
        assert system.rbac_manager is rbac


class TestAutoLaunchSystemRecordEvent:
    """Tests for AutoLaunchSystem.record_event method."""

    def test_record_event_does_not_raise(self) -> None:
        """record_event logs without raising."""
        from thegent.planning.auto_launch import AutoLaunchSystem

        system = AutoLaunchSystem()
        system.record_event("test_event", key="value")


class TestAutoLaunchSystemTryLaunchNext:
    """Tests for AutoLaunchSystem._try_launch_next method."""

    def test_hard_stop_aborts(self) -> None:
        """Hard stop status causes abort."""
        from thegent.planning.auto_launch import AutoLaunchSystem, _ThrottleResult

        system = AutoLaunchSystem()
        system.db = MagicMock()
        system.db.get_ready_items.return_value = []

        with patch(
            "thegent.planning.auto_launch.check_agent_throttle",
            return_value=_ThrottleResult("hard_stop", 80, 80, "hard stop"),
        ):
            asyncio.get_event_loop().run_until_complete(system._try_launch_next())

    def test_empty_ready_items_does_nothing(self) -> None:
        """No ready items means no launch."""
        from thegent.planning.auto_launch import AutoLaunchSystem, _ThrottleResult

        system = AutoLaunchSystem()
        system.db = MagicMock()
        system.db.get_ready_items.return_value = []
        system.launch_batch = AsyncMock()

        with patch(
            "thegent.planning.auto_launch.check_agent_throttle",
            return_value=_ThrottleResult("ok", 5, 20, "ok"),
        ):
            asyncio.get_event_loop().run_until_complete(system._try_launch_next())

        system.launch_batch.assert_not_called()


class TestAutoLaunchSystemLaunchBatch:
    """Tests for AutoLaunchSystem.launch_batch method."""

    def test_hard_stop_raises_runtime_error(self) -> None:
        """Hard stop raises RuntimeError."""
        from thegent.planning.auto_launch import AutoLaunchSystem, _ThrottleResult

        system = AutoLaunchSystem()
        system.rbac_manager = MagicMock()
        system.rbac_manager.has_permission.return_value = True
        system.alert_fatigue = MagicMock()

        with patch(
            "thegent.planning.auto_launch.check_agent_throttle",
            return_value=_ThrottleResult("hard_stop", 80, 80, "hard stop"),
        ):
            with pytest.raises(RuntimeError, match="HARD STOP"):
                asyncio.get_event_loop().run_until_complete(system.launch_batch([{"item_id": "x", "prompt": "p"}]))

    def test_throttle_raises_runtime_error(self) -> None:
        """Throttle raises RuntimeError."""
        from thegent.planning.auto_launch import AutoLaunchSystem, _ThrottleResult

        system = AutoLaunchSystem()
        system.rbac_manager = MagicMock()
        system.rbac_manager.has_permission.return_value = True
        system.alert_fatigue = MagicMock()

        with patch(
            "thegent.planning.auto_launch.check_agent_throttle",
            return_value=_ThrottleResult("throttle", 55, 50, "throttle"),
        ):
            with pytest.raises(RuntimeError, match="throttle limit"):
                asyncio.get_event_loop().run_until_complete(system.launch_batch([{"item_id": "x", "prompt": "p"}]))

    def test_rbac_denied_does_not_launch(self) -> None:
        """RBAC denial blocks launch."""
        from thegent.planning.auto_launch import AutoLaunchSystem, _ThrottleResult

        system = AutoLaunchSystem()
        system.rbac_manager = MagicMock()
        system.rbac_manager.has_permission.return_value = False
        system.rbac_manager._role_from_settings.return_value = MagicMock()
        system.alert_fatigue = MagicMock()
        system._launch_item = AsyncMock()

        with patch(
            "thegent.planning.auto_launch.check_agent_throttle",
            return_value=_ThrottleResult("ok", 5, 20, "ok"),
        ):
            asyncio.get_event_loop().run_until_complete(system.launch_batch([{"item_id": "x", "prompt": "p"}]))

        system._launch_item.assert_not_called()
