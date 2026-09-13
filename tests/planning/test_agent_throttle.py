"""Tests for agent load management and auto-throttle in AutoLaunchSystem.

@trace FR-ALS-THROTTLE-001 -- get_active_agent_count: returns non-negative integer.
@trace FR-ALS-THROTTLE-002 -- check_agent_throttle: returns "ok" below warn threshold.
@trace FR-ALS-THROTTLE-003 -- check_agent_throttle: returns "warn" at/above warn threshold.
@trace FR-ALS-THROTTLE-004 -- check_agent_throttle: returns "throttle" at/above throttle threshold.
@trace FR-ALS-THROTTLE-005 -- check_agent_throttle: returns "hard_stop" at/above hard-stop threshold.
@trace FR-ALS-THROTTLE-006 -- _try_launch_next: aborts immediately on hard_stop.
@trace FR-ALS-THROTTLE-007 -- _try_launch_next: sleeps then aborts if still throttled after sleep.
@trace FR-ALS-THROTTLE-008 -- _try_launch_next: proceeds after warn.
@trace FR-ALS-THROTTLE-009 -- launch_batch: raises RuntimeError on hard_stop.
@trace FR-ALS-THROTTLE-010 -- launch_batch: raises RuntimeError on throttle.
@trace FR-ALS-THROTTLE-011 -- get_active_agent_count: merges registry pids with psutil scan.
@trace FR-ALS-THROTTLE-012 -- check_agent_throttle: uses explicit count arg (no psutil call).
@trace FR-ALS-THROTTLE-013 -- _try_launch_next: proceeds and re-checks after throttle sleep.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thegent.planning.auto_launch import (
    _ThrottleResult,
    check_agent_throttle,
    get_active_agent_count,
)

# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------


def _make_throttle_result(
    action: str, count: int = 0, limit: int = 20
) -> _ThrottleResult:
    return _ThrottleResult(
        action=action, count=count, limit=limit, message=f"test {action}"
    )


def _non_blocked_do_next() -> dict[str, object]:
    """Return a do_next payload that does NOT trip the pre-work hard gate."""
    return {
        "next_items": [],
        "count": 0,
        "sources_checked": [],
        "governance_blocked": False,
    }


# ---------------------------------------------------------------------------
# get_active_agent_count tests
# ---------------------------------------------------------------------------


class TestGetActiveAgentCount:
    """Unit tests for get_active_agent_count. @trace FR-ALS-THROTTLE-001"""

    # ps_impl is imported inside get_active_agent_count's function body so we
    # must patch it at the source module path.
    _PS_IMPL_PATH = "thegent.cli.commands.impl.ps_impl"

    def test_returns_non_negative_integer(self) -> None:  # @trace FR-ALS-THROTTLE-001
        """get_active_agent_count must always return a non-negative integer."""
        with (
            patch("thegent.cli.commands.impl.ps_impl", return_value=[]),
            patch("psutil.process_iter", return_value=[]),
        ):
            count = get_active_agent_count()
        assert isinstance(count, int)
        assert count >= 0

    def test_counts_running_sessions_with_live_pid(
        self,
    ) -> None:  # @trace FR-ALS-THROTTLE-011
        """Running sessions whose PID is alive are counted."""
        sessions = [
            {"status": "running", "pid": 1234},
            {"status": "running", "pid": 5678},
            {"status": "completed", "pid": 9999},
        ]
        with (
            patch("thegent.cli.commands.impl.ps_impl", return_value=sessions),
            patch("psutil.pid_exists", return_value=True),
            patch("psutil.process_iter", return_value=[]),
        ):
            count = get_active_agent_count()
        assert count == 2  # only the two "running" entries

    def test_excludes_dead_pids(self) -> None:  # @trace FR-ALS-THROTTLE-001
        """Sessions whose PID no longer exists are not counted."""
        sessions = [{"status": "running", "pid": 1111}]
        with (
            patch("thegent.cli.commands.impl.ps_impl", return_value=sessions),
            patch("psutil.pid_exists", return_value=False),
            patch("psutil.process_iter", return_value=[]),
        ):
            count = get_active_agent_count()
        assert count == 0

    def test_psutil_scan_adds_untracked_agents(
        self,
    ) -> None:  # @trace FR-ALS-THROTTLE-011
        """Agent processes found by psutil but not in registry are counted."""
        fake_proc = MagicMock()
        fake_proc.pid = 7777
        fake_proc.info = {"pid": 7777, "name": "claude", "cmdline": ["claude", "--bg"]}

        with (
            patch("thegent.cli.commands.impl.ps_impl", return_value=[]),
            patch("psutil.process_iter", return_value=[fake_proc]),
        ):
            count = get_active_agent_count()
        assert count == 1

    def test_no_double_count_when_pid_in_both_sources(
        self,
    ) -> None:  # @trace FR-ALS-THROTTLE-011
        """PIDs already counted from registry are not double-counted by psutil scan."""
        sessions = [{"status": "running", "pid": 2222}]
        fake_proc = MagicMock()
        fake_proc.pid = 2222
        fake_proc.info = {"pid": 2222, "name": "claude", "cmdline": ["claude"]}

        with (
            patch("thegent.cli.commands.impl.ps_impl", return_value=sessions),
            patch("psutil.pid_exists", return_value=True),
            patch("psutil.process_iter", return_value=[fake_proc]),
        ):
            count = get_active_agent_count()
        assert count == 1  # counted once only

    def test_ps_impl_exception_falls_back_to_psutil(
        self,
    ) -> None:  # @trace FR-ALS-THROTTLE-001
        """Registry errors are swallowed; psutil scan still provides a count."""
        fake_proc = MagicMock()
        fake_proc.pid = 3333
        fake_proc.info = {"pid": 3333, "name": "codex", "cmdline": ["codex"]}

        with (
            patch(
                "thegent.cli.commands.impl.ps_impl", side_effect=RuntimeError("db gone")
            ),
            patch("psutil.process_iter", return_value=[fake_proc]),
        ):
            count = get_active_agent_count()
        assert count == 1


# ---------------------------------------------------------------------------
# check_agent_throttle tests
# ---------------------------------------------------------------------------


class TestCheckAgentThrottle:
    """Unit tests for check_agent_throttle. @trace FR-ALS-THROTTLE-002--005,012"""

    def _call(
        self, count: int, warn: int = 20, throttle: int = 50, hard_stop: int = 80
    ) -> _ThrottleResult:
        """Helper: call check_agent_throttle with explicit count (no psutil)."""
        return check_agent_throttle(
            count=count, warn_at=warn, throttle_at=throttle, hard_stop_at=hard_stop
        )

    def test_below_warn_is_ok(self) -> None:  # @trace FR-ALS-THROTTLE-002
        result = self._call(count=0)
        assert result.action == "ok"

    def test_just_below_warn_is_ok(self) -> None:  # @trace FR-ALS-THROTTLE-002
        result = self._call(count=19)
        assert result.action == "ok"

    def test_at_warn_threshold_is_warn(self) -> None:  # @trace FR-ALS-THROTTLE-003
        result = self._call(count=20)
        assert result.action == "warn"
        assert result.count == 20
        assert result.limit == 20

    def test_above_warn_below_throttle_is_warn(
        self,
    ) -> None:  # @trace FR-ALS-THROTTLE-003
        result = self._call(count=35)
        assert result.action == "warn"

    def test_at_throttle_threshold_is_throttle(
        self,
    ) -> None:  # @trace FR-ALS-THROTTLE-004
        result = self._call(count=50)
        assert result.action == "throttle"
        assert result.count == 50

    def test_above_throttle_below_hard_stop_is_throttle(
        self,
    ) -> None:  # @trace FR-ALS-THROTTLE-004
        result = self._call(count=65)
        assert result.action == "throttle"

    def test_at_hard_stop_threshold_is_hard_stop(
        self,
    ) -> None:  # @trace FR-ALS-THROTTLE-005
        result = self._call(count=80)
        assert result.action == "hard_stop"
        assert result.count == 80

    def test_above_hard_stop_is_hard_stop(self) -> None:  # @trace FR-ALS-THROTTLE-005
        result = self._call(count=290)  # the load average incident
        assert result.action == "hard_stop"

    def test_explicit_count_skips_psutil(self) -> None:  # @trace FR-ALS-THROTTLE-012
        """Passing count= must not trigger psutil or registry calls."""
        with patch("thegent.planning.auto_launch.get_active_agent_count") as mock_count:
            result = check_agent_throttle(
                count=5, warn_at=20, throttle_at=50, hard_stop_at=80
            )
        mock_count.assert_not_called()
        assert result.action == "ok"

    def test_message_is_non_empty_string(self) -> None:  # @trace FR-ALS-THROTTLE-002
        for count in (0, 20, 50, 80):
            result = self._call(count=count)
            assert isinstance(result.message, str)
            assert len(result.message) > 0

    def test_result_count_matches_input(self) -> None:  # @trace FR-ALS-THROTTLE-012
        for count in (0, 19, 20, 49, 50, 79, 80, 290):
            result = self._call(count=count)
            assert result.count == count

    def test_custom_thresholds(self) -> None:  # @trace FR-ALS-THROTTLE-003
        """Non-default thresholds are respected."""
        result = check_agent_throttle(
            count=5, warn_at=3, throttle_at=7, hard_stop_at=10
        )
        assert result.action == "warn"
        result2 = check_agent_throttle(
            count=2, warn_at=3, throttle_at=7, hard_stop_at=10
        )
        assert result2.action == "ok"


# ---------------------------------------------------------------------------
# _try_launch_next integration tests (mocked AutoLaunchSystem)
# ---------------------------------------------------------------------------


class TestTryLaunchNextThrottle:
    """Integration-level tests for _try_launch_next throttle enforcement.
    AutoLaunchSystem is not fully constructed; we test the async method directly.
    @trace FR-ALS-THROTTLE-006--008,013
    """

    def _make_system(self) -> Any:
        """Create a minimal mock that exposes _try_launch_next as a real coroutine."""
        from thegent.planning.auto_launch import AutoLaunchSystem

        # Patch __init__ to avoid heavyweight component construction
        with patch.object(AutoLaunchSystem, "__init__", lambda self, *a, **kw: None):
            system = AutoLaunchSystem.__new__(AutoLaunchSystem)

        # Provide just enough attributes for _try_launch_next to function
        system.db = MagicMock()
        system.db.get_ready_items.return_value = []
        system.db.get_running_count.return_value = 0
        system.launch_batch = AsyncMock()
        return system

    def test_hard_stop_aborts_immediately(self) -> None:  # @trace FR-ALS-THROTTLE-006
        """_try_launch_next must abort and not call launch_batch when hard_stop."""
        system = self._make_system()

        with patch(
            "thegent.planning.auto_launch.check_agent_throttle",
            return_value=_make_throttle_result("hard_stop", count=80, limit=80),
        ):
            asyncio.get_event_loop().run_until_complete(system._try_launch_next())

        system.launch_batch.assert_not_called()

    def test_throttle_sleeps_then_aborts_if_still_throttled(
        self,
    ) -> None:  # @trace FR-ALS-THROTTLE-007
        """_try_launch_next sleeps then aborts if still throttled after sleep."""

        system = self._make_system()

        # Both calls to check_agent_throttle return "throttle"
        with (
            patch(
                "thegent.planning.auto_launch.check_agent_throttle",
                side_effect=[
                    _make_throttle_result("throttle", count=55, limit=50),
                    _make_throttle_result("throttle", count=55, limit=50),
                ],
            ),
            patch("time.sleep") as mock_sleep,
            patch(
                "thegent.cli.commands.impl.do_next_impl",
                return_value=_non_blocked_do_next(),
            ),
        ):
            asyncio.get_event_loop().run_until_complete(system._try_launch_next())

        mock_sleep.assert_called_once()
        system.launch_batch.assert_not_called()

    def test_throttle_then_ok_after_sleep_proceeds(
        self,
    ) -> None:  # @trace FR-ALS-THROTTLE-013
        """_try_launch_next proceeds to launch_batch when throttle clears after sleep."""
        system = self._make_system()
        system.db.get_ready_items.return_value = [
            {"item_id": "ws-001", "prompt": "do stuff"}
        ]
        system.db.get_running_count.return_value = 0

        with (
            patch(
                "thegent.planning.auto_launch.check_agent_throttle",
                side_effect=[
                    _make_throttle_result("throttle", count=51, limit=50),
                    _make_throttle_result("ok", count=10, limit=20),
                ],
            ),
            patch("time.sleep"),
            patch(
                "thegent.planning.auto_launch.sample_resources",
                return_value=MagicMock(
                    cpu_count=4,
                    load_1m=0.5,
                    fd_used=50,
                    fd_limit=1024,
                    mem_rss_mb=200,
                    mem_available_mb=8000,
                ),
            ),
            patch(
                "thegent.planning.auto_launch.compute_dynamic_limit",
                return_value=(10, {}),
            ),
            patch(
                "thegent.cli.commands.impl.do_next_impl",
                return_value=_non_blocked_do_next(),
            ),
        ):
            asyncio.get_event_loop().run_until_complete(system._try_launch_next())

        system.launch_batch.assert_called_once()

    def test_warn_level_proceeds_without_sleep(
        self,
    ) -> None:  # @trace FR-ALS-THROTTLE-008
        """_try_launch_next logs a warning but does not sleep or abort on warn."""
        system = self._make_system()
        system.db.get_ready_items.return_value = [
            {"item_id": "ws-002", "prompt": "do more"}
        ]
        system.db.get_running_count.return_value = 0

        with (
            patch(
                "thegent.planning.auto_launch.check_agent_throttle",
                return_value=_make_throttle_result("warn", count=25, limit=20),
            ),
            patch("time.sleep") as mock_sleep,
            patch(
                "thegent.planning.auto_launch.sample_resources",
                return_value=MagicMock(
                    cpu_count=4,
                    load_1m=0.5,
                    fd_used=50,
                    fd_limit=1024,
                    mem_rss_mb=200,
                    mem_available_mb=8000,
                ),
            ),
            patch(
                "thegent.planning.auto_launch.compute_dynamic_limit",
                return_value=(10, {}),
            ),
            patch(
                "thegent.cli.commands.impl.do_next_impl",
                return_value=_non_blocked_do_next(),
            ),
        ):
            asyncio.get_event_loop().run_until_complete(system._try_launch_next())

        mock_sleep.assert_not_called()
        system.launch_batch.assert_called_once()


# ---------------------------------------------------------------------------
# launch_batch hard-stop / throttle tests
# ---------------------------------------------------------------------------


class TestLaunchBatchThrottle:
    """Tests that launch_batch raises RuntimeError on hard_stop and throttle.
    @trace FR-ALS-THROTTLE-009,010
    """

    def _make_system(self) -> Any:
        from thegent.planning.auto_launch import AutoLaunchSystem

        with patch.object(AutoLaunchSystem, "__init__", lambda self, *a, **kw: None):
            system = AutoLaunchSystem.__new__(AutoLaunchSystem)

        # Attach all attributes that launch_batch reads before the throttle check
        # (the check is the very first thing, so most are not reached on error)
        system.rbac_manager = MagicMock()
        system.rbac_manager.has_permission.return_value = True
        system.alert_fatigue = MagicMock()
        system.alert_fatigue.record_alert.return_value = False
        system.memory_manager = MagicMock()
        system.memory_manager.get_knowledge = AsyncMock(return_value=None)
        system.memory_manager.store_knowledge = AsyncMock()
        return system

    def test_hard_stop_raises_runtime_error(self) -> None:  # @trace FR-ALS-THROTTLE-009
        """launch_batch raises RuntimeError when hard_stop; message includes count."""
        system = self._make_system()

        # Use real check_agent_throttle with an explicit count at the hard-stop threshold
        # so the message is the real production message (contains "HARD STOP").
        async def _run():
            with patch(
                "thegent.planning.auto_launch.check_agent_throttle",
                return_value=check_agent_throttle(
                    count=80, warn_at=20, throttle_at=50, hard_stop_at=80
                ),
            ):
                await system.launch_batch([{"item_id": "x", "prompt": "p"}])

        with pytest.raises(RuntimeError, match="HARD STOP"):
            asyncio.get_event_loop().run_until_complete(_run())

    def test_throttle_raises_runtime_error(self) -> None:  # @trace FR-ALS-THROTTLE-010
        system = self._make_system()

        async def _run():
            with patch(
                "thegent.planning.auto_launch.check_agent_throttle",
                return_value=_make_throttle_result("throttle", count=55, limit=50),
            ):
                await system.launch_batch([{"item_id": "y", "prompt": "q"}])

        with pytest.raises(RuntimeError, match="throttle limit"):
            asyncio.get_event_loop().run_until_complete(_run())

    def test_ok_does_not_raise(self) -> None:  # @trace FR-ALS-THROTTLE-009
        """launch_batch must not raise on "ok" count; RBAC check may block instead."""
        system = self._make_system()
        # Make RBAC deny so we exit cleanly without needing full infrastructure
        system.rbac_manager.has_permission.return_value = False

        async def _run():
            with patch(
                "thegent.planning.auto_launch.check_agent_throttle",
                return_value=_make_throttle_result("ok", count=5, limit=20),
            ):
                await system.launch_batch([{"item_id": "z", "prompt": "r"}])

        # Should complete without raising
        asyncio.get_event_loop().run_until_complete(_run())
