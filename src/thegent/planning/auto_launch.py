"""Auto-launch system for managing agent startup and throttle enforcement."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class _ThrottleResult:
    """Result of an agent throttle check."""
    action: str
    count: int
    limit: int
    message: str


def check_agent_throttle(
    count: int | None = None,
    warn_at: int = 20,
    throttle_at: int = 50,
    hard_stop_at: int = 80,
) -> _ThrottleResult:
    """Check agent throttle status based on current count and thresholds.

    Args:
        count: Current active agent count. If None, calls get_active_agent_count().
        warn_at: Threshold for warn action.
        throttle_at: Threshold for throttle action.
        hard_stop_at: Threshold for hard_stop action.

    Returns:
        _ThrottleResult with action, count, limit, and message.
    """
    if count is None:
        count = get_active_agent_count()

    if count >= hard_stop_at:
        return _ThrottleResult(
            action="hard_stop",
            count=count,
            limit=hard_stop_at,
            message=f"AGENT HARD STOP: {count} active agents (limit: {hard_stop_at}). No new agents will be started.",
        )
    elif count >= throttle_at:
        return _ThrottleResult(
            action="throttle",
            count=count,
            limit=throttle_at,
            message=f"Agent throttle limit reached: {count} active (limit: {throttle_at}). Consider waiting.",
        )
    elif count >= warn_at:
        return _ThrottleResult(
            action="warn",
            count=count,
            limit=warn_at,
            message=f"Agent warning: {count} active agents (warn at: {warn_at}).",
        )
    else:
        return _ThrottleResult(
            action="ok",
            count=count,
            limit=warn_at,
            message=f"Agent load OK: {count} active agents.",
        )


def get_active_agent_count() -> int:
    """Get the count of currently active agents.

    Merges count from session registry with psutil scan of untracked agent processes.

    Returns:
        Total count of active agents as non-negative integer.
    """
    count = 0
    tracked_pids: set[int] = set()

    try:
        from thegent.cli.commands.impl import ps_impl
        sessions = ps_impl()
        for session in sessions:
            if session.get("status") == "running":
                pid = session.get("pid")
                if pid:
                    import psutil
                    if psutil.pid_exists(pid):
                        tracked_pids.add(pid)
                        count += 1
    except Exception:
        pass

    try:
        import psutil
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                info = proc.info
                pid = info.get("pid")
                if pid and pid not in tracked_pids:
                    cmdline = info.get("cmdline") or []
                    name = info.get("name") or ""
                    if _is_agent_process(name, cmdline):
                        count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass

    return count


def _is_agent_process(name: str, cmdline: list[str]) -> bool:
    """Check if a process is an agent process."""
    agent_names = {"claude", "codex", "claude-code", "agent", "thegent"}
    agent_cmdline_keywords = {"--bg", "--agent", "run-agent", "agent-mode"}

    name_lower = name.lower()
    if any(agent_name in name_lower for agent_name in agent_names):
        return True

    return any(any(keyword in cmd for keyword in agent_cmdline_keywords) for cmd in cmdline)


@dataclass
class _ResourceSample:
    """Snapshot of system resources."""
    cpu_count: int
    load_1m: float
    fd_used: int
    fd_limit: int
    mem_rss_mb: float
    mem_available_mb: float


def sample_resources() -> _ResourceSample:
    """Sample current system resources.

    Returns:
        _ResourceSample with resource usage data.
    """
    import os

    import psutil

    try:
        cpu_count = psutil.cpu_count() or 1
        load_1m = os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.0

        process = psutil.Process()
        fd_used = process.num_fds() if hasattr(process, "num_fds") else 0

        try:
            with open("/proc/self/fd") as f:
                fd_limit = len(f.readlines())
        except Exception:
            fd_limit = 1024

        mem = psutil.virtual_memory()
        mem_rss_mb = mem.used / (1024 * 1024)
        mem_available_mb = mem.available / (1024 * 1024)

        return _ResourceSample(
            cpu_count=cpu_count,
            load_1m=load_1m,
            fd_used=fd_used,
            fd_limit=fd_limit,
            mem_rss_mb=mem_rss_mb,
            mem_available_mb=mem_available_mb,
        )
    except Exception:
        return _ResourceSample(
            cpu_count=1,
            load_1m=0.0,
            fd_used=0,
            fd_limit=1024,
            mem_rss_mb=0.0,
            mem_available_mb=0.0,
        )


def compute_dynamic_limit(resources: _ResourceSample) -> tuple[int, dict[str, Any]]:
    """Compute dynamic agent limit based on available resources.

    Args:
        resources: Current resource sample.

    Returns:
        Tuple of (limit, metadata_dict).
    """
    base_limit = 20

    load_factor = max(0.0, 1.0 - (resources.load_1m / resources.cpu_count))

    fd_ratio = resources.fd_used / max(resources.fd_limit, 1)
    fd_factor = max(0.0, 1.0 - fd_ratio)

    mem_ratio = resources.mem_rss_mb / max(resources.mem_rss_mb + resources.mem_available_mb, 1)
    mem_factor = max(0.0, 1.0 - mem_ratio)

    combined_factor = (load_factor + fd_factor + mem_factor) / 3.0

    limit = int(base_limit * combined_factor)
    limit = max(1, min(limit, 100))

    metadata = {
        "load_factor": load_factor,
        "fd_factor": fd_factor,
        "mem_factor": mem_factor,
        "combined_factor": combined_factor,
    }

    return limit, metadata


class AutoLaunchSystem:
    """System for auto-launching agents with throttle enforcement."""

    def __init__(
        self,
        db: Any | None = None,
        rbac_manager: Any | None = None,
        alert_fatigue: Any | None = None,
        memory_manager: Any | None = None,
        settings: Any | None = None,
    ) -> None:
        """Initialize the auto-launch system.

        Args:
            db: Database for workstream items.
            rbac_manager: RBAC manager for permission checks.
            alert_fatigue: Alert fatigue tracker.
            memory_manager: Memory/knowledge manager.
            settings: Application settings.
        """
        self.db = db
        self.rbac_manager = rbac_manager
        self.alert_fatigue = alert_fatigue
        self.memory_manager = memory_manager
        self.settings = settings

    def record_event(self, event_type: str, **kwargs: Any) -> None:
        """Record an event in the system.

        Args:
            event_type: Type of event to record.
            **kwargs: Additional event data.
        """
        logger.info(f"AutoLaunch event: {event_type}", extra=kwargs)

    async def _try_launch_next(self) -> None:
        """Try to launch the next ready work item.

        Checks governance gate and throttle status before launching.
        """
        # Pre-work hard-gate (WP-HG-05): if the do_next fallback is blocked
        # by governance, do not proceed to throttle or launch paths.
        try:
            from thegent.cli.commands.impl import do_next_impl
            do_next_result = do_next_impl()
        except Exception:
            do_next_result = None
        if isinstance(do_next_result, dict) and do_next_result.get("governance_blocked"):
            gate = (do_next_result.get("governance_block") or {}).get("gate")
            self.record_event("governance_blocked", gate=gate)
            return

        result = check_agent_throttle()

        if result.action == "hard_stop":
            self.record_event("throttle_hard_stop", count=result.count, limit=result.limit)
            return

        if result.action == "throttle":
            self.record_event("throttle_waiting", count=result.count, limit=result.limit)
            time.sleep(5)
            result = check_agent_throttle()
            if result.action in ("throttle", "hard_stop"):
                self.record_event("throttle_aborted", count=result.count)
                return

        if result.action == "warn":
            self.record_event("throttle_warn", count=result.count)

        if self.db is None:
            return

        ready_items = self.db.get_ready_items() if hasattr(self.db, "get_ready_items") else []
        if not ready_items:
            return

        running_count = self.db.get_running_count() if hasattr(self.db, "get_running_count") else 0

        resources = sample_resources()
        dynamic_limit, _ = compute_dynamic_limit(resources)

        if running_count >= dynamic_limit:
            self.record_event("dynamic_limit_reached", running=running_count, limit=dynamic_limit)
            return

        await self.launch_batch(ready_items[:1])

    async def _launch_item(
        self,
        item: dict[str, Any],
        lane: str,
        model: str,
        budget: float,
    ) -> None:
        """Launch a single work item.

        Args:
            item: Work item to launch.
            lane: Lane for the work item.
            model: Model to use.
            budget: Budget for the item.
        """
        try:
            from thegent.cli.commands.impl import bg_impl, work_stream_claim_impl

            claim_result = work_stream_claim_impl(item.get("item_id"), lane=lane)

            if not claim_result.get("success", False):
                if claim_result.get("governance_blocked"):
                    self.record_event("claim_failed", reason="governance_block")
                else:
                    self.record_event("claim_failed", reason=claim_result.get("error", "unknown"))
                return

            bg_result = bg_impl(item, model=model, budget=budget)
            self.record_event("item_launched", item_id=item.get("item_id"), result=bg_result)

        except Exception as e:
            self.record_event("launch_error", item_id=item.get("item_id"), error=str(e))

    async def launch_batch(self, items: list[dict[str, Any]]) -> None:
        """Launch a batch of work items.

        Args:
            items: List of work items to launch.

        Raises:
            RuntimeError: If throttle limit is reached.
        """
        result = check_agent_throttle()

        if result.action == "hard_stop":
            msg = f"HARD STOP: {result.count} active agents (limit: {result.limit}). Cannot launch batch."
            self.record_event("batch_hard_stop", count=result.count, limit=result.limit)
            raise RuntimeError(msg)

        if result.action == "throttle":
            msg = f"throttle limit reached: {result.count} active (limit: {result.limit}). Cannot launch batch."
            self.record_event("batch_throttled", count=result.count, limit=result.limit)
            raise RuntimeError(msg)

        if self.rbac_manager is not None:
            has_perm = self.rbac_manager.has_permission(
                self.rbac_manager._role_from_settings(),
                "run_agent",
            )
            if not has_perm:
                self.record_event("batch_blocked_rbac")
                return

        if self.alert_fatigue is not None:
            should_alert = self.alert_fatigue.record_alert("batch_launch")
            if not should_alert:
                self.record_event("batch_suppressed_alert_fatigue")
                return

        for item in items:
            await self._launch_item(
                item,
                lane=item.get("lane", "standard"),
                model=item.get("model", "gpt-4o-mini"),
                budget=item.get("budget", 0.01),
            )


__all__ = [
    "AutoLaunchSystem",
    "_ThrottleResult",
    "check_agent_throttle",
    "compute_dynamic_limit",
    "get_active_agent_count",
    "sample_resources",
]
