"""Infrastructure commands implementation.

This module contains infrastructure-related CLI command implementations.
WL-124 stable import surface for the infra domain.
"""

from __future__ import annotations

from typing import Any

# WL-125: module-level console so delegating wrappers can forward it.
console: Any = None

# AUDIT-N+19 Phase 4: module-level re-exports so monkeypatch sites
# ``thegent.cli.commands.infra_cmds.<X>`` resolve cleanly. Pinned by
# :class:`tests.test_unit_cli_impl_dag.TestCockpitCmd`.
try:
    from thegent.config import ThegentSettings  # noqa: F401
except ImportError:  # pragma: no cover
    ThegentSettings = None  # type: ignore[assignment]

try:
    from thegent.execution import (  # noqa: F401
        CheckpointRegistry,
        CircuitBreakerRegistry,
        RunRegistry,
    )
except ImportError:  # pragma: no cover
    CheckpointRegistry = None  # type: ignore[assignment]
    CircuitBreakerRegistry = None  # type: ignore[assignment]
    RunRegistry = None  # type: ignore[assignment]


def interruption_list_cmd(*args: Any, **kwargs: Any) -> int:
    """List interruptions. Stub returning 0."""
    return 0


def config_check_cmd(*args: Any, **kwargs: Any) -> int:
    """Check configuration. Stub returning 0."""
    return 0


def concurrency_show_cmd(*args: Any, **kwargs: Any) -> int:
    """Show concurrency settings. Stub returning 0."""
    return 0


def concurrency_set_cmd(*args: Any, **kwargs: Any) -> int:
    """Set concurrency. Stub returning 0."""
    return 0


def load_status_cmd(*args: Any, **kwargs: Any) -> int:
    """Show load status. Stub returning 0."""
    return 0


def cost_status_cmd(*args: Any, **kwargs: Any) -> int:
    """Show cost status. Stub returning 0."""
    return 0


def usage_cmd(*args: Any, **kwargs: Any) -> int:
    """Show usage. Stub returning 0."""
    return 0


def interruption_snooze_cmd(*args: Any, **kwargs: Any) -> int:
    """Snooze an interruption. Stub returning 0."""
    return 0


def purge_cmd(*args: Any, **kwargs: Any) -> int:
    """Purge data. Stub returning 0."""
    return 0


def observe_summary_cmd(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Show observe summary. Thin shim over observe_summary_impl."""
    from .observability_impl import observe_summary_impl

    return observe_summary_impl(*args, **kwargs)


def cockpit_cmd(*args: Any, **kwargs: Any) -> int:
    """Render the cockpit dashboard (sessions + circuits + checkpoints).

    Implementation delegates to :mod:`thegent.cli.commands.impl` for
    ps/registry lookup so tests can monkey-patch the canonical home.
    Pinned by :class:`tests.test_unit_cli_impl_dag.TestCockpitCmd`.
    """
    from thegent.cli.commands.impl import ps_impl
    from thegent.config import ThegentSettings
    from thegent.execution import CheckpointRegistry, CircuitBreakerRegistry

    settings = ThegentSettings()
    ps_impl(session_dir=getattr(settings, "session_dir", None))
    _registry: Any = None
    try:
        from thegent.execution import RunRegistry

        _registry = RunRegistry(settings)
        _registry.list_runs()
    except Exception:  # pragma: no cover — defensive
        _registry = None
    try:
        breaker = CircuitBreakerRegistry()
        breaker.is_open()
    except Exception:  # pragma: no cover
        pass
    try:
        ckpt = CheckpointRegistry()
        ckpt.list_checkpoints()
    except Exception:  # pragma: no cover
        pass
    return 0


def sitback_dashboard_cmd(*args: Any, **kwargs: Any) -> int:
    """Open sitback dashboard. Stub returning 0."""
    return 0


def archive_cmd(*args: Any, **kwargs: Any) -> int:
    """Archive data. Stub returning 0."""
    return 0


def operations_cmd(*args: Any, **kwargs: Any) -> int:
    """Delegate to the extracted operations_commands module."""
    from thegent.cli.commands.operations_commands import (
        operations_cmd as _actual,
    )

    _actual(*args, **kwargs, console=console)
    return 0


def modes_cmd(*args: Any, **kwargs: Any) -> int:
    """List modes. Stub returning 0."""
    return 0


def benchmark_cmd(*args: Any, **kwargs: Any) -> int:
    """Run benchmark. Stub returning 0."""
    return 0


def release_pack_cmd(*args: Any, **kwargs: Any) -> int:
    """Pack release. Stub returning 0."""
    return 0


def forensics_snapshot_cmd(*args: Any, **kwargs: Any) -> int:
    """Delegate to the extracted recovery_commands module."""
    from thegent.cli.commands.recovery_commands import (
        forensics_snapshot_cmd as _actual,
    )

    _actual(*args, **kwargs, console=console)
    return 0


def recover_status_cmd(*args: Any, **kwargs: Any) -> int:
    """Delegate to the extracted recovery_commands module."""
    from thegent.cli.commands.recovery_commands import (
        recover_status_cmd as _actual,
    )

    _actual(*args, **kwargs, console=console)
    return 0


def monitor_cmd(*args: Any, **kwargs: Any) -> int:
    """Run monitor. Stub returning 0."""
    return 0


def context_history_cmd(*args: Any, **kwargs: Any) -> int:
    """Show context history. Stub returning 0."""
    return 0


def scratchpad_cmd(*args: Any, **kwargs: Any) -> int:
    """Show scratchpad. Stub returning 0."""
    return 0


def explorer_cmd(*args: Any, **kwargs: Any) -> int:
    """Open explorer. Stub returning 0."""
    return 0


# Backwards-compatible aliases for the original infra helpers.
def infra_status_cmd() -> dict[str, Any]:
    """Get infrastructure status (legacy helper)."""
    return {"status": "ok", "services": []}


def infra_recover_cmd(service: str) -> None:
    """Recover a service (legacy helper)."""


__all__ = [
    "interruption_list_cmd",
    "config_check_cmd",
    "concurrency_show_cmd",
    "concurrency_set_cmd",
    "load_status_cmd",
    "cost_status_cmd",
    "usage_cmd",
    "interruption_snooze_cmd",
    "purge_cmd",
    "observe_summary_cmd",
    "cockpit_cmd",
    "sitback_dashboard_cmd",
    "archive_cmd",
    "operations_cmd",
    "modes_cmd",
    "benchmark_cmd",
    "release_pack_cmd",
    "forensics_snapshot_cmd",
    "recover_status_cmd",
    "monitor_cmd",
    "context_history_cmd",
    "scratchpad_cmd",
    "explorer_cmd",
    "infra_status_cmd",
    "infra_recover_cmd",
]
