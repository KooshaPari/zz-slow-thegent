"""Adapter that implements ExecutionPort for agents.

This module bridges agents (which use ExecutionPort) to the CLI execution logic.
It isolates agents from direct CLI imports, breaking the circular dependency.
"""

from __future__ import annotations

import logging
from typing import Any

_logger = logging.getLogger(__name__)


class ExecutionPortAdapter:
    """Implements ExecutionPort for agent invocation without CLI imports."""

    def __init__(self) -> None:
        """Initialize the adapter. Lazy-loads CLI functions on first use."""
        self._run_impl: Any = None
        self._dag_status_impl: Any = None

    def _load_cli_run_impl(self) -> Any:
        """Lazy-load run_impl from CLI (called only when needed)."""
        if self._run_impl is None:
            try:
                # Import only when needed to avoid circular imports during module load
                from thegent.cli.commands.impl import run_impl as _run_impl_func
                self._run_impl = _run_impl_func
            except ImportError as e:
                _logger.error("Failed to load run_impl from CLI: %s", e)
                raise RuntimeError(
                    "ExecutionPort requires CLI to be installed; "
                    "ensure thegent.cli.commands.impl is available"
                ) from e
        return self._run_impl

    def _load_cli_dag_status(self) -> Any:
        """Lazy-load dag_status_impl from CLI."""
        if self._dag_status_impl is None:
            try:
                from thegent.cli.commands.impl import (
                    dag_status_impl as _dag_status_func,
                )
                self._dag_status_impl = _dag_status_func
            except ImportError as e:
                _logger.error("Failed to load dag_status_impl from CLI: %s", e)
                raise RuntimeError(
                    "ExecutionPort requires CLI to be installed; "
                    "ensure thegent.cli.commands.impl is available"
                ) from e
        return self._dag_status_impl

    def run_task(
        self,
        agent: str | None = None,
        prompt: str = "",
        cd: str = "",
        mode: str = "write",
        timeout: int = 300,
        model: str | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Execute a task via CLI's run_impl (lazy-loaded).

        Args:
            agent: Agent name
            prompt: Task prompt
            cd: Working directory
            mode: Execution mode
            timeout: Timeout
            model: Model override
            provider: Provider override

        Returns:
            Result dict
        """
        run_impl = self._load_cli_run_impl()
        result = run_impl(
            agent=agent,
            prompt=prompt,
            cd=cd,
            mode=mode,
            timeout=timeout,
            model=model,
            provider=provider,
        )
        return result if isinstance(result, dict) else {"output": str(result)}

    def get_dag_status(self, cd: str = "") -> dict[str, Any]:
        """Get current DAG/WBS status via CLI's dag_status_impl.

        Args:
            cd: Working directory

        Returns:
            Status dict
        """
        dag_status_impl = self._load_cli_dag_status()
        result = dag_status_impl(cd)
        return result if isinstance(result, dict) else {"status": "unknown"}


# Global singleton instance used by agents
_execution_port: ExecutionPortAdapter | None = None


def get_execution_port() -> ExecutionPortAdapter:
    """Get or create the global ExecutionPort adapter."""
    global _execution_port
    if _execution_port is None:
        _execution_port = ExecutionPortAdapter()
    return _execution_port


def set_execution_port(port: ExecutionPortAdapter | None) -> None:
    """Override the execution port (for testing)."""
    global _execution_port
    _execution_port = port


__all__ = [
    "ExecutionPortAdapter",
    "get_execution_port",
    "set_execution_port",
]
