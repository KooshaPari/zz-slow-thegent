"""Tests for WL-072: Fix asyncio.run() per-tick in NeverIdleLoop.

Verifies that NeverIdleLoop uses a persistent event loop (Option C) instead of
creating and destroying one on every gardening tick via asyncio.run().

@trace WL-072
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch


class TestNeverIdleLoopPersistentEventLoop:
    """Verify WL-072: dedicated async event loop reused across gardening ticks.

    @trace WL-072
    """

    def _make_loop(
        self,
        session_dir: Path | None = None,
        project_root: Path | None = None,
        sleep_interval: int = 45,
    ) -> Any:
        """Construct a NeverIdleLoop with mocked sub-components."""
        from thegent.sitback.never_idle import NeverIdleLoop

        with (
            patch("thegent.sitback.never_idle.BackgroundTaskWatcher"),
            patch("thegent.sitback.never_idle.GardeningManager"),
        ):
            loop = NeverIdleLoop(
                session_dir=session_dir or Path("/tmp/test-sessions"),
                sleep_interval=sleep_interval,
                project_root=project_root or Path("/tmp"),
            )
        return loop

    def test_async_loop_created_at_init(self) -> None:
        """NeverIdleLoop creates a persistent asyncio event loop at init time.

        @trace WL-072
        """
        loop = self._make_loop()
        assert isinstance(loop._async_loop, asyncio.AbstractEventLoop)
        # Cleanup
        loop._async_loop.call_soon_threadsafe(loop._async_loop.stop)
        loop._async_thread.join(timeout=2)

    def test_async_thread_is_alive_at_init(self) -> None:
        """The dedicated async thread is running immediately after __init__.

        @trace WL-072
        """
        loop = self._make_loop()
        assert loop._async_thread.is_alive()
        # Cleanup
        loop._async_loop.call_soon_threadsafe(loop._async_loop.stop)
        loop._async_thread.join(timeout=2)

    def test_async_thread_is_daemon(self) -> None:
        """The dedicated async thread is a daemon thread (won't block process exit).

        @trace WL-072
        """
        loop = self._make_loop()
        assert loop._async_thread.daemon is True
        # Cleanup
        loop._async_loop.call_soon_threadsafe(loop._async_loop.stop)
        loop._async_thread.join(timeout=2)

    def test_run_once_does_not_call_asyncio_run(self) -> None:
        """_run_once() must NOT call asyncio.run() — the event loop is persistent.

        @trace WL-072
        """
        from thegent.sitback.never_idle import NeverIdleLoop

        mock_watcher = MagicMock()
        mock_watcher.run_once.return_value = []

        mock_result: dict[str, Any] = {"needs_attention": False}
        mock_gardening = MagicMock()
        mock_gardening.run_step = AsyncMock(return_value=mock_result)

        with (
            patch("thegent.sitback.never_idle.BackgroundTaskWatcher", return_value=mock_watcher),
            patch("thegent.sitback.never_idle.GardeningManager", return_value=mock_gardening),
            patch("asyncio.run") as mock_asyncio_run,
        ):
            nil = NeverIdleLoop(session_dir=Path("/tmp/s"), project_root=Path("/tmp"))
            nil._run_once()
            nil._async_loop.call_soon_threadsafe(nil._async_loop.stop)
            nil._async_thread.join(timeout=2)

        mock_asyncio_run.assert_not_called()

    def test_run_once_uses_run_coroutine_threadsafe(self) -> None:
        """_run_once() submits gardening step via run_coroutine_threadsafe.

        @trace WL-072
        """
        from thegent.sitback.never_idle import NeverIdleLoop

        mock_watcher = MagicMock()
        mock_watcher.run_once.return_value = []

        mock_result: dict[str, Any] = {"needs_attention": False}
        mock_gardening = MagicMock()
        mock_gardening.run_step = AsyncMock(return_value=mock_result)

        submitted_coros: list[Any] = []
        original_threadsafe = asyncio.run_coroutine_threadsafe

        def capturing_threadsafe(coro: Any, loop: Any) -> Any:
            submitted_coros.append(coro)
            return original_threadsafe(coro, loop)

        with (
            patch("thegent.sitback.never_idle.BackgroundTaskWatcher", return_value=mock_watcher),
            patch("thegent.sitback.never_idle.GardeningManager", return_value=mock_gardening),
            patch("asyncio.run_coroutine_threadsafe", side_effect=capturing_threadsafe),
        ):
            nil = NeverIdleLoop(session_dir=Path("/tmp/s"), project_root=Path("/tmp"))
            nil._run_once()
            nil._async_loop.call_soon_threadsafe(nil._async_loop.stop)
            nil._async_thread.join(timeout=2)

        assert len(submitted_coros) >= 1

    def test_same_event_loop_used_across_multiple_ticks(self) -> None:
        """The same event loop instance is reused on consecutive _run_once() calls.

        @trace WL-072
        """
        from thegent.sitback.never_idle import NeverIdleLoop

        mock_watcher = MagicMock()
        mock_watcher.run_once.return_value = []

        mock_result: dict[str, Any] = {"needs_attention": False}
        mock_gardening = MagicMock()
        mock_gardening.run_step = AsyncMock(return_value=mock_result)

        captured_loops: list[asyncio.AbstractEventLoop] = []
        original_threadsafe = asyncio.run_coroutine_threadsafe

        def capturing_threadsafe(coro: Any, loop: Any) -> Any:
            captured_loops.append(loop)
            return original_threadsafe(coro, loop)

        with (
            patch("thegent.sitback.never_idle.BackgroundTaskWatcher", return_value=mock_watcher),
            patch("thegent.sitback.never_idle.GardeningManager", return_value=mock_gardening),
            patch("asyncio.run_coroutine_threadsafe", side_effect=capturing_threadsafe),
        ):
            nil = NeverIdleLoop(session_dir=Path("/tmp/s"), project_root=Path("/tmp"))
            nil._run_once()
            nil._run_once()
            nil._run_once()
            nil._async_loop.call_soon_threadsafe(nil._async_loop.stop)
            nil._async_thread.join(timeout=2)

        # All three ticks used the exact same loop object
        assert len(captured_loops) == 3
        assert captured_loops[0] is captured_loops[1]
        assert captured_loops[1] is captured_loops[2]

    def test_gardening_step_result_stored_when_needs_attention(self) -> None:
        """_run_once() stores findings when run_step returns needs_attention=True.

        @trace WL-072
        """
        from thegent.sitback.never_idle import NeverIdleLoop

        mock_watcher = MagicMock()
        mock_watcher.run_once.return_value = []

        step_name = NeverIdleLoop.GARDENING_STEPS[0]
        mock_result: dict[str, Any] = {"needs_attention": True, "detail": "something bad"}
        mock_gardening = MagicMock()
        mock_gardening.run_step = AsyncMock(return_value=mock_result)

        with (
            patch("thegent.sitback.never_idle.BackgroundTaskWatcher", return_value=mock_watcher),
            patch("thegent.sitback.never_idle.GardeningManager", return_value=mock_gardening),
        ):
            nil = NeverIdleLoop(session_dir=Path("/tmp/s"), project_root=Path("/tmp"))
            nil._run_once()
            nil._async_loop.call_soon_threadsafe(nil._async_loop.stop)
            nil._async_thread.join(timeout=2)

        assert step_name in nil._findings
        assert nil._findings[step_name]["detail"] == "something bad"

    def test_stop_shuts_down_async_thread(self) -> None:
        """stop() terminates the persistent async thread cleanly.

        @trace WL-072
        """
        from thegent.sitback.never_idle import NeverIdleLoop

        mock_watcher = MagicMock()
        mock_watcher.run_once.return_value = []
        mock_gardening = MagicMock()
        mock_gardening.run_step = AsyncMock(return_value={"needs_attention": False})
        mock_gardening.get_summary.return_value = {}

        with (
            patch("thegent.sitback.never_idle.BackgroundTaskWatcher", return_value=mock_watcher),
            patch("thegent.sitback.never_idle.GardeningManager", return_value=mock_gardening),
        ):
            nil = NeverIdleLoop(session_dir=Path("/tmp/s"), project_root=Path("/tmp"), sleep_interval=1)
            nil.start()
            nil.stop()

        # After stop(), the async thread must have terminated
        nil._async_thread.join(timeout=3)
        assert not nil._async_thread.is_alive()

    def test_multiple_run_once_calls_advance_step_rotation(self) -> None:
        """Consecutive _run_once() calls rotate through gardening steps.

        @trace WL-072
        """
        from thegent.sitback.never_idle import NeverIdleLoop

        mock_watcher = MagicMock()
        mock_watcher.run_once.return_value = []
        mock_gardening = MagicMock()
        mock_gardening.run_step = AsyncMock(return_value={"needs_attention": False})

        with (
            patch("thegent.sitback.never_idle.BackgroundTaskWatcher", return_value=mock_watcher),
            patch("thegent.sitback.never_idle.GardeningManager", return_value=mock_gardening),
        ):
            nil = NeverIdleLoop(session_dir=Path("/tmp/s"), project_root=Path("/tmp"))
            nil._run_once()
            nil._run_once()
            nil._run_once()
            nil._async_loop.call_soon_threadsafe(nil._async_loop.stop)
            nil._async_thread.join(timeout=2)

        assert nil._current_step == 3 % len(NeverIdleLoop.GARDENING_STEPS)
