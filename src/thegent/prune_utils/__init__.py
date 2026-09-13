"""STUB MODULE - thegent.prune_utils

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations


def is_agent_in_cmd(command: str) -> bool:
    """Check if an agent is referenced in a command."""
    return "agent" in command.lower()


# Stub implementation - functionality not available
__all__ = ["is_agent_in_cmd", "is_orphan_by_ppid"]


def is_orphan_by_ppid(ppid: int) -> bool:
    """Check if a process is an orphan based on parent PID."""
    return ppid == 1  # init/systemd process
